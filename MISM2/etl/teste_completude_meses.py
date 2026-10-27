import os
import tempfile

import carga_todas_bases as carga
import completude_meses as cm

# =====================================
# TESTE do completude_meses.py com buracos PLANTADOS:
#   - mama e ovário: 2024 sem set/out/nov/dez (download que falhou);
#   - mama: 2023/jul parcial (5 AIHs contra ~100 nos outros meses);
#   - ovário: 2022/mar faltando só nele.
# O script tem que desenhar a grade certa e listar o que baixar,
# dizendo quando falta em todos os cânceres.
# =====================================


def escrever(base, pasta, faltando=(), parciais=()):
    os.makedirs(os.path.join(base, pasta))
    with open(os.path.join(base, pasta, "dados.csv"), "w", encoding="latin1") as f:
        f.write("ANO_CMPT;MES_CMPT;MUNIC_RES\n")
        for ano in (2022, 2023, 2024):
            for mes in range(1, 13):
                if (ano, mes) in faltando:
                    continue
                n = 5 if (ano, mes) in parciais else 100
                f.writelines(f"{ano};{mes:02d};355030\n" for _ in range(n))


def main():
    base = tempfile.mkdtemp()
    buraco_2024 = {(2024, m) for m in (9, 10, 11, 12)}
    escrever(base, "cancer_mama_sp", faltando=buraco_2024, parciais={(2023, 7)})
    escrever(base, "cancer_ovario_sp", faltando=buraco_2024 | {(2022, 3)})

    s = cm.situacao_dos_meses(cm.contar_por_mes(os.path.join(base, "cancer_mama_sp", "dados.csv")))
    assert [s[2024][m] for m in (8, 9, 12)] == ["X", "-", "-"], s[2024]
    assert s[2023][7] == "p" and s[2023][6] == "X", s[2023]
    print("[OK] grade: 2024 sem set-dez, 2023/jul parcial")

    linhas = cm.grade(s)
    assert linhas[-1].endswith("|  8/12") and "12/12" in linhas[1], linhas
    print("[OK] contagem de meses por ano (8/12 em 2024)")

    situacoes = {"MAMA": s, "OVARIO": cm.situacao_dos_meses(
        cm.contar_por_mes(os.path.join(base, "cancer_ovario_sp", "dados.csv")))}
    faltas = cm.o_que_baixar(situacoes)
    assert len(faltas[(2024, 9)]) == 2 and faltas[(2022, 3)] == [("OVARIO", "-")], faltas
    assert faltas[(2023, 7)] == [("MAMA", "p")], faltas
    print("[OK] o que baixar: 2024/set-dez em todos, 2022/mar só ovário, 2023/jul parcial só mama")

    carga.BASE_DADOS = base
    cm.SAIDA_TXT = os.path.join(base, "saida.txt")
    cm.SAIDA_CSV = os.path.join(base, "saida.csv")
    cm.main()
    texto = open(cm.SAIDA_TXT, encoding="utf-8").read()
    assert "2024/09 (set): faltando -- todos os cânceres" in texto, texto
    assert "2022/03 (mar): faltando -- OVARIO" in texto and "2023/07 (jul): parcial -- MAMA" in texto
    assert os.path.exists(cm.SAIDA_CSV)
    print("\nTodas as checagens da completude dos meses passaram.")


if __name__ == "__main__":
    main()
