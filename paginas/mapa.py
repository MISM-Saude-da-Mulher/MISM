"""Aba MAPA: abre o mapa do MISM 1 (Rio Claro, internações por câncer em mulheres, por área de USF).

O mapa continua sendo o HTML que o MISM 1 já gera (MISM 1/gerar_mapa.py); aqui ele só é embutido na página.
"""
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "MISM 1"))

import gerar_mapa  # noqa: E402

# O mapa ocupa a tela toda: tira o respiro lateral e de cima da página só nesta aba.
st.markdown(
    """<style>
    .block-container { padding-top: 3.5rem !important; padding-left: 1rem !important; padding-right: 1rem !important; }
    iframe { border: 0; border-radius: 12px; }
    </style>""",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Montando o mapa…")
def html_do_mapa():
    return gerar_mapa.gerar_html()


components.html(html_do_mapa(), height=820, scrolling=False)
