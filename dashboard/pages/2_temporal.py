"""Página 2 — Análise Temporal"""

import time
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config     import COLORS, PLOT_BASE, PLOT_AXIS, PLOT_CONFIG
from components import render_sidebar, fmt_moeda, kpi_card
from queries    import (
    get_kpis_temporais,
    get_serie_mensal,
    get_yoy_anual,
    get_ytd_por_ano,
    get_heatmap_sazonalidade,
    get_insights_temporais,
)

MESES_PT = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr",
    5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago",
    9: "Set", 10: "Out", 11: "Nov", 12: "Dez",
}

# ── Filtros ────────────────────────────────────────────────────────────────────
t_inicio = time.perf_counter()
filtros  = render_sidebar()
anos, tipos, paises, ufs = filtros["anos"], filtros["tipos"], filtros["paises"], filtros["ufs"]

with st.spinner("Atualizando..."):

    # ── Cabeçalho ──────────────────────────────────────────────────────────────────
    c_sec = COLORS["text_sec"]
    st.markdown("## 📅 Análise Temporal")
    st.markdown(
        f"<p style='color:{c_sec};font-size:0.92rem;margin-top:-8px;margin-bottom:18px'>"
        "Como o comércio exterior brasileiro evoluiu ao longo do tempo? "
        "Esta página explora <b>tendências</b>, <b>sazonalidades</b> e "
        "<b>comparações período a período</b>."
        "</p>",
        unsafe_allow_html=True,
    )

    # ── KPIs Temporais ─────────────────────────────────────────────────────────────
    kpis_t = get_kpis_temporais(anos, tipos, paises, ufs)

    c1, c2, c3 = st.columns(3, gap="medium")

    with c1:
        if kpis_t["peak_ano"] is not None:
            mes_str = f"{MESES_PT[kpis_t['peak_mes']]}/{kpis_t['peak_ano']}"
            kpi_card("Maior Mês do Período", fmt_moeda(kpis_t["peak_val"]),
                     None, "🏆", cor_valor=COLORS["primary"])
            st.caption(f"📅 Referência: {mes_str}")
        else:
            kpi_card("Maior Mês do Período", "—", None, "🏆")

    with c2:
        avg_yoy = kpis_t["avg_yoy"]
        if avg_yoy is not None:
            icone_yoy = "📈" if avg_yoy >= 0 else "📉"
            cor_yoy   = COLORS["positive"] if avg_yoy >= 0 else COLORS["negative"]
            kpi_card("Crescimento YoY Médio", f"{avg_yoy:+.1f}%",
                     None, icone_yoy, cor_valor=cor_yoy)
            st.caption(
                "YoY: variação % em relação ao mesmo mês do ano anterior",
                help="YoY (Year-over-Year): compara o valor de um período com o mesmo período do ano anterior.",
            )
        else:
            kpi_card("Crescimento YoY Médio", "—", None, "📈")

    with c3:
        bt = kpis_t["best_trim"]
        if bt is not None:
            kpi_card("Melhor Trimestre", f"T{bt}",
                     None, "📅", cor_valor=COLORS["exp"])
            st.caption("Trimestre com maior média histórica de VL_FOB")
        else:
            kpi_card("Melhor Trimestre", "—", None, "📅")

    st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)

    # ── Série Temporal Mensal ──────────────────────────────────────────────────────
    st.markdown("### 📈 Série Temporal Mensal")
    st.caption(
        "Linhas sólidas = VL_FOB mensal · Linhas pontilhadas = Média Móvel 3 meses (MM3)",
        help="MM3 (Média Móvel de 3 meses): suaviza a série, reduzindo ruído sazonal de curto prazo.",
    )
    df_serie = get_serie_mensal(anos, tipos, paises, ufs)

    if not df_serie.empty:
        fig_serie = go.Figure()

        if "EXP" in tipos:
            df_serie["yoy_exp_fmt"] = df_serie["yoy_exp"].apply(
                lambda x: f"{x:+.1f}%" if pd.notna(x) else "N/D"
            )
            cd_exp = df_serie[["yoy_exp_fmt", "mm3_exp"]].values
            fig_serie.add_trace(go.Scatter(
                x=df_serie["data"],
                y=df_serie["exp"],
                name="Exportação",
                mode="lines",
                line=dict(color=COLORS["exp"], width=2),
                customdata=cd_exp,
                hovertemplate=(
                    "<b>%{x|%b %Y}</b><br>"
                    "EXP: %{y:$.3s}<br>"
                    "YoY: %{customdata[0]}<br>"
                    "MM3: %{customdata[1]:$.3s}"
                    "<extra></extra>"
                ),
            ))
            fig_serie.add_trace(go.Scatter(
                x=df_serie["data"],
                y=df_serie["mm3_exp"],
                name="MM3 EXP",
                mode="lines",
                line=dict(color=COLORS["exp"], width=1.5, dash="dot"),
                opacity=0.45,
                hoverinfo="skip",
            ))

        if "IMP" in tipos:
            df_serie["yoy_imp_fmt"] = df_serie["yoy_imp"].apply(
                lambda x: f"{x:+.1f}%" if pd.notna(x) else "N/D"
            )
            cd_imp = df_serie[["yoy_imp_fmt", "mm3_imp"]].values
            fig_serie.add_trace(go.Scatter(
                x=df_serie["data"],
                y=df_serie["imp"],
                name="Importação",
                mode="lines",
                line=dict(color=COLORS["imp"], width=2),
                customdata=cd_imp,
                hovertemplate=(
                    "<b>%{x|%b %Y}</b><br>"
                    "IMP: %{y:$.3s}<br>"
                    "YoY: %{customdata[0]}<br>"
                    "MM3: %{customdata[1]:$.3s}"
                    "<extra></extra>"
                ),
            ))
            fig_serie.add_trace(go.Scatter(
                x=df_serie["data"],
                y=df_serie["mm3_imp"],
                name="MM3 IMP",
                mode="lines",
                line=dict(color=COLORS["imp"], width=1.5, dash="dot"),
                opacity=0.45,
                hoverinfo="skip",
            ))

        fig_serie.update_layout(
            **PLOT_BASE,
            title=dict(
                text="<b>Série Temporal Mensal</b> — VL_FOB por Mês",
                font=dict(size=14, color=COLORS["text"]),
                x=0, xanchor="left",
            ),
            height=420,
            xaxis=dict(
                **PLOT_AXIS,
                type="date",
                title=dict(text="Mês", font=dict(color=COLORS["text_sec"])),
                rangeselector=dict(
                    bgcolor=COLORS["surface"],
                    activecolor=COLORS["primary"],
                    font=dict(color=COLORS["text_sec"], size=11),
                    buttons=[
                        dict(count=1, label="1A", step="year", stepmode="backward"),
                        dict(count=3, label="3A", step="year", stepmode="backward"),
                        dict(count=5, label="5A", step="year", stepmode="backward"),
                        dict(step="all", label="Tudo"),
                    ],
                ),
                rangeslider=dict(visible=True, thickness=0.05, bgcolor=COLORS["surface"]),
            ),
            yaxis=dict(
                **PLOT_AXIS,
                tickformat="$.2s",
                title=dict(text="US$ FOB", font=dict(color=COLORS["text_sec"])),
            ),
            hovermode="x unified",
        )
        st.plotly_chart(fig_serie, use_container_width=True, config=PLOT_CONFIG)
    else:
        st.info("Sem dados para o período selecionado.")

    st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)

    # ── YoY Anual + YTD ───────────────────────────────────────────────────────────
    col_l, col_r = st.columns(2, gap="large")

    with col_l:
        c_t = COLORS["text"]
        st.markdown(
            f"<p style='color:{c_t};font-size:0.95rem;font-weight:600;margin-bottom:4px'>"
            "Crescimento YoY Anual</p>",
            unsafe_allow_html=True,
        )
        df_yoy = get_yoy_anual(anos, tipos, paises, ufs)

        if not df_yoy.empty:
            fig_yoy = go.Figure()
            fig_yoy.add_hline(y=0, line_color=COLORS["border"], line_width=1)

            if "EXP" in tipos:
                df_e = df_yoy.dropna(subset=["yoy_exp"])
                fig_yoy.add_trace(go.Bar(
                    x=df_e["CO_ANO"],
                    y=df_e["yoy_exp"],
                    name="EXP",
                    marker_color=[
                        COLORS["positive"] if v >= 0 else COLORS["negative"]
                        for v in df_e["yoy_exp"]
                    ],
                    marker_line_width=0,
                    hovertemplate="<b>%{x}</b><br>YoY EXP: %{y:+.1f}%<extra></extra>",
                ))

            if "IMP" in tipos:
                df_i = df_yoy.dropna(subset=["yoy_imp"])
                fig_yoy.add_trace(go.Bar(
                    x=df_i["CO_ANO"],
                    y=df_i["yoy_imp"],
                    name="IMP",
                    marker_color=[
                        COLORS["positive"] if v >= 0 else COLORS["negative"]
                        for v in df_i["yoy_imp"]
                    ],
                    marker_line_width=0,
                    opacity=0.72,
                    hovertemplate="<b>%{x}</b><br>YoY IMP: %{y:+.1f}%<extra></extra>",
                ))

            fig_yoy.update_layout(
                **PLOT_BASE,
                barmode="group", bargap=0.22, bargroupgap=0.05,
                height=350,
                xaxis=dict(
                    **PLOT_AXIS, dtick=1, tickformat="d",
                    title=dict(text="Ano", font=dict(color=COLORS["text_sec"])),
                ),
                yaxis=dict(
                    **PLOT_AXIS, ticksuffix="%",
                    title=dict(text="Variação %", font=dict(color=COLORS["text_sec"])),
                ),
            )
            st.plotly_chart(fig_yoy, use_container_width=True, config=PLOT_CONFIG)

    with col_r:
        c_t = COLORS["text"]
        st.markdown(
            f"<p style='color:{c_t};font-size:0.95rem;font-weight:600;margin-bottom:4px'>"
            "YTD Acumulado por Ano</p>",
            unsafe_allow_html=True,
        )

        if "EXP" in tipos and "IMP" in tipos:
            tipo_ytd = st.radio(
                "Tipo YTD", ["EXP", "IMP"],
                horizontal=True, key="ytd_tipo",
                label_visibility="collapsed",
            )
        else:
            tipo_ytd = "EXP" if "EXP" in tipos else "IMP"

        df_ytd = get_ytd_por_ano(anos, paises, ufs, tipo_ytd)

        if not df_ytd.empty:
            fig_ytd    = go.Figure()
            anos_list  = sorted(df_ytd.columns.tolist())
            n          = len(anos_list)
            cor_ytd    = COLORS["exp"] if tipo_ytd == "EXP" else COLORS["imp"]
            meses_abbr = [MESES_PT.get(m, str(m)) for m in range(1, 13)]

            for i, ano in enumerate(anos_list):
                opac = 0.25 + 0.75 * ((i + 1) / n)
                col_data = df_ytd[ano].dropna()
                fig_ytd.add_trace(go.Scatter(
                    x=col_data.index,
                    y=col_data.values,
                    name=str(ano),
                    mode="lines",
                    line=dict(color=cor_ytd, width=1.8),
                    opacity=opac,
                    hovertemplate=f"<b>{ano}</b> — Mês %{{x}}: %{{y:$.3s}}<extra></extra>",
                ))

            fig_ytd.update_layout(
                **PLOT_BASE,
                height=350,
                xaxis=dict(
                    **PLOT_AXIS,
                    tickvals=list(range(1, 13)),
                    ticktext=meses_abbr,
                    title=dict(text="Mês", font=dict(color=COLORS["text_sec"])),
                ),
                yaxis=dict(
                    **PLOT_AXIS,
                    tickformat="$.2s",
                    title=dict(
                        text=f"US$ FOB Acumulado ({tipo_ytd})",
                        font=dict(color=COLORS["text_sec"]),
                    ),
                ),
            )
            st.plotly_chart(fig_ytd, use_container_width=True, config=PLOT_CONFIG)

    st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)

    # ── Heatmap de Sazonalidade ────────────────────────────────────────────────────
    c_t = COLORS["text"]
    st.markdown(
        f"<p style='color:{c_t};font-size:0.95rem;font-weight:600;margin-bottom:4px'>"
        "Heatmap de Sazonalidade</p>",
        unsafe_allow_html=True,
    )

    opcoes_heat: list[str] = []
    if "EXP" in tipos:
        opcoes_heat.append("EXP")
    if "IMP" in tipos:
        opcoes_heat.append("IMP")
    if "EXP" in tipos and "IMP" in tipos:
        opcoes_heat.append("SALDO")

    if len(opcoes_heat) > 1:
        metrica_lbl = st.radio(
            "Métrica heatmap", opcoes_heat,
            horizontal=True, key="heat_metrica",
            label_visibility="collapsed",
        )
    else:
        metrica_lbl = opcoes_heat[0] if opcoes_heat else "EXP"

    metrica_heat = metrica_lbl.lower()
    df_heat      = get_heatmap_sazonalidade(anos, tipos, paises, ufs, metrica_heat)

    if not df_heat.empty:
        meses_abbr_heat = [MESES_PT.get(m, str(m)) for m in df_heat.columns.tolist()]
        anos_heat       = [str(a) for a in df_heat.index.tolist()]

        if metrica_heat == "exp":
            colorscale = [[0, COLORS["bg"]], [1, COLORS["exp"]]]
            zmin_h = zmax_h = None
        elif metrica_heat == "imp":
            colorscale = [[0, COLORS["bg"]], [1, COLORS["imp"]]]
            zmin_h = zmax_h = None
        else:
            colorscale = [
                [0, COLORS["negative"]],
                [0.5, COLORS["surface"]],
                [1, COLORS["positive"]],
            ]
            flat    = df_heat.values.flatten()
            valid   = flat[~pd.isna(flat)]
            abs_max = max(abs(float(valid.min())), abs(float(valid.max()))) if len(valid) > 0 else 1.0
            zmin_h, zmax_h = -abs_max, abs_max

        heat_kwargs = dict(
            z=df_heat.values,
            x=meses_abbr_heat,
            y=anos_heat,
            colorscale=colorscale,
            texttemplate="%{z:$.2s}",
            textfont=dict(size=8, color=COLORS["text"]),
            hovertemplate="<b>%{y} — %{x}</b><br>%{z:.3s}<extra></extra>",
            showscale=True,
            colorbar=dict(
                tickformat="$.2s",
                tickfont=dict(color=COLORS["text_sec"], size=10),
                outlinewidth=0,
            ),
        )
        if zmin_h is not None:
            heat_kwargs["zmin"] = zmin_h
            heat_kwargs["zmax"] = zmax_h

        fig_heat = go.Figure(go.Heatmap(**heat_kwargs))
        base_heat = {**PLOT_BASE, "margin": dict(l=60, r=90, t=30, b=40)}
        fig_heat.update_layout(
            **base_heat,
            height=330,
            xaxis=dict(**PLOT_AXIS, title=dict(text="Mês", font=dict(color=COLORS["text_sec"]))),
            yaxis=dict(**PLOT_AXIS, title=dict(text="Ano", font=dict(color=COLORS["text_sec"]))),
        )
        st.plotly_chart(fig_heat, use_container_width=True, config=PLOT_CONFIG)

    # ── Rodapé — Insights ─────────────────────────────────────────────────────────
    st.divider()
    ins = get_insights_temporais(anos, tipos, paises, ufs)

    c_sec = COLORS["text_sec"]
    c_txt = COLORS["text"]
    c_neg = COLORS["negative"]
    c_acc = COLORS["exp"] if ins["tipo_p"] == "EXP" else COLORS["imp"]
    c_srf = COLORS["surface"]
    c_brd = COLORS["border"]
    tipo_label = "exportação" if ins["tipo_p"] == "EXP" else "importação"

    i1, i2, i3 = st.columns(3, gap="medium")

    with i1:
        if ins["melhor_ano"] is not None:
            st.markdown(
                f"<div style='background:{c_srf};border:1px solid {c_brd};"
                f"border-radius:10px;padding:14px 16px'>"
                f"<span style='font-size:1.1rem'>📌</span> "
                f"<span style='color:{c_sec};font-size:0.85rem'>O melhor ano para {tipo_label} foi "
                f"<b style='color:{c_txt}'>{ins['melhor_ano']}</b>, totalizando "
                f"<b style='color:{c_acc}'>{fmt_moeda(ins['melhor_ano_val'])}</b>.</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

    with i2:
        if ins["maior_queda_ano"] is not None:
            pct_q = f"{ins['maior_queda_pct']:.1f}%"
            st.markdown(
                f"<div style='background:{c_srf};border:1px solid {c_brd};"
                f"border-radius:10px;padding:14px 16px'>"
                f"<span style='font-size:1.1rem'>📉</span> "
                f"<span style='color:{c_sec};font-size:0.85rem'>A maior queda YoY foi em "
                f"<b style='color:{c_txt}'>{ins['maior_queda_ano']}</b>, com "
                f"<b style='color:{c_neg}'>{pct_q}</b>.</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

    with i3:
        if ins["mes_sazonal"] is not None:
            mes_nome = MESES_PT.get(ins["mes_sazonal"], str(ins["mes_sazonal"]))
            pct_s    = f"{ins['mes_sazonal_pct']:.1f}%"
            st.markdown(
                f"<div style='background:{c_srf};border:1px solid {c_brd};"
                f"border-radius:10px;padding:14px 16px'>"
                f"<span style='font-size:1.1rem'>🗓️</span> "
                f"<span style='color:{c_sec};font-size:0.85rem'>O mês de "
                f"<b style='color:{c_txt}'>{mes_nome}</b> concentra em média "
                f"<b style='color:{c_acc}'>{pct_s}</b> acima da média mensal histórica.</span>"
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
