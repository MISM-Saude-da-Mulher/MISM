"""Barra de navegação única das páginas do MISM2 (20/10/2026, autor: "poucas opções de retorno, é um labirinto").

Mesmos quatro destinos, na mesma ordem e em botões grandes, no topo de todas as páginas: Início, Apoio à mulher,
Onde ser atendida e Hospitais de câncer. A página em que a pessoa está aparece marcada e sem link. Só navegação:
não calcula nada e não abre o banco.
"""
import os

import streamlit as st

AQUI = os.path.dirname(os.path.abspath(__file__))

# Mesma ordem e mesmos rótulos da fileira de botões da página inicial (app.py): uma interface só em todas as páginas.
DESTINOS = [
    ("apoio", "Apoio à mulher", "pages/apoio.py", "/apoio"),
    ("onde", "Onde ser atendida", "pages/onde_ser_atendida.py", "/onde_ser_atendida"),
    ("hospitais", "Hospitais de câncer", "pages/hospitais_cancer.py", "/hospitais_cancer"),
]

# No site unificado (MISM) existem a página do mapa do grupo (paginas/mapa.py) e a dos gestores (paginas/rio_claro.py): entram no fim, como na página inicial.
if os.path.exists(os.path.join(AQUI, "..", "..", "paginas", "mapa.py")):
    DESTINOS.append(("mapa", "Mapa de Rio Claro", "paginas/mapa.py", "/mapa"))
if os.path.exists(os.path.join(AQUI, "..", "..", "paginas", "rio_claro.py")):
    DESTINOS.append(("rio_claro", "Estudo de Rio Claro", "paginas/rio_claro.py", "/estudo"))


def _ir_ao_inicio():
    st.session_state["aba"] = "Panorama"
    try:
        st.switch_page(os.path.abspath(os.path.join(AQUI, "app.py")))
    except Exception:  # página aberta fora do painel (teste isolado): sem destino
        pass


def botoes_das_paginas(atual=None):
    """A fileira de botões das páginas, igual em todas (a da página inicial). `atual`: a página aberta (marcada, sem link);
    None na página inicial. Só o primeiro botão (Apoio à mulher) é vermelho; o estilo está em estilo.py ("botao_apoio")."""
    try:
        caixa = st.container(key=f"botao_apoio_{atual or 'inicio'}")
    except TypeError:  # Streamlit antigo, sem key em container
        caixa = st.container()
    with caixa:
        for chave, rotulo, pagina, url in DESTINOS:
            if chave == atual:
                st.markdown(f'<div class="nav-aqui">{rotulo}<small>você está aqui</small></div>', unsafe_allow_html=True)
                continue
            try:
                st.page_link(pagina, label=rotulo)
            except Exception:  # Streamlit antigo, sem page_link
                st.markdown(f'<a href="{url}" target="_self">{rotulo}</a>', unsafe_allow_html=True)


def barra_de_navegacao(atual, chave_inicio=None, onde=None):
    """Topo padrão das páginas: a fileira de botões da página inicial e, logo abaixo, o botão Início ao lado da faixa
    "Você está em" (como a linha das abas da página inicial). `chave_inicio`: chave do botão Início (None = a página já tem o dela).
    `onde`: texto da faixa (None = sem faixa; a página desenha a sua)."""
    botoes_das_paginas(atual)
    if not (chave_inicio or onde):
        return
    col_onde, col_inicio = st.columns([5, 1], vertical_alignment="center")
    if onde:
        col_onde.markdown(f'<div class="escudo-voce-esta">📍 Você está em: <b>{onde}</b></div>', unsafe_allow_html=True)
    if chave_inicio:
        with col_inicio:
            with st.container(key=f"botao_inicio_{atual}"):
                if st.button("🏠 Início", key=chave_inicio, width="stretch", help="Volta à página inicial (Panorama)."):
                    _ir_ao_inicio()
