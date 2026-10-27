# Inventário do código — o que está em uso, o que guardar, o que pode sair

Leitura de todos os arquivos do repositório (24/09/2026), com o mapa de
quem importa quem. **Feito em 24/09/2026** (o autor pediu "faça o que for
melhor"): os itens da seção 3 saíram do repositório — incluindo
`algoritimos/teste_serie_temporal.py` e `teste_par_real_municipios.py`,
que dependiam da cadeia antiga —, os documentos-retrato foram para
`docs/historico/` e o teste do GitHub passou a rodar os testes do sistema
atual. Tudo continua no histórico do git e pode voltar a qualquer
momento (`git log --diff-filter=D --name-only` lista o que saiu).

## Resumo

O painel de hoje depende de **6 arquivos de código**: `dashboard/app.py`,
`dashboard/lia_rosto.py`, `algoritimos/lia.py`, `algoritimos/passeio.py`,
`algoritimos/inteligencia.py` e `algoritimos/configuracao_geografica.py`.
Nenhum deles importa a cadeia antiga (as 13 tabelas, o motor de
raciocínio, o chat de terminal). A cadeia antiga ainda roda, mas calcula
**por conta própria**, sem o ajuste dos meses que a fonte não oferece e
sem as regras novas — então pode dar números diferentes dos do painel.
Esse é o motivo principal para tirá-la do caminho.

## 1. Em uso (o sistema atual)

| Arquivo | Para quê |
|---|---|
| `dashboard/app.py` | o painel |
| `dashboard/lia_rosto.py` | o rosto da Lia (5 expressões) |
| `dashboard/teste_painel.py` | teste de aceitação: clica em tudo |
| `dashboard/estilo.py` | o CSS do painel, compartilhado com a lâmina de apoio |
| `dashboard/pages/apoio.py` | lâmina **Apoio à mulher** ("Encontre um caminho"), separada do estudo da doença |
| `dashboard/teste_apoio_tela.py` | teste de aceitação da lâmina de apoio: clica em tudo |
| `algoritimos/apoio.py` | catálogo de apoio (fontes oficiais) + árvore da Lia no apoio; testado por `teste_apoio.py` |
| `algoritimos/inteligencia.py` | **única fonte dos números** |
| `algoritimos/lia.py` | a Lia (árvore de caminhos) |
| `algoritimos/passeio.py` | o Passeio pelo Escudo |
| `algoritimos/configuracao_geografica.py` | lista de municípios do seletor |
| `algoritimos/teste_inteligencia.py`, `teste_lia.py` | testes do núcleo |
| `etl/carga_todas_bases.py` | monta o banco (só arquivos estaduais; guarda o mês) |
| `etl/criar_tabela_municipios.py` | catálogo IBGE dos municípios |
| `etl/completude_meses.py` | quais meses a fonte oferece |
| `etl/baixar_sih_sp.py` | baixa/confere o SIH de SP (usa `py -3.12`) |
| `etl/investigar_2025.py` | registro da investigação de 2025 |
| `etl/teste_*.py` (7 arquivos) | testes da carga e dos scripts acima |
| `etl/validar_banco.py` | conferência rápida: total e tipos de câncer no banco |
| `analises/base_preditiva_2013_2025.csv` | base pública usada pelos testes |
| `Abrir Escudo Feminino.bat`, `requirements.txt`, `.streamlit/config.toml` | abrir e rodar |
| `CLAUDE.md`, `README.md`, `docs/LIA.md`, `docs/FONTE_DOS_DADOS.md` | documentação viva |
| `docs/DADOS_2013_2025.md`, `docs/BASES_ORIGINAIS_2013_2025.md`, `analises/catalogo_bases_2013_2025.csv`, `analises/controle_qualidade_bases_2013_2025.csv` | documentam a base pública |

## 2. Pode ser útil no futuro (guardar, fora do caminho)

| Arquivo | Por que guardar | Quando voltaria |
|---|---|---|
| `algoritimos/conversa.py` + `teste_conversa.py` | motor de perguntas em texto (entender → calcular → explicar), já usa `inteligencia.py`; é a parte do ChatGPT | se um dia voltar pergunta em texto, ou para a população |
| `algoritimos/ia_linguagem.py` | integração com o Gemini (só redige, com regras de não inventar) | junto com o `conversa.py` |
| `algoritimos/analise_perguntas.py` | lê as perguntas registradas (`perguntas_usuarios`) | se a caixa de texto voltar |
| `algoritimos/teste_par_real_municipios.py` | compara dois municípios reais | ideia para a comparação entre cidades (com população do IBGE) — o código atual depende do motor antigo, serviria só de referência |
| Ideias da cadeia antiga: **vulnerabilidade**, **score epidemiológico**, **perfil epidemiológico** | perguntas que o painel ainda não responde | se voltarem, entram como função nova em `inteligencia.py` (regra: uma fonte só de números), não como os scripts antigos |

## 3. Não tem mais por que estar (candidatos a sair)

**Cadeia antiga das 13 tabelas** — tudo o que ela mostra hoje sai de
`inteligencia.py`, com as regras novas; ela calcula em paralelo e pode
divergir:

- `algoritimos/mortalidade.py`, `custos_hospitalares.py`,
  `permanencia_hospitalar.py`, `faixa_etaria.py`, `score_epidemiologico.py`,
  `tendencia_estadual.py`, `anomalias.py`, `serie_temporal.py`,
  `priorizador.py`, `base_conhecimento.py`, `perfil_epidemiologico.py`,
  `memoria_ia.py`, `fichas_ia.py`, `vulnerabilidade.py`,
  `relatorio_executivo.py` e o `relatorio_executivo.txt` que ele gera.

**Chat antigo de terminal** — substituído pela Lia:

- `algoritimos/chat_escudo.py`, `motor_raciocinio.py`, `padroes_analiticos.py`,
  `avaliacao_respostas_v2.py`, `teste_padroes_analiticos.py`,
  `teste_cobertura.py`, `teste_territorial.py`;
  `avaliacao_respostas_v2.md` e `catalogo_perguntas_v2.md` (na raiz).
- Em `configuracao_geografica.py`, as funções `salvar_tabela_municipio` /
  `ler_tabela_municipio` só servem à cadeia antiga (o resto do módulo fica).

**Scripts avulsos que repetem o que o painel faz:**

- `analises/*.py` (8 scripts exploratórios: rankings, Rio Claro x SP,
  evolução da mama...).
- `etl/consulta_banco.py`, `contar_registros.py`, `estrutura_banco.py`,
  `top_canceres.py`, `top_territorios.py`, `verificar_banco.py` e
  `banco/ver_banco.py` — sete espiadas no banco que fazem quase a mesma
  coisa; basta o `etl/validar_banco.py`.
- `etl/criar_banco.py` — a carga já cria a tabela.
- `etl/teste_nome_pastas.py` — script manual do padrão de pastas antigo.
- `dashboard/iniciar_dashboard.bat` — atalho antigo (porta 8501);
  substituído por `Abrir Escudo Feminino.bat`.

**Documentos que são retrato de outro momento** (mover para
`docs/historico/`, não apagar — contam a história do trabalho):

- `RELATORIO_STATUS_2026-09-19.md`, `VISAO_TECNICA_INTERFACE.md`,
  `docs/CONSOLIDACAO_V2.md`.

## Um cuidado antes de tirar

O teste automático do GitHub (`.github/workflows/testes-territoriais.yml`)
ainda roda **só testes da arquitetura antiga** (`teste_territorial.py`,
`teste_padroes_analiticos.py`, `teste_carga_territorial.py`) e nenhum do
sistema atual. Ao tirar a cadeia antiga, trocar para
`teste_inteligencia.py`, `teste_lia.py`, os testes do `etl/` e o
`dashboard/teste_painel.py`.

## Sugestão de como fazer

1. Um commit só, "tira a arquitetura antiga do caminho", com os itens da
   seção 3 e a troca do teste do GitHub.
2. Rodar todos os testes (o do painel inclusive) antes de enviar.
3. Atualizar `CLAUDE.md` e `README.md` (a ordem de execução dos scripts
   antigos sai do README).
