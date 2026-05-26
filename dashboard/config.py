"""
config.py — Configurações globais, paleta de cores e conexão DuckDB.
"""

from pathlib import Path
import duckdb
import streamlit as st

# ── Caminhos ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DB_PATH  = BASE_DIR / "dados.duckdb"

# ── Domínio temporal ───────────────────────────────────────────────────────────
ANO_MIN   = 2011
ANO_MAX   = 2021
TIPOS_ALL = ("EXP", "IMP")

# ── Paleta — tema escuro moderno (referência: GitHub Dark / Linear) ────────────
COLORS = {
    "bg":        "#0E1117",   # fundo global
    "surface":   "#1C1F26",   # fundo de cards / sidebar
    "surface2":  "#252932",   # superfície secundária (hover, header)
    "primary":   "#4F8BFF",   # azul vibrante — ações, links
    "exp":       "#00D9A3",   # verde — exportação
    "imp":       "#FF4D8D",   # rosa — importação
    "text":      "#FAFAFA",   # texto principal
    "text_sec":  "#8B949E",   # texto secundário
    "border":    "#2D3139",   # bordas e separadores
    "positive":  "#00D9A3",   # delta positivo
    "negative":  "#FF4D8D",   # delta negativo
}

# ── Configuração da página Streamlit ──────────────────────────────────────────
PAGE_CONFIG = dict(
    page_title="Comex Brasil 2011–2021",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Layout base dos gráficos Plotly ───────────────────────────────────────────
PLOT_BASE = dict(
    plot_bgcolor  = COLORS["surface"],
    paper_bgcolor = COLORS["bg"],
    font          = dict(color=COLORS["text"], family="system-ui, -apple-system, sans-serif", size=12),
    margin        = dict(l=50, r=20, t=50, b=40),
    legend        = dict(
        bgcolor     = COLORS["surface"],
        bordercolor = COLORS["border"],
        borderwidth = 1,
        font        = dict(color=COLORS["text"], size=11),
    ),
    hoverlabel = dict(
        bgcolor    = COLORS["surface2"],
        bordercolor= COLORS["border"],
        font_color = COLORS["text"],
        font_size  = 12,
    ),
)

PLOT_AXIS = dict(
    gridcolor  = COLORS["border"],
    linecolor  = COLORS["border"],
    tickfont   = dict(color=COLORS["text_sec"]),
    title_font = dict(color=COLORS["text_sec"]),
    zeroline   = False,
)

# Plotly: desabilita toolbar no modo de exibição
PLOT_CONFIG = {"displayModeBar": False, "responsive": True}


# ── Conexão DuckDB (singleton cacheado) ───────────────────────────────────────
@st.cache_resource
def get_connection() -> duckdb.DuckDBPyConnection:
    """Retorna conexão única e read-only com o banco DuckDB."""
    if not DB_PATH.exists():
        st.error(f"Banco não encontrado: {DB_PATH}")
        st.stop()
    return duckdb.connect(str(DB_PATH), read_only=True)
