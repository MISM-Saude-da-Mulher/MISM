# MISM — um projeto só, construído sobre o MISM2

O **MISM2** (painel + Lia, Apoio à mulher, Onde ser atendida, Hospitais de câncer) é a base. O **mapa de Rio Claro do projeto do grupo**
(`KaueFLima/MISM`, pasta `MISM 1/`) entra como mais uma página dele, o botão **"Mapa de Rio Claro"**, ao lado do Apoio à mulher.
Cada projeto continua com o seu código e a sua lógica.

## Rodar

```bash
python -m streamlit run app.py        # ou dê dois cliques em "Abrir MISM.bat"
```

## Como está montado
- `app.py`: só a navegação (a barra do Streamlit fica escondida; vale a barra do próprio MISM2). A tela inicial é a do MISM2.
- `paginas/mapa.py`: embute o mapa do grupo (`MISM 1/gerar_mapa.py`, função `gerar_html()`) com a mesma barra do MISM2.
- `MISM2/`: o projeto como era. Mudanças mínimas: `dashboard/navegacao.py` e `dashboard/app.py` ganham o destino "Mapa de Rio Claro"
  **só quando existe `paginas/mapa.py`** (o MISM2 sozinho segue com os 3 destinos de sempre); `algoritimos/fonte_parquet.py` (dados em Parquet),
  `configuracao_geografica.py`, `unidades_saude.py` e `inteligencia.carregar_tratamento` (memória) com alternativa ao formato antigo.
- `MISM 1/`: o projeto do grupo como era. Mudança: `gerar_mapa.py` lê o Parquet (ou o CSV de antes) e `main()` virou `gerar_html()` + gravação.
- `testes/teste_mapa_parquet.py`: confere o mapa em Parquet.

## Parquet: onde compensa (medido) e onde não
| Dado | Antes (CSV / SQLite) | Parquet | Resultado |
|---|---|---|---|
| CNES, "Onde ser atendida" | 28,8 s, 1.258 MB | 13,0 s, 182 MB; **3,5 s, ~45 MB só de SP** | mais rápido e 7–28× menor; resultado idêntico (Rio Claro, Campinas, Piracicaba) |
| Banco do painel (SQLite) | 174 MB | 9,1 MB (+8 s uma vez para montar) | 19× menor; consultas iguais |
| AIH (38 CSVs) | 227 MB | 16 MB | 14× menor (só arquivo morto: o site não o usa) |
| Mapa do grupo | CSV: 0,12 s | Parquet pequeno (34 KB): **0,11 s** | sem ganho de velocidade; só uniformiza o pacote |
| CSVs pequenos (hospitais, análises) | KB | — | **não convertidos** (sem ganho, e já estão no git) |

Nada foi removido: sem a pasta `dados_parquet`, o MISM2 lê o banco e os CSVs de sempre, e o mapa lê o CSV de antes.

## Dados e hospedagem
Os dados não vão para o GitHub: ficam num dataset privado do Hugging Face (`MISM_DATASET`, `HF_TOKEN` nos Secrets) e são baixados na primeira abertura
(**54 MB, 37 arquivos; partida a frio ~36 s**: download 23 s, banco 8 s, CNES 3 s). Gerar o pacote: `python preparar_dados_deploy.py` (`--completo` = CNES do Brasil).
Passo a passo em `HOSPEDAR.md`; estado e pendências em `PROGRESSO.md`.

## Observações
- Dentro do site, os links internos do MISM2 (ex.: "Apoio à mulher") usam o link de reserva `/apoio` que o próprio MISM2 já previa e recarregam a página.
- O mapa do grupo mostra dados por caso (CEP, logradouro, idade, valor): **não deixe o app acessível publicamente** até decidirem a privacidade (ver `PROGRESSO.md`).
