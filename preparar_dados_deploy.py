"""Monta `deploy_dados/`: só os Parquets que o site usa, prontos para subir no dataset privado do Hugging Face.

  python preparar_dados_deploy.py              # pacote enxuto (padrão)
  python preparar_dados_deploy.py --completo   # CNES do Brasil inteiro, sem filtro

Não altera nada em `dados_parquet/`. O pacote enxuto:
  - não leva o AIH completo (`aih_cancer_mulheres`): o mapa usa só `aih_rio_claro_geo`, que já traz as colunas de que precisa;
  - leva as 3 tabelas grandes do CNES só do Estado de SP (CO_ESTADO_GESTOR = 35), porque "Onde ser atendida" escolhe as
    unidades pelo município gestor (Rio Claro). O resultado para qualquer cidade de SP é o mesmo do arquivo completo.
Fica de fora, de propósito, `tbDadosProfissionalSus` (nomes de pessoas).
"""
import os
import shutil
import sys

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

RAIZ = os.path.dirname(os.path.abspath(__file__))
ORIGEM = os.path.join(RAIZ, "dados_parquet")
DESTINO = os.path.join(RAIZ, "deploy_dados")

CNES_PEQUENOS = ["tbClassificacaoServico", "tbServicoEspecializado", "tbAtividadeProfissional"]
CNES_FILTRADOS = ["rlEstabServClass", "tbCargaHorariaSus"]  # filtradas pelas unidades de SP (CO_UNIDADE)
UF_SP = "35"


def copiar(rel):
    origem, destino = os.path.join(ORIGEM, *rel.split("/")), os.path.join(DESTINO, *rel.split("/"))
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    shutil.copy2(origem, destino)


def filtrar_por_unidades(tabela, unidades):
    """Copia `tabela` mantendo só as linhas cujas CO_UNIDADE estão em `unidades` (em lotes, sem carregar tudo)."""
    arq = pq.ParquetFile(os.path.join(ORIGEM, "cnes", tabela + ".parquet"))
    destino = os.path.join(DESTINO, "cnes", tabela + ".parquet")
    valores = pa.array(unidades)
    with pq.ParquetWriter(destino, arq.schema_arrow, compression="zstd") as w:
        for lote in arq.iter_batches(batch_size=500_000):
            t = pa.Table.from_batches([lote])
            w.write_table(t.filter(pc.is_in(t["CO_UNIDADE"], value_set=valores)))


def main(completo=False):
    if os.path.isdir(DESTINO):
        shutil.rmtree(DESTINO)
    copiar("aih/aih_rio_claro_geo.parquet")
    copiar("cnes/COMPETENCIA.txt")
    for nome in sorted(os.listdir(os.path.join(ORIGEM, "mism2"))):
        copiar(f"mism2/{nome}")
    for t in CNES_PEQUENOS:
        copiar(f"cnes/{t}.parquet")
    if completo:
        for t in ["tbEstabelecimento"] + CNES_FILTRADOS:
            copiar(f"cnes/{t}.parquet")
    else:
        estab = pq.read_table(os.path.join(ORIGEM, "cnes", "tbEstabelecimento.parquet"))
        sp = estab.filter(pc.equal(estab["CO_ESTADO_GESTOR"], UF_SP))
        pq.write_table(sp, os.path.join(DESTINO, "cnes", "tbEstabelecimento.parquet"), compression="zstd")
        unidades = sp["CO_UNIDADE"].to_pylist()
        for t in CNES_FILTRADOS:
            filtrar_por_unidades(t, unidades)
        print(f"CNES filtrado para SP: {sp.num_rows:,} de {estab.num_rows:,} estabelecimentos")
    arquivos = [os.path.join(r, f) for r, _, fs in os.walk(DESTINO) for f in fs]
    total = sum(os.path.getsize(a) for a in arquivos)
    print(f"{len(arquivos)} arquivos, {total / 2**20:.1f} MB em {DESTINO}")


if __name__ == "__main__":
    main(completo="--completo" in sys.argv)
