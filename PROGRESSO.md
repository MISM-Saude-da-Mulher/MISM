# Progresso do site MISM (ponto de retomada — 27/10/2026)

> **ATUALIZAÇÃO (consolidação, 27/10/2026): `C:\MISM FINAL` é a ÚNICA pasta de trabalho e já é o repositório da organização**
> (`MISM-Saude-da-Mulher/MISM`, branch `main`, privado). Os dados (`dados_parquet/`, `MISM2/banco`, `MISM2/dados`, `.env`, `MISM 1/dados`) continuam aqui e o git os ignora.
> O `.git` antigo do MISM2 (remoto `vladimirsejas/MISM2`, commit `21d7ae1`) está guardado em `_backup\MISM2.git` (movido, não apagado); as versões antigas dos 7 arquivos
> substituídos estão em `_backup\antes_da_consolidacao\`. `C:\MISM2` e `C:\MISM3` não foram tocados. Rodar: `python -m streamlit run app.py` ou `Abrir MISM.bat`.
> As seções abaixo são o histórico do dia; onde falam de `C:\MISM_site_repo` (clone apagado a pedido do autor), vale esta pasta.

## Feito
1. **CSVs → Parquet** (`dados_parquet/`): AIH unificado (496.785 linhas), geo do MISM 1, referência, derivados, 103 tabelas do CNES. Detalhes: `dados_parquet/LEIAME.md`.
2. **Site único** (`app.py`, `paginas/mapa.py`): abas MAPA (MISM 1) e CENTRAL DE INFORMAÇÕES (MISM2). Rodar: `python -m streamlit run app.py`.
3. **SQLite do MISM2 → Parquet** (`dados_parquet/mism2/`): `MISM2/algoritimos/fonte_parquet.py` remonta o SQLite num cache (`.cache_mism/`); CNES lido do Parquet quando não há CSV.
   Conferido tabela a tabela contra o banco original. `MISM2/banco/` não é mais lido e não foi alterado.
4. Testes: lógica e telas passam; `teste_painel.py` completo exige >3 GB de RAM livre (a máquina tem 7,4 GB, ~2–3 GB livres): rodar **por cenário**.
   Falhas restantes do teste são ambientais (F: dados reais; I: `.env` tem GEMINI_API_KEY).
5. Levantamento da hospedagem: `dados_parquet/HOSPEDAGEM.md` (site usa ~208 MB de 586 MB).

## Mudanças em código existente (todas sem mudar comportamento)
- `MISM 1/gerar_mapa.py`: lê Parquet (fallback CSV); `main()` → `gerar_html()`.
- `MISM2/algoritimos/configuracao_geografica.py` (BANCO via `fonte_parquet`), `unidades_saude.py` (CNES CSV ou Parquet), `dashboard/app.py` (1 leitura do cache em vez de 2).
- Testes ajustados: `teste_unidades_saude.py`, `teste_onde_atendida_tela.py`, `teste_painel.py` (cenário E usa o banco em uso).
- Nada commitado. `MISM2` tem git próprio (CLAUDE.md autoriza push no `main`, mas só com pedido do autor).

## Regras do autor para seguir
- Mínimo de mudanças nas funções de cada projeto; não mudar comportamento.
- Máquina com pouca RAM: nada de rodar o teste completo à toa; não pedir para fechar o Claude.
- `MISM2/banco/` nunca é tocado.

## Hospedagem — regras CONFERIDAS nas páginas oficiais (27/10/2026)
- **Hugging Face Spaces NÃO serve no plano grátis:** só há SDK Gradio, Docker e estático; Gradio e Docker "exigem plano pago (PRO)" para criar (Streamlit já não é SDK próprio).
  Hardware grátis (16 GB RAM) só existe depois de ter o plano. Fonte: huggingface.co/docs/hub/spaces-overview.
- **Hugging Face como depósito de dados é viável e grátis:** repositório de *dataset* privado tem 100 GB grátis (público: "best-effort"); arquivo recomendado < 200 GB (Parquet é bem suportado).
- **Streamlit Community Cloud** (grátis): 690 MB–2,7 GB de memória, 1 GB garantido (docs, fev/2024, sujeito a mudança). O painel usa ~790 MB em repouso e ~1,4 GB no pico da primeira carga: risco real.
  O limite de tamanho de arquivo do GitHub (100 MB, de memória) não foi conferido em página oficial.

## Arquitetura recomendada (nada disso foi implementado ainda)
- **Código** no GitHub → Streamlit Community Cloud.
- **Parquets** (~208 MB necessários) num **dataset privado do Hugging Face** (token em `st.secrets`), baixados na primeira abertura para a pasta de cache. Muda só o passo de obter os arquivos (em `fonte_parquet.py`), não as funções do painel.
- Se a memória estourar no Community Cloud: reduzir a carga de `oncologia_ambulatorial` (muda função de `inteligencia.py`; só com autorização) ou escolher hospedagem paga com mais RAM.

## Feito depois (27/10/2026): arquitetura escolhida pelo autor — implementada no lado do código
- `preparar_dados_deploy.py` → `deploy_dados/` (38 arquivos, 207,6 MB); `fonte_parquet.garantir_dados()` baixa o dataset privado do HF quando `dados_parquet/` não existe
  (`MISM_DATASET`, `HF_TOKEN`); chamado no começo do `app.py`; `huggingface_hub` no `requirements.txt`. Testado com download simulado (banco e CNES montam só do que foi "baixado").
- Passo a passo para o autor (contas, upload, secrets): `HOSPEDAR.md`. `tbCargaHorariaSus` vai para o dataset PRIVADO; `tbDadosProfissionalSus` fica de fora.
- NÃO feito (exige as contas do autor): criar o dataset, subir os arquivos, criar o repositório/app.

## Memória reduzida (27/10/2026, autorizado pelo autor: "desde que não estrague o projeto")
- `inteligencia.carregar_tratamento` agora lê em pedaços e compacta os tipos (`_compactar_tratamento`: categorias no pandas ≥ 3, inteiros menores, nunca altera valores).
  Tabela de 193 MB → 27 MB; painel: repouso 790 → ~295 MB, pico 1.396 → ~485 MB. `resumo_tratamento` conferido: 328 combinações (41 cidades × 8 filtros) idênticas.
- `teste_painel.py` completo agora termina: 117 OK, sem MemoryError (pico 2,07 GB, 19 min). Falhas restantes ambientais: F (números dos dados reais) e I ×2 (`.env` tem GEMINI_API_KEY).
- `dashboard/app.py` lê o cache de `tabelas_ambulatorial_e_sim()` uma vez só.

## Ensaio de hospedagem (27/10/2026)
- Repositório git TEMPORÁRIO (fora do seu) com os `.gitignore` do projeto: 170 arquivos rastreados, sem `.env`, `.db`, Parquet nem dados de pacientes. Roda tudo (MAPA, CENTRAL, Onde ser atendida, Hospitais) só com esses arquivos + os `deploy_dados` como `dados_parquet/`. Sem erros.
- Achado e corrigido: `MISM 1/.gitignore` ignorava `dados/` inteira (os GeoJSON do mapa ficariam fora do git). Agora ignora só `brutos/`, `processados/`, `cache/`.
- Sobras do ensaio para apagar quando quiser (eu não apaguei: a verificação de segurança bloqueou remoções): `C:\MISM_ensaio`, `C:\MISM_ensaio_src` (vazia), `C:\MISM_ensaio2_src`, `C:\MISM_ensaio2`.
- O MISM2 tem `.git` próprio: o repositório do site precisa decidir se o inclui como pasta comum (copiar os arquivos) ou como submódulo. O ensaio o tratou como pasta comum.

## Commit (27/10/2026, autorizado pelo autor)
- `MISM2` (branch `main`): commit `b6b7d2d` com as 9 mudanças de código/testes. **Não foi feito push.** Ficaram de fora, por já estarem soltos antes: `banco/`, `algoritimos/explicador_ia.py`, `dashboard/app.py.backup`, `analises/*.txt`, `dados_geograficos/hospitais_oncologia_br_geo.csv`, `resultado_testes_notebook.txt`.
- Raiz (`app.py`, `paginas/`, `dados_parquet/`, docs) e `MISM 1` (`gerar_mapa.py`, `.gitignore`) NÃO têm repositório git: não há onde comitar até decidir como criar o repositório do site.

## Hugging Face (27/10/2026) — FEITO
- Login do autor feito (token salvo em `~/.cache/huggingface/token`, nunca visto por mim). Dataset privado `vladimirsejas/mism-dados` criado e com `deploy_dados` (38 arquivos, 207,6 MB).
- Download real testado com `fonte_parquet.garantir_dados()`: 38 arquivos idênticos por MD5, banco e CNES montam. Para a hospedagem criar um token de LEITURA (não usar o de escrita).
- Pendente: GitHub (repositório `vladimirsejas/MISM`, vazio e aparentemente público: decidir tornar privado antes de subir CLAUDE.md/docs) e Streamlit Cloud.

## GitHub (27/10/2026) — código ENVIADO
- Repositório da organização (privado, 404 sem login): https://github.com/MISM-Saude-da-Mulher/MISM — commit `4c22bf4` sobre o `Initial commit` (README dos colegas mantido). 168 arquivos; MISM2 entrou como pasta comum (sem o `.git` dele).
- Cópia de trabalho do repositório: `C:\MISM_site_repo` (clone). **Mudanças futuras feitas em `C:\MISM FINAL` precisam ser copiadas para lá e enviadas** (ainda não há rotina automática).
- O repositório `vladimirsejas/MISM2` (privado, pessoal) continua separado: decidir se transfere para a organização ou se o site passa a ser a fonte única.
- Falta: Streamlit Community Cloud (app + Secrets `MISM_DATASET` e token de LEITURA do Hugging Face).

## Publicação final no GitHub da organização (27/10/2026) — commit `b9d737d` em `main`
- Repositório privado: https://github.com/MISM-Saude-da-Mulher/MISM (404 sem login). Sem force push; histórico preservado (6 commits). Cópia de trabalho: `C:\MISM_site_repo`.
- Corrigido antes de enviar: `resumido3_com_coordenadas_google.csv` saiu do controle de versão (o site não o usa; termos do Google) — **continua no histórico do commit `4c22bf4`**;
  voltaram `MISM2/README.md` e os 3 CSVs de `analises/` (o filtro anterior os tinha excluído); saíram arquivos soltos (`explicador_ia.py`, `app.py.backup`, `resultado_testes_notebook.txt`, `analises/*.txt`).
- Testado em ambiente limpo (venv novo só com `requirements.txt`, clone novo, dados baixados do Hugging Face): MAPA e CENTRAL abrem; 14 testes passam. NÃO rodado nesse ambiente: `teste_painel.py` completo (precisa de >2 GB de RAM, ~20 min; passou antes com 117 OK).
- Pendências levantadas: (1) o MAPA mostra dados por caso (CEP, logradouro, idade, valor) no HTML da página: não publicar o app em acesso público antes de decidir (ver CLAUDE.md, condições do mapa);
  (2) estrutura: o autor quer o MISM como projeto único e o mapa como parte do MISM2, como o Apoio à mulher (conversa em aberto);
  (3) dois commits meus foram para `vladimirsejas/MISM2` antes da instrução de não enviar mais para lá (`b6b7d2d`, `21d7ae1`); nada mais será enviado para esse repositório.

## Revisão de eficiência e união mínima (27/10/2026, a pedido do autor: manter o que era bom, só unir, medir o Parquet)
- **União:** o MISM2 é a tela inicial (sem a barra MAPA | CENTRAL); o mapa do grupo é a página "Mapa de Rio Claro", botão ao lado do Apoio à mulher e destino da barra do MISM2.
  Só aparece quando existe `paginas/mapa.py`: o MISM2 sozinho segue idêntico (conferido: 3 destinos, teste de navegação passa). Busca por CEP e páginas novas: NÃO feitas (o autor pediu manter como era e só unir).
- **Medido (CSV/SQLite x Parquet):** CNES 28,8 s → 13,0 s (3,5 s só SP); banco 174 → 9,1 MB; AIH 227 → 16 MB; mapa sem ganho (0,12 x 0,15 s) e por isso passou a ler um Parquet de 34 KB (0,11 s).
  CSVs pequenos (hospitais, análises) NÃO foram convertidos. Nada foi removido: sem `dados_parquet` tudo lê o formato de antes.
- **Pacote de dados:** 207,6 → 54,1 MB (CNES só de SP, resultado idêntico em Rio Claro, Campinas e Piracicaba; sem o AIH completo). Dataset do Hugging Face atualizado (37 arquivos, privado).
  Partida a frio: download 23 s + banco 8 s + CNES 3 s + mapa 0,2 s = ~36 s (antes >100 s). Nenhum arquivo passa de 27 MB (o limite de 100 MB do GitHub deixou de ser problema).
- **Testes:** 15 testes de lógica/tela passam no site com o pacote enxuto + `testes/teste_mapa_parquet.py`. `teste_apoio_tela` e `teste_conversa_apoio_tela` falham só onde existe o `.env` com GEMINI_API_KEY (ambiental; passam na cópia limpa).
- **Trabalhar a partir de agora em `C:\MISM_site_repo`** (cópia do repositório da organização). `C:\MISM FINAL` ficou com os arquivos antigos da raiz: não sincronize dele para lá (sobrescreveria estas edições).

## Próximo
- Decisões pendentes do autor: (1) aceitar essa arquitetura (código no GitHub + dados em dataset privado do HF); (2) publicar ou não `cnes/tbCargaHorariaSus` (código de profissional; 110,7 MB); (3) `tbDadosProfissionalSus` fica de fora.
- Depois: montar a pasta de deploy (só cópia dos ~208 MB, sem alterar a origem) e o passo de download.

## 28/10/2026 - Identidade visual unica
Todas as paginas (Panorama e abas, Apoio, Onde ser atendida, Hospitais de cancer, Mapa de Rio Claro) abrem com a linha de marca "MISM . ..." e a mesma barra de navegacao; a Lia e o guia comum. Mapa passou a ter a linha de marca e o mesmo respiro de topo. Etapa fechada; proxima: etapa dois.
- Lia (28/10/2026): novo assunto "mapa_rio_claro" (onde fica o mapa, areas de USF) com texto fixo e link para a pagina do mapa; a Lia NAO foi levada para outras paginas (decisao do autor: Lia so onde ja estava). Teste: MISM2/algoritimos/teste_mapa_lia.py.
