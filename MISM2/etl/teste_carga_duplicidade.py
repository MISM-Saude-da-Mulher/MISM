import os
import sqlite3
import tempfile

import carga_todas_bases as carga

# =====================================
# TESTE: A CARGA NÃO CONTA A MESMA CIDADE EM DOBRO
#
# No banco real, as moradoras de Rio Claro estavam em `internacoes`
# duas vezes (pasta de Rio Claro + pasta estadual): 1.668 + 1.668.
# Agora a carga só lê os arquivos estaduais. Este teste roda
# carregar() de verdade, com CSVs e banco temporários, e prova que:
#   - pastas municipais antigas em dados\ são ignoradas (e avisadas);
#   - Rio Claro conta uma vez só, vinda do estadual;
#   - câncer sem pasta estadual fica de fora (e é avisado), em vez
#     de voltar a ler a pasta da cidade;
#   - no fim não sobra município com duas fontes.
# =====================================

CABECALHO = "ANO_CMPT;IDADE;DIAS_PERM;MORTE;VAL_TOT;MUNIC_RES\n"


def escrever_csv(pasta_base, pasta, linhas):
    caminho = os.path.join(pasta_base, pasta)
    os.makedirs(caminho)
    with open(os.path.join(caminho, "dados.csv"), "w", encoding="latin1") as arquivo:
        arquivo.write(CABECALHO + "".join(linhas))


def main():
    # ---- carga de ponta a ponta ----
    temporario = tempfile.mkdtemp()
    base_dados = os.path.join(temporario, "dados")
    banco = os.path.join(temporario, "teste.db")

    # as mesmas 3 internações de Rio Claro nas duas pastas de mama
    rio_claro = ["2024;50;3;0;100.0;354390\n"] * 3
    escrever_csv(base_dados, "cancer_mama_rio_claro", rio_claro)
    escrever_csv(base_dados, "cancer_mama_sp", rio_claro + ["2024;60;2;0;90.0;352690\n"] * 2)
    # ovário só existe na pasta de Rio Claro
    escrever_csv(base_dados, "cancer_ovario_rio_claro", ["2024;40;1;0;50.0;354390\n"] * 4)

    conexao = sqlite3.connect(banco)
    conexao.execute("CREATE TABLE municipios (codigo_ibge INTEGER, origem TEXT, nome TEXT, uf TEXT)")
    conexao.executemany("INSERT INTO municipios VALUES (?,?,?,?)", [
        (3543907, "RIO_CLARO", "Rio Claro", "SP"),
        (3526902, "LIMEIRA", "Limeira", "SP"),
    ])
    conexao.commit()
    conexao.close()

    assert carga.pastas_ignoradas(base_dados) == ["cancer_mama_rio_claro", "cancer_ovario_rio_claro"]
    print("[OK] pastas municipais antigas são reconhecidas como ignoradas")
    assert "OVARIO" in carga.canceres_faltando(carga.encontrar_pastas_validas(base_dados))
    print("[OK] câncer sem pasta estadual é avisado")

    carga.BASE_DADOS, carga.BANCO = base_dados, banco
    carga.carregar()

    conexao = sqlite3.connect(banco)
    contagem = dict(conexao.execute("""
        SELECT tipo_cancer, COUNT(*) FROM internacoes
        WHERE municipio = 'RIO_CLARO' GROUP BY tipo_cancer
    """).fetchall())
    duplicados = carga.municipios_duplicados(conexao)
    conexao.close()

    assert contagem.get("MAMA") == 3, contagem
    print("[OK] mama de Rio Claro conta 3, não 6")
    assert "OVARIO" not in contagem, contagem
    print("[OK] a pasta de Rio Claro não é lida nem quando falta o estadual")
    assert duplicados == [], duplicados
    print("[OK] nenhum município com duas fontes no fim da carga")

    print("\nTodas as checagens de duplicidade passaram.")


if __name__ == "__main__":
    main()
