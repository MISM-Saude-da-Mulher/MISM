@echo off
REM ============================================================
REM  ABRIR O SITE MISM (abas MAPA e CENTRAL DE INFORMACOES)
REM  Basta dar dois cliques.
REM  1. liga o site numa janela minimizada (nao feche essa janela)
REM  2. espera ficar pronto e abre o navegador
REM  Para fechar o site: feche a janela "MISM - site".
REM  A primeira abertura do dia leva mais tempo (monta o banco a partir
REM  dos dados em Parquet); as seguintes sao rapidas.
REM ============================================================
title MISM - abrindo o site
cd /d "%~dp0"

REM Sem a pasta dados_parquet neste computador, baixa os dados do Hugging Face (dataset privado; usa o login salvo).
if not exist "dados_parquet" set MISM_DATASET=vladimirsejas/mism-dados

where curl >nul 2>nul || goto sem_curl

REM Se o site ja estiver aberto, so abre o navegador de novo.
curl -s -o nul http://localhost:8610/_stcore/health && goto abrir

echo Ligando o site...
start "MISM - site" /min cmd /k py -m streamlit run app.py --server.port 8610 --server.headless true

set /a tentativas=0
:esperar
set /a tentativas+=1
curl -s -o nul http://localhost:8610/_stcore/health && goto abrir
if %tentativas% geq 90 goto demorou
timeout /t 1 /nobreak >nul
goto esperar

:abrir
start "" http://localhost:8610
exit

:sem_curl
echo Ligando o site...
start "MISM - site" /min cmd /k py -m streamlit run app.py --server.port 8610 --server.headless true
timeout /t 12 /nobreak >nul
goto abrir

:demorou
echo.
echo O site demorou mais de 1 minuto e meio para ligar.
echo Abra a janela "MISM - site" na barra de tarefas para ver a mensagem de erro.
pause
