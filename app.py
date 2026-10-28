"""MISM — um projeto só, construído sobre o MISM2 (painel, Apoio à mulher, Onde ser atendida, Hospitais de câncer).

O mapa de Rio Claro do projeto do grupo (MISM 1) entra como mais uma página do MISM2, ao lado do Apoio à mulher.

Este arquivo só monta a navegação. O código de cada projeto continua nas suas pastas, e as páginas do MISM2
são registradas como estão (a barra interna delas continua funcionando e ganhou o destino "Mapa de Rio Claro").

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
central = st.Page(f"{D}/app.py", title="MISM", icon="💗", default=True)
apoio = st.Page(f"{D}/pages/apoio.py", title="Apoio à mulher", url_path="apoio")
onde = st.Page(f"{D}/pages/onde_ser_atendida.py", title="Onde ser atendida", url_path="onde_ser_atendida")
hospitais = st.Page(f"{D}/pages/hospitais_cancer.py", title="Hospitais de câncer", url_path="hospitais_cancer")
mapa = st.Page("paginas/mapa.py", title="Mapa de Rio Claro", icon="🗺️", url_path="mapa")

# O MISM2 é a tela inicial; a navegação entre as páginas é a barra do próprio MISM2 (a do Streamlit fica escondida).
pagina = st.navigation([central, apoio, onde, hospitais, mapa], position="hidden")
pagina.run()
