"""Teste dos cálculos do Estudo de Rio Claro (idade ajustada e tendência): a matemática, com números conferíveis à mão, e os arquivos gerados.

Uso (da raiz do site):  python testes/teste_estudo_rio_claro.py      (precisa de scipy: só o script de cálculo usa, o site não)
"""
import json
import pathlib
import sys

import numpy as np
import pandas as pd

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "MISM 1"))
import calcular_estudo_rio_claro as ce  # noqa: E402

falhas = []


def checar(nome, ok):
    print(("OK   " if ok else "FALHOU ") + nome)
    if not ok:
        falhas.append(nome)


# ---- 1. margem de erro e chance de estar acima ----
baixo, alto = ce.ic_poisson_exato(10, 10)
checar("10 casos para 10 esperados: razão 1,0 dentro da margem (0,5 a 1,7) e a chance de estar acima é de cerca de 50%",
       0.45 < baixo < 0.60 and 1.55 < alto < 1.80 and 0.4 < ce.prob_acima(10, 10) < 0.6)
checar("0 casos: margem começa em zero e a chance de estar acima é pequena", ce.ic_poisson_exato(0, 5)[0] == 0.0 and ce.prob_acima(0, 5) < 0.1)
checar("o dobro do esperado com muitos casos: quase certeza de estar acima; a metade: quase certeza de estar abaixo",
       ce.prob_acima(100, 50) > 0.99 and ce.prob_acima(25, 50) < 0.01)
checar("mais casos, margem mais estreita (a mesma razão 1,5 com 10x os casos)",
       (lambda a, b: (b[1] - b[0]) < (a[1] - a[0]))(ce.ic_poisson_exato(15, 10), ce.ic_poisson_exato(150, 100)))

# ---- 2. padronização pela idade (3 áreas de brinquedo) ----
faixas = list(ce.FAIXAS)
mulheres = pd.DataFrame(0.0, index=["A", "B", "C"], columns=faixas)
mulheres.loc["A", ["m_40a49", "m_70mais"]] = [1000, 1000]          # A: metade jovem (40-49), metade idosa (70+)
mulheres.loc["B", ["m_40a49", "m_70mais"]] = [1900, 100]           # B: quase só jovem
mulheres.loc["C", ["m_40a49", "m_70mais"]] = [100, 1900]           # C: quase só idosa
casos = pd.DataFrame(0, index=["A", "B", "C"], columns=faixas)
casos.loc["A", ["m_40a49", "m_70mais"]] = [10, 100]
casos.loc["B", ["m_40a49", "m_70mais"]] = [19, 10]
casos.loc["C", ["m_40a49", "m_70mais"]] = [1, 190]
r = ce.razoes_por_idade(casos, mulheres).set_index("area_usf")
checar("o esperado soma exatamente os casos (a taxa de referência é a da própria cidade)", abs(r["esperado"].sum() - r["casos"].sum()) < 0.5)
checar("quem tem as mesmas taxas por idade da cidade (A, B e C) fica com razão perto de 1,0 mesmo com idades muito diferentes",
       all(0.85 < x < 1.15 for x in r["razao"]))
casos2 = casos.copy()
casos2.loc["C", "m_70mais"] = 380                                     # C passa a ter o dobro de internações por idade
r2 = ce.razoes_por_idade(casos2, mulheres).set_index("area_usf")
checar("dobrar as internações de uma área a faz subir de verdade (razão acima de 1,15 e chance de estar acima maior que 99%; as outras ficam abaixo de 1)",
       r2.loc["C", "razao"] > 1.15 and r2.loc["C", "prob_acima"] > 0.99 and r2.loc[["A", "B"], "razao"].lt(1).all())
checar("a margem de erro sempre envolve a razão", ((r2["ic90_baixo"] <= r2["razao"]) & (r2["razao"] <= r2["ic90_alto"])).all())
# o ponto da correção por idade: a taxa BRUTA de C é muito maior que a de B, mas a razão pela idade as iguala
taxa_bruta = casos.sum(axis=1) / mulheres.sum(axis=1)
checar("a taxa bruta enganaria (C tem 5x a taxa de B só por ser mais idosa), mas a razão pela idade as coloca lado a lado",
       taxa_bruta["C"] > 4 * taxa_bruta["B"] and abs(r.loc["C", "razao"] - r.loc["B", "razao"]) < 0.3)

# ---- 3. tendência ----
anos = list(range(2013, 2026))
doze = [12] * len(anos)
sobe = [100 * np.exp(0.10 * (a - 2013)) for a in anos]
pct, ic_b, ic_a, p, disp = ce.tendencia_poisson(anos, sobe, doze)
checar("série que cresce 10,5% ao ano exatos: o cálculo devolve 10,5% e a margem envolve esse valor", abs(pct - 10.517) < 0.3 and ic_b <= pct <= ic_a)
plano = ce.tendencia_poisson(anos, [50] * len(anos), doze)
checar("série plana: variação perto de zero e a margem envolve o zero", abs(plano[0]) < 0.5 and plano[1] < 0 < plano[2])
cai = ce.tendencia_poisson(anos, [100 * np.exp(-0.08 * (a - 2013)) for a in anos], doze)
checar("série que cai: variação negativa e a margem toda abaixo de zero", cai[0] < -5 and cai[2] < 0)
# meses que a fonte não oferece: mesma taxa mensal, só menos meses em alguns anos, não pode virar 'queda'
meses = [12 if a % 3 else 6 for a in anos]
mensal = ce.tendencia_poisson(anos, [4 * m for m in meses], meses)
checar("ano com a metade dos meses e metade das internações NÃO vira queda (a exposição é descontada)", abs(mensal[0]) < 0.5)

# ---- 4. os arquivos que o site lê ----
areas = pd.read_csv(ce.SAIDA_AREAS, sep=";", encoding="utf-8")
usf = json.load(open(RAIZ / "MISM 1" / "dados" / "referencia" / "mapaRioClaroUSF.geojson", encoding="utf-8"))
nomes = {f["properties"]["nome"] for f in usf["features"] if f["geometry"]["type"] == "Polygon" and f["properties"].get("nome")}
checar("o arquivo de áreas cobre as áreas de USF do mapa (mesmos nomes)", set(areas["area_usf"]) <= nomes and len(areas) >= 19)
checar("esperado total = casos totais (a referência é a própria cidade)", abs(areas["esperado"].sum() - areas["casos"].sum()) < 1)
checar("razão = casos / esperado, margem envolve a razão e a chance fica entre 0 e 1",
       (abs(areas["razao"] - areas["casos"] / areas["esperado"]) < 0.01).all() and ((areas["ic90_baixo"] <= areas["razao"]) & (areas["razao"] <= areas["ic90_alto"])).all()
       and areas["prob_acima"].between(0, 1).all())
tend = pd.read_csv(ce.SAIDA_TENDENCIA, sep=";", encoding="utf-8")
checar("a tendência tem os 7 cânceres e o total, e a margem envolve cada variação", len(tend) == 8 and "TODOS" in set(tend["tipo_cancer"])
       and ((tend["ic90_baixo"] <= tend["pct_ano"]) & (tend["pct_ano"] <= tend["ic90_alto"])).all())
checar("as internações dos 7 cânceres somam o total", tend.loc[tend["tipo_cancer"] != "TODOS", "internacoes"].sum() == tend.loc[tend["tipo_cancer"] == "TODOS", "internacoes"].iloc[0])
tamanhos = {len(s.split("|")) for s in tend["serie"]}
checar("toda série tem todos os anos da fonte (ano sem nenhuma internação entra como zero, não some da conta)", len(tamanhos) == 1)

if falhas:
    print(f"\n{len(falhas)} falha(s).")
    sys.exit(1)
print("\nTodas as checagens do estudo passaram.")
