"""Resumo para a Secretaria da Mulher: uma página só, em português simples, com o que os dados de Rio Claro mostram e o que fazer.

Texto fixo (os números foram conferidos nos dados do MISM em 30/10/2026; ver a data no rodapé da página). Não calcula nada nem abre o banco.
Se os dados mudarem, atualizar os números aqui e a data. Conta internações, não pessoas, e nunca explica causas.
"""
import sys
from pathlib import Path

import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "MISM2" / "dashboard"))

from estilo import CSS  # noqa: E402
from navegacao import barra_de_navegacao  # noqa: E402

st.markdown(CSS, unsafe_allow_html=True)
st.markdown('<div class="escudo-marca">MISM · Resumo para a Secretaria da Mulher</div>', unsafe_allow_html=True)
barra_de_navegacao("resumo", chave_inicio="resumo_inicio")

st.markdown("## Câncer em mulheres de Rio Claro: o que os dados mostram e o que fazer")
st.caption("Internações por câncer de mulheres que moram em Rio Claro, pelo SUS, de 2013 a 2026.")

st.markdown("### 1. Onde agir primeiro")
st.markdown(
    "As áreas de saúde com mais internações por câncer, **em proporção às mulheres que moram nelas**, são "
    "**Bela Vista/Cidade Nova, Grande Cervezão e Guanabara/Inocoop/Chácara Luza**. "
    "O tamanho da área não explica isso: é a proporção que está acima das outras.")
st.info("**Sugestão:** levar a prevenção e convocar as mulheres para mamografia e preventivo primeiro nessas áreas. "
        "O mapa mostra isso, escolhendo \"Internações por 10 mil mulheres\" (botão **Mapa de Rio Claro**).")

st.markdown("### 2. Quem sai da cidade para se tratar")
st.markdown(
    "**8 de cada 10** internações de moradoras são na Santa Casa de Rio Claro. A exceção é o **câncer de pele: "
    "mais da metade (56%) é tratada fora**, principalmente em Piracicaba.")
st.info("**Sugestão:** perguntar à Saúde se essa cirurgia pode ser feita na cidade e organizar o transporte de quem precisa viajar.")

st.markdown("### 3. Rio Claro atende a região")
st.markdown(
    "Mulheres de Santa Gertrudes, Itirapina, Ipeúna, Analândia e Corumbataí usam cada vez mais a Santa Casa: de "
    "**menos de 1 internação por mês** (2013) para cerca de **5 por mês** (2025).")
st.info("**Sugestão:** conversar com essas cidades sobre apoio, porque Rio Claro está atendendo mulheres que não moram aqui.")

st.markdown("### 4. Onde as mulheres morrem")
st.markdown(
    "Cerca de **1 em cada 3** mulheres que morrem de câncer em Rio Claro morre fora de hospital (no Estado de São Paulo, "
    "é 1 em cada 7). Isso **pode** indicar falta de cuidado em casa para quem está muito doente.")
st.info("**Sugestão:** perguntar à Saúde se existe cuidado paliativo em casa e como a mulher e a família chegam até ele.")

st.markdown("### 5. O que os dados NÃO mostram, e a Saúde tem")
st.markdown(
    "Quanto tempo a mulher espera por mamografia e consulta, quantos casos novos surgem por ano e em que fase a doença é descoberta. "
    "Esses números não são públicos: estão com a Prefeitura e com a Santa Casa.")
st.info("**Sugestão:** pedir à Saúde a **fila de exames** (regulação) e à Santa Casa o **registro hospitalar de câncer**. "
        "Com os dois, o MISM poderá dizer onde a mulher espera mais.")

st.caption(
    "Fonte: internações do SUS (DATASUS, 2013–2026) e população do Censo 2022 (IBGE), conferidos em 30/10/2026. "
    "Conta internações, não pessoas: uma mulher pode ter mais de uma. Mostra onde as coisas acontecem, não explica por quê, "
    "e não compara a qualidade dos hospitais.")
