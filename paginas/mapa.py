"""Mapa de Rio Claro: o mapa do projeto do grupo (internações por câncer em mulheres, por área de USF), dentro do MISM2.

O mapa continua sendo o HTML que o projeto do grupo já gera (MISM 1/gerar_mapa.py); aqui ele só é embutido na página,
com a mesma barra de navegação das outras páginas do MISM2.
"""
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "MISM 1"))
sys.path.insert(0, str(RAIZ / "MISM2" / "dashboard"))

import gerar_mapa  # noqa: E402
from estilo import CSS  # noqa: E402
from navegacao import barra_de_navegacao  # noqa: E402

st.markdown(CSS, unsafe_allow_html=True)
st.markdown('<div class="escudo-marca">MISM · Mapa de Rio Claro</div>', unsafe_allow_html=True)
barra_de_navegacao("mapa", chave_inicio="mapa_inicio")

# O mapa ocupa a largura toda: tira só o respiro lateral desta aba (o topo segue igual ao das outras páginas).
st.markdown(
    """<style>
    .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
    iframe { border: 0; border-radius: 12px; }
    </style>""",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Montando o mapa…")
def html_do_mapa(por_caso):
    return gerar_mapa.gerar_html(por_caso=por_caso)


# Os dados são do SIH/SUS (DATASUS, base pública): as duas visões estão a um clique. Padrão: totais por área de USF.
visao = st.radio("Visão do mapa", ["Totais por área de USF", "Casos detalhados (SIH/SUS, base pública)"], horizontal=True,
                 key="mapa_visao", label_visibility="collapsed")
components.html(html_do_mapa(visao.startswith("Casos")), height=820, scrolling=False)
