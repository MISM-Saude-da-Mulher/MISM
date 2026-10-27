import os
import sys

import pandas as pd

import carga_todas_bases as carga

# =====================================
# INVESTIGAR 2025: o salto é real ou é do registro?
#
# Em 2025 os 7 cânceres subiram de 33% a 83% ao mesmo tempo no
# Estado inteiro -- em Rio Claro, colo do útero foi de 6 para 28. O
# Escudo conta pelo ANO DE PROCESSAMENTO da AIH (ANO_CMPT), que pode
# não ser o ano em que a internação aconteceu (DT_INTER). Este
# script lê os CSVs estaduais BRUTOS (os mesmos da carga) e testa as
# explicações de registro, uma por uma:
#
#   A. Atraso: quantas AIHs processadas em cada ano são de
#      internações de anos ANTERIORES. Se 2025 tiver muito mais que
#      os outros anos, parte do salto é fila antiga processada agora.
#   B. Contagem pela data da internação (DT_INTER): o salto continua?
#      (2025 por DT_INTER fica incompleto: parte das internações do
#      fim de 2025 só é processada em 2026.)
#   C. Meses: 2025 tem mais competências (MES_CMPT) que 12, ou os
#      anos anteriores têm MENOS (meses que a fonte não oferece)?
#   D. Tipo de AIH (IDENT): 1 = normal, 5 = longa permanência
#      (continuação da mesma internação). Mais "5" = a mesma
#      internação contada mais vezes.
#   E. AIH repetida: o mesmo N_AIH mais de uma vez no ano.
#
# Só DETECTA; a decisão sobre 2025 é do autor. Uso (no Windows,
# da pasta do projeto):  py etl\investigar_2025.py
# O resultado sai na tela e em analises\investigacao_2025.txt.
# =====================================

COLUNAS = {"ANO_CMPT", "MES_CMPT", "DT_INTER", "IDENT", "N_AIH"}
CODIGOS_RIO_CLARO = {3543907, 354390}
ANO_ALVO = 2025
SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "analises", "investigacao_2025.txt")


def ler_base(caminho_csv):
    """Só as colunas necessárias (os arquivos estaduais são grandes)."""
    separador = carga.detectar_separador(caminho_csv)
    alvo = COLUNAS | set(carga.CANDIDATOS_CODIGO_MUNICIPIO)
    df = pd.read_csv(caminho_csv, sep=separador, encoding="latin1", dtype=str,
                     usecols=lambda c: c.strip().strip('"').upper() in alvo)
    df.columns = [c.strip().strip('"').upper() for c in df.columns]
    df["ANO_CMPT"] = pd.to_numeric(df["ANO_CMPT"], errors="coerce")
    if "DT_INTER" in df:
        df["ANO_INTER"] = pd.to_numeric(df["DT_INTER"].str.strip().str[:4], errors="coerce")
    coluna_mun = carga.encontrar_coluna_codigo(df)
    df["RIO_CLARO"] = (df[coluna_mun].map(carga.limpar_codigo).isin(CODIGOS_RIO_CLARO)
                       if coluna_mun else False)
    return df


def diagnosticar(df):
    """Uma linha por ano de processamento com os indicadores A, C, D, E."""
    linhas = []
    for ano, parte in df.groupby("ANO_CMPT"):
        linha = {"ano_cmpt": int(ano), "aihs": len(parte)}
        if "ANO_INTER" in parte:
            linha["pct_de_anos_anteriores"] = round(100 * (parte["ANO_INTER"] < ano).mean(), 1)
        if "MES_CMPT" in parte:
            linha["meses"] = parte["MES_CMPT"].nunique()
        if "IDENT" in parte:
            linha["pct_longa_permanencia"] = round(100 * (parte["IDENT"].str.strip() == "5").mean(), 1)
        if "N_AIH" in parte:
            linha["pct_aih_repetida"] = round(100 * parte["N_AIH"].duplicated().mean(), 1)
        linhas.append(linha)
    return pd.DataFrame(linhas)


def por_data_internacao(df):
    """Contagem pelo ano em que a internação aconteceu (B)."""
    if "ANO_INTER" not in df:
        return pd.Series(dtype=int)
    return df["ANO_INTER"].dropna().astype(int).value_counts().sort_index()


def veredito(tabela, contagem_inter, ano=ANO_ALVO):
    """Leitura cautelosa: compara o ano-alvo com a mediana dos outros."""
    frases = []
    if ano not in set(tabela["ano_cmpt"]):
        return [f"{ano} não está nesta base."]
    alvo = tabela[tabela["ano_cmpt"] == ano].iloc[0]
    outros = tabela[tabela["ano_cmpt"] < ano]
    if outros.empty:
        return ["Poucos anos para comparar."]

    def comparar(coluna, rotulo, folga=5.0):
        if coluna not in tabela:
            frases.append(f"{rotulo}: coluna não encontrada no CSV.")
            return
        base = float(outros[coluna].median())
        valor = float(alvo[coluna])
        destaque = valor > base + folga
        frases.append(f"{rotulo}: {ano} = {valor:g}% (outros anos, mediana: {base:g}%)"
                      + (" -> MUITO ACIMA: explica parte do salto." if destaque else " -> parecido."))

    comparar("pct_de_anos_anteriores", "A. AIHs de internações de anos anteriores")
    if "meses" in tabela:
        # Os dois lados: mais de 12 no ano-alvo (reprocessamento) OU menos
        # de 12 nos anos anteriores -- foi o caso real: o DATASUS não
        # oferece todos os meses (docs/FONTE_DOS_DADOS.md), e o ano
        # completo parecia "saltar" sobre anos incompletos.
        meses = int(alvo["meses"])
        incompletos = [f"{int(a)} ({int(m)})" for a, m in zip(outros["ano_cmpt"], outros["meses"]) if m < 12]
        frases.append(f"C. Competências em {ano}: {meses}"
                      + (" -> MAIS DE 12: há meses extras/reprocessados." if meses > 12 else "")
                      + (f" -> ANOS ANTERIORES COM MESES FALTANDO: {', '.join(incompletos)}. O salto pode ser "
                         f"só {ano} ter mais meses; compare por mês (py etl\\completude_meses.py)."
                         if incompletos and meses >= 12 else (" -> normal." if meses <= 12 else "")))
    comparar("pct_longa_permanencia", "D. AIHs de longa permanência (IDENT 5)", folga=2.0)
    comparar("pct_aih_repetida", "E. N_AIH repetido no ano", folga=2.0)

    if len(contagem_inter) and ano - 1 in contagem_inter.index and ano - 2 in contagem_inter.index:
        antes = contagem_inter[ano - 1] / max(contagem_inter[ano - 2], 1) - 1
        frases.append(f"B. Pela data da internação, {ano - 1} variou {antes * 100:+.0f}% sobre {ano - 2}. "
                      f"(Compare com o salto por ANO_CMPT; {ano} por DT_INTER fica incompleto.)")
    return frases


def main():
    linhas_relatorio = []

    def dizer(texto=""):
        print(texto)
        linhas_relatorio.append(str(texto))

    dizer(f"INVESTIGAÇÃO DE {ANO_ALVO} -- ANO_CMPT x DT_INTER (arquivos estaduais brutos)")
    for pasta in carga.encontrar_pastas_validas(carga.BASE_DADOS):
        csv = carga.selecionar_csv_unico(os.path.join(carga.BASE_DADOS, pasta), pasta)
        if csv is None:
            continue
        tipo_cancer = carga.MAPA[pasta][0]
        df = ler_base(csv)
        faltando = sorted(c for c in COLUNAS if c not in df.columns)
        dizer("\n" + "=" * 70)
        dizer(f"{tipo_cancer}  ({os.path.basename(csv)})")
        if faltando:
            dizer(f"Colunas ausentes neste CSV: {', '.join(faltando)} (os testes que dependem delas são pulados)")
        for rotulo, parte in (("ESTADO DE SP", df), ("RIO CLARO", df[df["RIO_CLARO"]])):
            if parte.empty:
                continue
            tabela = diagnosticar(parte)
            contagem = por_data_internacao(parte)
            dizer(f"\n--- {rotulo} ---")
            dizer(tabela.tail(5).to_string(index=False))
            if len(contagem):
                dizer("Internações pelo ano da DT_INTER (últimos 5): "
                      + ", ".join(f"{a}: {n}" for a, n in contagem.tail(5).items()))
            for frase in veredito(tabela, contagem):
                dizer("  " + frase)

    dizer("\nComo ler: se A (ou C, D, E) estiver MUITO ACIMA em 2025 em quase todos os cânceres, o salto é, "
          "ao menos em parte, do registro -- o Escudo pode passar a contar pelo ano da internação ou marcar "
          "2025. Se tudo estiver parecido e o salto aparecer também por DT_INTER, 2025 parece um novo patamar.")

    saida = SAIDA
    try:
        with open(saida, "w", encoding="utf-8") as arquivo:
            arquivo.write("\n".join(linhas_relatorio) + "\n")
        print(f"\nRelatório salvo em {os.path.normpath(saida)}")
    except OSError as erro:
        print(f"\n(não consegui salvar o relatório: {erro})", file=sys.stderr)


if __name__ == "__main__":
    main()
