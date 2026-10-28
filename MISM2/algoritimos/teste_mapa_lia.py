"""Teste: a Lia conhece o Mapa de Rio Claro e leva até ele (28/10/2026).

Perguntas sobre o mapa ou sobre as áreas de USF recebem uma resposta fixa, com link para a página do mapa; hospitais, postos e
"onde ser atendida" NÃO são sequestrados. Não precisa de banco, de Streamlit nem de IA.
"""
import sys

import assistente
import entendimento as e

falhas = []


def checar(nome, ok):
    print(("OK   " if ok else "FALHOU ") + nome)
    if not ok:
        falhas.append(nome)


for pergunta in ["onde fica o mapa?", "qual área de USF tem mais internações?", "abrir o mapa de Rio Claro", "tem mapa?"]:
    r = e.compreender(pergunta)
    checar(f"'{pergunta}' vai para 'mapa_rio_claro'", r.tipo == "intencao" and r.intencao == "mapa_rio_claro")

for pergunta, esperado in [("onde faço mamografia?", "onde_atendida"), ("o que é o MISM?", "sobre_mism"), ("o que há nos dados?", "alcance")]:
    r = e.compreender(pergunta)
    checar(f"'{pergunta}' continua em '{esperado}'", r.tipo == "intencao" and r.intencao == esperado)
for pergunta in ["mapa de hospitais de câncer", "quais hospitais atendem câncer de mama?", "onde fica o posto de saúde mais perto?"]:
    r = e.compreender(pergunta)
    checar(f"'{pergunta}' NÃO vira 'mapa_rio_claro'", not (r.tipo == "intencao" and r.intencao == "mapa_rio_claro"))

checar("o assunto tem rótulo e link para a página do mapa", "mapa_rio_claro" in e.ROTULOS_TODOS and assistente.LINKS["mapa_rio_claro"] == [assistente.LINK_MAPA])
checar("é texto fixo: a IA não reescreve", "mapa_rio_claro" not in assistente.SO_DADOS)

if falhas:
    print(f"\n{len(falhas)} falha(s).")
    sys.exit(1)
print("\nTodas as checagens do mapa na Lia passaram.")
