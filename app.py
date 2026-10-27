"""MISM — site único com duas abas principais:

  MAPA                      -> MISM 1 (mapa de Rio Claro por área de USF)
  CENTRAL DE INFORMAÇÕES    -> MISM2  (painel, Apoio à mulher, Onde ser atendida, Hospitais de câncer)

Este arquivo só monta a navegação. O código de cada projeto continua nas suas pastas, e as páginas do MISM2
são registradas como estão (a barra interna delas continua funcionando).

Rodar:  streamlit run app.py
"""
import sys
from pathlib import Path

import streamlit as st

# O MISM2 foi feito para rodar com dashboard/app.py como entrada (os módulos irmãos, como lia_rosto e estilo,
# são importados direto): a pasta dashboard precisa estar no caminho de importação.
sys.path.insert(0, str(Path(__file__).resolve().parent / "MISM2" / "dashboard"))
sys.path.insert(0, str(Path(__file__).resolve().parent / "MISM2" / "algoritimos"))

# Hospedagem: sem a pasta dados_parquet no servidor, baixa os arquivos do dataset privado (MISM_DATASET/HF_TOKEN). Local: não faz nada.
import fonte_parquet  # noqa: E402

fonte_parquet.garantir_dados()

st.set_page_config(page_title="MISM · Saúde da Mulher", page_icon="💗", layout="wide", initial_sidebar_state="collapsed")

D = "MISM2/dashboard"
mapa = st.Page("paginas/mapa.py", title="MAPA", icon="🗺️", url_path="mapa", default=True)
central = st.Page(f"{D}/app.py", title="CENTRAL DE INFORMAÇÕES", icon="📚", url_path="central")
apoio = st.Page(f"{D}/pages/apoio.py", title="Apoio à mulher", url_path="apoio")
onde = st.Page(f"{D}/pages/onde_ser_atendida.py", title="Onde ser atendida", url_path="onde_ser_atendida")
hospitais = st.Page(f"{D}/pages/hospitais_cancer.py", title="Hospitais de câncer", url_path="hospitais_cancer")

# A barra de páginas do próprio Streamlit fica escondida: as duas abas principais são desenhadas abaixo.
pagina = st.navigation([mapa, central, apoio, onde, hospitais], position="hidden")

st.markdown(
    """<style>
    div[class*="st-key-abas_principais"] { background:#1f1b33; border-radius:14px; padding:6px 8px; margin-bottom:10px; }
    div[class*="st-key-abas_principais"] a { justify-content:center; border-radius:10px; font-weight:800; letter-spacing:.04em; color:#e9e6f5 !important; }
    div[class*="st-key-abas_principais"] a * { color:inherit !important; }
    div[class*="st-key-abas_principais"] a[aria-current="page"] { background:#e11d48; color:#fff !important; }
    </style>""",
    unsafe_allow_html=True,
)
with st.container(key="abas_principais"):
    c1, c2 = st.columns(2)
    c1.page_link(mapa, label="MAPA", icon="🗺️", width="stretch")
    c2.page_link(central, label="CENTRAL DE INFORMAÇÕES", icon="📚", width="stretch")

pagina.run()
