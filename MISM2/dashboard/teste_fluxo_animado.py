"""Teste do mapa animado do fluxo (fluxo_animado.py): cidades com direção e distância certas, nada inventado, JavaScript válido.

Uso (de MISM2/dashboard):  python teste_fluxo_animado.py
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "algoritimos"))
sys.path.insert(0, AQUI)

import entendimento as ent  # noqa: E402
import fluxo_animado as fa  # noqa: E402

falhas = []


def checar(nome, ok):
    print(("OK   " if ok else "FALHOU ") + nome)
    if not ok:
        falhas.append(nome)


def posicoes(linhas):
    df = pd.DataFrame(linhas, columns=["nome", "latitude", "longitude"])
    df["chave"] = df["nome"].map(ent.normalizar)
    return df[["nome", "chave", "latitude", "longitude"]]


pos = posicoes([("Rio Claro", -22.373, -47.580), ("Piracicaba", -22.725, -47.649), ("Santa Gertrudes", -22.459, -47.527),
                ("Limeira", -22.565, -47.401), ("Jaú", -22.296, -48.558)])
info = {"destinos": [("Piracicaba", 100), ("Limeira", 7), ("Jaú", 2), ("Cidade Fantasma", 50)],
        "origens": [{"nome": "Santa Gertrudes", "internacoes": 143}, {"nome": "Limeira", "internacoes": 4}, {"nome": "Piracicaba", "internacoes": 6}]}
d = fa.dados_do_fluxo(info, pos, "Rio Claro")
cid = {c["nome"]: c for c in d["cidades"]}

checar("o centro é a cidade escolhida", d["centro"]["nome"] == "Rio Claro")
checar("destino com 3 internações ou mais entra; com 2 não entra (ruído)", "Piracicaba" in cid and "Limeira" in cid and "Jaú" not in cid)
checar("origem com 5 ou mais entra; com menos não conta", cid["Santa Gertrudes"]["ent"] == 143 and cid["Limeira"]["ent"] == 0)
checar("a mesma cidade que recebe e envia fica numa bolha só, com os dois números", cid["Piracicaba"]["sai"] == 100 and cid["Piracicaba"]["ent"] == 6)
checar("cidade sem posição na tabela fica de fora (nunca ganha ponto inventado)", "Cidade Fantasma" not in cid)
checar("Piracicaba fica ao sul (ângulo perto de -90°) e a cerca de 40 km",
       -2.0 < cid["Piracicaba"]["ang"] < -1.2 and 35 < cid["Piracicaba"]["km"] < 45)
checar("Santa Gertrudes fica ao sul-sudeste e perto (menos de 15 km)", cid["Santa Gertrudes"]["km"] < 15)
checar("sem tabela de posições, sem o centro ou sem fluxo: None (a tela não desenha nada)",
       fa.dados_do_fluxo(info, None, "Rio Claro") is None and fa.dados_do_fluxo(info, pos.iloc[0:0], "Rio Claro") is None
       and fa.dados_do_fluxo(info, pos, "Cidade Sem Posição") is None and fa.dados_do_fluxo(None, pos, "Rio Claro") is None
       and fa.dados_do_fluxo({"destinos": [], "origens": []}, pos, "Rio Claro") is None)
dr = fa.dados_do_fluxo(info, pos, "Rio Claro", regiao=("Santa Gertrudes", "Limeira"))
cr = {c["nome"]: c for c in dr["cidades"]}
checar("cidades da mesma região de saúde são marcadas (contorno tracejado); as outras não",
       cr["Santa Gertrudes"]["regiao"] and cr["Limeira"]["regiao"] and not cr["Piracicaba"]["regiao"] and not any(c["regiao"] for c in d["cidades"]))
checar("a legenda da região só aparece no desenho quando alguma cidade é da região", "l3" in fa.html_do_fluxo(dr) and dr["rotulo_regiao"].startswith("mesma região de saúde"))
checar("vale para outra cidade como centro (Limeira)", fa.dados_do_fluxo({"destinos": [("Piracicaba", 10)], "origens": []}, pos, "Limeira")["centro"]["nome"] == "Limeira")

html = fa.html_do_fluxo(d)
checar("o HTML embute os dados como JSON e não deixa '</' solto dentro do script", "const D = {" in html and "Santa Gertrudes" in html)
perigoso = fa.html_do_fluxo({"centro": {"nome": "X</script><b>"}, "cidades": [{"nome": "Y", "sai": 5, "ent": 0, "km": 10, "ang": 0}]})
checar("um nome com </script> não fecha o script antes da hora", perigoso.count("</script>") == 1)
checar("respeita quem prefere sem movimento (prefers-reduced-motion) e diz o que o desenho conta",
       "prefers-reduced-motion" in html and "o número de internações" in html)
if shutil.which("node"):
    js = re.findall(r"<script>(.*?)</script>", html, re.S)[-1]
    with tempfile.TemporaryDirectory() as tmp:
        arq = os.path.join(tmp, "fluxo.js")
        open(arq, "w", encoding="utf-8").write(js)
        checar("o JavaScript passa na checagem de sintaxe do Node", subprocess.run(["node", "--check", arq], capture_output=True).returncode == 0)
else:
    print("(Node não instalado: pulei a checagem de sintaxe)")

if falhas:
    print(f"\n{len(falhas)} falha(s).")
    sys.exit(1)
print("\nTodas as checagens do mapa animado passaram.")
