# MISM — site único

Duas abas principais, no topo:

| Aba | Projeto | O que abre |
|---|---|---|
| **MAPA** | `MISM 1/` | Mapa de Rio Claro (internações por câncer em mulheres, por área de USF), lido de `dados_parquet/aih/` |
| **CENTRAL DE INFORMAÇÕES** | `MISM2/` | Painel + Lia, Apoio à mulher, Onde ser atendida, Hospitais de câncer (a barra interna do MISM2 segue igual) |

## Rodar

```bash
python -m streamlit run app.py
```

## Como está montado
- `app.py` — só navegação (`st.navigation` oculta + as duas abas). Registra as páginas do MISM2 como estão.
- `paginas/mapa.py` — embute o HTML gerado por `MISM 1/gerar_mapa.py` (`gerar_html()`).
- `MISM 1/gerar_mapa.py` — única mudança: lê `dados_parquet/aih/*.parquet` (se não existirem, usa o CSV de antes) e `main()` foi dividido em `gerar_html()` + gravação. O HTML gerado é idêntico ao anterior.
- `MISM2/` — nenhum arquivo alterado.
- `dados_parquet/` — ver `dados_parquet/LEIAME.md`.

## De onde vêm os dados do MISM2 (Parquet)
- **Banco:** as 28 tabelas do `escudo_feminino.db` estão em `dados_parquet/mism2/*.parquet` + `esquema.sql`
  (`MISM2/etl/exportar_banco_parquet.py` refaz a exportação). O painel continua com as mesmas consultas SQL: na primeira abertura
  `MISM2/algoritimos/fonte_parquet.py` monta o SQLite a partir do Parquet (~10 s) em `.cache_mism/` e o reaproveita; se o Parquet mudar, refaz sozinho.
  Conferido tabela a tabela contra o banco original (mesmas linhas, tipos e índices). `banco\escudo_feminino.db` não é mais lido nem tocado.
  `perguntas_usuarios` vai só com o esquema (sem linhas). Para voltar ao banco antigo: `ESCUDO_BANCO_SQLITE=<caminho do .db>`.
- **CNES (Onde ser atendida):** `unidades_saude.py` usa o CSV se ele existir em `MISM2/banco/cnes`; senão, `dados_parquet/cnes/`
  (competência em `COMPETENCIA.txt`). Mesmo resultado nos dois caminhos.
- **Hospitais habilitados:** continuam nos CSVs pequenos de `MISM2/dados_geograficos/` (já versionados no git do MISM2).

## Pendências para hospedar (Streamlit Community Cloud)
- `dados_parquet/` tem ~580 MB e, no CNES, só 6 tabelas são usadas pelo painel (`tbEstabelecimento`, `rlEstabServClass`, `tbClassificacaoServico`,
  `tbServicoEspecializado`, `tbCargaHorariaSus` [110 MB, acima do limite de 100 MB por arquivo do GitHub], `tbAtividadeProfissional`).
  Decidir o que sobe para o repositório e o que vai para um banco/armazenamento externo.
- Dentro do site, os links internos do MISM2 (ex.: botão "Apoio à mulher") recarregam a página em vez de trocar de aba (usam o link de reserva `/apoio` que o próprio MISM2 já previa); a cidade escolhida volta ao padrão nesses saltos.
