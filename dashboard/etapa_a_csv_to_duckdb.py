"""
Etapa A — Conversão CSV → DuckDB
Carrega as 8 tabelas do Star Schema diretamente pelo DuckDB (sem pandas).
"""

import time
import duckdb
from pathlib import Path

DIR_LIMPOS = Path('/home/matheusma/Documentos/projeto_integrador/dados_limpos')
DB_PATH    = Path('/home/matheusma/Documentos/projeto_integrador/dashboard/dados.duckdb')

DB_PATH.unlink(missing_ok=True)   # recomeça do zero se já existir
con = duckdb.connect(str(DB_PATH))

# Opções comuns de leitura de CSV (UTF-8 com BOM, sep=;)
def csv(nome: str) -> str:
    return f"read_csv('{DIR_LIMPOS / nome}', delim=';', header=true, encoding='utf-8')"


# ── 1. Criar tabelas ───────────────────────────────────────────────────────────
print("=" * 60)
print("  Criando tabelas")
print("=" * 60)

tabelas = {
    # Dimensões pequenas — leitura simples, tipos inferidos (todos VARCHAR/int ok)
    'dCalendario': f"""
        SELECT
            CAST(Data       AS DATE)    AS Data,
            CAST(Ano        AS INTEGER) AS Ano,
            CAST(Mes        AS INTEGER) AS Mes,
            NomeMes, NomeMesAbrev,
            CAST(Trimestre  AS INTEGER) AS Trimestre,
            NomeTrimestre,
            CAST(Semestre   AS INTEGER) AS Semestre,
            NomeSemestre,
            CAST(AnoMes     AS INTEGER) AS AnoMes,
            AnoMesNome,
            CAST(DiaSemana  AS INTEGER) AS DiaSemana,
            NomeDiaSemana
        FROM {csv('dCalendario.csv')}""",

    'dNCM': f"""
        SELECT
            CAST(CO_NCM AS VARCHAR) AS CO_NCM,
            NO_NCM_POR
        FROM {csv('dNCM.csv')}""",

    'dPais': f"""
        SELECT
            CAST(CO_PAIS       AS VARCHAR) AS CO_PAIS,
            CAST(CO_PAIS_ISOA3 AS VARCHAR) AS CO_PAIS_ISOA3,
            NO_PAIS
        FROM {csv('dPais.csv')}""",

    'dUF': f"""
        SELECT
            CAST(SG_UF     AS VARCHAR) AS SG_UF,
            NO_UF, NO_REGIAO,
            CAST(CO_REGIAO AS INTEGER) AS CO_REGIAO
        FROM {csv('dUF.csv')}""",

    'dUnidade': f"""
        SELECT
            CAST(CO_UNID AS VARCHAR) AS CO_UNID,
            NO_UNID, SG_UNID
        FROM {csv('dUnidade.csv')}""",

    'dURF': f"""
        SELECT
            CAST(CO_URF AS VARCHAR) AS CO_URF,
            NO_URF
        FROM {csv('dURF.csv')}""",

    'dVia': f"""
        SELECT
            CAST(CO_VIA AS VARCHAR) AS CO_VIA,
            NO_VIA
        FROM {csv('dVia.csv')}""",
}

# Dimensões pequenas
for nome, query in tabelas.items():
    t0 = time.perf_counter()
    con.execute(f"CREATE TABLE {nome} AS {query}")
    n = con.execute(f"SELECT COUNT(*) FROM {nome}").fetchone()[0]
    print(f"  {nome:<14}  {n:>8,} linhas  ({time.perf_counter()-t0:.2f}s)")

# fato — tabela grande: CREATE com tipos explícitos + COPY
print(f"\n  fOperacao (1,8 GB — aguarde...)")
con.execute("""
    CREATE TABLE fOperacao (
        TIPO_OPERACAO VARCHAR,
        CO_ANO        INTEGER,
        CO_MES        INTEGER,
        CO_NCM        VARCHAR,
        CO_UNID       VARCHAR,
        CO_PAIS       VARCHAR,
        SG_UF_NCM     VARCHAR,
        CO_VIA        VARCHAR,
        CO_URF        VARCHAR,
        QT_ESTAT      DOUBLE,
        KG_LIQUIDO    DOUBLE,
        VL_FOB        DOUBLE
    )
""")
t0 = time.perf_counter()
con.execute(f"""
    COPY fOperacao FROM '{DIR_LIMPOS / 'fOperacao.csv'}'
    (DELIMITER ';', HEADER, ENCODING 'UTF-8')
""")
elapsed = time.perf_counter() - t0
n_fato = con.execute("SELECT COUNT(*) FROM fOperacao").fetchone()[0]
print(f"  {'fOperacao':<14}  {n_fato:>8,} linhas  ({elapsed:.1f}s)")


# ── 2. Índices ─────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("  Criando índices")
print("=" * 60)

indices = [
    ("idx_ano",        "fOperacao(CO_ANO)"),
    ("idx_mes",        "fOperacao(CO_MES)"),
    ("idx_pais",       "fOperacao(CO_PAIS)"),
    ("idx_tipo",       "fOperacao(TIPO_OPERACAO)"),
    ("idx_uf",         "fOperacao(SG_UF_NCM)"),
]
for nome, defn in indices:
    con.execute(f"CREATE INDEX {nome} ON {defn}")
    print(f"  {nome:<16}  →  {defn}")


# ── 3. Validação ───────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("  VALIDAÇÃO PÓS-CARGA")
print("=" * 60)

# a) Contagens
print("\na) Contagem de linhas:")
contagens = con.execute("""
    SELECT 'fOperacao'   AS tabela, COUNT(*) AS n FROM fOperacao   UNION ALL
    SELECT 'dCalendario',           COUNT(*)       FROM dCalendario UNION ALL
    SELECT 'dNCM',                  COUNT(*)       FROM dNCM        UNION ALL
    SELECT 'dPais',                 COUNT(*)       FROM dPais       UNION ALL
    SELECT 'dUF',                   COUNT(*)       FROM dUF         UNION ALL
    SELECT 'dUnidade',              COUNT(*)       FROM dUnidade    UNION ALL
    SELECT 'dURF',                  COUNT(*)       FROM dURF        UNION ALL
    SELECT 'dVia',                  COUNT(*)       FROM dVia
""").fetchall()
for tabela, n in contagens:
    print(f"   {tabela:<14}  {n:>12,}")

# b) Tipos das colunas críticas da fato
print("\nb) Tipos das colunas (fOperacao — DESCRIBE):")
desc = con.execute("DESCRIBE fOperacao").fetchall()
criticas = {'CO_NCM', 'CO_UNID', 'CO_PAIS', 'CO_VIA', 'CO_URF', 'SG_UF_NCM',
            'CO_ANO', 'CO_MES', 'QT_ESTAT', 'KG_LIQUIDO', 'VL_FOB', 'TIPO_OPERACAO'}
for row in desc:
    col, tipo = row[0], row[1]
    mark = ' ✓' if col in criticas else ''
    print(f"   {col:<16}  {tipo}{mark}")

# c) Sample
print("\nc) SELECT * FROM fOperacao LIMIT 5:")
rows = con.execute("SELECT * FROM fOperacao LIMIT 5").fetchall()
cols = [d[0] for d in con.execute("DESCRIBE fOperacao").fetchall()]
print("   " + " | ".join(f"{c:<12}" for c in cols))
print("   " + "-" * (15 * len(cols)))
for row in rows:
    print("   " + " | ".join(f"{str(v):<12}" for v in row))

# d) Tamanho do arquivo
mb = DB_PATH.stat().st_size / 1024**2
print(f"\nd) Tamanho do arquivo dados.duckdb: {mb:.1f} MB")


# ── 4. Benchmark ───────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("  PERFORMANCE BENCHMARK")
print("=" * 60)

benchmarks = [
    ("Q1 — SUM(VL_FOB) EXP",
     "SELECT SUM(VL_FOB) AS total_fob FROM fOperacao WHERE TIPO_OPERACAO='EXP'"),

    ("Q2 — VL_FOB por Ano",
     "SELECT CO_ANO, SUM(VL_FOB) AS total FROM fOperacao GROUP BY CO_ANO ORDER BY CO_ANO"),

    ("Q3 — Top 10 Países",
     """SELECT p.NO_PAIS, SUM(f.VL_FOB) AS total
        FROM fOperacao f
        JOIN dPais p ON f.CO_PAIS = p.CO_PAIS
        GROUP BY p.NO_PAIS
        ORDER BY total DESC
        LIMIT 10"""),
]

for label, query in benchmarks:
    t0 = time.perf_counter()
    result = con.execute(query).fetchall()
    elapsed_ms = (time.perf_counter() - t0) * 1000
    status = "OK" if elapsed_ms < 2000 else "LENTO"
    print(f"\n  {label}  [{status} — {elapsed_ms:.0f} ms]")
    for row in result[:10]:
        print(f"    {row}")

con.close()
print(f"\n{'='*60}")
print("  ETAPA A CONCLUÍDA — dados.duckdb pronto.")
print("=" * 60)
