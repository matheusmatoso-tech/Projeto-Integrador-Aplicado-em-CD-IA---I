"""Página 3 — Análise Geográfica"""

import time
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config     import COLORS, PLOT_BASE, PLOT_AXIS, PLOT_CONFIG
from components import render_sidebar, fmt_moeda, fmt_num, kpi_card
from queries    import (
    get_top_parceiro,
    get_uf_lider,
    get_mapa_mundi,
    get_distribuicao_regiao,
    get_ranking_ufs,
    get_insights_geograficos,
)

REGIAO_CORES = {
    "Sudeste":       "#4F8BFF",
    "Sul":           "#00D9A3",
    "Centro-Oeste":  "#FFB84D",
    "Nordeste":      "#C084FC",
    "Norte":         "#38BDF8",
    "Outros":        "#4A5568",
}

# ── Filtros ────────────────────────────────────────────────────────────────────
t_inicio = time.perf_counter()
filtros  = render_sidebar()
anos, tipos, paises, ufs = filtros["anos"], filtros["tipos"], filtros["paises"], filtros["ufs"]

with st.spinner("Atualizando..."):

    # ── Cabeçalho ──────────────────────────────────────────────────────────────────
    c_sec = COLORS["text_sec"]
    st.markdown("## 🗺️ Análise Geográfica")
    st.markdown(
        f"<p style='color:{c_sec};font-size:0.92rem;margin-top:-8px;margin-bottom:18px'>"
        "Quais são os principais parceiros comerciais do Brasil? E quais estados brasileiros "
        "lideram o comércio exterior? Esta página <b>mapeia geograficamente</b> os fluxos de "
        "exportação e importação."
        "</p>",
        unsafe_allow_html=True,
    )

    # ── KPIs Geográficos ───────────────────────────────────────────────────────────
    parceiro_exp = get_top_parceiro(anos, tipos, paises, ufs, "EXP") if "EXP" in tipos else {"nome": "—", "valor": 0.0, "pct": 0.0}
    parceiro_imp = get_top_parceiro(anos, tipos, paises, ufs, "IMP") if "IMP" in tipos else {"nome": "—", "valor": 0.0, "pct": 0.0}
    uf_lider     = get_uf_lider(anos, tipos, paises, ufs)

    c1, c2, c3 = st.columns(3, gap="medium")

    with c1:
        kpi_card("Principal Parceiro (EXP)", parceiro_exp["nome"],
                 None, "🌎", cor_valor=COLORS["exp"])
        st.caption(
            f"{fmt_moeda(parceiro_exp['valor'])} · "
            f"{parceiro_exp['pct']:.1f}% das exportações"
        )

    with c2:
        kpi_card("Principal Parceiro (IMP)", parceiro_imp["nome"],
                 None, "🚢", cor_valor=COLORS["imp"])
        st.caption(
            f"{fmt_moeda(parceiro_imp['valor'])} · "
            f"{parceiro_imp['pct']:.1f}% das importações"
        )

    with c3:
        kpi_card("UF Líder em Comércio Ext.", uf_lider["sigla"],
                 None, "📍", cor_valor=COLORS["primary"])
        st.caption(
            f"{uf_lider['nome']} · {uf_lider['regiao']} · "
            f"{fmt_moeda(uf_lider['total'])}"
        )

    st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)

    # ── Mapa-Múndi ─────────────────────────────────────────────────────────────────
    c_t = COLORS["text"]
    st.markdown(
        f"<p style='color:{c_t};font-size:0.95rem;font-weight:600;margin-bottom:6px'>"
        "Distribuição Global de Parceiros Comerciais</p>",
        unsafe_allow_html=True,
    )

    # Toggle EXP / IMP / BALANÇA
    opcoes_mapa = []
    if "EXP" in tipos:
        opcoes_mapa.append("EXP")
    if "IMP" in tipos:
        opcoes_mapa.append("IMP")
    if "EXP" in tipos and "IMP" in tipos:
        opcoes_mapa.append("BALANÇA")

    metrica_mapa = st.radio(
        "Métrica mapa", opcoes_mapa,
        horizontal=True, key="mapa_metrica",
        label_visibility="collapsed",
    ) if len(opcoes_mapa) > 1 else (opcoes_mapa[0] if opcoes_mapa else "EXP")

    df_mapa = get_mapa_mundi(anos, tipos, paises, ufs)

    if not df_mapa.empty:
        if metrica_mapa == "EXP":
            df_mapa["valor"] = df_mapa["exp"]
            colorscale_mapa  = [[0, COLORS["surface"]], [1, COLORS["exp"]]]
            label_mapa       = "Exportação"
            zmin_mapa = zmax_mapa = None
        elif metrica_mapa == "IMP":
            df_mapa["valor"] = df_mapa["imp"]
            colorscale_mapa  = [[0, COLORS["surface"]], [1, COLORS["imp"]]]
            label_mapa       = "Importação"
            zmin_mapa = zmax_mapa = None
        else:
            df_mapa["valor"] = df_mapa["saldo"]
            colorscale_mapa  = [
                [0, COLORS["imp"]],
                [0.5, COLORS["surface"]],
                [1, COLORS["exp"]],
            ]
            label_mapa = "Saldo (EXP−IMP)"
            abs_max = max(
                abs(float(df_mapa["valor"].min())),
                abs(float(df_mapa["valor"].max()))
            ) or 1.0
            zmin_mapa, zmax_mapa = -abs_max, abs_max

        total_mapa = df_mapa["valor"].abs().sum() or 1
        df_mapa["pct"]  = df_mapa["valor"].abs() / total_mapa * 100
        df_mapa["rank"] = df_mapa["valor"].abs().rank(ascending=False, method="min").astype(int)

        mapa_kwargs = dict(
            locations=df_mapa["iso3"],
            z=df_mapa["valor"],
            text=df_mapa["nome"],
            locationmode="ISO-3",
            colorscale=colorscale_mapa,
            customdata=df_mapa[["pct", "rank"]].values,
            hovertemplate=(
                "<b>%{text}</b><br>"
                "US$ %{z:.3s}<br>"
                "%{customdata[0]:.2f}% do total<br>"
                "Ranking: #%{customdata[1]}"
                "<extra></extra>"
            ),
            marker=dict(line=dict(color=COLORS["border"], width=0.4)),
            colorbar=dict(
                title=dict(text=label_mapa, font=dict(color=COLORS["text_sec"], size=11)),
                tickformat="$.2s",
                tickfont=dict(color=COLORS["text_sec"], size=10),
                outlinewidth=0,
            ),
            showscale=True,
        )
        if zmin_mapa is not None:
            mapa_kwargs["zmin"] = zmin_mapa
            mapa_kwargs["zmax"] = zmax_mapa

        fig_mapa = go.Figure(go.Choropleth(**mapa_kwargs))

        base_mapa = {**PLOT_BASE, "margin": dict(l=0, r=0, t=20, b=0)}
        fig_mapa.update_layout(
            **base_mapa,
            height=520,
            geo=dict(
                bgcolor=COLORS["bg"],
                showframe=False,
                showcoastlines=False,
                showland=True, landcolor=COLORS["surface"],
                showocean=True, oceancolor=COLORS["bg"],
                showcountries=True, countrycolor=COLORS["border"],
                showlakes=False,
                projection=dict(type="natural earth"),
            ),
        )
        st.plotly_chart(fig_mapa, use_container_width=True, config=PLOT_CONFIG)
    else:
        st.info("Sem dados geográficos para o período selecionado.")

    st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)

    # ── Top 10 Países + Distribuição por Região ────────────────────────────────────
    col_l, col_r = st.columns(2, gap="large")

    with col_l:
        st.markdown(
            f"<p style='color:{c_t};font-size:0.95rem;font-weight:600;margin-bottom:4px'>"
            "Top 10 Países Parceiros</p>",
            unsafe_allow_html=True,
        )

        vis_top = st.radio(
            "Visualização", ["Ambos", "Somente EXP", "Somente IMP"],
            horizontal=True, key="top_vis",
            label_visibility="collapsed",
        ) if "EXP" in tipos and "IMP" in tipos else (
            "Somente EXP" if "EXP" in tipos else "Somente IMP"
        )

        if not df_mapa.empty:
            if vis_top == "Somente EXP":
                df_top = df_mapa.nlargest(10, "exp").sort_values("exp", ascending=True)
            elif vis_top == "Somente IMP":
                df_top = df_mapa.nlargest(10, "imp").sort_values("imp", ascending=True)
            else:
                df_mapa["_total"] = df_mapa["exp"] + df_mapa["imp"]
                df_top = df_mapa.nlargest(10, "_total").sort_values("_total", ascending=True)

            fig_top = go.Figure()

            if vis_top in ("Ambos", "Somente EXP") and "EXP" in tipos:
                fig_top.add_trace(go.Bar(
                    x=df_top["exp"], y=df_top["nome"],
                    name="EXP",
                    orientation="h",
                    marker=dict(color=COLORS["exp"], line_width=0),
                    text=[fmt_moeda(v) for v in df_top["exp"]],
                    textposition="outside",
                    textfont=dict(size=9, color=COLORS["text_sec"]),
                    hovertemplate="<b>%{y}</b><br>EXP: %{x:$.3s}<extra></extra>",
                ))

            if vis_top in ("Ambos", "Somente IMP") and "IMP" in tipos:
                fig_top.add_trace(go.Bar(
                    x=df_top["imp"], y=df_top["nome"],
                    name="IMP",
                    orientation="h",
                    marker=dict(color=COLORS["imp"], line_width=0),
                    text=[fmt_moeda(v) for v in df_top["imp"]],
                    textposition="outside",
                    textfont=dict(size=9, color=COLORS["text_sec"]),
                    hovertemplate="<b>%{y}</b><br>IMP: %{x:$.3s}<extra></extra>",
                ))

            base_top = {**PLOT_BASE, "margin": dict(l=10, r=100, t=20, b=40)}
            fig_top.update_layout(
                **base_top,
                barmode="group",
                height=400,
                xaxis=dict(
                    **PLOT_AXIS, tickformat="$.2s",
                    title=dict(text="US$ FOB", font=dict(color=COLORS["text_sec"])),
                ),
                yaxis=dict(**PLOT_AXIS),
            )
            st.plotly_chart(fig_top, use_container_width=True, config=PLOT_CONFIG)

    with col_r:
        st.markdown(
            f"<p style='color:{c_t};font-size:0.95rem;font-weight:600;margin-bottom:4px'>"
            "Distribuição por Região do Brasil</p>",
            unsafe_allow_html=True,
        )
        df_regiao = get_distribuicao_regiao(anos, tipos, paises, ufs)

        if not df_regiao.empty:
            total_regiao = float(df_regiao["total"].sum())
            cores_lista  = [REGIAO_CORES.get(r, "#4A5568") for r in df_regiao["regiao"]]

            fig_pie = go.Figure(go.Pie(
                labels=df_regiao["regiao"],
                values=df_regiao["total"],
                hole=0.42,
                marker=dict(colors=cores_lista, line=dict(color=COLORS["border"], width=1)),
                textinfo="label+percent",
                textfont=dict(size=11, color=COLORS["text"]),
                hovertemplate=(
                    "<b>%{label}</b><br>"
                    "US$ %{value:.3s}<br>"
                    "%{percent}"
                    "<extra></extra>"
                ),
            ))

            base_pie = {**PLOT_BASE, "margin": dict(l=0, r=0, t=10, b=10)}
            fig_pie.update_layout(
                **base_pie,
                height=400,
                showlegend=False,
                annotations=[dict(
                    text=f"<b>{fmt_moeda(total_regiao)}</b>",
                    x=0.5, y=0.5,
                    font=dict(size=13, color=COLORS["text"], family="system-ui"),
                    showarrow=False,
                    align="center",
                )],
            )
            st.plotly_chart(fig_pie, use_container_width=True, config=PLOT_CONFIG)

    st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)

    # ── Ranking de UFs ─────────────────────────────────────────────────────────────
    st.markdown(
        f"<p style='color:{c_t};font-size:0.95rem;font-weight:600;margin-bottom:6px'>"
        "Ranking de Estados (UF)</p>",
        unsafe_allow_html=True,
    )

    mostrar_todos = st.checkbox("Ver todas as UFs (incluindo códigos especiais)", key="uf_todas")
    df_uf = get_ranking_ufs(anos, tipos, paises, ufs)

    if not df_uf.empty:
        df_tabela = df_uf if mostrar_todos else df_uf.head(15)
        n_exib    = len(df_tabela)

        df_display = pd.DataFrame({
            "#":            range(1, n_exib + 1),
            "UF":           df_tabela["SG_UF"].values,
            "Nome":         df_tabela["NO_UF"].values,
            "Região":       df_tabela["NO_REGIAO"].values,
            "EXP (bi)":     (df_tabela["exp"] / 1e9).round(2).values,
            "IMP (bi)":     (df_tabela["imp"] / 1e9).round(2).values,
            "Saldo (bi)":   (df_tabela["saldo"] / 1e9).round(2).values,
            "% Total":      df_tabela["pct"].round(2).values,
        })

        def hl_saldo(v):
            if isinstance(v, float) and v > 0:
                return f"color: {COLORS['positive']}"
            if isinstance(v, float) and v < 0:
                return f"color: {COLORS['negative']}"
            return ""

        styled = df_display.style.map(hl_saldo, subset=["Saldo (bi)"])
        st.dataframe(
            styled,
            hide_index=True,
            use_container_width=True,
            height=min(35 * n_exib + 38, 560),
            column_config={
                "#":          st.column_config.NumberColumn(width="small"),
                "UF":         st.column_config.TextColumn(width="small"),
                "Nome":       st.column_config.TextColumn(width="medium"),
                "Região":     st.column_config.TextColumn(width="medium"),
                "EXP (bi)":   st.column_config.NumberColumn("EXP (US$ bi)", format="%.2f", width="small"),
                "IMP (bi)":   st.column_config.NumberColumn("IMP (US$ bi)", format="%.2f", width="small"),
                "Saldo (bi)": st.column_config.NumberColumn("Saldo (US$ bi)", format="%.2f", width="small"),
                "% Total":    st.column_config.NumberColumn("% Total", format="%.2f%%", width="small"),
            },
        )

    # ── Rodapé — Insights Geográficos ─────────────────────────────────────────────
    st.divider()
    ins = get_insights_geograficos(anos, tipos, paises, ufs)

    c_sec = COLORS["text_sec"]
    c_txt = COLORS["text"]
    c_exp = COLORS["exp"]
    c_imp = COLORS["imp"]
    c_srf = COLORS["surface"]
    c_brd = COLORS["border"]

    i1, i2, i3 = st.columns(3, gap="medium")

    with i1:
        st.markdown(
            f"<div style='background:{c_srf};border:1px solid {c_brd};"
            f"border-radius:10px;padding:14px 16px'>"
            f"<span style='font-size:1.1rem'>🌎</span> "
            f"<span style='color:{c_sec};font-size:0.85rem'>O Brasil tem relação comercial com "
            f"<b style='color:{c_txt}'>{fmt_num(ins['n_paises'])}</b> países no período. "
            f"Os top 5 parceiros concentram "
            f"<b style='color:{c_exp}'>{ins['pct_top5']:.1f}%</b> do volume total.</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with i2:
        st.markdown(
            f"<div style='background:{c_srf};border:1px solid {c_brd};"
            f"border-radius:10px;padding:14px 16px'>"
            f"<span style='font-size:1.1rem'>📍</span> "
            f"<span style='color:{c_sec};font-size:0.85rem'>A região "
            f"<b style='color:{c_txt}'>{ins['regiao_lider']}</b> lidera o comércio exterior "
            f"brasileiro, respondendo por "
            f"<b style='color:{c_exp}'>{ins['pct_regiao']:.1f}%</b> do volume nacional.</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with i3:
        st.markdown(
            f"<div style='background:{c_srf};border:1px solid {c_brd};"
            f"border-radius:10px;padding:14px 16px'>"
            f"<span style='font-size:1.1rem'>⚖️</span> "
            f"<span style='color:{c_sec};font-size:0.85rem'>"
            f"<b style='color:{c_exp}'>{ins['n_superavit']}</b> países representam superávit "
            f"(exportamos mais) e "
            f"<b style='color:{c_imp}'>{ins['n_deficit']}</b> países representam déficit "
            f"para o Brasil no período.</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

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
