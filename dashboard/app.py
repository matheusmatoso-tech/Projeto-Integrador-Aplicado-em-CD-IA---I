"""
app.py — Entry point do dashboard Comex Brasil.
Define page config, CSS global e navegação multi-página.
"""

import streamlit as st
from config import PAGE_CONFIG, COLORS

st.set_page_config(**PAGE_CONFIG)

# ── CSS global ─────────────────────────────────────────────────────────────────
# Ajustes finos sobre o tema dark do Streamlit
st.markdown(f"""
<style>
/* Remove padding excessivo no topo */
.block-container {{ padding-top: 1.8rem; padding-bottom: 1rem; }}

/* Sidebar */
[data-testid="stSidebar"] {{
    background-color: {COLORS['surface']} !important;
    border-right: 1px solid {COLORS['border']};
}}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
    font-size: 0.85rem;
}}

/* Métricas nativas (rodapé) */
[data-testid="stMetric"] {{
    background   : {COLORS['surface']};
    border       : 1px solid {COLORS['border']};
    border-radius: 10px;
    padding      : 14px 18px;
}}
[data-testid="stMetricLabel"] {{ color: {COLORS['text_sec']}; font-size: 0.78rem; }}
[data-testid="stMetricValue"] {{ color: {COLORS['text']};     font-size: 1.2rem;  }}

/* Oculta "Made with Streamlit" no rodapé */
footer {{ visibility: hidden; }}

/* Divider */
hr {{ border-color: {COLORS['border']} !important; margin: 0.6rem 0; }}
</style>
""", unsafe_allow_html=True)

# ── Navegação multi-página ─────────────────────────────────────────────────────
pg = st.navigation([
    st.Page("pages/0_sobre_o_projeto.py",      title="Sobre o Projeto",    icon="🏠", default=True),
    st.Page("pages/1_visao_geral.py",          title="Visão Geral",        icon="📊"),
    st.Page("pages/2_temporal.py",             title="Análise Temporal",   icon="📅"),
    st.Page("pages/3_geografica.py",           title="Análise Geográfica", icon="🗺️"),
    st.Page("pages/4_produtos_logistica.py",   title="Produtos & Logística", icon="📦"),
])
pg.run()
