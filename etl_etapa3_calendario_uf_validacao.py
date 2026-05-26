"""
ETL - Etapa 3: dCalendario, dUF e validações finais consolidadas
"""

import pandas as pd
from pathlib import Path
from datetime import date, timedelta

DIR_LIMPOS = Path("/home/matheusma/Documentos/projeto_integrador/dados_limpos")

WRITE_OPTS = dict(index=False, sep=";", encoding="utf-8-sig")

# ── 1) dCalendario ─────────────────────────────────────────────────────────────
print("=" * 62)
print("  Gerando dCalendario.csv (2011-01-01 → 2021-12-31)")
print("=" * 62)

MESES_PT   = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
              "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
MESES_ABREV = ["", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
               "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
DIAS_PT     = ["", "Segunda-feira", "Terça-feira", "Quarta-feira",
               "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]

inicio = date(2011, 1, 1)
fim    = date(2021, 12, 31)
n_dias = (fim - inicio).days + 1

rows = []
d = inicio
while d <= fim:
    mes = d.month
    trim = (mes - 1) // 3 + 1
    sem  = 1 if mes <= 6 else 2
    rows.append({
        "Data":          d.strftime("%Y-%m-%d"),
        "Ano":           d.year,
        "Mes":           mes,
        "NomeMes":       MESES_PT[mes],
        "NomeMesAbrev":  MESES_ABREV[mes],
        "Trimestre":     trim,
        "NomeTrimestre": f"T{trim}",
        "Semestre":      sem,
        "NomeSemestre":  f"S{sem}",
        "AnoMes":        d.year * 100 + mes,
        "AnoMesNome":    f"{d.year}-{mes:02d} {MESES_ABREV[mes]}",
        "DiaSemana":     d.isoweekday(),        # 1=Seg … 7=Dom (ISO)
        "NomeDiaSemana": DIAS_PT[d.isoweekday()],
    })
    d += timedelta(days=1)

cal = pd.DataFrame(rows)
cal.to_csv(DIR_LIMPOS / "dCalendario.csv", **WRITE_OPTS)
print(f"  {len(cal):,} linhas geradas (esperado: {n_dias})")
assert len(cal) == n_dias, "ERRO: contagem de dias não bate!"
print("  OK: contagem correta")
print(cal.head(3).to_string(index=False))
print(f"  ...\n  {cal.tail(1).to_string(index=False, header=False)}")


# ── 2) dUF ─────────────────────────────────────────────────────────────────────
print(f"\n{'='*62}")
print("  Gerando dUF.csv")
print("=" * 62)

# 27 UFs oficiais (IBGE) + 6 códigos especiais encontrados na fato
UFS = [
    # Região Norte (1)
    ("AC", "Acre",                "Norte",        1),
    ("AM", "Amazonas",            "Norte",        1),
    ("AP", "Amapá",               "Norte",        1),
    ("PA", "Pará",                "Norte",        1),
    ("RO", "Rondônia",            "Norte",        1),
    ("RR", "Roraima",             "Norte",        1),
    ("TO", "Tocantins",           "Norte",        1),
    # Região Nordeste (2)
    ("AL", "Alagoas",             "Nordeste",     2),
    ("BA", "Bahia",               "Nordeste",     2),
    ("CE", "Ceará",               "Nordeste",     2),
    ("MA", "Maranhão",            "Nordeste",     2),
    ("PB", "Paraíba",             "Nordeste",     2),
    ("PE", "Pernambuco",          "Nordeste",     2),
    ("PI", "Piauí",               "Nordeste",     2),
    ("RN", "Rio Grande do Norte", "Nordeste",     2),
    ("SE", "Sergipe",             "Nordeste",     2),
    # Região Sudeste (3)
    ("ES", "Espírito Santo",      "Sudeste",      3),
    ("MG", "Minas Gerais",        "Sudeste",      3),
    ("RJ", "Rio de Janeiro",      "Sudeste",      3),
    ("SP", "São Paulo",           "Sudeste",      3),
    # Região Sul (4)
    ("PR", "Paraná",              "Sul",          4),
    ("RS", "Rio Grande do Sul",   "Sul",          4),
    ("SC", "Santa Catarina",      "Sul",          4),
    # Região Centro-Oeste (5)
    ("DF", "Distrito Federal",    "Centro-Oeste", 5),
    ("GO", "Goiás",               "Centro-Oeste", 5),
    ("MS", "Mato Grosso do Sul",  "Centro-Oeste", 5),
    ("MT", "Mato Grosso",         "Centro-Oeste", 5),
    # Códigos especiais presentes na fato (encontrados via validação)
    ("EX", "Exterior",                    "Não se aplica", 0),
    ("ND", "Não Declarado",               "Não se aplica", 0),
    ("ZN", "Zona Franca de Manaus",       "Não se aplica", 0),
    ("MN", "Município de Manaus (ZFM)",   "Não se aplica", 0),
    ("RE", "Recinto Especial",            "Não se aplica", 0),
    ("CB", "Codevasf / Brasília",         "Não se aplica", 0),
]

uf = pd.DataFrame(UFS, columns=["SG_UF", "NO_UF", "NO_REGIAO", "CO_REGIAO"])
uf.to_csv(DIR_LIMPOS / "dUF.csv", **WRITE_OPTS)
print(f"  {len(uf)} entradas (27 oficiais + 6 códigos especiais)")
print(uf.to_string(index=False))


# ── 3) Validações finais consolidadas ──────────────────────────────────────────
print(f"\n{'='*62}")
print("  VALIDAÇÕES FINAIS CONSOLIDADAS")
print("=" * 62)

FATO = DIR_LIMPOS / "fOperacao.csv"
DTYPE_STR_CHAVES = {
    "CO_NCM": str, "CO_UNID": str, "CO_PAIS": str,
    "CO_VIA": str, "CO_URF": str, "SG_UF_NCM": str,
}

# a) Lista de todos os arquivos em dados_limpos/
print("\na) Arquivos em dados_limpos/:")
arquivos = sorted(DIR_LIMPOS.glob("*.csv"))
for f in arquivos:
    mb = f.stat().st_size / 1024 ** 2
    print(f"   {f.name:<32}  {mb:>8.1f} MB")

# b) Contagem de linhas de cada arquivo
print("\nb) Contagem de linhas:")

def conta_linhas(path: Path) -> int:
    total = 0
    with open(path, "rb") as f:
        for buf in iter(lambda: f.read(1 << 20), b""):
            total += buf.count(b"\n")
    return total

for f in arquivos:
    n = conta_linhas(f) - 1  # desconta header
    print(f"   {f.name:<32}  {n:>12,} linhas")

# c) Integridade referencial completa
print("\nc) Integridade referencial:")

dims_todas = {
    "CO_PAIS":   (DIR_LIMPOS / "dPais.csv",      "CO_PAIS"),
    "CO_NCM":    (DIR_LIMPOS / "dNCM.csv",       "CO_NCM"),
    "CO_UNID":   (DIR_LIMPOS / "dUnidade.csv",   "CO_UNID"),
    "CO_VIA":    (DIR_LIMPOS / "dVia.csv",       "CO_VIA"),
    "CO_URF":    (DIR_LIMPOS / "dURF.csv",       "CO_URF"),
    "SG_UF_NCM": (DIR_LIMPOS / "dUF.csv",        "SG_UF"),
}

# Carrega só as colunas de chave da fato (em chunks para não estourar RAM)
print("   Carregando chaves da fato (pode demorar alguns segundos)...")
chaves_fato = {col: set() for col in dims_todas}
for chunk in pd.read_csv(FATO, sep=";", encoding="utf-8-sig",
                          usecols=list(dims_todas.keys()),
                          dtype=DTYPE_STR_CHAVES, chunksize=500_000):
    for col in dims_todas:
        chaves_fato[col].update(chunk[col].dropna().unique())

# Valida cada dimensão
todos_ok = True
for col, (dim_path, dim_col) in dims_todas.items():
    chaves_dim = set(
        pd.read_csv(dim_path, sep=";", encoding="utf-8-sig",
                    usecols=[dim_col], dtype=str)[dim_col]
    )
    fato_vals = chaves_fato[col]
    n_fato    = len(fato_vals)
    ausentes  = fato_vals - chaves_dim
    n_match   = n_fato - len(ausentes)
    pct       = n_match / n_fato * 100 if n_fato else 0
    status    = "OK     " if not ausentes else "ATENÇÃO"
    if ausentes:
        todos_ok = False
        print(f"   {status}  {col:<12}  {n_match}/{n_fato} valores únicos  ({pct:.4f}%)  ausentes: {sorted(ausentes)[:5]}")
    else:
        print(f"   {status}  {col:<12}  {n_match}/{n_fato} valores únicos  ({pct:.4f}%)")

# Valida cobertura de dCalendario por ANO+MES
print("\n   Verificando cobertura de dCalendario (CO_ANO / CO_MES)...")
anomes_fato = set()
for chunk in pd.read_csv(FATO, sep=";", encoding="utf-8-sig",
                          usecols=["CO_ANO", "CO_MES"], chunksize=500_000):
    for row in chunk[["CO_ANO", "CO_MES"]].drop_duplicates().itertuples(index=False):
        anomes_fato.add((row.CO_ANO, row.CO_MES))

cal_check = pd.read_csv(DIR_LIMPOS / "dCalendario.csv", sep=";", encoding="utf-8-sig",
                         usecols=["Ano", "Mes"]).drop_duplicates()
anomes_cal = set(zip(cal_check["Ano"], cal_check["Mes"]))

ausentes_cal = anomes_fato - anomes_cal
if ausentes_cal:
    todos_ok = False
    print(f"   ATENÇÃO  dCalendario  ausentes: {sorted(ausentes_cal)[:5]}")
else:
    print(f"   OK       dCalendario  {len(anomes_fato)} combinações Ano/Mês cobertas (100%)")

# d) Resumo do modelo Star Schema
print(f"\nd) Resumo do modelo Star Schema gerado:")
print(f"""
   ┌─────────────────────────────────────────────────────┐
   │              STAR SCHEMA — Comex Stat               │
   │                   (2011–2021)                       │
   ├─────────────────────────────────────────────────────┤
   │  FATO (1)                                           │
   │    fOperacao        30.782.936 linhas               │
   │    Colunas: TIPO_OPERACAO, CO_ANO, CO_MES,          │
   │             CO_NCM, CO_UNID, CO_PAIS, SG_UF_NCM,   │
   │             CO_VIA, CO_URF, QT_ESTAT,               │
   │             KG_LIQUIDO, VL_FOB                      │
   ├─────────────────────────────────────────────────────┤
   │  DIMENSÕES (7)                                      │
   │    dCalendario  →  FK: CO_ANO + CO_MES              │
   │    dNCM         →  FK: CO_NCM                       │
   │    dPais        →  FK: CO_PAIS                      │
   │    dUnidade     →  FK: CO_UNID                      │
   │    dURF         →  FK: CO_URF                       │
   │    dVia         →  FK: CO_VIA                       │
   │    dUF          →  FK: SG_UF_NCM                    │
   └─────────────────────────────────────────────────────┘""")

print()
if todos_ok:
    print("  Resultado geral: TODAS AS VALIDAÇÕES PASSARAM.")
else:
    print("  Resultado geral: EXISTEM PROBLEMAS — verifique acima.")

print("\nETAPA 3 CONCLUÍDA.")
