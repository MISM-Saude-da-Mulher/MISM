"""O que os dados mostram: uma página para gestores, em português simples, com o que os dados de Rio Claro revelam e o que fazer.

Nada aqui é digitado: os números vêm do banco e dos arquivos do MISM (as mesmas funções das outras abas), então a página muda quando os dados mudam.
Os visuais não são gráficos de barras: um mapa animado de fluxos (para onde vão e de onde vêm as mulheres), um mapa das áreas de saúde
pintado pela taxa e 100 pontinhos por cidade para mostrar onde as mulheres morrem. Cada bloco se protege: se um dado faltar, avisa e a página segue.
Conta internações, não pessoas, e nunca explica causas. Para levar a uma reunião: Ctrl+P e salvar em PDF.
"""
import html
import json
import math
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

RAIZ = Path(__file__).resolve().parents[1]
for _pasta in (RAIZ / "MISM2" / "dashboard", RAIZ / "MISM2" / "algoritimos", RAIZ / "MISM 1"):
    sys.path.insert(0, str(_pasta))

import fluxo_animado  # noqa: E402
import gerar_mapa  # noqa: E402
import inteligencia as ti  # noqa: E402
import localizacao as loc  # noqa: E402
from configuracao_geografica import BANCO  # noqa: E402
from estilo import CSS  # noqa: E402
from navegacao import barra_de_navegacao  # noqa: E402

ORIGEM, CODIGO, UF = "RIO_CLARO", 3543907, "SP"
# Região de Saúde de Rio Claro: 6 municípios (Rio Claro e estes cinco). Fonte: Plano da Rede de Urgência e Emergência 2023 da Prefeitura
# (saude-rioclaro.org.br/samu/plano rue 2023.pdf) e DRS X Piracicaba (saude.sp.gov.br).
REGIAO_DE_SAUDE = ("Analândia", "Corumbataí", "Ipeúna", "Itirapina", "Santa Gertrudes")

st.markdown(CSS, unsafe_allow_html=True)
st.markdown("""<style>
.res-cards { display: flex; flex-wrap: wrap; gap: 14px; margin: 18px 0 4px; }
.res-card { flex: 1 1 220px; background: #fff; border: 1px solid #e6dfe8; border-radius: 16px; padding: 16px 20px; }
.res-card b { display: block; font-family: Georgia, 'Times New Roman', serif; font-weight: 400; font-size: clamp(2.4rem, 4vw, 3.3rem);
              line-height: 1; letter-spacing: -.03em; color: #5b2a55; }
.res-card span { display: block; margin-top: 8px; color: #625d72; font-size: .95rem; line-height: 1.35; }
.res-cab { display: flex; align-items: center; gap: 14px; margin: 38px 0 8px; padding-top: 18px; border-top: 1px solid #ded3e3; }
.res-num { flex: 0 0 38px; width: 38px; height: 38px; border-radius: 50%; background: #5b2a55; color: #fff; font-weight: 700;
           display: flex; align-items: center; justify-content: center; font-size: 1.05rem; }
.res-tit { font-family: Georgia, 'Times New Roman', serif; font-size: clamp(1.35rem, 2vw, 1.75rem); color: #2a1730; line-height: 1.2; }
.res-txt { color: #3d3852; font-size: 1.06rem; line-height: 1.6; }
.res-txt b { color: #2a1730; }
.res-acao { background: #f3ecf5; border-left: 5px solid #5b2a55; border-radius: 10px; padding: 12px 16px; margin-top: 14px; color: #2a1730; line-height: 1.5; }
.res-acao small { display: block; font-family: ui-monospace, Menlo, Consolas, monospace; font-size: .68rem; letter-spacing: .12em;
                  text-transform: uppercase; font-weight: 700; color: #5b2a55; margin-bottom: 3px; }
.res-nota { color: #8a8599; font-size: .84rem; margin-top: 6px; line-height: 1.4; }
.res-pedido { background: #fff; border: 1px solid #e6dfe8; border-top: 4px solid #5b2a55; border-radius: 12px; padding: 14px 18px; height: 100%; }
.res-pedido h4 { margin: 4px 0 6px; font-family: Georgia, 'Times New Roman', serif; font-weight: 400; font-size: 1.25rem; color: #2a1730; }
.res-pedido p { margin: 0; color: #3d3852; line-height: 1.5; }
.res-pedido small { color: #8a7a90; font-family: ui-monospace, Menlo, Consolas, monospace; font-size: .68rem; letter-spacing: .1em; text-transform: uppercase; }
/* mapa das áreas: as três de cima pulsam devagar */
.res-mapa svg { width: 100%; height: auto; display: block; }
.res-mapa path { stroke: #faf6f2; stroke-width: 1.2; transition: opacity .2s; }
.res-mapa path:hover { opacity: .8; }
.res-mapa .pulsa { stroke: #eb6834; stroke-width: 2.6; animation: res-pulsa 2.2s ease-in-out infinite; }
@keyframes res-pulsa { 0%, 100% { stroke-opacity: 1; } 50% { stroke-opacity: .15; } }
.res-leg { display: flex; flex-wrap: wrap; gap: 4px 12px; margin-top: 8px; font-size: .84rem; color: #625d72; align-items: center; }
.res-leg i { display: inline-block; width: 14px; height: 14px; border-radius: 3px; margin-right: 4px; vertical-align: -2px; }
.res-top3 { margin: 10px 0 0; padding: 0; list-style: none; color: #3d3852; }
.res-top3 li { display: flex; gap: 10px; align-items: center; margin: 4px 0; }
.res-top3 em { flex: 0 0 24px; height: 24px; border-radius: 50%; background: #eb6834; color: #fff; font-style: normal; font-weight: 700;
               display: flex; align-items: center; justify-content: center; font-size: .85rem; }
/* tabela por tipo de câncer */
.res-sub { font-family: Georgia, 'Times New Roman', serif; font-size: 1.3rem; color: #2a1730; margin: 30px 0 8px; }
.res-tab { width: 100%; border-collapse: collapse; background: #fff; border: 1px solid #e6dfe8; border-radius: 12px; overflow: hidden; font-size: .98rem; }
.res-tab th { text-align: left; font-family: ui-monospace, Menlo, Consolas, monospace; font-size: .68rem; letter-spacing: .1em; text-transform: uppercase;
              color: #8a7a90; font-weight: 600; padding: 10px 12px; border-bottom: 1px solid #e6dfe8; background: #faf6f2; }
.res-tab td { padding: 10px 12px; border-bottom: 1px solid #f0eaf2; color: #3d3852; vertical-align: top; }
.res-tab tr:last-child td { border-bottom: 0; }
.res-tab td.pct { font-family: Georgia, 'Times New Roman', serif; font-size: 1.15rem; color: #5b2a55; white-space: nowrap; }
.res-tab tr.alto td { background: #fff6f0; }
.res-tab tr.alto td.pct { color: #c4501a; font-weight: 700; }
/* 100 pontinhos por cidade: aparecem aos poucos */
.res-pontos { display: flex; flex-wrap: wrap; gap: 28px; margin-top: 6px; }
.res-pontos > div { flex: 1 1 250px; }
.res-pontos h5 { margin: 0 0 8px; font-family: Georgia, 'Times New Roman', serif; font-weight: 400; font-size: 1.15rem; color: #2a1730; }
.res-grade { display: grid; grid-template-columns: repeat(10, 1fr); gap: 5px; max-width: 230px; }
.res-grade i { aspect-ratio: 1; border-radius: 50%; background: #d9d0de; animation: res-aparece .5s ease-out both; }
.res-grade i.f { background: #5b2a55; }
@keyframes res-aparece { from { opacity: 0; transform: scale(.2); } to { opacity: 1; transform: scale(1); } }
.res-pontos p { margin: 8px 0 0; color: #3d3852; }
.res-pontos p b { font-family: Georgia, 'Times New Roman', serif; font-weight: 400; font-size: 1.9rem; color: #5b2a55; }
@media (prefers-reduced-motion: reduce) { .res-mapa .pulsa, .res-grade i { animation: none; } }
@media print {
  [class*="st-key-barra_navegacao"], [data-testid="stToolbar"], [data-testid="stHeader"], header { display: none !important; }
  .res-cab, .res-acao, .res-pedido, .res-card { break-inside: avoid; }
}
</style>""", unsafe_allow_html=True)

st.markdown('<div class="mism-marca"><div class="escudo-marca">MISM<span> · saúde da mulher</span></div></div>', unsafe_allow_html=True)
barra_de_navegacao("rio_claro", chave_inicio="rio_claro_inicio")


# ---------- dados (tudo vem do banco e dos arquivos do MISM; nada digitado) ----------

@st.cache_data(show_spinner="Reunindo os números…")
def _banco():
    conn = sqlite3.connect(BANCO)
    try:
        out = {"por_cancer": ti.fluxo_por_cancer_da_cidade(conn, ORIGEM, CODIGO, UF),
               "cidade": ti.fluxo_da_cidade(conn, ORIGEM, CODIGO, UF), "meses": ti.meses_por_ano(conn, UF) or {},
               "posicoes": loc.carregar_localizacao(conn)}
        out["entradas"] = dict(conn.execute(
            "SELECT ano, COUNT(*) FROM internacoes WHERE origem = ? AND municipio_hospital = ? "
            "AND municipio NOT IN (?, 'OUTRO_ESTADO') GROUP BY ano", (UF, str(CODIGO)[:6], ORIGEM)).fetchall())
        try:
            def locais(filtro):
                linhas = conn.execute("SELECT local_obito, SUM(obitos) FROM obitos_sim WHERE ano <= 2025 AND codigo_residencia LIKE ? "
                                      "GROUP BY 1", (filtro,)).fetchall()
                total = sum(n for _, n in linhas) or 1
                por = {str(k): 100 * n / total for k, n in linhas}
                return 100 - por.get("1", 0)          # fora de hospital (no SIM, local 1 = hospital)
            out["fora_hospital"] = {"rc": locais(str(CODIGO)[:6] + "%"), "sp": locais("35%")}
        except Exception:
            out["fora_hospital"] = None
        return out
    finally:
        conn.close()


@st.cache_data(show_spinner=False)
def _areas():
    """[(área, casos, internações por 10 mil mulheres)] só das áreas com casos e mulheres suficientes (mesmas regras do mapa)."""
    den = gerar_mapa.carregar_denominadores()
    geo = pd.read_parquet(gerar_mapa.PARQUET_GEO, columns=["AREA_USF", "STATUS_AREA_USF"])
    casos = geo[geo["STATUS_AREA_USF"] == "CLASSIFICADO"].groupby("AREA_USF").size()
    linhas = [(a, int(n), n / den[a]["mulheres"] * 10_000) for a, n in casos.items()
              if a in den and n >= gerar_mapa.MINIMO_CASOS_TAXA and den[a]["mulheres"] >= gerar_mapa.MINIMO_MULHERES_TAXA]
    return sorted(linhas, key=lambda x: -x[2])


def _seguro(funcao, padrao=None):
    try:
        return funcao()
    except Exception:
        return padrao


dados = _seguro(_banco, {}) or {}
por_cancer = dados.get("por_cancer")
cidade = dados.get("cidade")
areas = _seguro(_areas, []) or []


def n_fmt(v, casas=0):
    return ti.formatar_numero(v, casas)


def cabecalho(numero, titulo):
    st.markdown(f'<div class="res-cab"><div class="res-num">{numero}</div><div class="res-tit">{titulo}</div></div>', unsafe_allow_html=True)


def acao(quem, texto):
    return f'<div class="res-acao"><small>O que a gestão pode fazer · {quem}</small>{texto}</div>'


# ---------- cabeçalho da página ----------

st.markdown('<div class="escudo-titulo">Mulheres e câncer em <em>Rio Claro</em>: o que os dados mostram e o que fazer</div>', unsafe_allow_html=True)
st.markdown('<div class="escudo-sub">Para quem decide. Internações por câncer de mulheres que moram em Rio Claro, pelo SUS, '
            '2013 a 2026. Para levar a uma reunião: Ctrl+P e salvar em PDF.</div>', unsafe_allow_html=True)

tabela = por_cancer["tabela"] if por_cancer else None
total = pct_cidade = pct_pele = None
if tabela is not None and not tabela.empty:
    total = int(tabela["moradoras"].sum()) + int(por_cancer["sem_hospital"])
    pct_cidade = 100 * tabela["na_cidade"].sum() / tabela["moradoras"].sum()
    pele = tabela[tabela["tipo_cancer"] == "PELE_NAO_MELANOMA"]
    if not pele.empty and pd.notna(pele.iloc[0]["pct_fora"]):
        pct_pele = float(pele.iloc[0]["pct_fora"])

cartoes = []
if total:
    cartoes += [(n_fmt(total), "internações por câncer de mulheres de Rio Claro"), (f"{n_fmt(pct_cidade)}%", "delas foram na própria cidade (Santa Casa)")]
if pct_pele is not None:
    cartoes.append((f"{n_fmt(pct_pele)}%", "das internações por câncer de pele foram em outras cidades"))
if cartoes:
    st.markdown('<div class="res-cards">' + "".join(f'<div class="res-card"><b>{n}</b><span>{t}</span></div>' for n, t in cartoes) + "</div>",
                unsafe_allow_html=True)
if not por_cancer:
    st.warning("Os números do banco não puderam ser lidos agora. Recarregue a página; se continuar, avise quem cuida do MISM.")


# ---------- 1. onde agir primeiro: mapa das áreas de saúde pintado pela taxa ----------

def _projetar(geojson_polys, largura=600, altura=520, margem=14):
    """Coordenadas (lon, lat) -> pontos de um SVG, sem distorcer (a longitude é encolhida pelo cosseno da latitude)."""
    pontos = [p for _, aneis in geojson_polys for anel in aneis for p in anel]
    lon0, lat0 = min(p[0] for p in pontos), max(p[1] for p in pontos)
    k = math.cos(math.radians(-22.4))
    w = (max(p[0] for p in pontos) - lon0) * k
    h = lat0 - min(p[1] for p in pontos)
    escala = min((largura - 2 * margem) / w, (altura - 2 * margem) / h)
    dx, dy = (largura - w * escala) / 2, (altura - h * escala) / 2
    return lambda lon, lat: (dx + (lon - lon0) * k * escala, dy + (lat0 - lat) * escala)


def mapa_das_areas(areas_com_taxa):
    usf = json.load(open(gerar_mapa.USF_GEOJSON_PATH, encoding="utf-8"))
    polys = []
    for f in usf["features"]:
        g = f.get("geometry") or {}
        if g.get("type") == "Polygon" and (f.get("properties") or {}).get("nome"):
            polys.append((f["properties"]["nome"], g["coordinates"]))
    # Áreas distantes (distritos rurais) esticariam o enquadramento e o mapa urbano ficaria minúsculo: ficam fora do desenho (todas têm poucos casos).
    cent = [(sum(p[0] for p in a[0]) / len(a[0]), sum(p[1] for p in a[0]) / len(a[0])) for _, a in polys]
    med = (sorted(c[0] for c in cent)[len(cent) // 2], sorted(c[1] for c in cent)[len(cent) // 2])
    k = math.cos(math.radians(-22.4))
    polys = [p for p, c in zip(polys, cent) if math.hypot((c[0] - med[0]) * k * 111.32, (c[1] - med[1]) * 110.57) <= 9]
    proj = _projetar(polys)
    taxa = {a: t for a, _, t in areas_com_taxa}
    casos = {a: c for a, c, _ in areas_com_taxa}
    valores = sorted(taxa.values())
    cortes = [valores[min(len(valores) - 1, int(p * len(valores)))] for p in (0.2, 0.4, 0.6, 0.8)] if len(valores) >= 5 else []
    cores = ["#efe4f1", "#d7bfdc", "#b78bc2", "#8e4f9c", "#5b2a55"]

    def cor(t):
        if not cortes:
            return cores[2]
        return cores[sum(1 for c in cortes if t >= c)]
    top3 = [a for a, _, _ in areas_com_taxa[:3]]
    desenho, centros = [], {}
    for nome, aneis in polys:
        d = " ".join("M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in (proj(lon, lat) for lon, lat in anel)) + "Z" for anel in aneis)
        t = taxa.get(nome)
        dica = f"{nome}: {n_fmt(t)} internações por 10 mil mulheres ({casos[nome]} casos)" if t is not None else f"{nome}: poucos casos para calcular"
        desenho.append(f'<path d="{d}" fill="{cor(t) if t is not None else "#e8e1ec"}" fill-rule="evenodd" class="{"pulsa" if nome in top3 else ""}">'
                       f'<title>{html.escape(dica)}</title></path>')
        xs, ys = zip(*(proj(lon, lat) for lon, lat in aneis[0]))
        centros[nome] = (sum(xs) / len(xs), sum(ys) / len(ys))
    marcas = "".join(f'<circle cx="{centros[a][0]:.1f}" cy="{centros[a][1]:.1f}" r="13" fill="#eb6834" stroke="#fff" stroke-width="2"/>'
                     f'<text x="{centros[a][0]:.1f}" y="{centros[a][1] + 5:.1f}" text-anchor="middle" font-size="14" font-weight="700" fill="#fff">{i + 1}</text>'
                     for i, a in enumerate(top3))
    faixas = ["menor"] + [""] * 3 + ["maior"]
    legenda = '<div class="res-leg">' + "".join(f'<span><i style="background:{c}"></i>{t}</span>' for c, t in zip(cores, faixas)) + \
              '<span><i style="background:#e8e1ec"></i>poucos casos</span></div>'
    return f'<div class="res-mapa"><svg viewBox="0 0 600 520" role="img" aria-label="Mapa das áreas de saúde de Rio Claro">{"".join(desenho)}{marcas}</svg>{legenda}</div>', top3


cabecalho(1, "Onde agir primeiro")
esq, dir_ = st.columns([1, 1.15], gap="large")
with esq:
    if areas:
        topo = areas[:3]
        itens = "".join(f"<li><em>{i + 1}</em><span><b>{html.escape(a)}</b> · {n_fmt(t)} por 10 mil mulheres</span></li>" for i, (a, _, t) in enumerate(topo))
        st.markdown('<div class="res-txt">Nas áreas de saúde abaixo há mais internações por câncer <b>em proporção às mulheres que moram nelas</b>. '
                    'É a proporção, e não o tamanho da área, que as coloca no topo. Quanto mais escuro o mapa, maior a proporção.</div>'
                    f'<ul class="res-top3">{itens}</ul>'
                    + acao("Saúde e Mulher", "Levar a prevenção e convocar as mulheres para mamografia e preventivo <b>primeiro nessas áreas</b>."),
                    unsafe_allow_html=True)
        st.markdown('<div class="res-nota">Internações por câncer para cada 10 mil mulheres da área (2021–2025). Taxa bruta, sem ajuste de idade; '
                    'só áreas com 20 casos ou mais. Passe o mouse sobre uma área para ver o número.</div>', unsafe_allow_html=True)
    else:
        st.info("A comparação por área não está disponível agora.")
with dir_:
    if areas:
        resultado = _seguro(lambda: mapa_das_areas(areas))
        if resultado:
            st.markdown(resultado[0], unsafe_allow_html=True)


# ---------- 2. quem sai e quem chega: mapa animado de fluxos ----------

cabecalho(2, "Quem sai da cidade e quem chega")
fluxo = _seguro(lambda: fluxo_animado.dados_do_fluxo(cidade, dados.get("posicoes"), "Rio Claro", REGIAO_DE_SAUDE))
esq, dir_ = st.columns(2, gap="large")
with esq:
    if tabela is not None and not tabela.empty and pct_cidade is not None:
        pele_txt = (f" A exceção é o <b>câncer de pele: {n_fmt(pct_pele)}% foram fora</b>, principalmente em Piracicaba." if pct_pele is not None and pct_pele >= 20 else "")
        st.markdown(f'<div class="res-txt"><b>{round(pct_cidade / 10)} de cada 10</b> internações de moradoras são na Santa Casa de Rio Claro.{pele_txt}</div>'
                    + acao("Saúde e Transporte", "Perguntar se a cirurgia de pele pode ser feita na cidade e organizar o transporte de quem precisa viajar."),
                    unsafe_allow_html=True)
with dir_:
    origens = list((cidade or {}).get("origens") or [])
    if origens:
        meses, entradas = dados.get("meses") or {}, dados.get("entradas") or {}
        anos = sorted(a for a in entradas if meses.get(a))
        crescimento = ""
        if len(anos) >= 2:
            p0, p1 = entradas[anos[0]] / meses[anos[0]], entradas[anos[-1]] / meses[anos[-1]]
            crescimento = (f" Em {anos[0]} eram {'menos de 1' if p0 < 1 else 'cerca de ' + n_fmt(p0)} internação por mês; em {anos[-1]}, cerca de {n_fmt(p1)} por mês.")
        cidades_txt = ", ".join(html.escape(o["nome"]) for o in origens[:4])
        regiao = {fluxo_animado.ent.normalizar(x) for x in REGIAO_DE_SAUDE}
        total_fora = (cidade or {}).get("outras_cidades") or 0
        da_regiao = sum(o["internacoes"] for o in origens if fluxo_animado.ent.normalizar(o["nome"]) in regiao)
        regiao_txt = (f" <b>{n_fmt(100 * da_regiao / total_fora)}%</b> dessas internações vêm das outras cinco cidades da "
                      "<b>Região de Saúde de Rio Claro</b> (contorno tracejado no mapa).") if total_fora and da_regiao else ""
        st.markdown(f'<div class="res-txt">Mulheres de outras cidades usam cada vez mais os hospitais de Rio Claro: <b>{cidades_txt}</b>.{regiao_txt}{crescimento}</div>'
                    + acao("Saúde e Gestão", "Conversar com essas cidades sobre apoio: Rio Claro atende mulheres que moram em outros municípios."),
                    unsafe_allow_html=True)
if fluxo:
    components.html(fluxo_animado.html_do_fluxo(fluxo), height=580)
    st.markdown('<div class="res-nota">Cada cidade fica na direção real em que está de Rio Claro; a distância é encolhida para caber todas na tela (os anéis são '
                '10, 50 e 150 km em linha reta). Internações de 2013 a 2026. Passe o mouse sobre uma cidade.</div>', unsafe_allow_html=True)


if tabela is not None and not tabela.empty:
    st.markdown('<div class="res-sub">Por tipo de câncer: quanto é tratado fora, e onde</div>', unsafe_allow_html=True)
    linhas = []
    for r in tabela.itertuples():
        tem = pd.notna(r.pct_fora)
        onde = "—"
        if r.n_destino:
            onde = f"{html.escape(r.destino)} ({n_fmt(r.n_destino)})" + (f" · {html.escape(r.hospital)} ({n_fmt(r.n_hospital)})" if r.n_hospital else "")
        linhas.append(f'<tr class="{"alto" if tem and r.pct_fora >= 20 else ""}"><td>{html.escape(r.doenca)}</td><td>{n_fmt(r.moradoras)}</td>'
                      f'<td>{n_fmt(r.fora)}</td><td class="pct">{n_fmt(r.pct_fora, 1) + "%" if tem else "poucos casos"}</td><td>{onde}</td></tr>')
    st.markdown('<table class="res-tab"><thead><tr><th>Câncer</th><th>Internações de moradoras</th><th>Fora da cidade</th><th>% fora</th>'
                '<th>Para onde (cidade · hospital mais frequente)</th></tr></thead><tbody>' + "".join(linhas) + "</tbody></table>", unsafe_allow_html=True)
    if por_cancer["sem_hospital"]:
        st.markdown(f'<div class="res-nota">Outras {n_fmt(por_cancer["sem_hospital"])} internações não trazem a cidade do hospital e ficaram fora desta tabela.</div>',
                    unsafe_allow_html=True)
    st.markdown('<div class="escudo-leitura"><b>O que mostra</b><ul>' + "".join(f"<li>{html.escape(f)}</li>" for f in ti.leitura_fluxo_por_cancer(por_cancer, "Rio Claro"))
                + "</ul></div>", unsafe_allow_html=True)


# ---------- 3. onde as mulheres morrem: 100 pontinhos por cidade ----------

def pontinhos(fora, ordem=0):
    n = max(0, min(100, round(fora)))
    return "".join(f'<i class="{"f" if i < n else ""}" style="animation-delay:{(i * 14) + ordem}ms"></i>' for i in range(100))


cabecalho(3, "Onde as mulheres morrem")
fh = dados.get("fora_hospital")
if fh:
    st.markdown('<div class="res-txt">Cada pontinho é uma mulher que morreu de câncer (para cada cem). Os <b style="color:#5b2a55">roxos</b> morreram '
                '<b>fora de hospital</b>: em casa ou em outro serviço de saúde. Isso <b>pode</b> indicar falta de cuidado em casa para quem está muito doente.</div>'
                '<div class="res-pontos">'
                f'<div><h5>Rio Claro</h5><div class="res-grade">{pontinhos(fh["rc"])}</div><p><b>{n_fmt(fh["rc"])}</b> de cada 100 morreram fora de hospital</p>'
                f'<div class="res-nota">Para comparar: no Estado de São Paulo, {n_fmt(fh["sp"])} de cada 100.</div></div>'
                '</div>'
                + acao("Saúde e Assistência Social", "Perguntar se existe cuidado paliativo em casa e como a mulher e a família chegam até ele."),
                unsafe_allow_html=True)
    st.markdown('<div class="res-nota">Mortes pelos 7 cânceres acompanhados, 2013–2025 (Sistema de Informações sobre Mortalidade).</div>', unsafe_allow_html=True)
else:
    st.info("Este dado não está disponível agora.")


# ---------- 4. o que falta ----------

cabecalho(4, "O que os dados públicos não mostram")
st.markdown('<div class="res-txt">Faltam três informações que decidem muita coisa, e elas não são públicas: <b>quanto tempo a mulher espera</b> '
            'por mamografia e consulta, <b>quantos casos novos</b> surgem por ano e <b>em que fase</b> a doença é descoberta. '
            'Quem tem esses números é a Prefeitura e a Santa Casa.</div>', unsafe_allow_html=True)
esq, dir_ = st.columns(2, gap="large")
esq.markdown('<div class="res-pedido"><small>Pedir à Secretaria de Saúde</small><h4>Fila de exames e consultas</h4>'
             '<p>Tempo de espera por mamografia, ultrassom, biópsia e consulta com especialista, por área de saúde.</p></div>', unsafe_allow_html=True)
dir_.markdown('<div class="res-pedido"><small>Pedir à Santa Casa</small><h4>Registro hospitalar de câncer</h4>'
              '<p>Casos novos por ano, fase em que a doença foi descoberta e tempo até o início do tratamento.</p></div>', unsafe_allow_html=True)
st.markdown(acao("Gestão", "Pedir esses dois conjuntos de dados. Com eles, o MISM poderá mostrar <b>onde a mulher espera mais</b> e orientar onde reforçar."),
            unsafe_allow_html=True)

st.markdown('<div class="res-nota" style="margin-top:30px">Fonte: internações do SUS (DATASUS), mortalidade (SIM) e população do Censo 2022 (IBGE). '
            'Conta internações, não pessoas: uma mulher pode ter mais de uma. Mostra onde as coisas acontecem, não explica por quê, '
            'e não compara a qualidade dos hospitais.</div>', unsafe_allow_html=True)
