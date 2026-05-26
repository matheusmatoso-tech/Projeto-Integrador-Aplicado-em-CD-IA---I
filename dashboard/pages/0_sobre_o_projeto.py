"""Página 0 — Sobre o Projeto (landing page)"""
import streamlit as st
from config import COLORS

st.markdown("## 🏠 Comex Brasil 2011–2021")
st.markdown(
    f"<p style='color:{COLORS['text_sec']};font-size:1.1rem;margin-top:-10px'>"
    "Análise interativa do comércio exterior brasileiro"
    "</p>",
    unsafe_allow_html=True,
)
st.divider()

# ── O que é este dashboard ─────────────────────────────────────────────────────
st.markdown("### 📌 O que é este dashboard")
st.markdown(
    f"""<div style="
        background:{COLORS['surface']};
        border:1px solid {COLORS['border']};
        border-radius:12px;
        padding:20px 24px;
        color:{COLORS['text_sec']};
        font-size:0.95rem;
        line-height:1.7;
    ">
    Este painel analítico explora <b style="color:{COLORS['text']}">30,7 milhões de operações</b>
    de importação e exportação registradas pela Receita Federal entre 2011 e 2021.
    Construído sobre um modelo dimensional <b style="color:{COLORS['primary']}">Star Schema</b>
    com 1 tabela fato e 7 dimensões, oferece análises temporais, geográficas e logísticas
    com filtros interativos em tempo real.
    </div>""",
    unsafe_allow_html=True,
)

st.markdown("<div style='margin-top:24px'></div>", unsafe_allow_html=True)

# ── Highlights ─────────────────────────────────────────────────────────────────
st.markdown("### 📊 Highlights do Projeto")

def _highlight_card(icone: str, valor: str, label: str, cor: str) -> str:
    return f"""
    <div style="
        background:{COLORS['surface']};
        border:1px solid {COLORS['border']};
        border-radius:12px;
        padding:22px 16px;
        text-align:center;
        min-height:120px;
    ">
        <div style="font-size:2rem;margin-bottom:8px">{icone}</div>
        <div style="font-size:1.55rem;font-weight:700;color:{cor};line-height:1.1">{valor}</div>
        <div style="font-size:0.78rem;color:{COLORS['text_sec']};margin-top:6px;font-weight:500">{label}</div>
    </div>"""

h1, h2, h3, h4 = st.columns(4)
with h1:
    st.markdown(_highlight_card("🗂️", "30,7 mi", "operações registradas", COLORS["primary"]), unsafe_allow_html=True)
with h2:
    st.markdown(_highlight_card("📅", "11 anos", "analisados (2011–2021)", COLORS["exp"]), unsafe_allow_html=True)
with h3:
    st.markdown(_highlight_card("🌍", "262", "países parceiros", COLORS["imp"]), unsafe_allow_html=True)
with h4:
    st.markdown(_highlight_card("📈", "30+", "análises interativas", COLORS["text"]), unsafe_allow_html=True)

st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)

# ── Como usar ─────────────────────────────────────────────────────────────────
st.markdown("### 🧭 Como usar este dashboard")

_how_card = lambda icone, titulo, texto: f"""
<div style="
    background:{COLORS['surface']};
    border:1px solid {COLORS['border']};
    border-radius:12px;
    padding:20px 20px 16px;
    height:160px;
">
    <div style="font-size:1.5rem;margin-bottom:8px">{icone}</div>
    <div style="font-size:0.8rem;font-weight:700;text-transform:uppercase;
                letter-spacing:.06em;color:{COLORS['text']};margin-bottom:8px">{titulo}</div>
    <div style="font-size:0.82rem;color:{COLORS['text_sec']};line-height:1.55">{texto}</div>
</div>"""

u1, u2, u3 = st.columns(3)
with u1:
    st.markdown(_how_card(
        "🎛️", "Filtros Globais",
        "Use a barra lateral para filtrar por período, tipo de operação "
        "(Exportação / Importação), países parceiros e estados brasileiros.",
    ), unsafe_allow_html=True)
with u2:
    st.markdown(_how_card(
        "📑", "Navegação Entre Páginas",
        "Cada página explora uma dimensão diferente: panorama geral, "
        "evolução temporal, distribuição geográfica e análise de produtos e logística.",
    ), unsafe_allow_html=True)
with u3:
    st.markdown(_how_card(
        "💡", "Insights Dinâmicos",
        "Todos os gráficos e métricas são recalculados em tempo real "
        "conforme você ajusta os filtros.",
    ), unsafe_allow_html=True)

st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)

# ── Arquitetura ────────────────────────────────────────────────────────────────
st.markdown("### 🏗️ Arquitetura Técnica")
st.markdown(
    f"""<div style="
        background:{COLORS['surface']};
        border:1px solid {COLORS['border']};
        border-radius:12px;
        padding:20px 28px;
        font-family:monospace;
        font-size:0.88rem;
        color:{COLORS['text_sec']};
        line-height:2;
    ">
    📂 <b style="color:{COLORS['text']}">CSVs Brutos</b> (3,7 GB)
    &nbsp;&nbsp;→&nbsp;&nbsp;
    🐍 <b style="color:{COLORS['primary']}">Python ETL</b> (pandas, chunks)
    &nbsp;&nbsp;→&nbsp;&nbsp;
    ⭐ <b style="color:{COLORS['exp']}">Star Schema</b> (1 fato + 7 dimensões)
    &nbsp;&nbsp;→&nbsp;&nbsp;
    🦆 <b style="color:{COLORS['text']}">DuckDB</b> (634 MB, colunar)
    &nbsp;&nbsp;→&nbsp;&nbsp;
    📊 <b style="color:{COLORS['imp']}">Streamlit Dashboard</b>
    </div>""",
    unsafe_allow_html=True,
)

st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)

# ── Stack tecnológico ─────────────────────────────────────────────────────────
st.markdown("### 🛠️ Stack Tecnológico")

_badge = lambda nome, desc, cor: f"""
<div style="
    display:inline-flex;
    align-items:center;
    gap:10px;
    background:{COLORS['surface']};
    border:1px solid {COLORS['border']};
    border-left:4px solid {cor};
    border-radius:8px;
    padding:10px 16px;
    margin:4px;
    font-size:0.84rem;
">
    <b style="color:{COLORS['text']}">{nome}</b>
    <span style="color:{COLORS['text_sec']}">{desc}</span>
</div>"""

st.markdown(
    _badge("Python 3.x",  "ETL e backend analítico",         COLORS["primary"]) +
    _badge("DuckDB",       "Engine OLAP columnar",            "#FFF000") +
    _badge("Streamlit",    "Interface web interativa",        "#FF4B4B") +
    _badge("Plotly",       "Visualizações interativas",       COLORS["exp"]) +
    _badge("pandas",       "Manipulação e transformação",     COLORS["imp"]),
    unsafe_allow_html=True,
)

st.markdown("<div style='margin-top:36px'></div>", unsafe_allow_html=True)
st.divider()

# ── Autores e contexto acadêmico ───────────────────────────────────────────────
st.markdown("### 👥 Autores e Contexto Acadêmico")

col_autores, col_contexto = st.columns(2)

with col_autores:
    st.markdown(
        f"""<div style="
            background:{COLORS['surface']};
            border:1px solid {COLORS['border']};
            border-radius:12px;
            padding:20px 22px;
        ">
            <div style="font-size:0.75rem;font-weight:700;text-transform:uppercase;
                        letter-spacing:.07em;color:{COLORS['text_sec']};margin-bottom:12px">
                Autores
            </div>
            <p style="font-size:0.82rem;color:{COLORS['text_sec']};margin-bottom:14px">
                Trabalho desenvolvido em grupo, sem hierarquia de liderança.
            </p>
            <div style="font-size:0.88rem;color:{COLORS['text']};line-height:2">
                👤 <b>Matheus Matoso de Almeida</b>
                <span style="color:{COLORS['text_sec']};font-size:0.78rem"> · 2512120034</span><br>
                👤 <b>Pedro Henrique Barbosa Portela</b>
                <span style="color:{COLORS['text_sec']};font-size:0.78rem"> · 2512120053</span><br>
                👤 <b>Thiago de Jesus Macedo</b>
                <span style="color:{COLORS['text_sec']};font-size:0.78rem"> · 2512120015</span>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

with col_contexto:
    st.markdown(
        f"""<div style="
            background:{COLORS['surface']};
            border:1px solid {COLORS['border']};
            border-radius:12px;
            padding:20px 22px;
        ">
            <div style="font-size:0.75rem;font-weight:700;text-transform:uppercase;
                        letter-spacing:.07em;color:{COLORS['text_sec']};margin-bottom:12px">
                Contexto Acadêmico
            </div>
            <div style="font-size:0.88rem;color:{COLORS['text']};line-height:2">
                🏛️ <b>IESB</b><br>
                📚 Ciência de Dados e Inteligência Artificial<br>
                📖 Projeto Integrador Aplicado em CD & IA - I<br>
                🗓️ 3º Semestre · 2024<br>
                👨‍🏫 <b>Prof. Me. Regiano S. Alves</b>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

# ── Rodapé de fonte ────────────────────────────────────────────────────────────
st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
st.markdown(
    f"<div style='text-align:center;color:{COLORS['text_sec']};font-size:0.75rem;padding:12px 0'>"
    "📦 Fonte dos dados: <b>Comex Stat / Ministério do Desenvolvimento, Indústria, "
    "Comércio e Serviços (MDIC)</b>"
    "</div>",
    unsafe_allow_html=True,
)
