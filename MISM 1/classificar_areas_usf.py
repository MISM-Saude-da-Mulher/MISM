"""Classifica os casos exclusivamente pelas áreas fixas das USFs.

Regra territorial única do projeto:
    LATITUDE/LONGITUDE do caso
        -> ponto espacial
        -> mapaRioClaroUSF.geojson
        -> AREA_USF

Nenhum campo de bairro e nenhuma API externa são usados para classificação.
"""

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

RAIZ_PROJETO = Path(__file__).resolve().parents[0]
ARQUIVO_ENTRADA = RAIZ_PROJETO / "dados" / "processados" / "saude_mulher_rio_claro_georreferenciado.csv"
ARQUIVO_GEOJSON = RAIZ_PROJETO / "dados" / "referencia" / "mapaRioClaroUSF.geojson"
ARQUIVO_SAIDA_CSV = RAIZ_PROJETO / "dados" / "processados" / "casos_por_area_usf.csv"
ARQUIVO_SAIDA_JSON = RAIZ_PROJETO / "dados" / "processados" / "casos_por_area_usf.json"


def main():
    print("=" * 72)
    print("CLASSIFICAÇÃO TERRITORIAL — ÁREAS USF")
    print("=" * 72)

    if not ARQUIVO_ENTRADA.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {ARQUIVO_ENTRADA}")
    if not ARQUIVO_GEOJSON.exists():
        raise FileNotFoundError(f"GeoJSON não encontrado: {ARQUIVO_GEOJSON}")

    df = pd.read_csv(ARQUIVO_ENTRADA, sep=";", dtype={"CEP_NORMALIZADO": str})
    areas = gpd.read_file(ARQUIVO_GEOJSON)

    if "nome" not in areas.columns:
        raise ValueError("O mapaRioClaroUSF.geojson não possui a propriedade 'nome' esperada para AREA_USF.")

    areas = areas[areas.geometry.notna()].copy()
    areas = areas[areas.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
    areas = areas[areas["nome"].notna()].copy()
    areas = areas[["nome", "geometry"]].rename(columns={"nome": "AREA_USF"})

    if areas.empty:
        raise ValueError("Nenhum polígono territorial foi encontrado no mapaRioClaroUSF.geojson.")

    if areas.crs is None:
        areas = areas.set_crs("EPSG:4326")
    else:
        areas = areas.to_crs("EPSG:4326")

    df["LATITUDE"] = pd.to_numeric(df.get("LATITUDE"), errors="coerce")
    df["LONGITUDE"] = pd.to_numeric(df.get("LONGITUDE"), errors="coerce")

    geometrias = [
        Point(lon, lat) if pd.notna(lat) and pd.notna(lon) else None
        for lat, lon in zip(df["LATITUDE"], df["LONGITUDE"])
    ]

    casos = gpd.GeoDataFrame(df.copy(), geometry=geometrias, crs="EPSG:4326")

    # Primeiro within; depois intersects apenas para pontos exatamente na fronteira.
    classificados = gpd.sjoin(casos, areas, how="left", predicate="within")

    sem_area = classificados["AREA_USF"].isna()
    if sem_area.any():
        casos_sem_area = casos.loc[sem_area].copy()
        if not casos_sem_area.empty:
            fronteira = gpd.sjoin(casos_sem_area, areas, how="left", predicate="intersects")
            classificados.loc[sem_area, "AREA_USF"] = fronteira["AREA_USF"].to_numpy()

    classificados["AREA_USF"] = classificados["AREA_USF"].fillna("NÃO CLASSIFICADO")
    classificados["STATUS_AREA_USF"] = classificados["AREA_USF"].where(
        classificados["AREA_USF"].eq("NÃO CLASSIFICADO"), "CLASSIFICADO"
    )

    classificados = pd.DataFrame(
        classificados.drop(columns=[c for c in ["geometry", "index_right"] if c in classificados.columns])
    )

    # Remove possíveis duplicações da junção em geometria sobreposta, sem remover casos.
    # Se o GeoJSON tiver polígonos sobrepostos, mantemos a primeira área encontrada.
    classificados = classificados.loc[~classificados.index.duplicated(keep="first")].reset_index(drop=True)

    ARQUIVO_SAIDA_CSV.parent.mkdir(parents=True, exist_ok=True)
    classificados.to_csv(ARQUIVO_SAIDA_CSV, sep=";", index=False, encoding="utf-8-sig")

    resumo = []
    for area, grupo in classificados.groupby("AREA_USF", dropna=False):
        lat = pd.to_numeric(grupo["LATITUDE"], errors="coerce")
        lon = pd.to_numeric(grupo["LONGITUDE"], errors="coerce")
        resumo.append({
            "area_usf": str(area),
            "casos": int(len(grupo)),
            "casos_com_coordenada": int((lat.notna() & lon.notna()).sum()),
            "casos_sem_coordenada": int((lat.isna() | lon.isna()).sum()),
            "latitude_casos_media": round(lat.mean(), 6) if lat.notna().any() else None,
            "longitude_casos_media": round(lon.mean(), 6) if lon.notna().any() else None,
        })

    with open(ARQUIVO_SAIDA_JSON, "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)

    classificados_count = int((classificados["AREA_USF"] != "NÃO CLASSIFICADO").sum())
    sem_area_count = len(classificados) - classificados_count

    print(f"Registros totais:       {len(classificados)}")
    print(f"Casos classificados:    {classificados_count}")
    print(f"Sem área USF:           {sem_area_count}")
    print(f"Áreas USF encontradas:  {classificados['AREA_USF'].nunique()}")
    print(f"CSV salvo em:           {ARQUIVO_SAIDA_CSV}")
    print(f"Resumo salvo em:        {ARQUIVO_SAIDA_JSON}")


if __name__ == "__main__":
    main()
