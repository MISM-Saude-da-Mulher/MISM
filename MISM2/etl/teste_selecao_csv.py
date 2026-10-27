import os
import tempfile

from carga_todas_bases import encontrar_pastas_validas, selecionar_csv_unico


def testar_encontrar_pastas_validas():
    with tempfile.TemporaryDirectory() as base_dados:

        # cenário das capturas de tela: CSVs/parquets soltos direto na
        # raiz de dados\, sem as subpastas por câncer x território --
        # nenhum nome bate com MAPA, então isso tem que falhar alto,
        # não silenciar e carregar zero linhas.
        open(
            os.path.join(
                base_dados, "cancer_mama_mulheres_rio_claro_2013_2025.csv"
            ),
            "w"
        ).close()

        try:
            encontrar_pastas_validas(base_dados)
        except RuntimeError as erro:
            assert "Nenhuma subpasta reconhecida" in str(erro)
        else:
            raise AssertionError(
                "Arquivos soltos na raiz de dados\\ (sem subpasta) "
                "deveriam falhar, não retornar lista vazia em silêncio"
            )

        # pasta municipal antiga sozinha também não vale: a carga só
        # lê as estaduais (as municipais contavam Rio Claro em dobro).
        os.mkdir(os.path.join(base_dados, "cancer_mama_rio_claro"))
        try:
            encontrar_pastas_validas(base_dados)
        except RuntimeError:
            pass
        else:
            raise AssertionError("pasta municipal não deveria ser reconhecida")

        # criando a subpasta estadual, a carga volta a reconhecer --
        # prova que o guard não é permanente, só reage à ausência da
        # estrutura correta.
        os.mkdir(os.path.join(base_dados, "cancer_mama_sp"))
        assert encontrar_pastas_validas(base_dados) == ["cancer_mama_sp"]

    print("Todas as checagens de pastas válidas passaram.")


def main():
    testar_encontrar_pastas_validas()

    with tempfile.TemporaryDirectory() as pasta:
        assert selecionar_csv_unico(pasta, "cancer_mama_sp") is None

        caminho_unico = os.path.join(pasta, "A123456780191307.csv")
        open(caminho_unico, "w").close()
        assert (
            selecionar_csv_unico(pasta, "cancer_mama_sp")
            == caminho_unico
        )

        caminho_novo = os.path.join(
            pasta, "cancer_mama_mulheres_rio_claro_2013_2025.csv"
        )
        open(caminho_novo, "w").close()

        try:
            selecionar_csv_unico(pasta, "cancer_mama_sp")
        except RuntimeError as erro:
            assert "mais de um CSV" in str(erro)
        else:
            raise AssertionError(
                "Duas CSVs na mesma pasta deveriam falhar, "
                "não escolher uma sozinha"
            )

    print("Todas as checagens de seleção de CSV único passaram.")


if __name__ == "__main__":
    main()
