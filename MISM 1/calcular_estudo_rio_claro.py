"""Cálculos do Estudo de Rio Claro: (1) quem está acima do esperado pela idade e (2) a tendência de cada câncer. Rodar no notebook.

    python "MISM 1/calcular_estudo_rio_claro.py"

Grava dois arquivos pequenos em MISM 1/dados/referencia/, que o site só lê (assim o site não precisa de scipy):
  estudo_areas_idade_ajustada.csv     uma linha por área de USF: casos, esperado pela idade, razão, margem de erro (90%), chance de estar acima
  estudo_tendencia_por_cancer.csv     uma linha por câncer: variação por ano, margem de erro (90%) e a série por ano (ajustada pelos meses da fonte)

(1) Padronização INDIRETA pela idade. Para cada faixa de idade, a taxa de referência é a de Rio Claro inteiro (casos das áreas / mulheres das áreas).
    Esperado de uma área = soma, nas faixas, de (mulheres da área na faixa x taxa de referência da faixa). Razão = casos / esperado:
    1,0 é "o que a idade das mulheres explica"; 1,5 é 50% a mais. Margem de erro: intervalo exato de Poisson de 90% (Garwood).
    "Chance de estar acima" = probabilidade a posteriori de a razão passar de 1, com um prior fraco (Gamma(1, 1)) que encolhe áreas com poucos casos.
(2) Tendência: regressão de Poisson do número de internações de moradoras por ano, com o número de meses que a fonte tem em cada ano como
    exposição (mês que a fonte não oferece não é zero). Devolve a variação % por ano e a margem de erro de 90%, alargada quando os dados oscilam
    mais do que Poisson (superdispersão). É TENDÊNCIA do período, não previsão.
Limites: conta internações do SUS (SIH), não pessoas nem casos novos; quem tem plano particular não aparece; a idade vem dos casos que têm
área de USF classificada (2021-2025); o Censo é de 2022.
"""
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import optimize, stats

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ.parent / "MISM2" / "algoritimos"))

DENOMINADORES = RAIZ / "dados" / "referencia" / "mulheres_por_area_usf.csv"
PARQUET_GEO = RAIZ.parent / "dados_parquet" / "aih" / "aih_rio_claro_geo.parquet"
SAIDA_AREAS = RAIZ / "dados" / "referencia" / "estudo_areas_idade_ajustada.csv"
SAIDA_TENDENCIA = RAIZ / "dados" / "referencia" / "estudo_tendencia_por_cancer.csv"

# faixas de idade dos casos (limite inferior, superior) <-> colunas de mulheres do CSV de denominadores
FAIXAS = {"m_ate29": (0, 29), "m_30a39": (30, 39), "m_40a49": (40, 49), "m_50a59": (50, 59), "m_60a69": (60, 69), "m_70mais": (70, 200)}
NIVEL = 0.90


def ic_poisson_exato(observado, esperado, nivel=NIVEL):
    """Intervalo exato (Garwood) da razão observado/esperado."""
    alfa = (1 - nivel) / 2
    baixo = stats.chi2.ppf(alfa, 2 * observado) / 2 / esperado if observado > 0 else 0.0
    alto = stats.chi2.ppf(1 - alfa, 2 * (observado + 1)) / 2 / esperado
    return float(baixo), float(alto)


def prob_acima(observado, esperado):
    """Probabilidade (a posteriori) de a razão verdadeira passar de 1, com prior Gamma(1, 1)."""
    return float(1 - stats.gamma.cdf(1.0, a=observado + 1, scale=1.0 / (esperado + 1)))


def razoes_por_idade(casos, mulheres):
    """`casos`: DataFrame área x faixa (contagens); `mulheres`: DataFrame área x faixa (mesmas colunas). Devolve a tabela por área."""
    colunas = list(FAIXAS)
    taxa_ref = casos[colunas].sum() / mulheres[colunas].sum()                 # taxa de Rio Claro inteiro, por faixa
    esperado = (mulheres[colunas] * taxa_ref).sum(axis=1)
    observado = casos[colunas].sum(axis=1)
    linhas = []
    for area in mulheres.index:
        o, e = float(observado.get(area, 0)), float(esperado[area])
        if e <= 0:
            continue
        baixo, alto = ic_poisson_exato(o, e)
        linhas.append({"area_usf": area, "casos": int(o), "mulheres": int(mulheres.loc[area, colunas].sum()), "esperado": round(e, 2),
                       "razao": round(o / e, 3), "ic90_baixo": round(baixo, 3), "ic90_alto": round(alto, 3), "prob_acima": round(prob_acima(o, e), 3)})
    return pd.DataFrame(linhas).sort_values("razao", ascending=False).reset_index(drop=True)


def tendencia_poisson(anos, valores, meses):
    """log(internações por mês) = a + b x ano. Devolve (% por ano, IC baixo, IC alto, p, dispersão)."""
    x = np.array(anos, float) - np.mean(anos)
    y = np.array(valores, float)
    deslocamento = np.log(np.array(meses, float))

    def menos_log_verossimilhanca(p):
        mu = np.exp(p[0] + p[1] * x + deslocamento)
        return float((mu - y * np.log(mu)).sum())

    ajuste = optimize.minimize(menos_log_verossimilhanca, [np.log(max(y.mean(), 0.1) / np.mean(meses)), 0.0], method="BFGS")
    mu = np.exp(ajuste.x[0] + ajuste.x[1] * x + deslocamento)
    matriz = np.c_[np.ones_like(x), x]
    erro = float(np.sqrt(np.linalg.inv(matriz.T @ (matriz * mu[:, None]))[1, 1]))
    dispersao = max(1.0, float(((y - mu) ** 2 / mu).sum() / (len(y) - 2)))   # Poisson puro = 1; maior = dados mais "bagunçados"
    erro *= np.sqrt(dispersao)
    b = float(ajuste.x[1])
    z = stats.norm.ppf(1 - (1 - NIVEL) / 2)
    p = float(2 * (1 - stats.norm.cdf(abs(b / erro))))
    return float(np.expm1(b) * 100), float(np.expm1(b - z * erro) * 100), float(np.expm1(b + z * erro) * 100), p, dispersao


def calcular_areas():
    den = pd.read_csv(DENOMINADORES, sep=";", encoding="utf-8").set_index("area_usf")
    geo = pd.read_parquet(PARQUET_GEO, columns=["AREA_USF", "STATUS_AREA_USF", "IDADE_ANOS"])
    geo = geo[geo["STATUS_AREA_USF"] == "CLASSIFICADO"].copy()
    geo["IDADE_ANOS"] = pd.to_numeric(geo["IDADE_ANOS"], errors="coerce")
    geo = geo.dropna(subset=["IDADE_ANOS"])
    limites = [-1] + [hi for _, hi in FAIXAS.values()]
    geo["faixa"] = pd.cut(geo["IDADE_ANOS"], bins=limites, labels=list(FAIXAS))
    casos = geo.groupby(["AREA_USF", "faixa"], observed=False).size().unstack(fill_value=0).reindex(columns=list(FAIXAS), fill_value=0)
    casos = casos.reindex(den.index).fillna(0)
    return razoes_por_idade(casos, den[list(FAIXAS)])


def calcular_tendencia():
    import inteligencia as ti
    from configuracao_geografica import BANCO
    conn = sqlite3.connect(f"file:{BANCO}?mode=ro", uri=True)
    try:
        meses = ti.meses_por_ano(conn) or {}
        dados = pd.read_sql("SELECT tipo_cancer, ano, COUNT(*) AS n FROM internacoes WHERE origem = 'SP' AND municipio = 'RIO_CLARO' "
                            "AND ano BETWEEN 2013 AND 2025 GROUP BY 1, 2", conn)
    finally:
        conn.close()
    linhas = []

    anos_da_fonte = [a for a in sorted(meses) if 2013 <= a <= 2025]

    def linha(codigo, nome, serie):
        # ano em que a fonte tem meses mas não há nenhuma internação deste câncer é ZERO de verdade e precisa entrar na conta
        serie = serie.set_index("ano")["n"].reindex(anos_da_fonte, fill_value=0).rename_axis("ano").reset_index()
        pct, baixo, alto, p, disp = tendencia_poisson(serie["ano"], serie["n"], [meses[a] for a in serie["ano"]])
        anual = "|".join(f"{int(a)}:{n / meses[a] * 12:.1f}" for a, n in zip(serie["ano"], serie["n"]))   # internações por ano, ajustadas pelos meses
        linhas.append({"tipo_cancer": codigo, "doenca": nome, "internacoes": int(serie["n"].sum()), "pct_ano": round(pct, 2),
                       "ic90_baixo": round(baixo, 2), "ic90_alto": round(alto, 2), "p": round(p, 4), "dispersao": round(disp, 2), "serie": anual})
    for codigo, grupo in dados.groupby("tipo_cancer"):
        linha(codigo, ti.nome_doenca(codigo), grupo)
    linha("TODOS", "Os 7 cânceres juntos", dados.groupby("ano", as_index=False)["n"].sum())
    return pd.DataFrame(linhas)


def main():
    areas = calcular_areas()
    areas.to_csv(SAIDA_AREAS, sep=";", index=False, encoding="utf-8")
    print(f"{len(areas)} áreas gravadas em {SAIDA_AREAS}")
    tendencia = calcular_tendencia()
    tendencia.to_csv(SAIDA_TENDENCIA, sep=";", index=False, encoding="utf-8")
    print(f"{len(tendencia)} linhas de tendência gravadas em {SAIDA_TENDENCIA}")


if __name__ == "__main__":
    main()
