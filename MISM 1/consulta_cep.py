"""Consulta por CEP no Mapa de Rio Claro: em qual área de USF fica o CEP e quais UBS estão mais perto (28/10/2026).

Decisão (autor delegou ao Claude): sem tabela de CEP com coordenadas do Google (os termos do Google restringem guardar o resultado).
A coordenada vem na hora das APIs públicas gratuitas que o grupo já usava (BrasilAPI v2, depois AwesomeAPI); nada é gravado: nem o CEP,
nem a coordenada. As áreas e as UBS vêm do arquivo do grupo (mapaRioClaroUSF.geojson).

Limites que a página precisa dizer: o CEP dá a posição da RUA (ou do CEP), não da casa; as áreas são as do mapa do grupo, não um
limite oficial; a UBS "mais perto" é em linha reta, não é a unidade de referência da pessoa.
"""
import json
import math
import re
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
USF_GEOJSON = RAIZ / "dados" / "referencia" / "mapaRioClaroUSF.geojson"
CODIGO_IBGE_RIO_CLARO = "3543907"

# A BrasilAPI devolve este mesmo ponto (o centro de Rio Claro) para QUALQUER CEP da cidade (conferido em 28/10/2026 com 5 CEPs):
# não é a posição da rua, e usá-lo mostraria sempre a mesma área. Coordenada assim é recusada.
COORDENADAS_GENERICAS = {(-22.4114, -47.5614)}


def _generica(lat, lon):
    return (round(lat, 4), round(lon, 4)) in COORDENADAS_GENERICAS


def normalizar_cep(valor):
    """'13.500-000' -> '13500000'; None se não tiver 8 dígitos."""
    digitos = re.sub(r"\D", "", str(valor or ""))
    return digitos if len(digitos) == 8 else None


def carregar_areas(caminho=USF_GEOJSON):
    """([(nome, anel)], [UBS]) do arquivo do grupo. Anel = lista de (lon, lat); UBS = dict com nome, endereço, telefone, horário, lat, lon."""
    with open(caminho, encoding="utf-8") as f:
        dados = json.load(f)
    areas, ubs = [], []
    for item in dados.get("features", []):
        geo, prop = item.get("geometry") or {}, item.get("properties") or {}
        if geo.get("type") == "Polygon" and prop.get("nome") and geo.get("coordinates"):
            areas.append((prop["nome"], [(p[0], p[1]) for p in geo["coordinates"][0]]))
        elif geo.get("type") == "Point" and prop.get("nome"):
            lon, lat = geo["coordinates"][:2]
            ubs.append({**{k: prop.get(k, "") for k in ("nome", "endereco", "telefone", "horario")}, "lat": lat, "lon": lon})
    return areas, ubs


def _dentro(lon, lat, anel):
    """Ponto no polígono (regra do número de cruzamentos)."""
    dentro = False
    j = len(anel) - 1
    for i in range(len(anel)):
        xi, yi = anel[i]
        xj, yj = anel[j]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            dentro = not dentro
        j = i
    return dentro


def area_do_ponto(lat, lon, areas):
    """Nome da área de USF que contém o ponto, ou None (fora das áreas mapeadas)."""
    return next((nome for nome, anel in areas if _dentro(lon, lat, anel)), None)


def distancia_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def ubs_mais_proximas(lat, lon, ubs, quantas=3):
    """As UBS mais perto em linha reta, com a distância em km."""
    return [{**u, "km": distancia_km(lat, lon, u["lat"], u["lon"])}
            for u in sorted(ubs, key=lambda u: distancia_km(lat, lon, u["lat"], u["lon"]))[:quantas]]


def _pegar_json(url, tempo=8):
    pedido = urllib.request.Request(url, headers={"User-Agent": "MISM/1.0 (consulta por CEP)"})
    with urllib.request.urlopen(pedido, timeout=tempo) as resposta:
        return json.loads(resposta.read().decode("utf-8"))


def localizar_cep(cep, buscar=_pegar_json):
    """Coordenada do CEP pelas APIs públicas: {'lat','lon','rua','bairro','cidade','fonte'} ou {'erro': texto}. `buscar` é trocável nos testes."""
    cep = normalizar_cep(cep)
    if not cep:
        return {"erro": "Digite um CEP com 8 números."}
    tentativas = [
        ("AwesomeAPI", f"https://cep.awesomeapi.com.br/json/{cep}",
         lambda d: d.get("lat"), lambda d: d.get("lng"),
         lambda d: (d.get("address", ""), d.get("district", ""), d.get("city", ""))),
        ("BrasilAPI", f"https://brasilapi.com.br/api/cep/v2/{cep}",
         lambda d: ((d.get("location") or {}).get("coordinates") or {}).get("latitude"),
         lambda d: ((d.get("location") or {}).get("coordinates") or {}).get("longitude"),
         lambda d: (d.get("street", ""), d.get("neighborhood", ""), d.get("city", ""))),
    ]
    achou_sem_coordenada = False
    for fonte, url, pega_lat, pega_lon, pega_texto in tentativas:
        try:
            dados = buscar(url)
            lat, lon = float(pega_lat(dados)), float(pega_lon(dados))
            rua, bairro, cidade = pega_texto(dados)
            if _generica(lat, lon):
                achou_sem_coordenada = True
                continue                      # centro da cidade, não a posição do CEP
            return {"lat": lat, "lon": lon, "rua": rua, "bairro": bairro, "cidade": cidade, "fonte": fonte, "cep": cep}
        except (TypeError, ValueError):
            achou_sem_coordenada = True      # o CEP existe, mas a fonte não trouxe coordenada
        except Exception:
            continue                          # rede, 404, limite de uso: tenta a próxima fonte
    if achou_sem_coordenada:
        return {"erro": "Esse CEP existe, mas as fontes públicas não trazem a posição dele. Procure pelo bairro no mapa."}
    return {"erro": "Não consegui consultar esse CEP agora (CEP não encontrado ou fontes fora do ar). Confira os números ou tente mais tarde."}


def consultar(cep, areas, ubs, buscar=_pegar_json):
    """Resposta completa da consulta: posição, área de USF e UBS mais perto. Em caso de erro, {'erro': texto}."""
    pos = localizar_cep(cep, buscar)
    if "erro" in pos:
        return pos
    if pos["cidade"] and "rio claro" not in pos["cidade"].lower():
        return {"erro": f"Esse CEP é de {pos['cidade']}. O mapa cobre só Rio Claro."}
    return {**pos, "area": area_do_ponto(pos["lat"], pos["lon"], areas), "ubs": ubs_mais_proximas(pos["lat"], pos["lon"], ubs)}
