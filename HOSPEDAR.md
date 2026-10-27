# Como publicar o site (passo a passo, feito por você)

Arquitetura escolhida: **código no GitHub → Streamlit Community Cloud**, **dados num dataset privado do Hugging Face**.
O que já está pronto no projeto: `deploy_dados/` (os 38 arquivos que o site usa, 207,6 MB), `preparar_dados_deploy.py` (refaz essa pasta),
e o passo de download em `MISM2/algoritimos/fonte_parquet.py` (`garantir_dados()`), chamado no começo do `app.py`.
Nada abaixo foi feito por mim: exige suas contas.

## STATUS (27/10/2026)
- **Passo 1 concluído:** dataset privado `vladimirsejas/mism-dados` criado e com os 38 arquivos (207,6 MB). Download testado de verdade com a função do site
  (pasta vazia → 38 arquivos idênticos por MD5 → banco e CNES montam). Falta só o GitHub (passo 2) e o Streamlit (passo 3).
- Nos Secrets do Streamlit use `MISM_DATASET = "vladimirsejas/mism-dados"` e um token **só de leitura** (crie outro em Settings → Access Tokens, tipo *Read*, restrito a esse dataset);
  não use o token de escrita `MISM-VSCode` na hospedagem.
- Para atualizar os dados depois: `python preparar_dados_deploy.py` e `HfApi().upload_folder(folder_path="deploy_dados", repo_id="vladimirsejas/mism-dados", repo_type="dataset")`.

## 1) Dados no Hugging Face (dataset privado) — FEITO
1. Crie uma conta em huggingface.co (grátis) e um **token** com permissão de escrita (Settings → Access Tokens).
2. Crie um dataset **privado** (ex.: `seu-usuario/mism-dados`).
3. Suba o conteúdo de `deploy_dados/` (as pastas `aih`, `mism2`, `cnes` na raiz do dataset):
   ```bash
   pip install huggingface_hub
   hf auth login
   hf upload seu-usuario/mism-dados deploy_dados . --repo-type dataset --private
   ```
   (se o comando `hf` não existir na sua versão, use `huggingface-cli upload`, com os mesmos argumentos)
4. Para trocar os dados depois: rode `python preparar_dados_deploy.py` e suba de novo.

## 2) Código no GitHub
- Suba a pasta do site **sem** `dados_parquet/`, `deploy_dados/`, `.cache_mism/` (o `.gitignore` já cobre o cache e os `.db`; acrescente as duas pastas de dados antes do primeiro commit).
- O `MISM2` tem git próprio: decidir se o site vira um repositório novo (raiz `C:\MISM FINAL`) ou usa o do MISM2 (o CLAUDE.md autoriza push no `main`, só com seu pedido).
- Não suba `MISM2/.env` (tem a chave do Gemini).

## 3) Streamlit Community Cloud
1. share.streamlit.io → New app → o repositório → arquivo principal `app.py`.
2. Em **Secrets** coloque (no formato TOML, nível superior — o Streamlit os expõe como variáveis de ambiente):
   ```toml
   MISM_DATASET = "seu-usuario/mism-dados"
   HF_TOKEN = "seu-token-de-leitura"
   GEMINI_API_KEY = "sua-chave"
   ```
3. Primeira abertura: baixa os dados e monta o banco (alguns minutos); depois fica em cache.

## O que pode dar errado
- **Memória:** depois da compactação de `oncologia_ambulatorial` (`inteligencia._compactar_tratamento`, resultados idênticos) o painel usa ~295 MB em repouso e ~485 MB no pico, abaixo do 1 GB garantido do Community Cloud. Medido no notebook, não na hospedagem: confira lá.
- `tbCargaHorariaSus` (110,7 MB) está no dataset privado; o painel só usa o código do profissional para contar, em memória.
