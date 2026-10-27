"""
Georreferencia as sete bases de Saúde da Mulher de Rio Claro.
Prioridade: banco local resumido3_com_coordenadas_google.csv, por CEP.
APIs são consultadas apenas quando não há coordenada válida no banco/cache.
Não usa bairro para classificar território e não inventa coordenadas.
"""
import asyncio
import json
from pathlib import Path

import httpx
import pandas as pd

RAIZ_PROJETO = Path(__file__).resolve().parents[0]
DIRETORIO_BRUTOS = RAIZ_PROJETO / "dados" / "brutos"
ARQUIVO_BANCO_CEP = RAIZ_PROJETO / "dados" / "referencia" / "resumido3_com_coordenadas_google.csv"
ARQUIVO_CSV_SAIDA = RAIZ_PROJETO / "dados" / "processados" / "saude_mulher_rio_claro_georreferenciado.csv"
CACHE_FILE = RAIZ_PROJETO / "dados" / "cache" / "ceps_rio_claro.json"

ARQUIVOS_CSV_ENTRADA = [
    ("cancer_mama_mulheres_rio_claro_2021_2025.csv", "Câncer de Mama"),
    ("cancer_colo_utero_mulheres_rio_claro_2021_2025.csv", "Câncer do Colo do Útero"),
    ("cancer_colorretal_mulheres_rio_claro_2021_2025.csv", "Câncer Colorretal"),
    ("cancer_ovario_mulheres_rio_claro_2021_2025.csv", "Câncer de Ovário"),
    ("cancer_pele_nao_melanoma_mulheres_rio_claro_2021_2025.csv", "Câncer de Pele (Não Melanoma)"),
    ("cancer_pulmao_mulheres_rio_claro_2021_2025.csv", "Câncer de Pulmão"),
    ("cancer_tireoide_mulheres_rio_claro_2021_2025.csv", "Câncer de Tireoide"),
]
LAT_MIN, LAT_MAX = -22.60, -22.20
LON_MIN, LON_MAX = -47.80, -47.35
COORDENADA_PROBLEMATICA = (-22.411390, -47.561390)


def normalizar_cep(valor):
    if pd.isna(valor):
        return None
    digitos = "".join(c for c in str(valor).split(".")[0] if c.isdigit())
    if not digitos or len(digitos) > 8:
        return None
    digitos = digitos.zfill(8)
    return None if digitos == "00000000" else digitos


def ler_csv(caminho):
    # O banco fornecido é separado por ponto e vírgula; as bases do projeto
    # também costumam usar esse separador. Tenta autodetecção se necessário.
    try:
        df = pd.read_csv(caminho, sep=";", dtype=str, low_memory=False)
        if len(df.columns) == 1:
            df = pd.read_csv(caminho, sep=None, engine="python", dtype=str, low_memory=False)
        return df
    except Exception:
        return pd.read_csv(caminho, sep=None, engine="python", dtype=str, low_memory=False)


def coordenada_valida(lat, lon):
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError):
        return False
    if not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
        return False
    return not (round(lat, 6) == COORDENADA_PROBLEMATICA[0]
                and round(lon, 6) == COORDENADA_PROBLEMATICA[1])


def carregar_banco_cep():
    if not ARQUIVO_BANCO_CEP.exists():
        raise FileNotFoundError(
            f"Banco de CEPs não encontrado: {ARQUIVO_BANCO_CEP}\n"
            "Coloque resumido3_com_coordenadas_google.csv em dados/referencia/."
        )
    banco = ler_csv(ARQUIVO_BANCO_CEP)
    banco.columns = [str(c).strip().lstrip("\\ufeff") for c in banco.columns]
    obrigatorias = {"CEP", "Latitude", "Longitude"}
    if not obrigatorias.issubset(banco.columns):
        raise ValueError(f"O banco de CEPs precisa conter as colunas {sorted(obrigatorias)}. Encontradas: {banco.columns.tolist()}")
    banco["CEP_NORMALIZADO"] = banco["CEP"].map(normalizar_cep)
    banco["LAT_NUM"] = pd.to_numeric(banco["Latitude"].astype(str).str.replace(",", ".", regex=False), errors="coerce")
    banco["LON_NUM"] = pd.to_numeric(banco["Longitude"].astype(str).str.replace(",", ".", regex=False), errors="coerce")
    validos = banco.apply(lambda r: coordenada_valida(r["LAT_NUM"], r["LON_NUM"]), axis=1)
    banco = banco[validos & banco["CEP_NORMALIZADO"].notna()].copy()

    # O banco enviado tem CEP único. Se uma versão futura tiver duplicatas,
    # mantém a primeira coordenada válida para cada CEP.
    banco = banco.drop_duplicates("CEP_NORMALIZADO", keep="first")
    mapa = {}
    for _, row in banco.iterrows():
        mapa[row["CEP_NORMALIZADO"]] = {
            "cep": row["CEP_NORMALIZADO"],
            "lat": float(row["LAT_NUM"]),
            "lon": float(row["LON_NUM"]),
            "bairro": str(row.get("Bairro", "") or ""),
            "logradouro": str(row.get("Logradouro", "") or ""),
            "fonte": "BANCO_GOOGLE",
            "motivo_falha": "",
            "status_awesomeapi": "",
            "status_brasilapi": "",
        }
    return mapa, len(banco)


def carregar_cache():
    if not CACHE_FILE.exists():
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
        return dados if isinstance(dados, dict) else {}
    except Exception as erro:
        print(f"[AVISO] Cache inválido; será recriado: {erro}")
        return {}


def salvar_cache(cache):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = CACHE_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    tmp.replace(CACHE_FILE)


def tem_coord(item):
    return isinstance(item, dict) and coordenada_valida(item.get("lat"), item.get("lon"))


async def requisicao_json(client, url, tentativas=2):
    ultimo_erro = ""
    for tentativa in range(tentativas):
        try:
            resposta = await client.get(url, timeout=10.0)
            try:
                dados = resposta.json()
            except Exception:
                dados = None
            return resposta.status_code, dados
        except httpx.HTTPError as erro:
            ultimo_erro = str(erro)
            if tentativa + 1 < tentativas:
                await asyncio.sleep(0.8)
    return None, {"_erro": ultimo_erro}


async def buscar_api(client, cep, cache, sem):
    # Cache somente depois do banco local; não sobrescreve coordenada do banco.
    if tem_coord(cache.get(cep)):
        item = dict(cache[cep])
        item["fonte"] = "CACHE"
        return item

    resultado = {
        "cep": cep, "logradouro": "", "bairro": "", "lat": None, "lon": None,
        "fonte": "", "motivo_falha": "", "status_awesomeapi": "", "status_brasilapi": ""
    }
    async with sem:
        status, data = await requisicao_json(client, f"https://cep.awesomeapi.com.br/json/{cep}")
        resultado["status_awesomeapi"] = str(status or "ERRO_REDE")
        if status == 200 and isinstance(data, dict):
            resultado["bairro"] = data.get("district") or ""
            resultado["logradouro"] = data.get("address") or ""
            lat, lon = data.get("lat"), data.get("lng")
            if coordenada_valida(lat, lon):
                resultado.update(lat=float(lat), lon=float(lon), fonte="AwesomeAPI")

        if resultado["lat"] is None:
            status, data = await requisicao_json(client, f"https://brasilapi.com.br/api/cep/v2/{cep}")
            resultado["status_brasilapi"] = str(status or "ERRO_REDE")
            if status == 200 and isinstance(data, dict):
                resultado["logradouro"] = resultado["logradouro"] or data.get("street") or ""
                resultado["bairro"] = resultado["bairro"] or data.get("neighborhood") or ""
                coords = (data.get("location") or {}).get("coordinates") or {}
                lat, lon = coords.get("latitude"), coords.get("longitude")
                if coordenada_valida(lat, lon):
                    resultado.update(lat=float(lat), lon=float(lon), fonte="BrasilAPI")

        if not resultado["bairro"] or not resultado["logradouro"]:
            status, data = await requisicao_json(client, f"https://viacep.com.br/ws/{cep}/json/")
            if status == 200 and isinstance(data, dict) and not data.get("erro"):
                resultado["bairro"] = resultado["bairro"] or data.get("bairro") or ""
                resultado["logradouro"] = resultado["logradouro"] or data.get("logradouro") or ""

        if resultado["lat"] is None:
            if resultado["status_awesomeapi"] in {"429", "500", "502", "503", "504", "ERRO_REDE"} or resultado["status_brasilapi"] in {"429", "500", "502", "503", "504", "ERRO_REDE"}:
                resultado["motivo_falha"] = "FALHA_TRANSITORIA_DA_API"
            elif resultado["status_awesomeapi"] == "404" and resultado["status_brasilapi"] == "404":
                resultado["motivo_falha"] = "CEP_NAO_ENCONTRADO_NAS_APIS"
            else:
                resultado["motivo_falha"] = "SEM_COORDENADA_VALIDADA"
        cache[cep] = resultado
    return resultado


async def main():
    print("=" * 72)
    print("GEORREFERENCIAMENTO — BANCO LOCAL DE CEPs + APIs COMO FALLBACK")
    print("=" * 72)

    banco, total_banco = carregar_banco_cep()
    print(f"CEPs com coordenadas válidas no banco local: {total_banco}")

    dfs = []
    for nome, doenca in ARQUIVOS_CSV_ENTRADA:
        caminho = DIRETORIO_BRUTOS / nome
        if not caminho.exists():
            print(f"[AVISO] Não encontrado: {caminho}")
            continue
        df_temp = ler_csv(caminho)
        if "CEP" not in df_temp.columns:
            print(f"[AVISO] Ignorado (sem coluna CEP): {nome}")
            continue
        df_temp["DOENCA"] = doenca
        dfs.append(df_temp)
        print(f"{doenca}: {len(df_temp)} registros")
    if not dfs:
        raise FileNotFoundError("Nenhuma das sete bases foi encontrada em dados/brutos.")

    df = pd.concat(dfs, ignore_index=True, sort=False)
    df["CEP_NORMALIZADO"] = df["CEP"].map(normalizar_cep)
    ceps = sorted(df["CEP_NORMALIZADO"].dropna().unique())
    cache = carregar_cache()

    # Ordem de prioridade: banco local -> cache/API. A API só recebe CEP
    # para o qual o banco local não oferece uma coordenada válida.
    faltantes_banco = [cep for cep in ceps if cep not in banco]
    ceps_api = [cep for cep in faltantes_banco if not tem_coord(cache.get(cep))]
    print(f"\nRegistros combinados: {len(df)}")
    print(f"CEPs únicos válidos nos casos: {len(ceps)}")
    print(f"CEPs resolvidos diretamente pelo banco: {len([c for c in ceps if c in banco])}")
    print(f"CEPs fora do banco com coordenada válida no cache: {len([c for c in faltantes_banco if tem_coord(cache.get(c))])}")
    print(f"CEPs que precisam de consulta à API: {len(ceps_api)}")

    sem = asyncio.Semaphore(8)
    headers = {"User-Agent": "RioClaroSaudeMulherMap/5.0", "Accept": "application/json"}
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        for inicio in range(0, len(ceps_api), 30):
            lote = ceps_api[inicio:inicio + 30]
            await asyncio.gather(*(buscar_api(client, cep, cache, sem) for cep in lote))
            salvar_cache(cache)
            print(f"CEPs consultados por API: {min(inicio + len(lote), len(ceps_api))}/{len(ceps_api)}")
            if inicio + len(lote) < len(ceps_api):
                await asyncio.sleep(1)
    salvar_cache(cache)

    def obter(cep, campo, padrao=""):
        if not cep:
            return padrao
        item = banco.get(cep)
        if item and campo in item:
            return item.get(campo, padrao)
        item = cache.get(cep, {})
        return item.get(campo, padrao)

    df["LATITUDE"] = df["CEP_NORMALIZADO"].map(lambda c: obter(c, "lat", None))
    df["LONGITUDE"] = df["CEP_NORMALIZADO"].map(lambda c: obter(c, "lon", None))
    df["BAIRRO_API"] = df["CEP_NORMALIZADO"].map(lambda c: obter(c, "bairro", ""))
    df["LOGRADOURO"] = df["CEP_NORMALIZADO"].map(lambda c: obter(c, "logradouro", ""))
    df["FONTE_GEO"] = df["CEP_NORMALIZADO"].map(
        lambda c: "BANCO_GOOGLE" if c in banco else obter(c, "fonte", "")
    )
    df["MOTIVO_FALHA_GEO"] = df["CEP_NORMALIZADO"].map(lambda c: obter(c, "motivo_falha", ""))
    df["STATUS_AWESOMEAPI"] = df["CEP_NORMALIZADO"].map(lambda c: obter(c, "status_awesomeapi", ""))
    df["STATUS_BRASILAPI"] = df["CEP_NORMALIZADO"].map(lambda c: obter(c, "status_brasilapi", ""))

    for coluna in ["IDADE", "DT_INTER", "VAL_TOT"]:
        if coluna not in df.columns:
            df[coluna] = ""
    df["IDADE_ANOS"] = pd.to_numeric(df["IDADE"], errors="coerce")
    df["ANO_INTERNACAO"] = df["DT_INTER"].astype(str).str.extract(r"(\d{4})", expand=False)
    df["VAL_TOT_NUM"] = pd.to_numeric(
        df["VAL_TOT"].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
        errors="coerce"
    )

    ARQUIVO_CSV_SAIDA.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ARQUIVO_CSV_SAIDA, sep=";", index=False, encoding="utf-8-sig")

    tem = df["LATITUDE"].notna() & df["LONGITUDE"].notna()
    print("\n" + "=" * 72)
    print("RESULTADO")
    print("=" * 72)
    print(f"Registros totais:       {len(df)}")
    print(f"Com coordenadas:        {int(tem.sum())}")
    print(f"Sem coordenadas:        {int((~tem).sum())}")
    print(f"Cobertura geográfica:   {(tem.mean() * 100) if len(df) else 0:.1f}%")
    print("\nRegistros com coordenadas por fonte:")
    print(df.loc[tem, "FONTE_GEO"].value_counts().to_string())
    print(f"\nArquivo salvo em: {ARQUIVO_CSV_SAIDA}")


if __name__ == "__main__":
    asyncio.run(main())
