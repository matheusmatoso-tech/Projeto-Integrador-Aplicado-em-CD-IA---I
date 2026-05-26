"""
components.py — Componentes reutilizáveis: KPI cards, sidebar, formatação.
"""

import streamlit as st
from config import COLORS, ANO_MIN, ANO_MAX, TIPOS_ALL
from queries import get_top_paises, get_todas_ufs


# ── Formatação ─────────────────────────────────────────────────────────────────

def fmt_moeda(valor: float) -> str:
    """Formata valor monetário em US$ com sufixo (tri / bi / mi)."""
    v = abs(valor)
    sinal = "-" if valor < 0 else ""
    if v >= 1e12:
        return f"{sinal}US$ {v/1e12:.2f} tri"
    if v >= 1e9:
        return f"{sinal}US$ {v/1e9:.2f} bi"
    if v >= 1e6:
        return f"{sinal}US$ {v/1e6:.1f} mi"
    return f"{sinal}US$ {v:,.0f}"


def fmt_num(valor: int | float) -> str:
    """Formata número inteiro com separador de milhar brasileiro (ponto)."""
    return f"{int(valor):,}".replace(",", ".")


# ── KPI Card ───────────────────────────────────────────────────────────────────

def kpi_card(
    titulo:    str,
    valor:     str,
    delta_pct: float | None,
    icone:     str,
    cor_valor: str | None = None,
) -> None:
    """
    Renderiza um card KPI com título, valor grande, ícone e delta percentual.

    Parameters
    ----------
    titulo    : label pequeno acima do valor
    valor     : string já formatada (ex: "US$ 2.45 tri")
    delta_pct : variação % vs período anterior; None oculta o delta
    icone     : emoji exibido no canto superior direito
    cor_valor : cor CSS do valor; None usa COLORS["text"]
    """
    cor = cor_valor or COLORS["text"]

    if delta_pct is not None:
        seta  = "▲" if delta_pct >= 0 else "▼"
        cd    = COLORS["positive"] if delta_pct >= 0 else COLORS["negative"]
        delta_html = (
            f'<div style="color:{cd};font-size:0.78rem;margin-top:5px;font-weight:500">'
            f'{seta} {abs(delta_pct):.1f}% CAGR no período</div>'
        )
    else:
        delta_html = '<div style="height:1.1rem"></div>'

    st.markdown(f"""
    <div style="
        background    : {COLORS['surface']};
        border        : 1px solid {COLORS['border']};
        border-radius : 12px;
        padding       : 20px 22px 16px;
        min-height    : 130px;
        display       : flex;
        flex-direction: column;
        justify-content: space-between;
    ">
        <div style="display:flex;justify-content:space-between;align-items:center">
            <span style="
                color         : {COLORS['text_sec']};
                font-size     : 0.75rem;
                font-weight   : 600;
                text-transform: uppercase;
                letter-spacing: 0.06em;
            ">{titulo}</span>
            <span style="font-size:1.2rem;opacity:0.75">{icone}</span>
        </div>
        <div style="
            color      : {cor};
            font-size  : 1.6rem;
            font-weight: 700;
            line-height: 1.1;
            margin-top : 10px;
        ">{valor}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


# ── Sidebar de filtros ─────────────────────────────────────────────────────────

def render_sidebar() -> dict:
    """
    Renderiza a sidebar de filtros e retorna os valores selecionados como
    dicionário com chaves: anos, tipos, paises, ufs (todos tuplas hashable).
    """
    # Inicializa session_state na primeira execução
    defaults = {
        "filtro_anos":   (ANO_MIN, ANO_MAX),
        "filtro_tipos":  list(TIPOS_ALL),
        "filtro_paises": [],
        "filtro_ufs":    [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    with st.sidebar:
        # Cabeçalho
        st.markdown(f"""
        <div style="padding:6px 0 14px">
            <div style="font-size:1.05rem;font-weight:700;color:{COLORS['text']}">
                🇧🇷 Comex Brasil
            </div>
            <div style="color:{COLORS['text_sec']};font-size:0.75rem;margin-top:2px">
                Exportações e Importações · 2011–2021
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        st.markdown(
            f"<p style='color:{COLORS['text_sec']};font-size:0.72rem;"
            f"text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px'>"
            f"Filtros</p>",
            unsafe_allow_html=True,
        )

        # ── Período (anos)
        anos = st.slider(
            "Período",
            min_value=ANO_MIN, max_value=ANO_MAX,
            value=st.session_state["filtro_anos"],
            key="filtro_anos",
        )

        # ── Tipo de operação
        tipos = st.multiselect(
            "Tipo de Operação",
            options=["EXP", "IMP"],
            default=st.session_state["filtro_tipos"],
            key="filtro_tipos",
            format_func=lambda x: "📤 Exportação" if x == "EXP" else "📥 Importação",
        )
        if not tipos:
            tipos = list(TIPOS_ALL)
            st.caption("⚠️ Sem tipo selecionado — exibindo ambos.")

        # ── Países (top 50)
        top50       = get_top_paises(50)
        pais_labels = dict(zip(top50["CO_PAIS"], top50["NO_PAIS"]))
        paises_sel  = st.multiselect(
            "Países (top 50 por volume)",
            options=top50["CO_PAIS"].tolist(),
            default=st.session_state["filtro_paises"],
            key="filtro_paises",
            format_func=lambda x: pais_labels.get(x, x),
            placeholder="Todos os países",
        )

        # ── UFs
        ufs_sel = st.multiselect(
            "Estados (UF)",
            options=get_todas_ufs(),
            default=st.session_state["filtro_ufs"],
            key="filtro_ufs",
            placeholder="Todas as UFs",
        )

        # Resumo dos filtros ativos
        st.divider()
        n_anos = anos[1] - anos[0]
        partes = [
            f"{n_anos} ano{'s' if n_anos > 1 else ''}",
            f"{len(tipos)} tipo{'s' if len(tipos) > 1 else ''}",
            "todos os países" if not paises_sel else f"{len(paises_sel)} país(es)",
            "todas as UFs"    if not ufs_sel    else f"{len(ufs_sel)} UF(s)",
        ]
        st.caption("🔎 " + " · ".join(partes))

    return {
        "anos":   tuple(anos),
        "tipos":  tuple(sorted(tipos)),
        "paises": tuple(sorted(paises_sel)),
        "ufs":    tuple(sorted(ufs_sel)),
    }
