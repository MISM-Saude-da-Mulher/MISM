# Relatório de status — 19/09/2026

Fechamento do dia de trabalho (Claude + ChatGPT, mais de 24h de sessão
combinada). Este documento existe pra retomar amanhã sem precisar
reconstruir o contexto do zero.

## Onde as coisas estão

**`main`** no GitHub está em `e8fec3b` ("Adiciona comparação direta
entre municípios"). Branches extras que apareceram durante o dia e
ainda não foram limpos: `comparacao-municipios`,
`territorial-dados-estaduais`, `territorial-dados-pretest`,
`territorial-estadual`, `territorial-pretest` (provavelmente
experimentos/staging do ChatGPT — não investigados a fundo, não
parecem sessões ativas).

### O que foi construído e validado (Rio Claro, ponta a ponta)

- Bug de mistura Rio Claro + Estado de SP corrigido em 7 indicadores
  (`mortalidade`, `custos_hospitalares`, `permanencia_hospitalar`,
  `faixa_etaria`, `score_epidemiologico`, `anomalias`,
  `vulnerabilidade`) — testado com dados sintéticos mostrando a
  distorção real (ex.: taxa de mortalidade que parecia 3,6% e era
  30% de verdade).
- Correção do classificador de intenção do chat (ordem de
  `MUDANCA_TEMPORAL` vs `SITUACAO_GERAL` em `classificar_intencao`).
- Arquitetura territorial por código IBGE: tabela `municipios`,
  `configuracao_geografica.py` com `obter_municipio()` /
  `obter_codigo_ibge()` / `obter_nome_municipio()` /
  `listar_municipios_disponiveis()`.
- Todas as 13 tabelas derivadas viraram multi-tenant
  (`salvar_tabela_municipio()` / `ler_tabela_municipio()`) —
  processar um segundo município não apaga o primeiro. Provado com
  teste automatizado (`algoritimos/teste_territorial.py`, 16
  checagens A-J, todas passando com banco sintético).
- Textos fixos "Rio Claro" eliminados das respostas do chat, do
  relatório executivo e da base de conhecimento — tudo usa
  `obter_nome_municipio()` agora.
- Dashboard com seletor de município que realmente filtra os dados
  exibidos (e avisa quando o município escolhido ainda não foi
  processado, em vez de mostrar dado errado).

### O que outra fonte (ChatGPT, direto no `main`) construiu por cima

- `etl/criar_tabela_municipios.py` passou a baixar o catálogo
  oficial de municípios de SP da API do IBGE (~645 cidades, só
  metadado: código, nome, UF — nenhum dado de saúde).
- `etl/carga_todas_bases.py` passou a **desagregar o arquivo
  estadual de SP por município de residência** (usando a coluna
  `MUNIC_RES` que o DATASUS já inclui), gravando o resultado numa
  coluna nova `internacoes.municipio` (+ `codigo_ibge`). Ideia boa:
  os dados de todas as cidades de SP já estavam dentro do CSV
  estadual, nunca foi preciso baixar nada novo por cidade.
- Dashboard ganhou uma seção de "comparação direta entre
  municípios" (`e8fec3b`) que já usa essa coluna `municipio` nova.

## A aresta técnica pendente (atualizado — corrigida em parte sem eu perceber na hora)

**Correção sobre o que escrevi antes neste mesmo relatório:** ao
puxar o `main` mais recente para poder commitar este documento, vi
que o commit `c76dbe2` (do ChatGPT) já corrigiu boa parte do que eu
tinha apontado como pendente:

- `listar_municipios_disponiveis()` já faz `INNER JOIN` com
  `internacoes.municipio` (não mais `origem`) — corrigido.
- `mortalidade.py`, `custos_hospitalares.py`,
  `permanencia_hospitalar.py`, `faixa_etaria.py`,
  `score_epidemiologico.py` e `anomalias.py` já filtram
  `internacoes` por `municipio` — corrigido.
- `tendencia_estadual.py` ficou com um `UNION ALL`: a parte do
  município usa `municipio = ?`, a parte da referência estadual usa
  `origem = ?` (= `"SP"`) — isso está **certo de propósito**: a
  referência estadual precisa somar todas as linhas que vieram do
  arquivo estadual, não só as de um município dentro dele.

Rodei `py_compile` em tudo e `teste_territorial.py` de novo depois
da mesclagem: **16/16 checagens continuam passando**. As duas
frentes de trabalho (a minha e a do ChatGPT) se mostraram
compatíveis, pelo menos no que o teste cobre.

**O que realmente ainda falta corrigir:** só `vulnerabilidade.py`,
que continua filtrando `internacoes` por `origem = ?` em vez de
`municipio = ?`. É o único arquivo que ainda vai retornar vazio/errado
para qualquer cidade que não seja Rio Claro. Pequeno, isolado, mesma
correção que já foi aplicada nos outros 6.

## Próximo passo combinado: interface

Conversamos bastante sobre isso hoje, sem decidir nada — só
ideias. Resumo do que foi levantado, pra não perder:

### Personas identificadas (cada uma "entra" na ferramenta de um jeito diferente)

- **Gestor de uma cidade específica** (secretário de saúde,
  prefeito) — já sabe qual cidade quer, quer comparar com o Estado
  ou com cidades parecidas.
- **Pesquisador** — parte de uma pergunta/padrão, não de uma
  cidade; **vai fazer comparações entre cidades** (ponto que você
  destacou explicitamente).
- **Investidor** (ex.: decidir onde colocar um plano de saúde) —
  pensa em oportunidade/demanda, não em urgência de política
  pública. Ressalva importante: os dados são só de internações do
  SUS (sistema público), então não capturam quem já tem plano
  privado — isso precisa aparecer na interface se esse público for
  atendido.
- **População em geral** — já existe um modo de linguagem simples
  no chat; pensar se a interface nova preserva isso.

### Tensão em aberto (não decidida)

Interface principal deveria ser **conversa** (chat, escala bem em
variedade de pergunta, mas exige saber o que perguntar) ou
**navegação** (mapa/lista/busca, resolve "não sei o que existe", mas
não escala pra pergunta aberta)? Provável que a resposta seja "as
duas, uma como porta de entrada e outra como aprofundamento" — mas
qual é qual ainda não foi decidido.

### Ideias soltas levantadas (nenhuma escolhida ainda)

- Busca com autocomplete de cidade em vez de lista de 645 itens.
- Mapa de SP clicável, colorido por indicador.
- Seleção múltipla de cidades (checkboxes) + "cesta" de comparação
  salva entre perguntas.
- Tabela lado a lado, um município por coluna.
- Gráfico de dispersão (scatter) posicionando várias cidades de uma
  vez por dois indicadores.
- Comparação relativa a uma cidade-base ("+15% em relação a X") em
  vez de números absolutos soltos.
- Destacar visualmente quando um indicador comparado vem de amostra
  pequena (o selo de confiabilidade que já existe no texto).
- Exportação/CSV para o pesquisador levar a análise pra fora.
- Onboarding de uma pergunta ("você é gestor/pesquisador/outro?")
  que adapta o que aparece depois.
- Alertas proativos ("estas N cidades entraram em alerta esta
  semana") para quem não sabe o que perguntar.

## Visão de arquitetura para a interface (síntese do ChatGPT, discutida à noite)

Ideia central: **uma inteligência só, várias portas de entrada**, não
cinco sistemas separados.

```
INTERFACE (muda conforme quem pergunta) → BIBLIOTECA
              └──────────┬──────────┘
                         ↓
                  DECODIFICADOR (linguagem natural → intenção estruturada)
                         ↓
                  MOTOR DE RACIOCÍNIO / MOTOR DETERMINÍSTICO
                         ↓
                  BASE DE CONHECIMENTO / DADOS
                         ↓
                  RESPOSTA EXPLICADA
```

**Portas de entrada propostas** (mesma base, linguagem/foco diferente
cada uma):
1. Usuária comum — perguntas simples, sem números/estatística
   aparecendo.
2. Secretaria de Saúde da Mulher — indicadores + tendência +
   anomalias + priorização + comparação com outras cidades.
3. Prefeitura/gestor municipal — visão executiva, "quais problemas
   estão chamando mais atenção", resposta explicada, não tabela.
4. Operadora/plano de saúde — outro vocabulário (perfil assistencial:
   internações, permanência, custo, distribuição etária), mesma
   base de dados.
5. Investidor — "mercado/necessidades de saúde" (população atendida,
   perfil epidemiológico, demanda, infraestrutura) em vez de
   "prioridade de política pública". *(Lembrete da ressalva que já
   registramos: dados são só de internações do SUS, não capturam
   quem já usa rede privada — isso precisa aparecer nessa porta.)*

**Biblioteca**: não é pasta de documento, é uma base de conhecimento
navegável (Doenças / Indicadores / Territórios / Conceitos como
tendência, anomalia, risco) — serve tanto pra a pessoa navegar sem
perguntar nada, quanto de contexto pro decodificador.

**Decodificador**: transforma pergunta solta em algo estruturado, ex.:
"Como está o câncer de mama aqui comparado com uma cidade maior?"
vira `INTENÇÃO: COMPARAR, DOENÇA: MAMA, MUNICÍPIO_1: RIO_CLARO,
MUNICÍPIO_2: ?, INDICADORES: [...]`. A IA nunca inventa o dado, só
busca nos componentes determinísticos já construídos.

**Gap real entre essa visão e o código de hoje** (ver reação que dei
na hora, vale reler amanhã antes de desenhar):
- `classificar_intencao()` hoje escolhe **uma categoria única** por
  pergunta; a visão acima pede extração de **múltiplos campos**
  (doença + cidade A + cidade B + indicadores) — é uma evolução de
  classificador pra extrator de estrutura, não um ajuste pequeno.
- Só existem 2 portas hoje (perfil técnico/simples no chat), não as
  5 personas descritas. A "biblioteca" navegável também não existe
  como estrutura própria — hoje é só tabelas soltas no banco.

## Perguntas em aberto para amanhã

1. A interface nova é sobre o **dashboard** (Streamlit), o **chat**,
   ou um terceiro formato ainda não escolhido?
2. Porta de entrada: cidade primeiro ou pergunta/problema primeiro?
3. O investidor entra mesmo no escopo do projeto (que nasceu como
   apoio à decisão de política pública), ou fica de fora por
   enquanto?
4. Só falta `vulnerabilidade.py` na correção `origem` → `municipio`
   (o resto já foi corrigido, ver seção acima). Vale corrigir esse
   último antes de desenhar a interface, já que é rápido e isolado?
5. O que fazer com os branches soltos (`comparacao-municipios`,
   `territorial-*`) — investigar, mesclar, ou descartar?

---
*Gerado ao final da sessão de 19/09/2026, a pedido do usuário, para
retomada no dia seguinte.*
