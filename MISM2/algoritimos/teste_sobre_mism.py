"""Teste: a Lia sabe responder para que serve o MISM e até onde ele alcança (28/10/2026).

"MISM" é o nome do projeto e da Lia (antes, Escudo Feminino). Perguntas que citam o MISM e pedem a função, o que é ou o alcance recebem
uma resposta fixa; as demais perguntas NÃO mudam de caminho. Não precisa de banco, de Streamlit nem de IA.
"""
import sys

import assistente
import entendimento as e
import lia

falhas = []


def checar(nome, ok):
    print(("OK   " if ok else "FALHOU ") + nome)
    if not ok:
        falhas.append(nome)


for pergunta in ["Qual é a função do MISM?", "para que serve o MISM?", "o que é o MISM?", "até onde o MISM alcança?",
                 "o que o MISM faz?", "me explica o MISM2", "para que serve o mism"]:
    r = e.compreender(pergunta)
    checar(f"'{pergunta}' vai para 'sobre_mism'", r.tipo == "intencao" and r.intencao == "sobre_mism")

# o que já existia continua igual
for pergunta, esperado in [("o que há nos dados?", "alcance"), ("quais cânceres vocês acompanham?", "alcance"),
                           ("onde faço mamografia?", "onde_atendida")]:
    r = e.compreender(pergunta)
    checar(f"'{pergunta}' continua em '{esperado}'", r.tipo == "intencao" and r.intencao == esperado)
for pergunta in ["o câncer de mama está aumentando em Rio Claro?", "o que é câncer de mama?", "qual a função do hospital de amor?"]:
    r = e.compreender(pergunta)
    checar(f"'{pergunta}' NÃO vira 'sobre_mism'", not (r.tipo == "intencao" and r.intencao == "sobre_mism"))


class Ctx:  # o mínimo que a resposta usa
    alcance = None
    cidade = "Rio Claro"


resp = lia.sobre_mism(Ctx())
texto = resp.fala.lower()
checar("a resposta diz o que o MISM é e para que a Lia serve (câncer, onde ser atendida, apoio à mulher)",
       "painel" in texto and "câncer" in texto and "onde ser atendida" in texto and "apoio à mulher" in texto)
checar("traz os telefones de emergência", all(n in resp.fala for n in ("190", "192", "180")))
checar("diz os limites (sem diagnóstico, sem causa, internação não é caso novo)",
       "não faço diagnóstico" in texto and "não explico causas" in texto and "não é caso novo" in texto)
checar("sem promessa nem previsão ('vai ficar', 'deve ficar') e sem orçamento",
       not any(p in texto for p in ("vai ficar", "deve ficar", "vai aumentar", "orçamento")))
checar("sem banco lido, responde só a função (não dá mensagem de erro)", "não consegui ler o banco" not in texto)
checar("é texto fixo: não está entre os assuntos que a IA reescreve", "sobre_mism" not in assistente.SO_DADOS)
if falhas:
    print(f"\n{len(falhas)} falha(s).")
    sys.exit(1)
print("\nTodas as checagens de 'sobre o MISM' passaram.")
