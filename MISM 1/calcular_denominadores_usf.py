"""Calcula quantas mulheres (e domicílios) moram em cada área de USF de Rio Claro, a partir do Censo 2022 (IBGE).

Por que existe: o mapa contava internações por área, e a contagem acompanha o tamanho da área. Para comparar áreas é preciso
dividir pela população. O IBGE publica o Censo 2022 por SETOR CENSITÁRIO (áreas pequenas); aqui cada setor é repartido entre as
áreas de USF pela fração da sua superfície que cai dentro de cada área.

Uso (rodar no computador de quem mantém o MISM; o site só lê o CSV pronto, não precisa de shapely nem dos arquivos do IBGE):

    python "MISM 1/calcular_denominadores_usf.py" --setores SP_setores_CD2022.gpkg ^
        --basico Agregados_por_setores_basico_BR_20260520.zip --demografia Agregados_por_setores_demografia_BR.zip

Arquivos (todos públicos do IBGE):
  --setores     malha de setores censitários de SP (SP_setores_CD2022.gpkg)
  --basico      https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/Agregados_por_Setor_csv/
                Agregados_por_setores_basico_BR_20260520.zip  (v0003 = domicílios particulares)
  --demografia  mesma pasta, Agregados_por_setores_demografia_BR.zip  (V01008 = mulheres; V01027 a V01030 = mulheres de 40 anos ou mais)

Saída: MISM 1/dados/referencia/mulheres_por_area_usf.csv (uma linha por área de USF). Só totais por área: nada de pessoa nem de endereço.
Precisa de pandas e shapely (só este script). Os setores sem dado no IBGE contam como zero e a soma fora das áreas é impressa.
"""
import argparse
import json
import math
import sqlite3
import zipfile
from pathlib import Path

import pandas as pd
from shapely import affinity, from_wkb
from shapely.geometry import shape

RAIZ = Path(__file__).resolve().parent
USF_GEOJSON = RAIZ / "dados" / "referencia" / "mapaRioClaroUSF.geojson"
SAIDA = RAIZ / "dados" / "referencia" / "mulheres_por_area_usf.csv"
COD_MUNICIPIO = "3543907"          # Rio Claro (SP)
LATITUDE_CIDADE = -22.4            # só para achatar a longitude (cos da latitude) ao medir frações de superfície
COLUNAS_MULHERES_40_MAIS = ["V01027", "V01028", "V01029", "V01030"]   # feminino: 40-49, 50-59, 60-69, 70 ou mais


def numero(serie):
    return pd.to_numeric(serie.astype(str).str.replace(".", "", regex=False), errors="coerce")


def ler_do_zip(caminho, filtro_coluna):
    """Linhas de Rio Claro de um CSV do IBGE dentro de um zip (o arquivo do Brasil inteiro é grande: lê em pedaços)."""
    zf = zipfile.ZipFile(caminho)
    nome = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
    pedacos = []
    for pedaco in pd.read_csv(zf.open(nome), sep=";", encoding="latin-1", dtype=str, chunksize=200_000):
        coluna = next(c for c in pedaco.columns if c.lower() == filtro_coluna.lower())
        pedacos.append(pedaco[pedaco[coluna].str.startswith(COD_MUNICIPIO)])
    return pd.concat(pedacos)


def geometria_do_geopackage(blob):
    """Geometria WKB de uma linha do GeoPackage (pula o cabeçalho de 8 bytes e o envelope, se houver)."""
    envelope = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[(blob[3] >> 1) & 7]
    return from_wkb(bytes(blob[8 + envelope:]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--setores", required=True)
    ap.add_argument("--basico", required=True)
    ap.add_argument("--demografia", required=True)
    args = ap.parse_args()

    basico = ler_do_zip(args.basico, "CD_SETOR").set_index("CD_SETOR")
    demografia = ler_do_zip(args.demografia, "CD_setor").set_index("CD_setor")
    tabela = pd.DataFrame(index=basico.index)
    tabela["domicilios"] = numero(basico["v0003"])
    tabela["mulheres"] = numero(demografia["V01008"]).reindex(tabela.index)
    tabela["mulheres_40_mais"] = demografia[COLUNAS_MULHERES_40_MAIS].apply(numero).sum(axis=1, min_count=1).reindex(tabela.index)
    tabela = tabela.fillna(0)

    achata = lambda g: affinity.scale(g, xfact=math.cos(math.radians(LATITUDE_CIDADE)), yfact=1, origin=(0, 0))
    con = sqlite3.connect(f"file:{args.setores}?mode=ro", uri=True)
    setores = {cd: achata(geometria_do_geopackage(blob)) for blob, cd in
               con.execute("SELECT geom, CD_SETOR FROM SP_setores_CD2022 WHERE CD_MUN = ?", (COD_MUNICIPIO,))}
    with open(USF_GEOJSON, encoding="utf-8") as f:
        areas = {ft["properties"]["nome"]: achata(shape(ft["geometry"])) for ft in json.load(f)["features"]
                 if ft["geometry"]["type"] == "Polygon" and ft["properties"].get("nome")}

    colunas = ["mulheres", "mulheres_40_mais", "domicilios"]
    por_area = {a: dict.fromkeys(colunas, 0.0) for a in areas}
    fora = dict.fromkeys(colunas, 0.0)
    for cd, g in setores.items():
        if cd not in tabela.index or g.area == 0:
            continue
        valores, dentro = tabela.loc[cd], 0.0
        for a, ga in areas.items():
            fracao = g.intersection(ga).area / g.area
            if fracao > 0:
                dentro += fracao
                for c in colunas:
                    por_area[a][c] += valores[c] * fracao
        for c in colunas:
            fora[c] += valores[c] * (1 - min(dentro, 1.0))

    saida = pd.DataFrame(por_area).T.round(0).astype(int)
    saida.index.name = "area_usf"
    saida = saida[colunas].sort_index()
    saida.to_csv(SAIDA, sep=";", encoding="utf-8")
    print(f"{len(saida)} áreas de USF gravadas em {SAIDA}")
    print("Município (soma dos setores):", {c: int(tabela[c].sum()) for c in colunas})
    print("Dentro das áreas de USF:     ", {c: int(saida[c].sum()) for c in colunas})
    print("Fora das áreas de USF:       ", {c: round(v) for c, v in fora.items()})


if __name__ == "__main__":
    main()
