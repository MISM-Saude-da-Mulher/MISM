# De onde vêm os dados do MISM

**Tudo o que o MISM mostra vem de bases públicas, baixadas pela própria equipe.** Segundo os autores, não houve ofício, pedido de acesso nem
dado cedido por ninguém: foram downloads diretos dos portais abertos do Ministério da Saúde e do IBGE, com ferramentas livres. Qualquer pessoa
pode refazer o caminho com as mesmas fontes.

| Dado | Fonte pública | Como foi obtido | No MISM |
|---|---|---|---|
| **Internações por câncer em mulheres** (7 cânceres, SP, 2013–2026) | **SIH/SUS**, arquivos RD (AIH reduzida), DATASUS / Ministério da Saúde | download com o [PySUS](https://github.com/AlertaDengue/PySUS), uma competência por vez | painel, Lia, Evolução, Rede hospitalar, mapa |
| **Tratamento ambulatorial** (quimio e radioterapia) | **SIA/SUS** (APACs de quimioterapia e radioterapia), DATASUS | PySUS | Lia ("tratamento") |
| **Óbitos** | **SIM** (declarações de óbito), DATASUS | PySUS | Lia ("mortalidade") |
| **Estabelecimentos, serviços e profissionais** | **CNES**, cnes.datasus.gov.br (Download de dados) | arquivos da competência 08/2026 baixados do portal | Onde ser atendida |
| **Equipamentos e leitos** | **CNES** (EQ e LT), DATASUS | PySUS | base de dados do painel |
| **População de mulheres** | **IBGE**, Censo 2022 (SIDRA, tabela 9514) | download pela API do IBGE | taxas por 100 mil e ranking |
| **Centro de cada município** | **IBGE**, malha municipal | API do IBGE | distâncias em linha reta até hospitais |
| **Hospitais habilitados em oncologia** (361 no Brasil, 88 em SP) | planilha publicada pelo **Ministério da Saúde** (habilitação 2023) | planilha pública, tratada em `etl/gerar_lista_hospitais_oncologia.py` | Hospitais de câncer |
| **Catálogo de serviços de Rio Claro e conteúdo do Apoio à mulher** | páginas oficiais (prefeitura, Estado de SP, INCA, Ministério) | conferido item a item, com a **fonte e a data de conferência em cada cartão** | Apoio à mulher, Onde ser atendida |
| **Áreas de USF e limite de Rio Claro** | arquivos do **projeto territorial do grupo** (`KaueFLima/MISM`) | recebidos do projeto do grupo (a origem dos polígonos ainda não está registrada nos arquivos) | mapa de Rio Claro |
| **CEP para localização** | consulta na hora às APIs públicas gratuitas de CEP (AwesomeAPI; a BrasilAPI só devolve o centro da cidade e é recusada); o MISM não guarda o CEP nem usa tabela de coordenadas do Google | `MISM 1/consulta_cep.py` | consulta "Qual é a minha área de USF?" no mapa de Rio Claro |

## O que o MISM faz com esses dados
- **Só descreve.** Mostra o que o SUS registrou: internações, óbitos na internação, valores registrados, onde há serviço. Não diagnostica, não indica tratamento e não
  explica causas. Internação **não** é caso novo nem incidência.
- **Diz o que a fonte não tem.** Por exemplo, o DATASUS não oferece 35 dos 156 meses de 2013 a 2025 no SIH/SUS (a conferência está em `MISM2/docs/FONTE_DOS_DADOS.md`);
  mês ausente aparece como ausente, nunca como zero.
- **A IA só redige.** O Gemini reescreve respostas a partir de números que o próprio MISM calculou, e cada texto é conferido antes de aparecer.

## Como refazer
1. Instale o PySUS (Python 3.12) e rode os scripts de `MISM2/etl/` (`baixar_sih_sp.py`, `baixar_sia_oncologia.py`, `baixar_sim_obitos.py`, `baixar_cnes_capacidade.py`,
   `baixar_populacao.py`, `baixar_centroides.py`); o CNES completo vem do portal do CNES.
2. Rode `MISM2/etl/carga_todas_bases.py` para montar o banco e `MISM2/etl/exportar_banco_parquet.py` para gerar os Parquets.
3. Detalhes e medições: `LEIAME.md`, `PROGRESSO.md` e `dados_parquet/LEIAME.md`.

## Créditos
- **MISM2** (painel, Lia, Apoio à mulher, Onde ser atendida, Hospitais de câncer): projeto principal.
- **Mapa de Rio Claro** (áreas de USF e georreferenciamento): projeto do grupo, repositório `KaueFLima/MISM`, com contribuições de Kauê, brendolalves e Gabriel-nascimento31.
