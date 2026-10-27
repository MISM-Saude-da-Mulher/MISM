import os
import tempfile

from carga_todas_bases import detectar_separador

CABECALHO_PONTO_VIRGULA = (
    "UF_ZI;ANO_CMPT;MES_CMPT;MUNIC_RES;IDADE;DIAS_PERM;MORTE;VAL_TOT\n"
)

CABECALHO_VIRGULA = (
    "UF_ZI,ANO_CMPT,MES_CMPT,MUNIC_RES,IDADE,DIAS_PERM,MORTE,VAL_TOT\n"
)

CABECALHO_SEM_ANO_CMPT = "UF_ZI;ANO_INTERNACAO;MES_CMPT;MUNIC_RES\n"


def _escrever(pasta, nome, conteudo):
    caminho = os.path.join(pasta, nome)
    with open(caminho, "w", encoding="latin1") as arquivo:
        arquivo.write(conteudo)
    return caminho


def main():
    with tempfile.TemporaryDirectory() as pasta:

        caminho_pv = _escrever(pasta, "ponto_virgula.csv", CABECALHO_PONTO_VIRGULA)
        assert detectar_separador(caminho_pv) == ";"

        caminho_v = _escrever(pasta, "virgula.csv", CABECALHO_VIRGULA)
        assert detectar_separador(caminho_v) == ","

        caminho_sem = _escrever(pasta, "sem_ano_cmpt.csv", CABECALHO_SEM_ANO_CMPT)
        try:
            detectar_separador(caminho_sem)
        except RuntimeError as erro:
            assert "Não encontrei a coluna ANO_CMPT" in str(erro)
        else:
            raise AssertionError(
                "Cabeçalho sem ANO_CMPT em nenhum separador deveria falhar"
            )

    print("Todas as checagens de detecção de separador passaram.")


if __name__ == "__main__":
    main()
