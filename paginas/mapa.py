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

import consulta_cep  # noqa: E402
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


@st.cache_data
def _areas_e_ubs():
    return consulta_cep.carregar_areas()


# Consulta por CEP: em qual área de USF fica e quais UBS estão mais perto. O CEP não é guardado (só é enviado às APIs públicas de CEP).
with st.expander("📮 Qual é a minha área de USF? Consulte pelo CEP"):
    with st.form("form_cep", border=False):
        cep_digitado = st.text_input("CEP de Rio Claro", placeholder="13500-000", max_chars=9, key="mapa_cep")
        consultar_cep = st.form_submit_button("Consultar")
    if consultar_cep and cep_digitado:
        areas, ubs = _areas_e_ubs()
        with st.spinner("Consultando o CEP…"):
            achado = consulta_cep.consultar(cep_digitado, areas, ubs)
        if "erro" in achado:
            st.warning(achado["erro"])
        else:
            local = ", ".join(x for x in (achado["rua"], achado["bairro"]) if x) or "o CEP informado"
            if achado["area"]:
                st.success(f"{local}: área de USF **{achado['area']}** (no mapa do grupo).")
            else:
                st.info(f"{local}: fica fora das áreas de USF desenhadas no mapa.")
            st.markdown("**Unidades de saúde mais perto (em linha reta):**")
            for u in achado["ubs"]:
                st.markdown(f"- **{u['nome']}**, a {u['km']:.1f} km. {u['endereco']}. {u['telefone']}. {u['horario']}".replace("  ", " "))
            st.caption("O CEP mostra a posição da rua, não da sua casa. As áreas são as do mapa do grupo, não um limite oficial, e a unidade mais perto "
                       "não é necessariamente a sua de referência: confirme com a Secretaria de Saúde ou pelo Cadu. "
                       f"Posição obtida na hora em {achado['fonte']} (API pública); o MISM não guarda o CEP.")

# Os dados são do SIH/SUS (DATASUS, base pública): as duas visões estão a um clique. Padrão: totais por área de USF.
visao = st.radio("Visão do mapa", ["Totais por área de USF", "Casos detalhados (SIH/SUS, base pública)"], horizontal=True,
                 key="mapa_visao", label_visibility="collapsed")
components.html(html_do_mapa(visao.startswith("Casos")), height=820, scrolling=False)
