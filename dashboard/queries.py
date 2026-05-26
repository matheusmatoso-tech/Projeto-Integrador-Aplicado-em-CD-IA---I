"""
queries.py — Todas as queries SQL do dashboard.
Cada função recebe filtros como tuplas hashable e retorna pandas DataFrame ou dict.
"""

import pandas as pd
import streamlit as st
from config import get_connection, TIPOS_ALL, ANO_MIN


# ── Helpers internos ───────────────────────────────────────────────────────────

def _where(
    anos:   tuple[int, int],
    tipos:  tuple[str, ...],
    paises: tuple[str, ...],
    ufs:    tuple[str, ...],
    prefix: str = "f",
) -> str:
    """Monta cláusula WHERE a partir dos filtros selecionados."""
    p = f"{prefix}." if prefix else ""
    clauses: list[str] = [f"{p}CO_ANO BETWEEN {anos[0]} AND {anos[1]}"]

    if set(tipos) != set(TIPOS_ALL):
        tipos_str = "','".join(tipos)
        clauses.append(f"{p}TIPO_OPERACAO IN ('{tipos_str}')")

    if paises:  # tupla vazia = todos os países
        paises_str = "','".join(paises)
        clauses.append(f"{p}CO_PAIS IN ('{paises_str}')")

    if ufs:     # tupla vazia = todas as UFs
        ufs_str = "','".join(ufs)
        clauses.append(f"{p}SG_UF_NCM IN ('{ufs_str}')")

    return "WHERE " + " AND ".join(clauses)


# ── Dados para sidebar ─────────────────────────────────────────────────────────

@st.cache_data
def get_top_paises(n: int = 50) -> pd.DataFrame:
    """Top N países por VL_FOB total — usado para popular o filtro de países."""
    con = get_connection()
    return con.execute(f"""
        SELECT p.CO_PAIS, p.NO_PAIS, SUM(f.VL_FOB) AS total
        FROM fOperacao f
        JOIN dPais p ON f.CO_PAIS = p.CO_PAIS
        GROUP BY p.CO_PAIS, p.NO_PAIS
        ORDER BY total DESC
        LIMIT {n}
    """).df()


@st.cache_data
def get_todas_ufs() -> list[str]:
    """Lista de siglas de UF presentes na dimensão dUF."""
    con = get_connection()
    return (
        con.execute("SELECT SG_UF FROM dUF ORDER BY SG_UF")
        .df()["SG_UF"]
        .tolist()
    )


# ── KPIs Visão Geral ───────────────────────────────────────────────────────────

@st.cache_data
def get_kpis(
    anos:   tuple[int, int],
    tipos:  tuple[str, ...],
    paises: tuple[str, ...],
    ufs:    tuple[str, ...],
) -> dict:
    """KPIs principais: total EXP, IMP, saldo comercial, contagem de operações."""
    con   = get_connection()
    where = _where(anos, tipos, paises, ufs)
    row   = con.execute(f"""
        SELECT
            SUM(CASE WHEN TIPO_OPERACAO = 'EXP' THEN VL_FOB ELSE 0 END) AS total_exp,
            SUM(CASE WHEN TIPO_OPERACAO = 'IMP' THEN VL_FOB ELSE 0 END) AS total_imp,
            COUNT(*) AS n_ops
        FROM fOperacao f
        {where}
    """).fetchone()
    total_exp, total_imp, n_ops = (row[0] or 0), (row[1] or 0), (row[2] or 0)
    return {
        "total_exp": total_exp,
        "total_imp": total_imp,
        "saldo":     total_exp - total_imp,
        "n_ops":     n_ops,
    }


@st.cache_data
def get_kpis_ano(
    ano:    int,
    tipos:  tuple[str, ...],
    paises: tuple[str, ...],
    ufs:    tuple[str, ...],
) -> dict:
    """KPIs para um único ano — usado no cálculo do delta YoY."""
    return get_kpis((ano, ano), tipos, paises, ufs)


# ── Gráfico anual ──────────────────────────────────────────────────────────────

@st.cache_data
def get_vlfob_anual(
    anos:   tuple[int, int],
    tipos:  tuple[str, ...],
    paises: tuple[str, ...],
    ufs:    tuple[str, ...],
) -> pd.DataFrame:
    """VL_FOB somado por ano e tipo de operação — para gráfico de barras."""
    con   = get_connection()
    where = _where(anos, tipos, paises, ufs)
    return con.execute(f"""
        SELECT CO_ANO, TIPO_OPERACAO, SUM(VL_FOB) AS vl_fob
        FROM fOperacao f
        {where}
        GROUP BY CO_ANO, TIPO_OPERACAO
        ORDER BY CO_ANO, TIPO_OPERACAO
    """).df()


@st.cache_data
def get_record_ano(
    anos:   tuple[int, int],
    tipo:   str,
    paises: tuple[str, ...],
    ufs:    tuple[str, ...],
) -> tuple[int, float]:
    """Retorna (ano, valor) do pico de VL_FOB para um tipo de operação."""
    con   = get_connection()
    where = _where(anos, (tipo,), paises, ufs)
    row   = con.execute(f"""
        SELECT CO_ANO, SUM(VL_FOB) AS total
        FROM fOperacao f
        {where}
        GROUP BY CO_ANO
        ORDER BY total DESC
        LIMIT 1
    """).fetchone()
    return (row[0], row[1]) if row else (anos[0], 0.0)


# ── Rodapé — dimensões únicas ──────────────────────────────────────────────────

@st.cache_data
def get_metadados(
    anos:   tuple[int, int],
    tipos:  tuple[str, ...],
    paises: tuple[str, ...],
    ufs:    tuple[str, ...],
) -> dict:
    """Contagem de dimensões únicas ativas no recorte selecionado."""
    con   = get_connection()
    where = _where(anos, tipos, paises, ufs)
    row   = con.execute(f"""
        SELECT
            COUNT(DISTINCT CO_PAIS)   AS n_paises,
            COUNT(DISTINCT CO_NCM)    AS n_ncms,
            COUNT(DISTINCT SG_UF_NCM) AS n_ufs,
            COUNT(DISTINCT CO_VIA)    AS n_vias
        FROM fOperacao f
        {where}
    """).fetchone()
    return {"n_paises": row[0], "n_ncms": row[1], "n_ufs": row[2], "n_vias": row[3]}


# ── Análise Temporal ───────────────────────────────────────────────────────────

@st.cache_data
def get_kpis_temporais(
    anos:   tuple[int, int],
    tipos:  tuple[str, ...],
    paises: tuple[str, ...],
    ufs:    tuple[str, ...],
) -> dict:
    """KPIs temporais: pico mensal, YoY médio anual, melhor trimestre."""
    con   = get_connection()
    where = _where(anos, tipos, paises, ufs)
    df    = con.execute(f"""
        SELECT CO_ANO, CO_MES,
            SUM(CASE WHEN TIPO_OPERACAO='EXP' THEN VL_FOB ELSE 0 END) AS exp,
            SUM(CASE WHEN TIPO_OPERACAO='IMP' THEN VL_FOB ELSE 0 END) AS imp
        FROM fOperacao f
        {where}
        GROUP BY CO_ANO, CO_MES
        ORDER BY CO_ANO, CO_MES
    """).df()

    if df.empty:
        return {"peak_ano": None, "peak_mes": None, "peak_val": 0,
                "avg_yoy": None, "best_trim": None}

    df["total"] = (
        df["exp"] if set(tipos) == {"EXP"}
        else df["imp"] if set(tipos) == {"IMP"}
        else df["exp"] + df["imp"]
    )

    idx      = df["total"].idxmax()
    peak_ano = int(df.loc[idx, "CO_ANO"])
    peak_mes = int(df.loc[idx, "CO_MES"])
    peak_val = float(df.loc[idx, "total"])

    anual    = df.groupby("CO_ANO")["total"].sum()
    yoy_vals = anual.pct_change().dropna() * 100
    avg_yoy  = float(yoy_vals.mean()) if not yoy_vals.empty else None

    df["trim"] = ((df["CO_MES"] - 1) // 3 + 1)
    best_trim  = int(df.groupby("trim")["total"].mean().idxmax())

    return {
        "peak_ano":  peak_ano,
        "peak_mes":  peak_mes,
        "peak_val":  peak_val,
        "avg_yoy":   avg_yoy,
        "best_trim": best_trim,
    }


@st.cache_data
def get_serie_mensal(
    anos:   tuple[int, int],
    tipos:  tuple[str, ...],
    paises: tuple[str, ...],
    ufs:    tuple[str, ...],
) -> pd.DataFrame:
    """Série temporal mensal com média móvel 3m e YoY por mês."""
    con   = get_connection()
    where = _where(anos, tipos, paises, ufs)
    df    = con.execute(f"""
        SELECT CO_ANO, CO_MES,
            SUM(CASE WHEN TIPO_OPERACAO='EXP' THEN VL_FOB ELSE 0 END) AS exp,
            SUM(CASE WHEN TIPO_OPERACAO='IMP' THEN VL_FOB ELSE 0 END) AS imp
        FROM fOperacao f
        {where}
        GROUP BY CO_ANO, CO_MES
        ORDER BY CO_ANO, CO_MES
    """).df()

    if df.empty:
        return df

    df["saldo"] = df["exp"] - df["imp"]
    df["data"]  = pd.to_datetime(
        df["CO_ANO"].astype(str) + "-" + df["CO_MES"].astype(str).str.zfill(2) + "-01"
    )
    df = df.sort_values("data").reset_index(drop=True)
    df["mm3_exp"] = df["exp"].rolling(3, min_periods=1).mean()
    df["mm3_imp"] = df["imp"].rolling(3, min_periods=1).mean()
    df["yoy_exp"] = df["exp"].pct_change(12) * 100
    df["yoy_imp"] = df["imp"].pct_change(12) * 100
    return df


@st.cache_data
def get_yoy_anual(
    anos:   tuple[int, int],
    tipos:  tuple[str, ...],
    paises: tuple[str, ...],
    ufs:    tuple[str, ...],
) -> pd.DataFrame:
    """YoY anual por tipo de operação."""
    ano_ext   = max(anos[0] - 1, ANO_MIN)
    con       = get_connection()
    where_ext = _where((ano_ext, anos[1]), tipos, paises, ufs)
    df        = con.execute(f"""
        SELECT CO_ANO,
            SUM(CASE WHEN TIPO_OPERACAO='EXP' THEN VL_FOB ELSE 0 END) AS exp,
            SUM(CASE WHEN TIPO_OPERACAO='IMP' THEN VL_FOB ELSE 0 END) AS imp
        FROM fOperacao f
        {where_ext}
        GROUP BY CO_ANO
        ORDER BY CO_ANO
    """).df()
    df["yoy_exp"] = df["exp"].pct_change() * 100
    df["yoy_imp"] = df["imp"].pct_change() * 100
    return df[df["CO_ANO"].between(anos[0], anos[1])].reset_index(drop=True)


@st.cache_data
def get_ytd_por_ano(
    anos:   tuple[int, int],
    paises: tuple[str, ...],
    ufs:    tuple[str, ...],
    tipo:   str = "EXP",
) -> pd.DataFrame:
    """YTD acumulado mensal por ano (pivot: index=mês, colunas=anos)."""
    con   = get_connection()
    where = _where(anos, (tipo,), paises, ufs)
    df    = con.execute(f"""
        SELECT CO_ANO, CO_MES, SUM(VL_FOB) AS vl_fob
        FROM fOperacao f
        {where}
        GROUP BY CO_ANO, CO_MES
        ORDER BY CO_ANO, CO_MES
    """).df()
    if df.empty:
        return pd.DataFrame()
    df["ytd"] = df.groupby("CO_ANO")["vl_fob"].cumsum()
    return df.pivot(index="CO_MES", columns="CO_ANO", values="ytd")


@st.cache_data
def get_heatmap_sazonalidade(
    anos:    tuple[int, int],
    tipos:   tuple[str, ...],
    paises:  tuple[str, ...],
    ufs:     tuple[str, ...],
    metrica: str = "exp",
) -> pd.DataFrame:
    """Matriz de sazonalidade: linhas=anos, colunas=meses."""
    con   = get_connection()
    where = _where(anos, tipos, paises, ufs)
    df    = con.execute(f"""
        SELECT CO_ANO, CO_MES,
            SUM(CASE WHEN TIPO_OPERACAO='EXP' THEN VL_FOB ELSE 0 END) AS exp,
            SUM(CASE WHEN TIPO_OPERACAO='IMP' THEN VL_FOB ELSE 0 END) AS imp
        FROM fOperacao f
        {where}
        GROUP BY CO_ANO, CO_MES
        ORDER BY CO_ANO, CO_MES
    """).df()
    if df.empty:
        return pd.DataFrame()
    df["saldo"] = df["exp"] - df["imp"]
    return df.pivot(index="CO_ANO", columns="CO_MES", values=metrica)


@st.cache_data
def get_insights_temporais(
    anos:   tuple[int, int],
    tipos:  tuple[str, ...],
    paises: tuple[str, ...],
    ufs:    tuple[str, ...],
) -> dict:
    """Insights dinâmicos para o rodapé temporal."""
    con            = get_connection()
    tipo_p         = "EXP" if "EXP" in tipos else "IMP"
    where_p        = _where(anos, (tipo_p,), paises, ufs)
    ano_ext        = max(anos[0] - 1, ANO_MIN)
    where_p_ext    = _where((ano_ext, anos[1]), (tipo_p,), paises, ufs)

    row = con.execute(f"""
        SELECT CO_ANO, SUM(VL_FOB) AS total
        FROM fOperacao f {where_p}
        GROUP BY CO_ANO ORDER BY total DESC LIMIT 1
    """).fetchone()
    melhor_ano     = int(row[0]) if row else None
    melhor_ano_val = float(row[1]) if row else 0.0

    df_anual = con.execute(f"""
        SELECT CO_ANO, SUM(VL_FOB) AS total
        FROM fOperacao f {where_p_ext}
        GROUP BY CO_ANO ORDER BY CO_ANO
    """).df()
    df_anual["yoy"] = df_anual["total"].pct_change() * 100
    df_anual        = df_anual[df_anual["CO_ANO"] >= anos[0]].dropna()

    maior_queda_ano = None
    maior_queda_pct = None
    if not df_anual.empty:
        idx_min         = df_anual["yoy"].idxmin()
        maior_queda_ano = int(df_anual.loc[idx_min, "CO_ANO"])
        maior_queda_pct = float(df_anual.loc[idx_min, "yoy"])

    df_mes = con.execute(f"""
        SELECT CO_MES, AVG(mensal) AS media_mes
        FROM (
            SELECT CO_ANO, CO_MES, SUM(VL_FOB) AS mensal
            FROM fOperacao f {where_p}
            GROUP BY CO_ANO, CO_MES
        ) t
        GROUP BY CO_MES
        ORDER BY media_mes DESC
        LIMIT 1
    """).df()

    row_global = con.execute(f"""
        SELECT AVG(mensal) FROM (
            SELECT CO_ANO, CO_MES, SUM(VL_FOB) AS mensal
            FROM fOperacao f {where_p}
            GROUP BY CO_ANO, CO_MES
        ) t
    """).fetchone()

    mes_sazonal = None
    mes_pct     = None
    if not df_mes.empty and row_global and row_global[0]:
        mes_sazonal = int(df_mes.iloc[0]["CO_MES"])
        mes_pct     = float((df_mes.iloc[0]["media_mes"] / row_global[0] - 1) * 100)

    return {
        "tipo_p":        tipo_p,
        "melhor_ano":    melhor_ano,
        "melhor_ano_val": melhor_ano_val,
        "maior_queda_ano": maior_queda_ano,
        "maior_queda_pct": maior_queda_pct,
        "mes_sazonal":   mes_sazonal,
        "mes_sazonal_pct": mes_pct,
    }


# ── Análise Geográfica ─────────────────────────────────────────────────────────

@st.cache_data
def get_top_parceiro(
    anos:   tuple[int, int],
    tipos:  tuple[str, ...],
    paises: tuple[str, ...],
    ufs:    tuple[str, ...],
    tipo:   str = "EXP",
) -> dict:
    """País com maior VL_FOB para um tipo de operação e % do total."""
    con     = get_connection()
    where_t = _where(anos, (tipo,), paises, ufs)
    row     = con.execute(f"""
        SELECT p.NO_PAIS,
               SUM(f.VL_FOB) AS valor,
               SUM(f.VL_FOB) * 100.0 / SUM(SUM(f.VL_FOB)) OVER () AS pct
        FROM fOperacao f
        JOIN dPais p ON f.CO_PAIS = p.CO_PAIS
        {where_t}
        GROUP BY p.NO_PAIS
        ORDER BY valor DESC
        LIMIT 1
    """).fetchone()
    if not row:
        return {"nome": "—", "valor": 0.0, "pct": 0.0}
    return {"nome": row[0], "valor": float(row[1]), "pct": float(row[2])}


@st.cache_data
def get_mapa_mundi(
    anos:   tuple[int, int],
    tipos:  tuple[str, ...],
    paises: tuple[str, ...],
    ufs:    tuple[str, ...],
) -> pd.DataFrame:
    """EXP, IMP e saldo por país (ISO-3 válido) para o choropleth."""
    con   = get_connection()
    where = _where(anos, tipos, paises, ufs)
    df    = con.execute(f"""
        SELECT p.CO_PAIS_ISOA3 AS iso3, p.NO_PAIS AS nome,
            SUM(CASE WHEN f.TIPO_OPERACAO='EXP' THEN f.VL_FOB ELSE 0 END) AS exp,
            SUM(CASE WHEN f.TIPO_OPERACAO='IMP' THEN f.VL_FOB ELSE 0 END) AS imp
        FROM fOperacao f
        JOIN dPais p ON f.CO_PAIS = p.CO_PAIS
        {where}
        AND p.CO_PAIS_ISOA3 != 'ZZZ'
        GROUP BY p.CO_PAIS_ISOA3, p.NO_PAIS
    """).df()
    if df.empty:
        return df
    df["saldo"] = df["exp"] - df["imp"]
    return df


@st.cache_data
def get_distribuicao_regiao(
    anos:   tuple[int, int],
    tipos:  tuple[str, ...],
    paises: tuple[str, ...],
    ufs:    tuple[str, ...],
) -> pd.DataFrame:
    """VL_FOB por região brasileira (agrupa 'Não se aplica' em 'Outros')."""
    con   = get_connection()
    where = _where(anos, tipos, paises, ufs)
    df    = con.execute(f"""
        SELECT
            CASE WHEN u.NO_REGIAO = 'Não se aplica' OR u.NO_REGIAO IS NULL
                 THEN 'Outros' ELSE u.NO_REGIAO END AS regiao,
            SUM(f.VL_FOB) AS total
        FROM fOperacao f
        JOIN dUF u ON f.SG_UF_NCM = u.SG_UF
        {where}
        GROUP BY regiao
        ORDER BY total DESC
    """).df()
    if df.empty:
        return df
    df["pct"] = df["total"] / df["total"].sum() * 100
    return df


@st.cache_data
def get_ranking_ufs(
    anos:   tuple[int, int],
    tipos:  tuple[str, ...],
    paises: tuple[str, ...],
    ufs:    tuple[str, ...],
) -> pd.DataFrame:
    """Ranking completo de UFs com EXP, IMP, saldo e % do total."""
    con   = get_connection()
    where = _where(anos, tipos, paises, ufs)
    df    = con.execute(f"""
        SELECT u.SG_UF, u.NO_UF,
            COALESCE(u.NO_REGIAO, 'Não se aplica') AS NO_REGIAO,
            SUM(CASE WHEN f.TIPO_OPERACAO='EXP' THEN f.VL_FOB ELSE 0 END) AS exp,
            SUM(CASE WHEN f.TIPO_OPERACAO='IMP' THEN f.VL_FOB ELSE 0 END) AS imp
        FROM fOperacao f
        JOIN dUF u ON f.SG_UF_NCM = u.SG_UF
        {where}
        GROUP BY u.SG_UF, u.NO_UF, u.NO_REGIAO
        ORDER BY exp + imp DESC
    """).df()
    if df.empty:
        return df
    df["total"]  = df["exp"] + df["imp"]
    df["saldo"]  = df["exp"] - df["imp"]
    df["pct"]    = df["total"] / df["total"].sum() * 100
    return df


@st.cache_data
def get_uf_lider(
    anos:   tuple[int, int],
    tipos:  tuple[str, ...],
    paises: tuple[str, ...],
    ufs:    tuple[str, ...],
) -> dict:
    """UF com maior volume combinado (EXP+IMP)."""
    df = get_ranking_ufs(anos, tipos, paises, ufs)
    if df.empty:
        return {"sigla": "—", "nome": "—", "regiao": "—", "total": 0.0}
    r = df.iloc[0]
    return {
        "sigla":  r["SG_UF"],
        "nome":   r["NO_UF"],
        "regiao": r["NO_REGIAO"],
        "total":  float(r["total"]),
    }


@st.cache_data
def get_insights_geograficos(
    anos:   tuple[int, int],
    tipos:  tuple[str, ...],
    paises: tuple[str, ...],
    ufs:    tuple[str, ...],
) -> dict:
    """Insights geográficos: total países, top-5 concentração, superávit/déficit."""
    con   = get_connection()
    where = _where(anos, tipos, paises, ufs)

    n_paises = con.execute(f"""
        SELECT COUNT(DISTINCT CO_PAIS) FROM fOperacao f {where}
    """).fetchone()[0] or 0

    total_all = con.execute(f"""
        SELECT SUM(VL_FOB) FROM fOperacao f {where}
    """).fetchone()[0] or 1

    df_top5 = con.execute(f"""
        SELECT SUM(f.VL_FOB) AS total
        FROM fOperacao f
        JOIN dPais p ON f.CO_PAIS = p.CO_PAIS
        {where}
        GROUP BY p.NO_PAIS
        ORDER BY total DESC
        LIMIT 5
    """).df()
    pct_top5 = float(df_top5["total"].sum() / total_all * 100)

    df_regiao = get_distribuicao_regiao(anos, tipos, paises, ufs)
    regiao_lider = df_regiao.iloc[0]["regiao"] if not df_regiao.empty else "—"
    pct_regiao   = float(df_regiao.iloc[0]["pct"]) if not df_regiao.empty else 0.0

    df_mapa   = get_mapa_mundi(anos, tipos, paises, ufs)
    n_superavit = int((df_mapa["saldo"] > 0).sum()) if not df_mapa.empty else 0
    n_deficit   = int((df_mapa["saldo"] < 0).sum()) if not df_mapa.empty else 0

    return {
        "n_paises":     int(n_paises),
        "pct_top5":     pct_top5,
        "regiao_lider": regiao_lider,
        "pct_regiao":   pct_regiao,
        "n_superavit":  n_superavit,
        "n_deficit":    n_deficit,
    }


# ── Produtos & Logística ───────────────────────────────────────────────────────

@st.cache_data
def get_ncm_agg(
    anos:   tuple[int, int],
    tipos:  tuple[str, ...],
    paises: tuple[str, ...],
    ufs:    tuple[str, ...],
) -> pd.DataFrame:
    """Agregação completa por NCM em uma única passagem na tabela fato.

    Colunas: CO_NCM, nome, exp, imp, total, kg_exp, kg_imp, n_exp, n_imp, nome_trunc.
    Substitui get_produto_top×2 + get_top_produtos + get_valor_vs_peso.
    """
    con   = get_connection()
    where = _where(anos, tipos, paises, ufs)
    df    = con.execute(f"""
        SELECT n.CO_NCM, n.NO_NCM_POR AS nome,
            SUM(CASE WHEN f.TIPO_OPERACAO='EXP' THEN f.VL_FOB     ELSE 0 END) AS exp,
            SUM(CASE WHEN f.TIPO_OPERACAO='IMP' THEN f.VL_FOB     ELSE 0 END) AS imp,
            SUM(CASE WHEN f.TIPO_OPERACAO='EXP' THEN f.KG_LIQUIDO ELSE 0 END) AS kg_exp,
            SUM(CASE WHEN f.TIPO_OPERACAO='IMP' THEN f.KG_LIQUIDO ELSE 0 END) AS kg_imp,
            COUNT(CASE WHEN f.TIPO_OPERACAO='EXP' THEN 1 END)                 AS n_exp,
            COUNT(CASE WHEN f.TIPO_OPERACAO='IMP' THEN 1 END)                 AS n_imp,
            SUM(SUM(CASE WHEN f.TIPO_OPERACAO='EXP' THEN f.VL_FOB ELSE 0 END)) OVER () AS total_exp_all,
            SUM(SUM(CASE WHEN f.TIPO_OPERACAO='IMP' THEN f.VL_FOB ELSE 0 END)) OVER () AS total_imp_all
        FROM fOperacao f
        JOIN dNCM n ON f.CO_NCM = n.CO_NCM
        {where}
        GROUP BY n.CO_NCM, n.NO_NCM_POR
        ORDER BY SUM(f.VL_FOB) DESC
        LIMIT 300
    """).df()
    if df.empty:
        return df
    df["total"]      = df["exp"] + df["imp"]
    df["nome_trunc"] = df["nome"].apply(lambda s: s[:42] + "…" if len(s) > 42 else s)
    return df


@st.cache_data
def get_produto_top(
    anos:   tuple[int, int],
    tipos:  tuple[str, ...],
    paises: tuple[str, ...],
    ufs:    tuple[str, ...],
    tipo:   str = "EXP",
) -> dict:
    """Produto (NCM) com maior VL_FOB para um tipo de operação."""
    con     = get_connection()
    where_t = _where(anos, (tipo,), paises, ufs)
    row     = con.execute(f"""
        SELECT n.NO_NCM_POR,
               SUM(f.VL_FOB) AS valor,
               SUM(f.VL_FOB) * 100.0 / SUM(SUM(f.VL_FOB)) OVER () AS pct
        FROM fOperacao f
        JOIN dNCM n ON f.CO_NCM = n.CO_NCM
        {where_t}
        GROUP BY n.NO_NCM_POR
        ORDER BY valor DESC
        LIMIT 1
    """).fetchone()
    if not row:
        return {"nome": "—", "valor": 0.0, "pct": 0.0}
    return {"nome": row[0], "valor": float(row[1]), "pct": float(row[2])}


@st.cache_data
def get_modal_principal(
    anos:   tuple[int, int],
    tipos:  tuple[str, ...],
    paises: tuple[str, ...],
    ufs:    tuple[str, ...],
) -> dict:
    """Via de transporte com maior VL_FOB no período."""
    con   = get_connection()
    where = _where(anos, tipos, paises, ufs)
    row   = con.execute(f"""
        SELECT v.NO_VIA,
               SUM(f.VL_FOB) AS valor,
               SUM(f.VL_FOB) * 100.0 / SUM(SUM(f.VL_FOB)) OVER () AS pct
        FROM fOperacao f
        JOIN dVia v ON f.CO_VIA = v.CO_VIA
        {where}
        GROUP BY v.NO_VIA
        ORDER BY valor DESC
        LIMIT 1
    """).fetchone()
    if not row:
        return {"nome": "—", "valor": 0.0, "pct": 0.0}
    return {"nome": row[0], "valor": float(row[1]), "pct": float(row[2])}


@st.cache_data
def get_urf_principal(
    anos:   tuple[int, int],
    tipos:  tuple[str, ...],
    paises: tuple[str, ...],
    ufs:    tuple[str, ...],
) -> dict:
    """URF com maior VL_FOB no período."""
    con   = get_connection()
    where = _where(anos, tipos, paises, ufs)
    row   = con.execute(f"""
        SELECT REGEXP_REPLACE(u.NO_URF, '^\\d+ - ', '') AS nome,
               SUM(f.VL_FOB) AS valor,
               SUM(f.VL_FOB) * 100.0 / SUM(SUM(f.VL_FOB)) OVER () AS pct
        FROM fOperacao f
        JOIN dURF u ON f.CO_URF = u.CO_URF
        {where}
        GROUP BY u.NO_URF
        ORDER BY valor DESC
        LIMIT 1
    """).fetchone()
    if not row:
        return {"nome": "—", "valor": 0.0, "pct": 0.0}
    return {"nome": row[0], "valor": float(row[1]), "pct": float(row[2])}


@st.cache_data
def get_top_produtos(
    anos:          tuple[int, int],
    tipos:         tuple[str, ...],
    paises:        tuple[str, ...],
    ufs:           tuple[str, ...],
    limite:        int = 15,
    tipo_produtos: str = "EXP",
) -> pd.DataFrame:
    """Top N produtos (NCM) com VL_FOB EXP e IMP."""
    con   = get_connection()
    where = _where(anos, tipos, paises, ufs)
    order = (
        "SUM(CASE WHEN TIPO_OPERACAO='EXP' THEN VL_FOB ELSE 0 END)"
        if tipo_produtos == "EXP"
        else "SUM(CASE WHEN TIPO_OPERACAO='IMP' THEN VL_FOB ELSE 0 END)"
        if tipo_produtos == "IMP"
        else "SUM(VL_FOB)"
    )
    df = con.execute(f"""
        SELECT n.CO_NCM, n.NO_NCM_POR AS nome,
            SUM(CASE WHEN TIPO_OPERACAO='EXP' THEN VL_FOB ELSE 0 END) AS exp,
            SUM(CASE WHEN TIPO_OPERACAO='IMP' THEN VL_FOB ELSE 0 END) AS imp
        FROM fOperacao f
        JOIN dNCM n ON f.CO_NCM = n.CO_NCM
        {where}
        GROUP BY n.CO_NCM, n.NO_NCM_POR
        ORDER BY {order} DESC
        LIMIT {limite}
    """).df()
    if df.empty:
        return df
    df["nome_trunc"] = df["nome"].apply(lambda s: s[:42] + "…" if len(s) > 42 else s)
    return df


@st.cache_data
def get_distribuicao_via(
    anos:     tuple[int, int],
    tipos:    tuple[str, ...],
    paises:   tuple[str, ...],
    ufs:      tuple[str, ...],
    tipo_via: str = "AMBOS",
) -> pd.DataFrame:
    """VL_FOB por via de transporte, agrupando vias < 1% em 'Outras'."""
    con       = get_connection()
    tipos_eff = (tipo_via,) if tipo_via in ("EXP", "IMP") else tipos
    where     = _where(anos, tipos_eff, paises, ufs)
    df        = con.execute(f"""
        SELECT v.NO_VIA, SUM(f.VL_FOB) AS total
        FROM fOperacao f
        JOIN dVia v ON f.CO_VIA = v.CO_VIA
        {where}
        GROUP BY v.NO_VIA
        ORDER BY total DESC
    """).df()
    if df.empty:
        return df
    total_g  = df["total"].sum()
    df["pct"] = df["total"] / total_g * 100
    mask_min  = df["pct"] < 1.0
    if mask_min.any():
        outras = pd.DataFrame({
            "NO_VIA": ["Outras"],
            "total":  [df.loc[mask_min, "total"].sum()],
            "pct":    [df.loc[mask_min, "pct"].sum()],
        })
        df = pd.concat([df[~mask_min], outras], ignore_index=True)
    return df


@st.cache_data
def get_valor_vs_peso(
    anos:   tuple[int, int],
    tipos:  tuple[str, ...],
    paises: tuple[str, ...],
    ufs:    tuple[str, ...],
    limite: int = 100,
) -> pd.DataFrame:
    """Top N NCMs para scatter VL_FOB vs KG_LIQUIDO, por tipo de operação."""
    con   = get_connection()
    where = _where(anos, tipos, paises, ufs)
    df    = con.execute(f"""
        WITH top_ncm AS (
            SELECT CO_NCM
            FROM fOperacao f
            {where} AND KG_LIQUIDO > 0 AND VL_FOB > 0
            GROUP BY CO_NCM
            ORDER BY SUM(VL_FOB) DESC
            LIMIT {limite}
        )
        SELECT n.CO_NCM, n.NO_NCM_POR AS nome,
            f.TIPO_OPERACAO,
            SUM(f.VL_FOB)      AS vl_fob,
            SUM(f.KG_LIQUIDO)  AS kg,
            COUNT(*)           AS n_ops
        FROM fOperacao f
        JOIN dNCM n     ON f.CO_NCM = n.CO_NCM
        JOIN top_ncm tc ON f.CO_NCM = tc.CO_NCM
        {where} AND f.KG_LIQUIDO > 0 AND f.VL_FOB > 0
        GROUP BY n.CO_NCM, n.NO_NCM_POR, f.TIPO_OPERACAO
        HAVING SUM(f.KG_LIQUIDO) > 0
    """).df()
    if df.empty:
        return df
    df["usd_per_kg"]  = df["vl_fob"] / df["kg"]
    df["nome_trunc"]  = df["nome"].apply(lambda s: s[:50] + "…" if len(s) > 50 else s)
    return df


@st.cache_data
def get_ranking_urfs(
    anos:   tuple[int, int],
    tipos:  tuple[str, ...],
    paises: tuple[str, ...],
    ufs:    tuple[str, ...],
) -> pd.DataFrame:
    """Ranking completo de URFs com EXP, IMP, saldo e % do total."""
    con   = get_connection()
    where = _where(anos, tipos, paises, ufs)
    df    = con.execute(f"""
        SELECT u.CO_URF,
            REGEXP_REPLACE(u.NO_URF, '^\\d+ - ', '') AS nome,
            SUM(CASE WHEN TIPO_OPERACAO='EXP' THEN VL_FOB ELSE 0 END) AS exp,
            SUM(CASE WHEN TIPO_OPERACAO='IMP' THEN VL_FOB ELSE 0 END) AS imp
        FROM fOperacao f
        JOIN dURF u ON f.CO_URF = u.CO_URF
        {where}
        GROUP BY u.CO_URF, u.NO_URF
        ORDER BY exp + imp DESC
    """).df()
    if df.empty:
        return df
    df["total"] = df["exp"] + df["imp"]
    df["pct"]   = df["total"] / df["total"].sum() * 100
    return df


@st.cache_data
def get_insights_produtos_logistica(
    anos:   tuple[int, int],
    tipos:  tuple[str, ...],
    paises: tuple[str, ...],
    ufs:    tuple[str, ...],
) -> dict:
    """Insights dinâmicos para Fase 4 — deriva tudo de funções já cacheadas."""
    df_ncm = get_ncm_agg(anos, tipos, paises, ufs)

    # Concentração top-10 EXP (usa total_exp_all = soma de TODOS os NCMs antes do LIMIT 300)
    total_exp = float(df_ncm["total_exp_all"].iloc[0]) if not df_ncm.empty else 1.0
    if total_exp == 0:
        total_exp = 1.0
    pct_top10 = float(df_ncm.nlargest(10, "exp")["exp"].sum() / total_exp * 100)

    # Modal principal — via get_distribuicao_via (cacheada pela página)
    df_via = get_distribuicao_via(anos, tipos, paises, ufs, "AMBOS")
    if not df_via.empty:
        row_m      = df_via.sort_values("total", ascending=False).iloc[0]
        modal_nome = row_m["NO_VIA"]
        modal_pct  = float(row_m["pct"])
    else:
        modal_nome, modal_pct = "—", 0.0

    # Maior USD/kg — derivado do ncm_agg
    df_kg = df_ncm[(df_ncm["kg_exp"] > 0) & (df_ncm["exp"] > 0)].copy()
    if not df_kg.empty:
        df_kg["usd_per_kg"] = df_kg["exp"] / df_kg["kg_exp"]
        idx     = df_kg["usd_per_kg"].idxmax()
        prod_vk = df_kg.loc[idx, "nome_trunc"]
        usd_kg  = float(df_kg.loc[idx, "usd_per_kg"])
    else:
        prod_vk, usd_kg = "—", 0.0

    # URF líder — cacheada pela página
    df_urf = get_ranking_urfs(anos, tipos, paises, ufs)
    if not df_urf.empty:
        urf_nome = df_urf.iloc[0]["nome"]
        urf_pct  = float(df_urf.iloc[0]["pct"])
    else:
        urf_nome, urf_pct = "—", 0.0

    return {
        "pct_top10_exp": pct_top10,
        "modal_nome":    modal_nome,
        "modal_pct":     modal_pct,
        "prod_vk_nome":  prod_vk,
        "prod_usd_kg":   usd_kg,
        "urf_nome":      urf_nome,
        "urf_pct":       urf_pct,
    }
