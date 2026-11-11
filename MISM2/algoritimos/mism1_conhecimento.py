"""O que a Lia sabe do MISM1 (o Mapa de Rio Claro por área de USF e o Estudo de Rio Claro).

Só lê AGREGADOS (contagem por área, mulheres por área do Censo 2022, estudo já calculado): nunca CEP, rua, coordenada nem registro de
paciente. Se os arquivos não existirem (instalação só do MISM2), devolve None e a Lia segue sem este bloco.
"""
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
PASTA_MISM1 = RAIZ / "MISM 1" / "dados" / "referencia"
GEO = RAIZ / "dados_parquet" / "aih" / "aih_rio_claro_geo.parquet"
MINIMO_CASOS_TAXA = 20       # as mesmas regras do mapa (MISM 1/gerar_mapa.py)
MINIMO_MULHERES_TAXA = 1000

_cache = {}


def _ler(caminho, **kw):
    try:
        return pd.read_csv(caminho, sep=";", encoding="utf-8", **kw) if caminho.exists() else None
    except Exception:
        return None


def carregar():
    """{"areas": [(área, casos, mulheres, taxa por 10 mil ou None)], "idade": DataFrame|None, "tendencia": DataFrame|None, "anos": (ini, fim)|None,
    "nao_classificados": n} ou None se nenhuma das três partes existir. Cada parte é lida sozinha: faltar uma (por exemplo o Parquet das áreas
    ou os denominadores do Censo) não tira as outras da Lia.

    Escopo do Parquet das áreas (conferido em 11/2026): `aih_rio_claro_geo.parquet` tem 913 linhas = TODAS as internações por câncer de
    mulheres (SEXO = 3) moradoras de Rio Claro (MUNIC_RES 354390) de 2021 a 2025 no `aih_cancer_mulheres.parquet`; o `gerar_mapa` o liga ao AIH
    só com esse município. Por isso não há filtro de sexo, cidade ou câncer aqui."""
    if "dados" in _cache:
        return _cache["dados"]
    dados = {"areas": [], "idade": _ler(PASTA_MISM1 / "estudo_areas_idade_ajustada.csv"),
             "tendencia": _ler(PASTA_MISM1 / "estudo_tendencia_por_cancer.csv"), "anos": None, "nao_classificados": 0, "total": 0}
    try:
        if GEO.exists():
            geo = pd.read_parquet(GEO, columns=["AREA_USF", "STATUS_AREA_USF", "ANO_INTERNACAO"])
            ok = geo[geo["STATUS_AREA_USF"] == "CLASSIFICADO"]
            casos = ok.groupby("AREA_USF").size()
            den = _ler(PASTA_MISM1 / "mulheres_por_area_usf.csv")   # sem ele as áreas aparecem só com a contagem
            mulheres = dict(zip(den["area_usf"], den["mulheres"])) if den is not None else {}
            for area, n in casos.sort_values(ascending=False).items():
                m = int(mulheres[area]) if area in mulheres else None
                taxa = n / m * 10_000 if m and n >= MINIMO_CASOS_TAXA and m >= MINIMO_MULHERES_TAXA else None
                dados["areas"].append((area, int(n), m, taxa))
            anos = geo["ANO_INTERNACAO"].dropna()
            dados.update(anos=(int(anos.min()), int(anos.max())) if len(anos) else None,
                         nao_classificados=int(len(geo) - len(ok)), total=int(len(ok)))
    except Exception:
        dados["areas"] = []
    if not dados["areas"] and dados["idade"] is None and dados["tendencia"] is None:
        dados = None
    _cache["dados"] = dados
    return dados


def _n(v, casas=0):
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


DEFINICAO = (
    "O MISM1 é o **Mapa de Rio Claro**, projeto do grupo que faz parte do MISM. Mostra as internações por câncer em mulheres moradoras de Rio Claro "
    "(SIH/SUS, base pública do DATASUS; os 7 cânceres que o MISM acompanha) **por área de USF** (Unidade de Saúde da Família, o posto do bairro). "
    "O mapa tem filtros de câncer, ano e idade e duas visões: totais por área (padrão) e casos detalhados. Cada área aparece como ponto no centro "
    "dela, nunca no endereço de alguém, e grupos com menos de 5 casos são somados. A página também tem a consulta \"Qual é a minha área de USF?\" "
    "pelo CEP (o CEP não é guardado) e mostra as unidades de saúde mais perto, em linha reta. As áreas são as desenhadas pelo grupo, não um limite "
    "oficial. Internação não é caso novo nem incidência. A página \"Estudo de Rio Claro\" traz a taxa ajustada pela idade por área, a tendência de "
    "cada câncer e o fluxo de mulheres entre cidades."
)


def blocos_da_ficha(cidade="Rio Claro"):
    """Blocos para a ficha do Gemini: o que o mapa é e os números por área. [] se os arquivos não existem."""
    d = carregar()
    blocos = ["[O QUE É O MAPA DE RIO CLARO (MISM1)]\n" + DEFINICAO]
    if not d:
        return blocos
    if d["areas"]:
        periodo = f"{d['anos'][0]} a {d['anos'][1]}, " if d["anos"] else ""
        tabela = "; ".join(f"{a}: {_n(n)} internações" + (f", {_n(m)} mulheres" if m else "") + (f", {_n(t, 1)} por 10 mil mulheres" if t else "")
                           for a, n, m, t in d["areas"])
        blocos.append(f"[INTERNAÇÕES POR ÁREA DE USF, RIO CLARO ({periodo}SIH/SUS; mulheres = Censo 2022 do IBGE; a taxa por 10 mil só aparece para "
                      f"área com 20 casos ou mais e 1.000 mulheres ou mais; é taxa bruta de internações, não incidência; {_n(d['nao_classificados'])} internações "
                      f"não puderam ser ligadas a uma área e ficam fora)]\n{tabela}")
    ida = d["idade"]
    if ida is not None and len(ida):
        acima = ida[ida["prob_acima"] >= 0.95].sort_values("razao", ascending=False)
        abaixo = ida[ida["prob_acima"] <= 0.05].sort_values("razao")
        partes = [f"{r.area_usf}: {_n(r.razao, 2)} vezes o esperado pela idade (intervalo de 90%: {_n(r.ic90_baixo, 2)} a {_n(r.ic90_alto, 2)})"
                  for r in acima.itertuples()]
        texto = "ÁREAS ACIMA DO ESPERADO pela idade das mulheres, com confiança alta: " + ("; ".join(partes) or "nenhuma") + "."
        if len(abaixo):
            texto += " ABAIXO do esperado: " + "; ".join(f"{r.area_usf} ({_n(r.razao, 2)})" for r in abaixo.itertuples()) + "."
        texto += (" Razão de 1 = como o esperado para a cidade. O SIH só conta quem usa o SUS: áreas com mais plano particular podem parecer abaixo "
                  "do esperado.")
        blocos.append("[ESTUDO DE RIO CLARO: INTERNAÇÕES AJUSTADAS PELA IDADE, POR ÁREA]\n" + texto)
    t = d["tendencia"]
    if t is not None and len(t):
        itens = []
        for r in t.itertuples():
            claro = (r.ic90_baixo > 0) or (r.ic90_alto < 0)
            itens.append(f"{r.doenca}: {_n(r.pct_ano, 1)}% ao ano ({'mudança clara' if claro else 'sem mudança clara'}; {_n(r.internacoes)} internações no período)")
        blocos.append("[ESTUDO DE RIO CLARO: TENDÊNCIA POR CÂNCER (internações de moradoras de Rio Claro, ao ano; é tendência, não previsão)]\n" + "; ".join(itens))
    return blocos


def resumo_fixo():
    """Texto fixo para a resposta direta (sem IA): a definição e as áreas com mais internações."""
    d = carregar()
    texto = DEFINICAO
    if d and d["areas"]:
        topo = d["areas"][:3]
        texto += ("\n\nNo mapa, as áreas com mais internações no período são "
                  + ", ".join(f"**{a}** ({_n(n)})" for a, n, _, _ in topo)
                  + ". Número maior pode ser só uma área com mais mulheres: para comparar áreas use a taxa por mulheres ou o estudo ajustado pela idade.")
    return texto
