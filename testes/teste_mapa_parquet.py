"""Teste do mapa lendo do Parquet (dados_parquet/aih): o Parquet do mapa basta, sem o AIH completo.

Uso (da raiz do site):  python testes/teste_mapa_parquet.py
Precisa de dados_parquet/aih/aih_rio_claro_geo.parquet (o site baixa do Hugging Face; ver HOSPEDAR.md).
"""
import json
import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "MISM 1"))
import gerar_mapa  # noqa: E402
import pandas as pd  # noqa: E402

falhas = []


def checar(nome, ok):
    print(("OK   " if ok else "FALHOU ") + nome)
    if not ok:
        falhas.append(nome)


geo = pd.read_parquet(gerar_mapa.PARQUET_GEO)
checar("o Parquet do mapa traz as colunas de que ele precisa (DIAS_PERM, MORTE, DIAG_PRINC)",
       all(c in geo.columns for c in ("DIAS_PERM", "MORTE", "DIAG_PRINC")))
gerar_mapa.PARQUET_AIH = pathlib.Path("/nao/existe/aih_cancer_mulheres.parquet")  # sem o AIH completo
html = gerar_mapa.gerar_html()
registros = json.loads(re.search(r"const rawData = (\[.*?\]);\n", html, re.S).group(1))
checar("gera o mapa sem o AIH completo", len(registros) == len(geo) > 0)
checar("cada caso traz área de USF, doença e ano", all(r["area_usf"] and r["doenca"] and r["ano"] for r in registros))
checar("mortes e permanência vêm do Parquet do mapa", any(r["dias"] > 0 for r in registros) and any(r["morte"] for r in registros))
if falhas:
    print(f"\n{len(falhas)} falha(s).")
    sys.exit(1)
print("\nTodas as checagens do mapa em Parquet passaram.")
