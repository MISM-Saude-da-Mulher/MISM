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
barra_de_navegacao("mapa", chave_inicio="mapa_inicio")

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
