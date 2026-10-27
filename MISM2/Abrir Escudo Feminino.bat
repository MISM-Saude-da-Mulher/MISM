@echo off
REM ============================================================
REM  ABRIR O ESCUDO FEMININO (com a Lia) -- basta dar dois cliques.
REM  1. baixa a versao mais nova do GitHub (se nao der, segue assim mesmo);
REM     se veio codigo novo e o painel ja estava aberto, reinicia o painel
REM  2. liga o painel numa janela minimizada (nao feche essa janela)
REM  3. espera o painel ficar pronto e abre o navegador
REM  Para fechar o painel: feche a janela "Escudo Feminino - painel".
REM ============================================================
title Escudo Feminino - abrindo a Lia
cd /d "%~dp0"

echo Atualizando o Escudo Feminino...
set antes=
for /f %%h in ('git rev-parse HEAD 2^>nul') do set antes=%%h
git pull --quiet 2>nul || echo Nao deu para atualizar agora - abrindo a versao deste computador.
set depois=
for /f %%h in ('git rev-parse HEAD 2^>nul') do set depois=%%h

REM Painel aberto de antes continua com o codigo VELHO na memoria
REM (o Streamlit nao recarrega algoritimos\lia.py, conversa.py...).
REM Ao ligar, o painel anota a versao em dashboard\versao_no_ar.txt;
REM se a versao da pasta for outra (git pull por aqui OU pela janela
REM preta), fecha o painel antigo para ligar o novo.
set no_ar=
if exist "dashboard\versao_no_ar.txt" set /p no_ar=<"dashboard\versao_no_ar.txt"
if not "%no_ar%"=="%depois%" call :desligar_painel_antigo

REM Sem curl (Windows antigo): liga o painel, espera 10 s e abre.
where curl >nul 2>nul || goto sem_curl

REM Se o painel ja estiver aberto, so abre o navegador de novo.
curl -s -o nul http://localhost:8600/_stcore/health && goto abrir

echo Ligando o painel...
>"dashboard\versao_no_ar.txt" echo(%depois%
start "Escudo Feminino - painel" /min cmd /k py -m streamlit run dashboard\app.py --server.port 8600 --server.headless true

set /a tentativas=0
:esperar
set /a tentativas+=1
curl -s -o nul http://localhost:8600/_stcore/health && goto abrir
if %tentativas% geq 60 goto demorou
timeout /t 1 /nobreak >nul
goto esperar

:abrir
start "" http://localhost:8600
exit

:sem_curl
echo Ligando o painel...
>"dashboard\versao_no_ar.txt" echo(%depois%
start "Escudo Feminino - painel" /min cmd /k py -m streamlit run dashboard\app.py --server.port 8600 --server.headless true
timeout /t 10 /nobreak >nul
goto abrir

:desligar_painel_antigo
echo Versao nova baixada: reiniciando o painel...
taskkill /f /t /fi "WINDOWTITLE eq Escudo Feminino - painel*" >nul 2>nul
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8600" ^| findstr "LISTENING"') do taskkill /f /pid %%p >nul 2>nul
timeout /t 2 /nobreak >nul
goto :eof

:demorou
echo.
echo O painel demorou mais de 1 minuto para ligar.
echo Abra a janela "Escudo Feminino - painel" na barra de tarefas para ver a mensagem de erro.
pause
