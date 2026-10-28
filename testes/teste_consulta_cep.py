"""Consulta por CEP do mapa: área de USF, UBS mais perto e erros (sem rede; as APIs são simuladas)."""
import pathlib, sys
RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "MISM 1"))
import consulta_cep as c

falhas = []
def checar(nome, ok):
    print(("OK   " if ok else "FALHOU ") + nome)
    if not ok: falhas.append(nome)

areas, ubs = c.carregar_areas()
checar("lê as 21 áreas e as 21 UBS do arquivo do grupo", len(areas) == 21 and len(ubs) == 21)
checar("normaliza o CEP", c.normalizar_cep("13.500-000") == "13500000" and c.normalizar_cep("123") is None and c.normalizar_cep(None) is None)

nome, anel = areas[0]
lon = sum(p[0] for p in anel) / len(anel); lat = sum(p[1] for p in anel) / len(anel)
dentro = [n for n, a in areas if c._dentro(lon, lat, a)]
checar("o centro de uma área cai em alguma área (ponto em polígono funciona)", len(dentro) >= 1)
checar("um ponto no meio do oceano não cai em área nenhuma", c.area_do_ponto(0.0, 0.0, areas) is None)
perto = c.ubs_mais_proximas(ubs[0]["lat"], ubs[0]["lon"], ubs)
checar("a UBS mais perto de uma UBS é ela mesma, a 0 km, e vêm 3 em ordem", perto[0]["nome"] == ubs[0]["nome"] and perto[0]["km"] < 0.001 and len(perto) == 3 and perto[0]["km"] <= perto[1]["km"] <= perto[2]["km"])

def fake_brasil(url):
    if "brasilapi" in url: return {"street": "Rua X", "neighborhood": "Centro", "city": "Rio Claro", "location": {"coordinates": {"latitude": str(lat), "longitude": str(lon)}}}
    raise RuntimeError("fora do ar")
r = c.consultar("13500-000", areas, ubs, fake_brasil)
checar("consulta completa: posição, área e 3 UBS, com a fonte", "erro" not in r and r["fonte"] == "BrasilAPI" and r["area"] in dentro and len(r["ubs"]) == 3)

def so_awesome(url):
    if "awesomeapi" in url: return {"address": "Rua Y", "district": "Bairro", "city": "Rio Claro", "lat": str(lat), "lng": str(lon)}
    raise RuntimeError("429")
checar("se a primeira fonte falha, usa a segunda", c.consultar("13500000", areas, ubs, so_awesome).get("fonte") == "AwesomeAPI")
checar("CEP de outra cidade é recusado com o nome da cidade",
       "Campinas" in c.consultar("13010000", areas, ubs, lambda u: {"city": "Campinas", "lat": "-22.9", "lng": "-47.0", "location": {"coordinates": {"latitude": "-22.9", "longitude": "-47.0"}}}).get("erro", ""))
checar("coordenada genérica (centro da cidade) é recusada, não vira área",
       "não trazem a posição" in c.consultar("13500110", areas, ubs, lambda u: {"city": "Rio Claro", "lat": "-22.41139", "lng": "-47.56139", "location": {"coordinates": {"latitude": "-22.41139", "longitude": "-47.56139"}}}).get("erro", ""))
checar("CEP sem coordenada nas fontes diz isso, sem inventar posição", "não trazem a posição" in c.consultar("13500000", areas, ubs, lambda u: {"city": "Rio Claro", "location": {}}).get("erro", ""))
def fora(url): raise RuntimeError("sem rede")
checar("sem rede: mensagem de erro clara, sem quebrar", "Não consegui consultar" in c.consultar("13500000", areas, ubs, fora)["erro"])
checar("CEP inválido não chama a rede", "8 números" in c.consultar("12", areas, ubs, fora)["erro"])
if falhas: print(f"\n{len(falhas)} falha(s)."); sys.exit(1)
print("\nTodas as checagens da consulta por CEP passaram.")
