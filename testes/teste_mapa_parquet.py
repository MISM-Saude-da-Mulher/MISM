"""Teste do mapa do grupo (Rio Claro): Parquet sem o AIH completo e privacidade (totais por área, sem dados por caso).

Uso (da raiz do site):  python testes/teste_mapa_parquet.py
Precisa de dados_parquet/aih/aih_rio_claro_geo.parquet (o site baixa do Hugging Face; ver HOSPEDAR.md).
"""
import json
import os
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


def registros_do_html(html):
    return json.loads(re.search(r"const rawData = (\[.*?\]);\n", html, re.S).group(1))


# ---- 1. o Parquet do mapa basta (sem o AIH completo) ----
geo = pd.read_parquet(gerar_mapa.PARQUET_GEO)
checar("o Parquet do mapa traz as colunas de que ele precisa (DIAS_PERM, MORTE, DIAG_PRINC)",
       all(c in geo.columns for c in ("DIAS_PERM", "MORTE", "DIAG_PRINC")))
gerar_mapa.PARQUET_AIH = pathlib.Path("/nao/existe/aih_cancer_mulheres.parquet")  # sem o AIH completo
os.environ.pop("MISM_MAPA_POR_CASO", None)
html = gerar_mapa.gerar_html()
registros = registros_do_html(html)
checar("gera o mapa sem o AIH completo", 0 < len(registros) <= len(geo))

# ---- 2. privacidade: totais por área, nada por caso ----
checar("nenhum registro traz CEP, logradouro ou CID", not any(r["cep"] or r["logradouro"] or r["cid"] for r in registros))
checar("as coordenadas são só os centros das áreas (poucos pontos, não um por caso)",
       len({(r["lat"], r["lng"]) for r in registros}) <= 25)
checar("o mapa explica a regra de pequenos números (grupos com menos de 5 casos são somados)", "Totais por área de USF" in html and "menos de 5" in html)
checar("não sobrou texto de 'coordenada' nem a linha de CEP no popup", "por coordenada" not in html and "CEP(s)" not in html)
checar("cada registro ainda tem área, doença e ano para os filtros do mapa",
       all(r["area_usf"] and r["doenca"] and "ano" in r for r in registros))

# ---- 3. a regra de 'menos de 5', com dados sintéticos ----
usf = {"features": [{"properties": {"nome": "Area A"}, "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]]}},
                    {"properties": {"nome": "Area B"}, "geometry": {"type": "Polygon", "coordinates": [[[10, 10], [12, 10], [12, 12], [10, 12], [10, 10]]]}}]}
cidade = {"features": [{"geometry": {"type": "Polygon", "coordinates": [[[0, 0], [20, 0], [20, 20], [0, 20], [0, 0]]]}}]}


def caso(area, doenca, ano, idade, valor=100.0, morte=False):
    return {"cep": "13500000", "bairro": area, "area_usf": area, "logradouro": "Rua X", "lat": 1.234567, "lng": 7.654321, "idade": idade,
            "ano": ano, "valor": valor, "dias": 3, "morte": morte, "cid": "C509", "cid_desc": "x", "doenca": doenca}


casos = ([caso("Area A", "Mama", "2021", 55, 200.0) for _ in range(6)]                    # grupo de 6: aparece
         + [caso("Area A", "Mama", "2022", 52) for _ in range(2)] + [caso("Area A", "Pulmão", "2023", 58) for _ in range(3)]  # 2 + 3 (mesma faixa): somam 5 no restante
         + [caso("Area A", "Colorretal", "2021", 60) for _ in range(3)] + [caso("Area A", "Colorretal", "2022", 61) for _ in range(3)]  # 3 + 3: soma 6 na doença
         + [caso("Area B", "Mama", "2021", 45) for _ in range(4)])                           # 4 casos: some
agg, ocultos, sem_nada = gerar_mapa.agregar_por_area(casos, usf, cidade)
checar("grupo com 6 casos aparece", sum(1 for r in agg if r["area_usf"] == "Area A" and r["doenca"] == "Mama" and r["ano"] == "2021") == 6)
checar("grupos pequenos da mesma doença somam anos e faixas e mantêm a doença (o filtro de doença continua valendo)",
       sum(1 for r in agg if r["doenca"] == "Colorretal" and r["area_usf"] == "Area A" and r["restante"] and r["ano"] == "") == 6)
checar("o que ainda sobra se junta por área em 'Outros (poucos casos)' e atinge 5",
       sum(1 for r in agg if r["doenca"] == "Outros (poucos casos)" and r["area_usf"] == "Area A") == 5)
checar("o filtro de faixa etária ignora o 'restante' (ele mistura faixas)", "item.restante && filtroFaixaAtiva" in html)
checar("nenhum caso se perde sem aviso: o que aparece + o que fica oculto = o total",
       len(agg) + ocultos == len(casos))
checar("área com só 4 casos não aparece e é contada como oculta", not any(r["area_usf"] == "Area B" for r in agg) and ocultos == 4 and sem_nada == ["Area B"])
checar("o valor total é preservado nos grupos que aparecem", abs(sum(r["valor"] for r in agg if r["area_usf"] == "Area A" and r["ano"] == "2021") - 1200.0) < 1e-6)
checar("nenhum registro agregado guarda CEP, rua, CID nem a coordenada do caso",
       not any(r["cep"] or r["logradouro"] or r["cid"] or (r["lat"], r["lng"]) == (1.234567, 7.654321) for r in agg))
checar("o ponto de cada área é o centro dela", {(r["lat"], r["lng"]) for r in agg if r["area_usf"] == "Area A"} == {(1.0, 1.0)})

# ---- 4. uso interno do grupo: o mapa original, caso a caso, continua disponível ----
os.environ["MISM_MAPA_POR_CASO"] = "1"
por_caso = registros_do_html(gerar_mapa.gerar_html())
os.environ.pop("MISM_MAPA_POR_CASO", None)
checar("com MISM_MAPA_POR_CASO=1 o mapa volta a ser caso a caso", len(por_caso) == len(geo) and any(r["cep"] for r in por_caso))
html_detalhado = gerar_mapa.gerar_html(por_caso=True)          # é o que a opção "Casos detalhados" da página do mapa usa
detalhado = registros_do_html(html_detalhado)
checar("a opção 'Casos detalhados' mostra todas as internações públicas do SIH/SUS", len(detalhado) == len(geo) and "base pública do DATASUS" in html_detalhado)
checar("sem a opção, o padrão continua sendo os totais por área", len(registros_do_html(gerar_mapa.gerar_html(por_caso=False))) == len(registros))

if falhas:
    print(f"\n{len(falhas)} falha(s).")
    sys.exit(1)
print("\nTodas as checagens do mapa passaram.")
