"""
ETL - Etapa 2: Processamento das tabelas fato (EXP + IMP)
Saída: fExportacao_parcial.csv, fImportacao_parcial.csv, fOperacao.csv
"""

import math
import os
import pandas as pd
from pathlib import Path

try:
    import psutil
    _proc = psutil.Process(os.getpid())
    def mem_info() -> str:
        return f"  RAM: {_proc.memory_info().rss / 1024**2:.0f} MB"
except ImportError:
    def mem_info() -> str:
        return ""

DIR_BRUTOS = Path("/home/matheusma/Documentos/projeto_integrador/dados_brutos")
DIR_LIMPOS = Path("/home/matheusma/Documentos/projeto_integrador/dados_limpos")

CHUNKSIZE = 500_000
ANO_MIN, ANO_MAX = 2011, 2021

# CO_ANO lido como int para filtro numérico direto; métricas como float;
# chaves com zeros à esquerda como str
DTYPE_FATO = {
    "CO_ANO":     int,
    "CO_MES":     int,
    "CO_NCM":     str,
    "CO_UNID":    str,
    "CO_PAIS":    str,
    "SG_UF_NCM":  str,
    "CO_VIA":     str,
    "CO_URF":     str,
    "QT_ESTAT":   float,
    "KG_LIQUIDO": float,
    "VL_FOB":     float,
}

# dtypes de string para leitura dos parciais na fase de unificação
DTYPE_PARCIAL_STR = {
    "CO_NCM": str, "CO_UNID": str, "CO_PAIS": str,
    "CO_VIA": str, "CO_URF": str, "SG_UF_NCM": str,
}


def conta_linhas_rapido(path: Path) -> int:
    """Conta newlines em blocos de 1 MB — muito mais rápido que linha a linha."""
    total = 0
    with open(path, "rb") as f:
        for buf in iter(lambda: f.read(1 << 20), b""):
            total += buf.count(b"\n")
    return total  # inclui o header


def processar_fato(arquivo: Path, saida: Path, tipo: str) -> tuple[int, int]:
    """
    Lê em chunks, filtra 2011-2021, escreve CSV intermediário.
    Retorna (total_lido, total_mantido).
    """
    print(f"\n{'='*62}")
    print(f"  Contando linhas de {arquivo.name}...")
    total_linhas = conta_linhas_rapido(arquivo) - 1  # desconta header
    n_chunks_est = math.ceil(total_linhas / CHUNKSIZE)
    print(f"  {total_linhas:,} linhas  →  ~{n_chunks_est} chunks de {CHUNKSIZE:,}")
    print(f"  Saída: {saida.name}")
    print(f"{'='*62}")

    total_lido = 0
    total_mantido = 0
    primeiro_chunk = True

    reader = pd.read_csv(
        arquivo,
        sep=";",
        encoding="utf-8",
        dtype=DTYPE_FATO,
        quotechar='"',
        chunksize=CHUNKSIZE,
    )

    for i, chunk in enumerate(reader, start=1):
        n_lido = len(chunk)
        total_lido += n_lido

        chunk = chunk[(chunk["CO_ANO"] >= ANO_MIN) & (chunk["CO_ANO"] <= ANO_MAX)]
        chunk["SG_UF_NCM"] = chunk["SG_UF_NCM"].str.strip().str.upper()

        n_mantido = len(chunk)
        total_mantido += n_mantido

        pct_prog = i / n_chunks_est * 100
        print(
            f"  Chunk {i:>3}/{n_chunks_est}"
            f"  |  lido: {n_lido:>7,}"
            f"  mantido: {n_mantido:>7,}"
            f"  ({pct_prog:>5.1f}%)"
            f"{mem_info()}"
        )

        if not chunk.empty:
            chunk.to_csv(
                saida,
                index=False,
                sep=";",
                encoding="utf-8-sig",
                mode="w" if primeiro_chunk else "a",
                header=primeiro_chunk,
            )
            primeiro_chunk = False

    pct_mantido = total_mantido / total_lido * 100 if total_lido else 0
    print(
        f"\n  RESUMO {tipo}: {total_lido:,} lidas "
        f"→ {total_mantido:,} mantidas ({pct_mantido:.1f}%)"
    )
    return total_lido, total_mantido


# ── Etapa 2a: processar EXP ────────────────────────────────────────────────────
exp_lido, exp_mantido = processar_fato(
    DIR_BRUTOS / "EXP_COMPLETA.csv",
    DIR_LIMPOS  / "fExportacao_parcial.csv",
    "EXP",
)

# ── Etapa 2b: processar IMP ────────────────────────────────────────────────────
imp_lido, imp_mantido = processar_fato(
    DIR_BRUTOS / "IMP_COMPLETA.csv",
    DIR_LIMPOS  / "fImportacao_parcial.csv",
    "IMP",
)

# ── Etapa 2c: unificar → fOperacao.csv ────────────────────────────────────────
print(f"\n{'='*62}")
print("  Unificando parciais → fOperacao.csv")
print(f"{'='*62}")

saida_fato = DIR_LIMPOS / "fOperacao.csv"
primeiro = True

for parcial, tipo in [
    (DIR_LIMPOS / "fExportacao_parcial.csv", "EXP"),
    (DIR_LIMPOS / "fImportacao_parcial.csv", "IMP"),
]:
    n_chunks_uni = 0
    for chunk in pd.read_csv(
        parcial, sep=";", encoding="utf-8-sig",
        dtype=DTYPE_PARCIAL_STR, chunksize=CHUNKSIZE,
    ):
        chunk.insert(0, "TIPO_OPERACAO", tipo)
        chunk.to_csv(
            saida_fato,
            index=False,
            sep=";",
            encoding="utf-8-sig",
            mode="w" if primeiro else "a",
            header=primeiro,
        )
        primeiro = False
        n_chunks_uni += 1
    print(f"  {tipo}: {n_chunks_uni} chunk(s) adicionados")

# ── Validação final ────────────────────────────────────────────────────────────
print(f"\n{'='*62}")
print("  VALIDAÇÃO FINAL")
print(f"{'='*62}")

fato_linhas = conta_linhas_rapido(saida_fato) - 1

print(f"\n  Contagens:")
print(f"    EXP original:  {exp_lido:>12,}  →  filtrado: {exp_mantido:>10,}")
print(f"    IMP original:  {imp_lido:>12,}  →  filtrado: {imp_mantido:>10,}")
print(f"    fOperacao.csv:                    total:   {fato_linhas:>10,}")

if fato_linhas == exp_mantido + imp_mantido:
    print("    Contagem: OK (EXP + IMP == fOperacao)")
else:
    print(f"    ERRO DE CONTAGEM: esperado {exp_mantido + imp_mantido:,}, encontrado {fato_linhas:,}")

print(f"\n  Tamanhos:")
for f in [
    DIR_LIMPOS / "fExportacao_parcial.csv",
    DIR_LIMPOS / "fImportacao_parcial.csv",
    saida_fato,
]:
    mb = f.stat().st_size / 1024 ** 2
    print(f"    {f.name:<32}  {mb:>8.1f} MB")

print(f"\n  head(5) de fOperacao.csv:")
fato_head = pd.read_csv(
    saida_fato, sep=";", encoding="utf-8-sig", nrows=5,
    dtype=DTYPE_PARCIAL_STR,
)
print(fato_head.to_string(index=False))

print(f"\n  Integridade referencial:")
dims = {
    "CO_PAIS":  (DIR_LIMPOS / "dPais.csv",    "CO_PAIS"),
    "CO_NCM":   (DIR_LIMPOS / "dNCM.csv",     "CO_NCM"),
    "CO_UNID":  (DIR_LIMPOS / "dUnidade.csv", "CO_UNID"),
    "CO_VIA":   (DIR_LIMPOS / "dVia.csv",     "CO_VIA"),
    "CO_URF":   (DIR_LIMPOS / "dURF.csv",     "CO_URF"),
}

fato_chaves = pd.read_csv(
    saida_fato, sep=";", encoding="utf-8-sig",
    usecols=list(dims.keys()),
    dtype={k: str for k in dims},
)

todos_ok = True
for col, (dim_path, dim_col) in dims.items():
    chaves_dim = set(
        pd.read_csv(dim_path, sep=";", encoding="utf-8-sig",
                    usecols=[dim_col], dtype=str)[dim_col]
    )
    vals = fato_chaves[col].dropna()
    n_total = len(vals)
    n_match = vals.isin(chaves_dim).sum()
    pct = n_match / n_total * 100 if n_total else 0
    status = "OK     " if pct == 100.0 else "ATENÇÃO"
    if pct < 100.0:
        todos_ok = False
        ausentes = vals[~vals.isin(chaves_dim)].unique()[:5]
        print(f"    {status}  {col:<12}  {n_match:,}/{n_total:,}  ({pct:.4f}%)  ex. ausentes: {list(ausentes)}")
    else:
        print(f"    {status}  {col:<12}  {n_match:,}/{n_total:,}  ({pct:.4f}%)")

print()
if todos_ok:
    print("  Integridade referencial: 100% em todas as chaves.")
else:
    print("  Integridade referencial: existem chaves sem correspondência nas dimensões.")

print("\nETAPA 2 CONCLUÍDA.")
