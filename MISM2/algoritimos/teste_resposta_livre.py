"""Testes da resposta livre da Lia (Gemini simulado: sem chave, sem rede) e do conhecimento do MISM1.

Rodar: py algoritimos\\teste_resposta_livre.py
"""
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import assistente as a  # noqa: E402
import entendimento as ent  # noqa: E402
import mism1_conhecimento as m1  # noqa: E402

falhas = []


def checar(nome, condicao, detalhe=""):
    print(("OK   " if condicao else "FALHOU ") + nome + (f"\n       {detalhe}" if detalhe and not condicao else ""))
    if not condicao:
        falhas.append(nome)


FICHA = "[INTERNAÇÕES POR ANO]\n2023: 210; 2024: 230 internações. Mama: 40%."
a.ficha_com_diagnostico = lambda ctx, limite=None: (FICHA, [], [])   # a ficha real precisa do banco
CTX = SimpleNamespace(cidade="Rio Claro")
COMUM = dict(pergunta="p", tipo="fora", origem="regras")
E = ent.Entendimento("fora", nota=0, palpites=[])


def livre(texto=None, erro=None, omitidos=(), pergunta="O que é endometriose?"):
    vistos = {}

    def fala(p, ficha, perfil):
        vistos["ficha"] = ficha
        if erro:
            raise erro
        return texto

    if omitidos:
        a.ficha_com_diagnostico = lambda ctx, limite=None: (FICHA, list(omitidos), [])
    else:
        a.ficha_com_diagnostico = lambda ctx, limite=None: (FICHA, [], [])
    ia = a.IA(livre=fala, ligada=True)
    r = a._resposta_livre(CTX, E, pergunta, "SIMPLES", ia, dict(COMUM))
    return r, ia, vistos


# 1. resposta boa passa e leva o selo
r, ia, _ = livre("A endometriose é uma condição em que tecido parecido com o do útero cresce fora dele. Procure a UBS do seu bairro.")
checar("1. resposta livre válida vira RespostaIA com selo de IA e sem diagnóstico", r is not None and r.usou_ia and "Não é diagnóstico" in r.selo and r.tipo == "livre")

# 2. fora do escopo, vazio e conferência
checar("2a. FORA_DO_ESCOPO devolve None (vale a recusa de sempre)", livre("FORA_DO_ESCOPO")[0] is None)
checar("2b. texto vazio devolve None", livre("   ")[0] is None)
checar("2c. número que não está na ficha derruba a resposta", livre("Em 2024 foram 999 internações.")[0] is None)
checar("2d. número que está na ficha passa", livre("Em 2024 foram 230 internações (SIH/SUS).")[0] is not None)
checar("2e. link derruba", livre("Veja https://exemplo.com para saber mais.")[0] is None)
checar("2f. 'vai ficar' derruba", livre("A situação vai ficar pior.")[0] is None)
checar("2g. causa atribuída derruba", livre("Isso acontece por causa do celular.")[0] is None)
checar("2h. 190/192 em caso de risco são permitidos", livre("Se estiver passando mal, ligue 192.")[0] is not None)

# 3. erros do Gemini: nunca quebram, e dizem o motivo sem expor nada
for erro, esperado in ((RuntimeError("401 UNAUTHENTICATED API key not valid"), "autenticacao"), (RuntimeError("429 RESOURCE_EXHAUSTED quota"), "cota"),
                       (RuntimeError("404 model not found"), "modelo"), (TimeoutError("timed out"), "tempo"), (ConnectionError("falha"), "rede")):
    r, ia, _ = livre(erro=erro)
    checar(f"3. erro '{esperado}' devolve None e guarda a categoria", r is None and ia.erro == esperado, str(ia.erro))
checar("3b. a categoria do erro nunca carrega a mensagem (que poderia ter a chave)", "api key" not in str(livre(erro=RuntimeError("API key AIza123"))[1].erro).lower())

# 4. sem IA
checar("4. sem Gemini ligado, a resposta livre não existe", a._resposta_livre(CTX, E, "p", "SIMPLES", a.IA(), dict(COMUM)) is None)

# 5. a ficha enviada avisa o que ficou de fora (não é "dado que não existe") e traz a pergunta só como dado
_, _, vistos = livre("Em 2024 foram 230 internações.", omitidos=["TODAS AS MORTES POR CÂNCER (SIM)"])
checar("5. blocos omitidos viram AVISO na ficha enviada ao Gemini", "AVISO DO SISTEMA" in vistos["ficha"] and "TODAS AS MORTES" in vistos["ficha"])

# 6. o selo dos palpites diz por que a IA não respondeu
e_palpite = ent.Entendimento("palpites", nota=0.3, palpites=[("mais_aparece", 0.3)])
ia_erro = a.IA(ligada=True, erro="autenticacao")
resp = a.montar(SimpleNamespace(cidade="Rio Claro", serie=None), e_palpite, "pergunta qualquer", None, "SIMPLES", ia_erro)
checar("6. palpites com erro de autenticação avisam que a chave não foi aceita", "chave do Gemini não foi aceita" in (resp.selo or ""), resp.selo)

# 7. MISM1: cada parte é lida sozinha e nada de dado individual
m1._cache.clear()
blocos = m1.blocos_da_ficha()
texto = "\n".join(blocos)
checar("7a. a ficha do MISM1 traz a definição do mapa", "MAPA DE RIO CLARO" in blocos[0])
checar("7b. nenhum CEP, logradouro ou coordenada na ficha", not any(p in texto.lower() for p in ("cep_normalizado", "logradouro", "latitude", "longitude")))
original = m1.GEO
m1.GEO = original.with_name("nao_existe.parquet")
m1._cache.clear()
sem_geo = m1.blocos_da_ficha()
checar("7c. sem o Parquet das áreas, idade ajustada e tendência continuam disponíveis",
       any("AJUSTADAS PELA IDADE" in b for b in sem_geo) or m1.carregar() is None)
m1.GEO = original
m1._cache.clear()
if m1.carregar() and m1.carregar()["areas"]:
    d = m1.carregar()
    checar("7d. o total por área bate com as internações classificadas do Parquet", sum(n for _, n, _, _ in d["areas"]) == d["total"])
    checar("7e. a taxa por 10 mil só existe com casos e mulheres suficientes",
           all((t is None) or (n >= m1.MINIMO_CASOS_TAXA and m >= m1.MINIMO_MULHERES_TAXA) for _, n, m, t in d["areas"]))

print()
print("Todas as checagens da resposta livre passaram." if not falhas else f"{len(falhas)} checagem(ns) falharam.")
sys.exit(1 if falhas else 0)
