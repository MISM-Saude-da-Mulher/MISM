@echo off
REM ============================================================
REM  ATUALIZAR OS DADOS DO ESCUDO FEMININO -- basta dar dois cliques.
REM  1. baixa a versao mais nova do GitHub
REM  2. refaz o banco com os 7 canceres (py etl\carga_todas_bases.py)
REM  3. confere o resultado (py etl\validar_banco.py)
REM  Tudo o que aparece na tela tambem fica em carga_resultado.txt,
REM  nesta pasta: se algo der errado, mande esse arquivo ao Claude.
REM  Feche o painel antes (a janela "Escudo Feminino - painel").
REM ============================================================
title Escudo Feminino - atualizando os dados
cd /d "%~dp0"
chcp 65001 >nul

echo Baixando a versao mais nova...
git pull --quiet 2>nul || echo Nao deu para atualizar agora - seguindo com a versao deste computador.

echo.
echo Refazendo o banco (pode levar alguns minutos)...
py etl\carga_todas_bases.py > carga_resultado.txt 2>&1
echo. >> carga_resultado.txt
echo ============================================================ >> carga_resultado.txt
py etl\validar_banco.py >> carga_resultado.txt 2>&1

type carga_resultado.txt
start "" notepad carga_resultado.txt
echo.
echo ============================================================
echo O resultado tambem esta em carga_resultado.txt (nesta pasta).
echo Se aparecer "OK: os 7 canceres estao no banco", abra o painel
echo de novo pelo "Abrir Escudo Feminino.bat".
echo ============================================================
pause
