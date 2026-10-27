import os
import tempfile

import carga_todas_bases as carga
import investigar_2025 as inv

# =====================================
# TESTE do investigar_2025.py com um atraso PLANTADO: de 2021 a 2024,
# 5% das AIHs de cada ano são de internações do ano anterior; em
# 2025, 40%. O script tem que apontar A como "MUITO ACIMA" em 2025,
# separar Rio Claro pelo MUNIC_RES e não quebrar sem DT_INTER.
# =====================================


def linhas(ano, n, pct_atraso, munic):
    atrasadas = int(n * pct_atraso)
    for i in range(n):
        inter = ano - 1 if i < atrasadas else ano
        yield f"{ano};{(i % 12) + 1:02d};{inter}0315;1;{ano}{i:06d};{munic}\n"


def main():
    base = tempfile.mkdtemp()
    pasta = os.path.join(base, "cancer_mama_sp")
    os.makedirs(pasta)
    with open(os.path.join(pasta, "mama.csv"), "w", encoding="latin1") as f:
        f.write("ANO_CMPT;MES_CMPT;DT_INTER;IDENT;N_AIH;MUNIC_RES\n")
        for ano in range(2021, 2026):
            pct = 0.40 if ano == 2025 else 0.05
            f.writelines(linhas(ano, 100, pct, 355030))
            f.writelines(linhas(ano, 20, pct, 354390))

    df = inv.ler_base(os.path.join(pasta, "mama.csv"))
    assert df["RIO_CLARO"].sum() == 100, df["RIO_CLARO"].sum()
    print("[OK] Rio Claro separada pelo MUNIC_RES")

    tabela = inv.diagnosticar(df)
    t25 = tabela[tabela["ano_cmpt"] == 2025].iloc[0]
    assert t25["pct_de_anos_anteriores"] == 40.0 and t25["meses"] == 12, t25
    print("[OK] 40% de internações antigas em 2025, 12 competências")

    frases = inv.veredito(tabela, inv.por_data_internacao(df))
    assert "MUITO ACIMA" in frases[0] and "normal" in frases[1], frases
    print("[OK] veredito aponta o atraso de 2025 e não inventa meses extras")

    # o caso REAL: 2025 completo, anos anteriores com meses faltando na fonte
    import pandas as pd
    real = pd.DataFrame({"ano_cmpt": [2022, 2023, 2024, 2025], "aihs": [100, 110, 80, 150],
                         "pct_de_anos_anteriores": [4.0, 4.0, 4.0, 3.0], "meses": [10, 11, 8, 12]})
    frase_c = [f for f in inv.veredito(real, pd.Series(dtype=int)) if f.startswith("C.")][0]
    assert "ANOS ANTERIORES COM MESES FALTANDO" in frase_c and "2024 (8)" in frase_c, frase_c
    print("[OK] veredito aponta os anos anteriores com meses faltando (o caso real)")

    sem = os.path.join(base, "sem_dt.csv")
    with open(sem, "w", encoding="latin1") as f:
        f.write("ANO_CMPT;MUNIC_RES\n2024;355030\n2025;355030\n")
    t = inv.diagnosticar(inv.ler_base(sem))
    assert "pct_de_anos_anteriores" not in t and len(t) == 2
    print("[OK] CSV sem DT_INTER não quebra (testes pulados)")

    carga.BASE_DADOS = base
    inv.SAIDA = os.path.join(base, "relatorio.txt")
    inv.main()
    assert os.path.exists(inv.SAIDA)
    print("\nTodas as checagens do investigar_2025 passaram.")


if __name__ == "__main__":
    main()
