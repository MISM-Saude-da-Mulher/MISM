# Visão técnica da interface — Escudo Feminino

Este documento é a minha opinião de verdade sobre como construir a
interface discutida (uma inteligência, várias portas de entrada), não
uma repetição da síntese do ChatGPT. Complementa
`RELATORIO_STATUS_2026-09-19.md`. A maquete interativa que constrói
essa visão está publicada separadamente (link enviado no chat) —
mostra as 5 portas de entrada e o decodificador de perguntas
funcionando de verdade (clicável).

## Minha posição, direto

**Não construam 5 telas.** Construam 1 aplicativo Streamlit (o que já
existe) com uma função de despacho por perfil. O dado, a query, o
motor de raciocínio — tudo isso já é único no projeto. O que muda por
perfil é só: qual vocabulário usar, qual componente mostrar primeiro,
o que esconder. Isso é uma função de apresentação, não uma
arquitetura nova.

**O maior gap real não é a interface visual — é o decodificador.**
Hoje `classificar_intencao()` (em `chat_escudo.py`) escolhe **uma
categoria única** por pergunta, de uma lista fixa de ~15. A visão
que vocês desenharam ("comparar mama entre Rio Claro e uma cidade
maior") exige **extrair vários campos ao mesmo tempo** (doença +
município A + município B + indicador). Isso é uma mudança de
categoria de problema: de classificação para extração estruturada.
É o trabalho tecnicamente mais difícil de tudo que foi discutido
hoje — mais difícil que qualquer parte visual.

**Não subestimem a "biblioteca".** Ela não é decoração de sidebar —
ela é o que resolve "eu não sei o que perguntar" (a tensão que
discutimos ontem entre chat e navegação). Se ela só listar nomes sem
explicar o que cada conceito significa, não resolve nada. Ela precisa
ter texto curto e explicativo por item (o que é "anomalia", o que é
"confiabilidade") — sem isso, é só mais uma lista.

## Requisitos técnicos (o que realmente precisa mudar no código)

### 1. Motor de intenção → extrator de estrutura (o item mais importante)

`classificar_intencao(pergunta_norm)` retorna uma string
(`"TENDENCIA_ESTADUAL"`, `"MORTALIDADE"` etc.). Para suportar
comparação, ele precisa evoluir para devolver uma estrutura, tipo:

```python
{
    "intencao": "COMPARAR",
    "doenca": "MAMA",              # ou None
    "municipio_1": "RIO_CLARO",    # já resolvido, não texto livre
    "municipio_2": None,           # "uma cidade maior" ainda não sabe resolver isso
    "indicadores": ["internacoes", "tendencia"],
}
```

O ponto difícil não é achar `"MAMA"` ou `"RIO_CLARO"` (isso já existe
— `detectar_cancer()` e `listar_municipios_disponiveis()` já
resolvem nomes conhecidos por *string matching*, sem IA). O ponto
difícil é frases como **"uma cidade maior"**, que não é um nome de
município, é uma referência relativa que exige saber população de
cada cidade (dado que **não existe ainda** em nenhuma tabela do
projeto). Registrar isso agora: se quiserem que o decodificador
resolva referências desse tipo, alguém precisa trazer dado de
população por município (o próprio IBGE tem API pública pra isso,
mesma família de endpoint já usada para o catálogo de municípios).

### 2. Uma função de despacho por perfil, não 5 apps

```python
PERFIS = {
    "cidada": renderizar_cidada,
    "gestora": renderizar_gestora,
    "prefeitura": renderizar_prefeitura,
    "operadora": renderizar_operadora,
    "investidor": renderizar_investidor,
}

perfil_atual = st.session_state.get("perfil", "gestora")
PERFIS[perfil_atual](contexto_municipio)
```

Cada `renderizar_*` recebe os **mesmos dados** já calculados
(`base_conhecimento`, `priorizacao_executiva` etc.) e decide só como
mostrar — nunca recalcula nada, mesma regra que já vale para o chat
hoje ("a IA não escolhe o dado").

### 3. Cesta de comparação como estado de sessão

Não precisa de tabela nova nem de banco — é estado de UI, dura só a
sessão do usuário:

```python
if "cesta_comparacao" not in st.session_state:
    st.session_state.cesta_comparacao = [ORIGEM]  # começa com o município atual

def adicionar_a_cesta(origem):
    if origem not in st.session_state.cesta_comparacao:
        st.session_state.cesta_comparacao.append(origem)
```

### 4. Autocomplete de 645 cidades

Duas opções honestas, sem fingir que uma é obviamente melhor:

- **Sem dependência nova**: `st.text_input` pra filtrar +
  `st.selectbox` só com o resultado filtrado. Funciona, é feio de
  digitar, mas é zero risco.
- **Com dependência nova**: pacote `streamlit-searchbox` (PyPI) —
  dropdown de busca de verdade, assíncrono. Um pacote a mais pra
  manter, mas resolve a experiência de vez. Eu escolheria essa,
  dado que 645 opções é exatamente o caso que justifica a
  dependência extra.

### 5. Mapa de SP (se decidirem construir)

Não existe hoje. Precisa de duas coisas novas:
- GeoJSON dos municípios de SP —
  `servicodados.ibge.gov.br/api/v3/malhas/estados/35?formato=application/vnd.geo+json`
  (mesma API do IBGE já usada pro catálogo de municípios, só endpoint
  diferente).
- `plotly.express.choropleth` ou `choropleth_mapbox` pra desenhar —
  já é `plotly`, já é dependência do projeto, nada novo aí.

## Bibliotecas — o que eu manteria, o que eu adicionaria

| Já usado | Manter? | Motivo |
|---|---|---|
| Streamlit | Sim | Reescrever em outra stack (FastAPI+React etc.) não se paga pro tamanho e prazo deste projeto |
| Plotly | Sim | Cobre gráfico, dispersão, mapa coroplético — não falta nada |
| Pandas/SQLite | Sim | Já é a espinha dorsal de tudo, sem motivo pra trocar |

| Novo, se decidirem construir | Pra quê |
|---|---|
| `streamlit-searchbox` | Autocomplete de verdade pro seletor de 645 cidades |
| Nenhuma lib de NLU pesada (spaCy etc.) | O extrator de estrutura do item 1 dá pra fazer com *string matching* contra listas já conhecidas (cânceres, municípios) + regras — não precisa de modelo de linguagem próprio; a IA (Gemini, já integrada) só escreve o texto final, nunca decide o dado |

## O que a maquete mostra (e o que ela não resolve)

A maquete publicada mostra as 5 portas de entrada trocando de verdade
(clique nos botões no topo) e o decodificador com um exemplo de
comparação já "decodificado" em chips. Ela **não** é código
funcional — é para vocês dois concordarem no visual e no conceito
antes de qualquer linha de Python. Reparem que ela já usa nomes reais
do projeto (`MAMA`, `COLO_UTERO`, `RIO_CLARO`, código IBGE 3543907)
propositalmente, não dado genérico.

## Ordem que eu sugeriria (não é a única certa)

1. Decidir o visual/conceito olhando a maquete (rápido, sem código).
2. Corrigir `vulnerabilidade.py` (pendência isolada do dia anterior).
3. Função de despacho por perfil no dashboard atual — baixo risco,
   não mexe no motor de raciocínio.
4. Extrator de estrutura (item 1) — é o que realmente falta pra
   comparação funcionar pelo chat, e o mais arriscado tecnicamente.
5. Autocomplete/mapa — melhoria de experiência, não bloqueia nada.
