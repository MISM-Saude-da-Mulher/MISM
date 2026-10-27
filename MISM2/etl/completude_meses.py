import os
import sys

import pandas as pd

import carga_todas_bases as carga

# =====================================
# COMPLETUDE DOS MESES: quais meses existem em cada arquivo?
#
# investigar_2025.py mostrou que o "salto de 2025" não era de 2025:
# 2025 tem os 12 meses de competência (MES_CMPT) e os anos anteriores
# NÃO (2024 só 8, 2022 só 10...). Por mês, o crescimento é suave. O
# total anual de um ano com meses faltando sai menor, e isso distorce
# tendência, anos fora do padrão, projeção e radar.
#
# Este script só LÊ os CSVs estaduais (os mesmos da carga) e mostra,
# por câncer, uma grade ano x mês:
#     X = mês presente    - = mês faltando    p = mês parcial
# (parcial = menos da metade da mediana dos meses daquele ano: pode
# ser um download interrompido). No fim, a lista do que baixar de
# novo no DATASUS -- os meses faltam quase sempre em todos os
# cânceres juntos, porque o download é por mês.
#
# Uso (no Windows, da pasta do projeto):  py etl\completude_meses.py
# Saída na tela, em analises\completude_meses.txt e, com a contagem
# de AIHs por mês, em analises\completude_meses.csv.
# =====================================

SAIDA_TXT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "analises", "completude_meses.txt")
SAIDA_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "analises", "completude_meses.csv")
MESES = list(range(1, 13))
NOMES_MES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
FRACAO_PARCIAL = 0.5


def contar_por_mes(caminho_csv):
    """AIHs por (ano, mês de competência). Só lê ANO_CMPT e MES_CMPT."""
    separador = carga.detectar_separador(caminho_csv)
    df = pd.read_csv(caminho_csv, sep=separador, encoding="latin1", dtype=str,
                     usecols=lambda c: c.strip().strip('"').upper() in {"ANO_CMPT", "MES_CMPT"})
    df.columns = [c.strip().strip('"').upper() for c in df.columns]
    if "MES_CMPT" not in df:
        raise RuntimeError(f"'{os.path.basename(caminho_csv)}' não tem a coluna MES_CMPT.")
    df["ano"] = pd.to_numeric(df["ANO_CMPT"], errors="coerce")
    df["mes"] = pd.to_numeric(df["MES_CMPT"], errors="coerce")
    df = df.dropna(subset=["ano", "mes"])
    return (df.groupby(["ano", "mes"]).size().rename("aihs").reset_index()
              .astype({"ano": int, "mes": int, "aihs": int}))


def situacao_dos_meses(contagem):
    """{ano: {mes: 'X' | '-' | 'p'}} para todos os anos do arquivo."""
    situacao = {}
    for ano, parte in contagem.groupby("ano"):
        por_mes = dict(zip(parte["mes"], parte["aihs"]))
        mediana = float(pd.Series(list(por_mes.values())).median()) if por_mes else 0.0
        situacao[int(ano)] = {
            m: "-" if m not in por_mes else ("p" if por_mes[m] < FRACAO_PARCIAL * mediana else "X")
            for m in MESES
        }
    return situacao


def grade(situacao):
    linhas = ["ano   " + " ".join(f"{n:>3}" for n in NOMES_MES) + "  | meses"]
    for ano in sorted(situacao):
        marcas = situacao[ano]
        presentes = sum(v != "-" for v in marcas.values())
        linhas.append(f"{ano}  " + " ".join(f"{marcas[m]:>3}" for m in MESES) + f"  | {presentes:>2}/12")
    return linhas


def o_que_baixar(situacoes):
    """(ano, mês) faltando ou parciais, e em quantos cânceres."""
    faltas = {}
    for cancer, situacao in situacoes.items():
        for ano, marcas in situacao.items():
            for mes, marca in marcas.items():
                if marca != "X":
                    faltas.setdefault((ano, mes), []).append((cancer, marca))
    return dict(sorted(faltas.items()))


def main():
    linhas_relatorio = []

    def dizer(texto=""):
        print(texto)
        linhas_relatorio.append(str(texto))

    dizer("COMPLETUDE DOS MESES -- arquivos estaduais brutos (X presente, - faltando, p parcial)")
    situacoes, tabelas = {}, []
    for pasta in carga.encontrar_pastas_validas(carga.BASE_DADOS):
        csv = carga.selecionar_csv_unico(os.path.join(carga.BASE_DADOS, pasta), pasta)
        if csv is None:
            continue
        cancer = carga.MAPA[pasta][0]
        contagem = contar_por_mes(csv)
        situacoes[cancer] = situacao_dos_meses(contagem)
        tabelas.append(contagem.assign(tipo_cancer=cancer))
        dizer("\n" + "=" * 70)
        dizer(f"{cancer}  ({os.path.basename(csv)})")
        for linha in grade(situacoes[cancer]):
            dizer(linha)

    faltas = o_que_baixar(situacoes)
    total = len(situacoes)
    dizer("\n" + "=" * 70)
    if not faltas:
        dizer("Todos os anos têm os 12 meses em todos os cânceres. Nada a baixar.")
    else:
        dizer("O QUE BAIXAR DE NOVO NO DATASUS (competência ano/mês):")
        for (ano, mes), quem in faltas.items():
            todos = len(quem) == total
            tipo = "parcial" if all(m == "p" for _, m in quem) else "faltando"
            alvo = "todos os cânceres" if todos else ", ".join(c for c, _ in quem)
            dizer(f"  {ano}/{mes:02d} ({NOMES_MES[mes - 1]}): {tipo} -- {alvo}")
        anos = sorted({a for a, _ in faltas})
        dizer(f"\nAnos com mês faltando ou parcial: {', '.join(map(str, anos))}. O total anual desses anos "
              f"sai menor que o real; tendência, anos fora do padrão e projeção ficam distorcidos até baixar.")

    for caminho, conteudo in ((SAIDA_TXT, "\n".join(linhas_relatorio) + "\n"), (SAIDA_CSV, None)):
        try:
            if conteudo is None:
                if tabelas:
                    pd.concat(tabelas)[["tipo_cancer", "ano", "mes", "aihs"]].to_csv(
                        caminho, sep=";", index=False, encoding="utf-8")
            else:
                with open(caminho, "w", encoding="utf-8") as arquivo:
                    arquivo.write(conteudo)
            print(f"Salvo em {os.path.normpath(caminho)}")
        except OSError as erro:
            print(f"(não consegui salvar {caminho}: {erro})", file=sys.stderr)


if __name__ == "__main__":
    main()
