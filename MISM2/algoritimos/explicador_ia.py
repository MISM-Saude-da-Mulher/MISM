import sqlite3
import pandas as pd

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

base = pd.read_sql(
    """
    SELECT *
    FROM base_conhecimento
    ORDER BY pontuacao_final DESC
    """,
    conn
)

print("\n=== EXPLICADOR IA ===\n")

cancer = input(
    "Digite o cancer (ou ENTER para o primeiro): "
).upper()

if cancer.strip() == "":

    registro = base.iloc[0]

else:

    filtro = base[
        base["tipo_cancer"].str.upper() == cancer
    ]

    if filtro.empty:

        print("\nCancer nao encontrado.")
        conn.close()
        raise SystemExit

    registro = filtro.iloc[0]

texto = []

texto.append(
    f"O cancer {registro['tipo_cancer']} "
    f"foi classificado como prioridade "
    f"{registro['nivel_prioridade']}."
)

texto.append(
    f"Sua pontuacao final foi "
    f"{registro['pontuacao_final']:.2f}."
)

if registro["desvio"] > 0:

    texto.append(
        f"O comportamento apresentou desvio "
        f"de {registro['desvio']:.2f}% acima "
        f"da tendencia estadual."
    )

else:

    texto.append(
        f"O comportamento apresentou desvio "
        f"de {abs(registro['desvio']):.2f}% abaixo "
        f"da tendencia estadual."
    )

if registro["situacao"] == "ANOMALIA_POSITIVA":

    texto.append(
        "Foi identificada uma anomalia positiva "
        "em relacao ao historico analisado."
    )

elif registro["situacao"] == "ANOMALIA_NEGATIVA":

    texto.append(
        "Foi identificada uma anomalia negativa "
        "em relacao ao historico analisado."
    )

else:

    texto.append(
        "Nao foram identificadas anomalias "
        "relevantes no periodo."
    )

texto.append(
    f"O evento registrado foi "
    f"{registro['evento']}."
)

texto.append(
    f"A recomendacao atual e: "
    f"{registro['recomendacao']}"
)

print("\n=== ANALISE EXECUTIVA ===\n")

for frase in texto:

    print(frase)
    print()

conn.close()