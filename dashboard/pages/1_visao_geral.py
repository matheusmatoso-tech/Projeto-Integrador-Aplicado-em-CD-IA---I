"""
Página 1 — Visão Geral
Panorama macro do comércio exterior brasileiro: KPIs, tendência anual, rodapé.
"""

import time
import plotly.graph_objects as go
import streamlit as st

from config  import COLORS, PLOT_BASE, PLOT_AXIS, PLOT_CONFIG, ANO_MIN
from components import render_sidebar, kpi_card, fmt_moeda, fmt_num
from queries import (
    get_kpis, get_kpis_ano,
    get_vlfob_anual, get_record_ano,
    get_metadados,
)

# ── Filtros ────────────────────────────────────────────────────────────────────
t_inicio = time.perf_counter()
filtros = render_sidebar()
anos, tipos, paises, ufs = filtros["anos"], filtros["tipos"], filtros["paises"], filtros["ufs"]

with st.spinner("Atualizando..."):

    # ── Cabeçalho / Storytelling ──────────────────────────────────────────────────
    st.markdown("## Panorama do Comércio Exterior Brasileiro")
    st.markdown(
        f"<p style='color:{COLORS['text_sec']};font-size:0.92rem;margin-top:-8px;margin-bottom:18px'>"
        "Este dashboard analisa <b>30,7 milhões de operações</b> registradas pela Receita Federal "
        "entre <b>2011 e 2021</b>. Use os filtros na barra lateral para explorar diferentes recortes."
        "</p>",
        unsafe_allow_html=True,
    )

    # ── KPIs ───────────────────────────────────────────────────────────────────────
    kpis = get_kpis(anos, tipos, paises, ufs)

    # CAGR: (valor_final / valor_inicial)^(1/num_anos) - 1
    delta_exp = delta_imp = delta_saldo = delta_ops = None
    num_anos = anos[1] - anos[0]
    if num_anos > 0:
        k_ini = get_kpis_ano(anos[0], tipos, paises, ufs)
        k_fim = get_kpis_ano(anos[1], tipos, paises, ufs)

        if k_ini["total_exp"] > 0 and k_fim["total_exp"] > 0:
            delta_exp   = ((k_fim["total_exp"] / k_ini["total_exp"]) ** (1 / num_anos) - 1) * 100
        if k_ini["total_imp"] > 0 and k_fim["total_imp"] > 0:
            delta_imp   = ((k_fim["total_imp"] / k_ini["total_imp"]) ** (1 / num_anos) - 1) * 100
        s_ini, s_fim = k_ini["saldo"], k_fim["saldo"]
        if (s_ini > 0 and s_fim > 0) or (s_ini < 0 and s_fim < 0):
            delta_saldo = ((s_fim / s_ini) ** (1 / num_anos) - 1) * 100
        if k_ini["n_ops"] > 0 and k_fim["n_ops"] > 0:
            delta_ops   = ((k_fim["n_ops"] / k_ini["n_ops"]) ** (1 / num_anos) - 1) * 100

    st.caption(
        "ℹ️ **CAGR** (Taxa Composta de Crescimento Anual): mede o crescimento "
        "médio ao longo do período, eliminando distorções de volatilidade anual.",
        help="CAGR = (Valor Final / Valor Inicial)^(1/nº de anos) − 1",
    )

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        kpi_card("Total Exportado",   fmt_moeda(kpis["total_exp"]),
                 delta_exp,   "📤", cor_valor=COLORS["exp"])
    with c2:
        kpi_card("Total Importado",   fmt_moeda(kpis["total_imp"]),
                 delta_imp,   "📥", cor_valor=COLORS["imp"])
    with c3:
        saldo = kpis["saldo"]
        kpi_card("Saldo Comercial",   fmt_moeda(saldo),
                 delta_saldo, "⚖️",
                 cor_valor=COLORS["positive"] if saldo >= 0 else COLORS["negative"])
    with c4:
        kpi_card("Total de Operações", fmt_num(kpis["n_ops"]),
                 delta_ops, "🗂️", cor_valor=COLORS["primary"])

    st.markdown("<div style='margin-top:24px'></div>", unsafe_allow_html=True)

    # ── Gráfico — VL_FOB anual EXP vs IMP ─────────────────────────────────────────
    df = get_vlfob_anual(anos, tipos, paises, ufs)

    fig = go.Figure()

    df_exp = df[df["TIPO_OPERACAO"] == "EXP"]
    df_imp = df[df["TIPO_OPERACAO"] == "IMP"]

    if not df_exp.empty and "EXP" in tipos:
        fig.add_trace(go.Bar(
            x=df_exp["CO_ANO"],
            y=df_exp["vl_fob"],
            name="Exportação",
            marker_color=COLORS["exp"],
            marker_line_width=0,
            hovertemplate="<b>%{x}</b><br>Exportação: %{y:$.3s}<extra></extra>",
        ))

    if not df_imp.empty and "IMP" in tipos:
        fig.add_trace(go.Bar(
            x=df_imp["CO_ANO"],
            y=df_imp["vl_fob"],
            name="Importação",
            marker_color=COLORS["imp"],
            marker_line_width=0,
            hovertemplate="<b>%{x}</b><br>Importação: %{y:$.3s}<extra></extra>",
        ))

    fig.update_layout(
        **PLOT_BASE,
        title=dict(
            text="<b>VL_FOB Anual</b> — Exportação vs Importação",
            font=dict(size=14, color=COLORS["text"]),
            x=0, xanchor="left",
        ),
        barmode  = "group",
        bargap   = 0.25,
        bargroupgap = 0.06,
        height   = 380,
        xaxis    = dict(**PLOT_AXIS, dtick=1, tickformat="d",
                        title=dict(text="Ano", font=dict(color=COLORS["text_sec"]))),
        yaxis    = dict(**PLOT_AXIS, tickformat="$.2s",
                        title=dict(text="US$ FOB", font=dict(color=COLORS["text_sec"]))),
    )

    st.plotly_chart(fig, use_container_width=True, config=PLOT_CONFIG)

    # Mini storytelling dinâmico
    if "EXP" in tipos and not df_exp.empty:
        rec_ano, rec_val = get_record_ano(anos, "EXP", paises, ufs)
        if rec_val > 0:
            c_sec = COLORS["text_sec"]
            c_txt = COLORS["text"]
            c_exp = COLORS["exp"]
            st.markdown(
                f"<p style='color:{c_sec};font-size:0.85rem;margin-top:-10px'>"
                f"📌 Em <b style='color:{c_txt}'>{rec_ano}</b>, o Brasil registrou o maior "
                f"valor de exportações no período analisado, totalizando "
                f"<b style='color:{c_exp}'>{fmt_moeda(rec_val)}</b> (US$ FOB).</p>",
                unsafe_allow_html=True,
            )

    # ── Rodapé — dimensões únicas ──────────────────────────────────────────────────
    st.divider()

    meta  = get_metadados(anos, tipos, paises, ufs)
    cols  = st.columns(4, gap="medium")
    items = [
        ("🌐 Países parceiros",    meta["n_paises"]),
        ("📦 Produtos (NCM)",      meta["n_ncms"]),
        ("📍 UFs envolvidas",      meta["n_ufs"]),
        ("🚢 Vias de transporte",  meta["n_vias"]),
    ]
    for col, (label, val) in zip(cols, items):
        col.metric(label, fmt_num(val))

    # ── Rodapé global ─────────────────────────────────────────────────────────────
    elapsed = time.perf_counter() - t_inicio
    st.divider()
    st.markdown(
        f"<div style='display:flex;justify-content:space-between;align-items:center;"
        f"color:{COLORS['text_sec']};font-size:0.72rem;padding:4px 0'>"
        f"<span>📦 Dados: <b>Comex Stat / MDIC</b> · Período: 2011–2021 · "
        f"Atualizado conforme arquivo fonte</span>"
        f"<span>⚡ {elapsed*1000:.0f} ms</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
