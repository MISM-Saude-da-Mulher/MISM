"""Copia para `deploy_dados/` só os Parquets que o site usa (~208 MB), prontos para subir num dataset privado.

  python preparar_dados_deploy.py

Não altera nada em `dados_parquet/`. Fica de fora tudo que o site não lê (e, de propósito, `tbDadosProfissionalSus`).
"""
import os
import shutil

RAIZ = os.path.dirname(os.path.abspath(__file__))
ORIGEM = os.path.join(RAIZ, "dados_parquet")
DESTINO = os.path.join(RAIZ, "deploy_dados")

CNES_USADOS = ["tbEstabelecimento", "rlEstabServClass", "tbClassificacaoServico", "tbServicoEspecializado",
               "tbCargaHorariaSus", "tbAtividadeProfissional"]

ARQUIVOS = (
    [f"aih/{n}.parquet" for n in ("aih_cancer_mulheres", "aih_rio_claro_geo")]
    + [f"mism2/{n}" for n in sorted(os.listdir(os.path.join(ORIGEM, "mism2")))]
    + [f"cnes/{t}.parquet" for t in CNES_USADOS] + ["cnes/COMPETENCIA.txt"]
)


def main():
    if os.path.isdir(DESTINO):
        shutil.rmtree(DESTINO)
    total = 0
    for rel in ARQUIVOS:
        origem = os.path.join(ORIGEM, *rel.split("/"))
        destino = os.path.join(DESTINO, *rel.split("/"))
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        shutil.copy2(origem, destino)
        total += os.path.getsize(destino)
    print(f"{len(ARQUIVOS)} arquivos, {total / 2**20:.1f} MB em {DESTINO}")


if __name__ == "__main__":
    main()
