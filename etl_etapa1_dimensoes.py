"""
ETL - Etapa 1: Processamento das dimensões pequenas
Saída: dNCM, dPais, dUnidade, dVia, dURF em dados_limpos/
"""

import pandas as pd
from pathlib import Path

DIR_BRUTOS = Path("/home/matheusma/Documentos/projeto_integrador/dados_brutos")
DIR_LIMPOS = Path("/home/matheusma/Documentos/projeto_integrador/dados_limpos")
DIR_LIMPOS.mkdir(exist_ok=True)

READ_OPTS = dict(sep=";", encoding="utf-8", dtype=str, quotechar='"')


def trim_df(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]):
            df[col] = df[col].str.strip()
    return df


def validate_trim(df: pd.DataFrame, nome: str) -> bool:
    ok = True
    for col in df.select_dtypes(include=["object", "string"]).columns:
        n = (df[col] != df[col].str.strip()).sum()
        if n > 0:
            print(f"  AINDA TEM PADDING em {col}: {n} linhas")
            ok = False
        else:
            print(f"  OK: {col}")
    return ok


# ── dPais ──────────────────────────────────────────────────────────────────────
print("Processando dPais...")
pais = pd.read_csv(DIR_BRUTOS / "CO_PAIS.csv", **READ_OPTS,
                   usecols=["CO_PAIS", "CO_PAIS_ISOA3", "NO_PAIS"])
pais = trim_df(pais)
pais = pais.drop_duplicates(subset="CO_PAIS")
validate_trim(pais, "dPais")
pais.to_csv(DIR_LIMPOS / "dPais.csv", index=False, sep=";", encoding="utf-8-sig")
print(f"  {len(pais):,} países  →  dados_limpos/dPais.csv")
print(pais.head(3).to_string(index=False))

# ── dUnidade ───────────────────────────────────────────────────────────────────
print("\nProcessando dUnidade...")
unid = pd.read_csv(DIR_BRUTOS / "CO_UNID.csv", **READ_OPTS,
                   usecols=["CO_UNID", "NO_UNID", "SG_UNID"])
unid = trim_df(unid)
unid = unid.drop_duplicates(subset="CO_UNID")
validate_trim(unid, "dUnidade")
unid.to_csv(DIR_LIMPOS / "dUnidade.csv", index=False, sep=";", encoding="utf-8-sig")
print(f"  {len(unid):,} unidades  →  dados_limpos/dUnidade.csv")
print(unid.head(3).to_string(index=False))

# ── dURF ───────────────────────────────────────────────────────────────────────
print("\nProcessando dURF...")
urf = pd.read_csv(DIR_BRUTOS / "CO_URF.csv", **READ_OPTS,
                  usecols=["CO_URF", "NO_URF"])
urf = trim_df(urf)
urf = urf.drop_duplicates(subset="CO_URF")
validate_trim(urf, "dURF")
urf.to_csv(DIR_LIMPOS / "dURF.csv", index=False, sep=";", encoding="utf-8-sig")
print(f"  {len(urf):,} URFs  →  dados_limpos/dURF.csv")
print(urf.head(3).to_string(index=False))

# ── dVia ───────────────────────────────────────────────────────────────────────
print("\nProcessando dVia...")
via = pd.read_csv(DIR_BRUTOS / "CO_VIA.csv", **READ_OPTS,
                  usecols=["CO_VIA", "NO_VIA"])
via = trim_df(via)
via = via.drop_duplicates(subset="CO_VIA")
validate_trim(via, "dVia")
via.to_csv(DIR_LIMPOS / "dVia.csv", index=False, sep=";", encoding="utf-8-sig")
print(f"  {len(via):,} vias  →  dados_limpos/dVia.csv")
print(via.head(3).to_string(index=False))

# ── dNCM ───────────────────────────────────────────────────────────────────────
print("\nProcessando dNCM...")
ncm = pd.read_csv(DIR_BRUTOS / "CO_NCM.csv", **READ_OPTS,
                  usecols=["CO_NCM", "NO_NCM_POR"])
ncm = trim_df(ncm)
ncm = ncm.drop_duplicates(subset="CO_NCM")
validate_trim(ncm, "dNCM")
ncm.to_csv(DIR_LIMPOS / "dNCM.csv", index=False, sep=";", encoding="utf-8-sig")
print(f"  {len(ncm):,} NCMs  →  dados_limpos/dNCM.csv")
print(ncm.head(3).to_string(index=False))

# ── Resumo ─────────────────────────────────────────────────────────────────────
print("\n" + "="*55)
print("ETAPA 1 CONCLUÍDA — arquivos gerados em dados_limpos/:")
for f in sorted(DIR_LIMPOS.glob("*.csv")):
    size_kb = f.stat().st_size / 1024
    print(f"  {f.name:<20}  {size_kb:>8.1f} KB")
