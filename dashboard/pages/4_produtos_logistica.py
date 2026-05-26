"""Página 4 — Produtos & Logística"""
import time

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import fmt_moeda, kpi_card, render_sidebar
from config import COLORS, PLOT_BASE, PLOT_AXIS, PLOT_CONFIG
from queries import (
    get_distribuicao_via,
    get_insights_produtos_logistica,
    get_ncm_agg,
    get_ranking_urfs,
)

t0 = time.perf_counter()
filtros = render_sidebar()
anos, tipos, paises, ufs = filtros["anos"], filtros["tipos"], filtros["paises"], filtros["ufs"]

with st.spinner("Atualizando..."):

    st.markdown("## 📦 Produtos & Logística")

    # ── Carrega dados consolidados (3 queries no total) ───────────────────────────
    df_ncm  = get_ncm_agg(anos, tipos, paises, ufs)
    df_via  = get_distribuicao_via(anos, tipos, paises, ufs, "AMBOS")
    df_urf  = get_ranking_urfs(anos, tipos, paises, ufs)

    # ── Deriva KPIs de produto sem queries extras ─────────────────────────────────
    if not df_ncm.empty:
        row_e        = df_ncm.nlargest(1, "exp").iloc[0]
        top_exp_nome  = row_e["nome"]
        top_exp_valor = float(row_e["exp"])
        total_exp_all = float(df_ncm["total_exp_all"].iloc[0]) or 1.0
        top_exp_pct   = top_exp_valor / total_exp_all * 100

        row_i        = df_ncm.nlargest(1, "imp").iloc[0]
        top_imp_nome  = row_i["nome"]
        top_imp_valor = float(row_i["imp"])
        total_imp_all = float(df_ncm["total_imp_all"].iloc[0]) or 1.0
        top_imp_pct   = top_imp_valor / total_imp_all * 100
    else:
        top_exp_nome = top_imp_nome = "—"
        top_exp_valor = top_imp_valor = top_exp_pct = top_imp_pct = 0.0

    # Deriva KPIs de modal e URF das queries já carregadas
    if not df_via.empty:
        row_m      = df_via.sort_values("total", ascending=False).iloc[0]
        modal_nome  = row_m["NO_VIA"]
        modal_valor = float(row_m["total"])
        modal_pct   = float(row_m["pct"])
    else:
        modal_nome, modal_valor, modal_pct = "—", 0.0, 0.0

    if not df_urf.empty:
        row_u     = df_urf.iloc[0]
        urf_nome  = row_u["nome"]
        urf_valor = float(row_u["total"])
        urf_pct   = float(row_u["pct"])
    else:
        urf_nome, urf_valor, urf_pct = "—", 0.0, 0.0

    # ── KPI cards ─────────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        n = top_exp_nome[:30] + "…" if len(top_exp_nome) > 30 else top_exp_nome
        kpi_card("Produto Mais Exportado", n, None, "📤", cor_valor=COLORS["exp"])
        st.caption(f"{fmt_moeda(top_exp_valor)} · {top_exp_pct:.1f}% do total EXP")
    with c2:
        n = top_imp_nome[:30] + "…" if len(top_imp_nome) > 30 else top_imp_nome
        kpi_card("Produto Mais Importado", n, None, "📥", cor_valor=COLORS["imp"])
        st.caption(f"{fmt_moeda(top_imp_valor)} · {top_imp_pct:.1f}% do total IMP")
    with c3:
        kpi_card("Principal Modal", modal_nome.title(), None, "🚢", cor_valor=COLORS["primary"])
        st.caption(f"{fmt_moeda(modal_valor)} · {modal_pct:.1f}% do volume total")
    with c4:
        n = urf_nome[:28] + "…" if len(urf_nome) > 28 else urf_nome
        kpi_card("Principal URF", n, None, "🏛️", cor_valor=COLORS["text"])
        st.caption(f"{fmt_moeda(urf_valor)} · {urf_pct:.1f}% do volume total")

    st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)

    # ── Top 15 produtos ───────────────────────────────────────────────────────────
    st.markdown("### 🏆 Top 15 Produtos (NCM)")

    tp_toggle = st.radio(
        "Ordenar por",
        ["Top EXP", "Top IMP", "Top Geral"],
        horizontal=True,
        key="tp_toggle",
        label_visibility="collapsed",
    )

    if not df_ncm.empty:
        sort_col = {"Top EXP": "exp", "Top IMP": "imp", "Top Geral": "total"}[tp_toggle]
        df_prod  = df_ncm.nlargest(15, sort_col).copy()

        base_prod = {**PLOT_BASE, "margin": dict(l=320, r=20, t=30, b=40)}
        fig_prod  = go.Figure(layout=base_prod)

        fig_prod.add_trace(go.Bar(
            y=df_prod["nome_trunc"].iloc[::-1],
            x=df_prod["exp"].iloc[::-1],
            name="EXP",
            orientation="h",
            marker_color=COLORS["exp"],
            hovertemplate="%{y}<br>EXP: %{x:$,.0f}<extra></extra>",
        ))
        fig_prod.add_trace(go.Bar(
            y=df_prod["nome_trunc"].iloc[::-1],
            x=df_prod["imp"].iloc[::-1],
            name="IMP",
            orientation="h",
            marker_color=COLORS["imp"],
            hovertemplate="%{y}<br>IMP: %{x:$,.0f}<extra></extra>",
        ))
        fig_prod.update_layout(
            barmode="group",
            height=480,
            xaxis=dict(**PLOT_AXIS, title="VL_FOB (US$)", tickprefix="US$ ", tickformat=",.2s"),
            yaxis=dict(**PLOT_AXIS),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_prod, use_container_width=True, config=PLOT_CONFIG)
    else:
        st.info("Nenhum produto encontrado para os filtros selecionados.")

    # ── Modal de transporte + Scatter valor vs peso ────────────────────────────────
    col_via, col_scatter = st.columns([1, 1.6])

    with col_via:
        st.markdown("### 🚚 Modal de Transporte")
        via_toggle = st.radio(
            "Tipo",
            ["Ambos", "Somente EXP", "Somente IMP"],
            horizontal=True,
            key="via_toggle",
            label_visibility="collapsed",
        )
        via_map = {"Ambos": "AMBOS", "Somente EXP": "EXP", "Somente IMP": "IMP"}
        df_via_sel = (
            df_via if via_toggle == "Ambos"
            else get_distribuicao_via(anos, tipos, paises, ufs, via_map[via_toggle])
        )

        if not df_via_sel.empty:
            VIA_CORES = [COLORS["primary"], COLORS["exp"], COLORS["imp"],
                         "#F4B942", "#9B59B6", "#E67E22", "#1ABC9C"]
            base_via = {**PLOT_BASE, "margin": dict(l=10, r=10, t=30, b=10)}
            fig_via  = go.Figure(layout=base_via)
            fig_via.add_trace(go.Pie(
                labels=df_via_sel["NO_VIA"],
                values=df_via_sel["total"],
                hole=0.45,
                marker=dict(colors=VIA_CORES[:len(df_via_sel)], line=dict(color=COLORS["bg"], width=2)),
                textinfo="percent+label",
                textfont=dict(size=10, color=COLORS["text"]),
                hovertemplate="%{label}<br>%{value:$,.2s}<br>%{percent}<extra></extra>",
            ))
            fig_via.update_layout(
                height=370,
                showlegend=False,
                annotations=[dict(
                    text="<b>Modal</b>", x=0.5, y=0.5,
                    font=dict(size=12, color=COLORS["text_sec"]), showarrow=False,
                )],
            )
            st.plotly_chart(fig_via, use_container_width=True, config=PLOT_CONFIG)
        else:
            st.info("Sem dados para o modal selecionado.")

    with col_scatter:
        st.markdown("### ⚖️ Valor vs Peso (top 100 NCMs)")

        if not df_ncm.empty:
            top100  = df_ncm.head(100)

            # Converte wide → long para o scatter
            rows_exp = top100[(top100["exp"] > 0) & (top100["kg_exp"] > 0)].copy()
            rows_exp = rows_exp.assign(
                TIPO_OPERACAO="EXP", vl_fob=rows_exp["exp"],
                kg=rows_exp["kg_exp"], n_ops=rows_exp["n_exp"],
            )
            rows_exp["usd_per_kg"] = rows_exp["vl_fob"] / rows_exp["kg"]

            rows_imp = top100[(top100["imp"] > 0) & (top100["kg_imp"] > 0)].copy()
            rows_imp = rows_imp.assign(
                TIPO_OPERACAO="IMP", vl_fob=rows_imp["imp"],
                kg=rows_imp["kg_imp"], n_ops=rows_imp["n_imp"],
            )
            rows_imp["usd_per_kg"] = rows_imp["vl_fob"] / rows_imp["kg"]

            df_scat = pd.concat([rows_exp, rows_imp], ignore_index=True)

            base_scat = {**PLOT_BASE, "margin": dict(l=60, r=20, t=30, b=50)}
            fig_scat  = go.Figure(layout=base_scat)

            for tipo_op, cor in [("EXP", COLORS["exp"]), ("IMP", COLORS["imp"])]:
                sub = df_scat[df_scat["TIPO_OPERACAO"] == tipo_op]
                if sub.empty:
                    continue
                fig_scat.add_trace(go.Scatter(
                    x=sub["kg"],
                    y=sub["vl_fob"],
                    mode="markers",
                    name=tipo_op,
                    marker=dict(color=cor, size=8, opacity=0.65,
                                line=dict(width=0.5, color=COLORS["bg"])),
                    text=sub["nome_trunc"],
                    customdata=sub[["usd_per_kg", "n_ops"]],
                    hovertemplate=(
                        "<b>%{text}</b><br>"
                        "Peso: %{x:,.0f} kg<br>"
                        "Valor: US$ %{y:,.0f}<br>"
                        "USD/kg: %{customdata[0]:,.2f}<br>"
                        "Operações: %{customdata[1]:,}<extra></extra>"
                    ),
                ))
            fig_scat.update_layout(
                height=370,
                xaxis=dict(**PLOT_AXIS, title="Peso Líquido (kg)", type="log", tickformat=",.0s"),
                yaxis=dict(**PLOT_AXIS, title="VL_FOB (US$)", type="log",
                           tickprefix="US$ ", tickformat=",.0s"),
                legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
            )
            st.plotly_chart(fig_scat, use_container_width=True, config=PLOT_CONFIG)
        else:
            st.info("Sem dados para o scatter.")

    # ── Ranking de URFs ───────────────────────────────────────────────────────────
    st.markdown("### 🏛️ Ranking de URFs (Unidades da Receita Federal)")

    if not df_urf.empty:
        ver_todas = st.checkbox(f"Ver todas as {len(df_urf)} URFs", value=False)
        df_show   = df_urf if ver_todas else df_urf.head(20)

        df_display = df_show[["nome", "exp", "imp", "total", "pct"]].copy()
        df_display.columns = ["URF", "EXP (US$)", "IMP (US$)", "Total (US$)", "% Total"]

        def hl_total(val):
            return f"color: {COLORS['exp']}; font-weight: 600" if isinstance(val, (int, float)) and val > 0 else ""

        styled = (
            df_display.style
            .format({
                "EXP (US$)":   "${:,.0f}",
                "IMP (US$)":   "${:,.0f}",
                "Total (US$)": "${:,.0f}",
                "% Total":     "{:.2f}%",
            })
            .map(hl_total, subset=["Total (US$)"])
        )
        n_rows = min(len(df_show), 20)
        st.dataframe(
            styled,
            hide_index=True,
            use_container_width=True,
            height=min(40 * n_rows + 38, 680),
            column_config={
                "URF":         st.column_config.TextColumn("URF", width="large"),
                "EXP (US$)":   st.column_config.TextColumn("EXP (US$)"),
                "IMP (US$)":   st.column_config.TextColumn("IMP (US$)"),
                "Total (US$)": st.column_config.TextColumn("Total (US$)"),
                "% Total":     st.column_config.TextColumn("% Total"),
            },
        )
    else:
        st.info("Sem dados de URF para os filtros selecionados.")

    # ── Insights ──────────────────────────────────────────────────────────────────
    st.markdown("### 💡 Insights")
    ins = get_insights_produtos_logistica(anos, tipos, paises, ufs)

    _ins = (
        f"<div style='background:{COLORS['surface']};border:1px solid {COLORS['border']};"
        f"border-radius:10px;padding:16px 18px;font-size:0.85rem;"
        f"color:{COLORS['text_sec']};min-height:90px'>{{content}}</div>"
    )

    ic1, ic2, ic3, ic4 = st.columns(4)
    with ic1:
        st.markdown(_ins.format(content=(
            f"<b style='color:{COLORS['text']}'>Concentração de pauta</b><br>"
            f"Os <b>10 principais produtos</b> respondem por "
            f"<b style='color:{COLORS['exp']}'>{ins['pct_top10_exp']:.1f}%</b> do total exportado."
        )), unsafe_allow_html=True)
    with ic2:
        st.markdown(_ins.format(content=(
            f"<b style='color:{COLORS['text']}'>Dominância marítima</b><br>"
            f"<b style='color:{COLORS['primary']}'>{ins['modal_nome'].title()}</b> responde por "
            f"<b style='color:{COLORS['primary']}'>{ins['modal_pct']:.1f}%</b> de todo o volume transacionado."
        )), unsafe_allow_html=True)
    with ic3:
        st.markdown(_ins.format(content=(
            f"<b style='color:{COLORS['text']}'>Maior valor agregado</b><br>"
            f"<b style='color:{COLORS['exp']}'>{ins['prod_vk_nome']}</b> lidera em valor por kg com "
            f"<b>US$ {ins['prod_usd_kg']:,.0f}/kg</b>."
        )), unsafe_allow_html=True)
    with ic4:
        st.markdown(_ins.format(content=(
            f"<b style='color:{COLORS['text']}'>Maior URF</b><br>"
            f"<b style='color:{COLORS['primary']}'>{ins['urf_nome']}</b> concentra "
            f"<b style='color:{COLORS['primary']}'>{ins['urf_pct']:.1f}%</b> do fluxo total no período."
        )), unsafe_allow_html=True)

    # ── Rodapé global ─────────────────────────────────────────────────────────────
    elapsed = time.perf_counter() - t0
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
