# 🇧🇷 Análise Exploratória e Visual do Comércio Exterior Brasileiro (2011–2021)

> Projeto Integrador Aplicado em CD & IA - I — IESB

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.36+-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![DuckDB](https://img.shields.io/badge/DuckDB-0.10+-FFF000?style=flat&logo=duckdb&logoColor=black)](https://duckdb.org/)
[![Plotly](https://img.shields.io/badge/Plotly-5.18+-3F4F75?style=flat&logo=plotly&logoColor=white)](https://plotly.com/)
[![pandas](https://img.shields.io/badge/pandas-2.0+-150458?style=flat&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![License](https://img.shields.io/badge/License-Acadêmico-blue)](#licença)

---

## 🚀 Demo ao Vivo

[![Hugging Face Spaces](https://img.shields.io/badge/🤗%20Hugging%20Face-Spaces-yellow)](https://matheus-matoso-tech-comex-brasil-2011-2021.hf.space)

**Dashboard interativo:** https://matheus-matoso-tech-comex-brasil-2011-2021.hf.space

> Hospedado no Hugging Face Spaces (CPU Basic, gratuito).  
> O cold start pode levar até 30 segundos após período de inatividade.

---

## 📋 Sobre o Projeto

**Análise Exploratória e Visual do Comércio Exterior Brasileiro (2011–2021)** é um painel analítico desenvolvido como **Projeto Integrador** para análise de **30,7 milhões de operações** de comércio exterior do Brasil entre 2011 e 2021. O projeto cobre o pipeline completo de Engenharia de Dados: ingestão, ETL, modelagem dimensional (Star Schema), otimização OLAP com DuckDB e visualização interativa com Streamlit + Plotly.

**Instituição:** IESB  
**Curso:** Ciência de Dados e Inteligência Artificial  
**Disciplina:** Projeto Integrador Aplicado em CD & IA - I · 3º Semestre  
**Professor:** Me. Regiano S. Alves

---

## ✨ Destaques

| | |
|---|---|
| 🗂️ **30,7 M operações** | Pipeline Python com leitura em chunks (3,7 GB de CSVs brutos) |
| ⭐ **Star Schema** | 1 tabela fato + 7 dimensões, incluindo `dCalendario` e `dUF` |
| 🦆 **DuckDB OLAP** | Queries em < 250 ms sobre 30 M linhas, arquivo de 634 MB |
| 📊 **4 páginas analíticas** | Filtros globais interativos e storytelling dinâmico |
| 🌙 **Tema escuro moderno** | Paleta inspirada no GitHub Dark / Linear |
| 📈 **Inteligência de Tempo** | CAGR, YoY, YTD, médias móveis 3M e análise de sazonalidade |

---

## 🏗️ Arquitetura

```
📂 CSVs Brutos (3,7 GB — Comex Stat/MDIC)
    │
    ▼
🐍 Python ETL  (etl_etapa1_dimensoes.py · etl_etapa2_fato.py · etl_etapa3_calendario_uf_validacao.py)
    │  ↓ Filtragem 2011–2021
    │  ↓ Padronização de tipos e encodings
    │  ↓ Validação de integridade referencial
    │  ↓ Geração de dCalendario e dUF
    ▼
⭐ Star Schema (CSVs limpos em dados_limpos/)
    │  fato:   fOperacao (~30,7 M linhas)
    │  dims:   dPais · dNCM · dVia · dURF · dUF · dCalendario · dUnidade
    ▼
🦆 DuckDB  (dashboard/dados.duckdb — 634 MB, formato colunar)
    │  ↓ Compressão automática + zonemaps
    │  ↓ Queries SQL analíticas com @st.cache_data
    ▼
📊 Streamlit Dashboard  (dashboard/app.py)
    │  ↓ 5 páginas: Sobre · Visão Geral · Temporal · Geográfica · Produtos
    │  ↓ Plotly para gráficos interativos
    └─→ Interface web responsiva com tema escuro
```

---

## 📁 Estrutura do Repositório

```
projeto_integrador/
│
├── dados_brutos/               # CSVs originais do Comex Stat (não versionados)
├── dados_limpos/               # Saída do ETL — Star Schema em CSV
│   ├── fOperacao.csv           # Tabela fato unificada (30,7 M linhas)
│   ├── dCalendario.csv
│   ├── dNCM.csv
│   ├── dPais.csv
│   ├── dUF.csv
│   ├── dUnidade.csv
│   ├── dURF.csv
│   └── dVia.csv
│
├── etl_etapa1_dimensoes.py     # Gera as 7 tabelas de dimensão
├── etl_etapa2_fato.py          # Consolida a tabela fato fOperacao
├── etl_etapa3_calendario_uf_validacao.py  # dCalendario, dUF e validações
│
├── dashboard/
│   ├── app.py                  # Entry point — st.navigation() + CSS global
│   ├── config.py               # Paleta de cores, PAGE_CONFIG, get_connection()
│   ├── queries.py              # Todas as queries DuckDB (@st.cache_data)
│   ├── components.py           # KPI cards, sidebar, fmt_moeda, fmt_num
│   ├── dados.duckdb            # Banco DuckDB (não versionado — 634 MB)
│   ├── etapa_a_csv_to_duckdb.py   # Ingestão dos CSVs limpos no DuckDB
│   │
│   ├── pages/
│   │   ├── 0_sobre_o_projeto.py    # Landing page com contexto do projeto
│   │   ├── 1_visao_geral.py        # KPIs globais, série anual, storytelling
│   │   ├── 2_temporal.py           # Série mensal, YoY, YTD, sazonalidade
│   │   ├── 3_geografica.py         # Mapa-múndi, ranking países e UFs
│   │   └── 4_produtos_logistica.py # Top NCMs, modais, URFs, scatter valor×peso
│   │
│   ├── .streamlit/
│   │   └── config.toml         # Tema escuro e configurações do Streamlit
│   ├── assets/                 # Recursos estáticos
│   └── screenshots/            # Vazio — screenshots adicionados manualmente
│
├── requirements.txt            # Dependências Python
├── .gitignore
└── README.md
```

---

## 🗂️ Modelo Dimensional (Star Schema)

```
                    ┌─────────────┐
                    │  dCalendario │
                    │  CO_ANO      │
                    │  CO_MES      │
                    └──────┬──────┘
                           │
 ┌──────────┐   ┌──────────┴──────────┐   ┌──────────┐
 │  dPais   │   │                     │   │   dNCM   │
 │ CO_PAIS  ├───┤     fOperacao        ├───┤  CO_NCM  │
 │ NO_PAIS  │   │   (30,7 M linhas)   │   │NO_NCM_POR│
 │ CO_ISO3  │   │                     │   └──────────┘
 └──────────┘   │  VL_FOB             │
                │  KG_LIQUIDO         │   ┌──────────┐
 ┌──────────┐   │  TIPO_OPERACAO      ├───┤   dVia   │
 │   dURF   │   │                     │   │  CO_VIA  │
 │  CO_URF  ├───┤                     │   │  NO_VIA  │
 │  NO_URF  │   └──────────┬──────────┘   └──────────┘
 └──────────┘              │
                    ┌──────┴──────┐
                    │     dUF      │
                    │   SG_UF      │
                    │   NO_UF      │
                    │  NO_REGIAO   │
                    └─────────────┘
```

> Os diagramas DER Lógico Normalizado e Star Schema foram desenvolvidos como parte da documentação do projeto.

---

## 📊 Páginas do Dashboard

| Página | Conteúdo |
|--------|----------|
| 🏠 **Sobre o Projeto** | Contexto acadêmico, arquitetura, stack tecnológico |
| 📊 **Visão Geral** | KPIs globais (EXP/IMP/Saldo/Ops), série VL_FOB anual, CAGR |
| 📅 **Análise Temporal** | Série mensal MM3, YoY anual, YTD acumulado, heatmap de sazonalidade |
| 🗺️ **Análise Geográfica** | Choropleth mundial, top 10 países, distribuição por região brasileira, ranking UFs |
| 📦 **Produtos & Logística** | Top 15 NCMs, distribuição por modal, scatter valor×peso, ranking URFs |

> 📸 Screenshots disponíveis em `dashboard/screenshots/`

---

## ⚙️ Pré-requisitos e Instalação

### 1. Ambiente Python

Recomendamos **micromamba** (ou conda/mamba):

```bash
# Com micromamba
micromamba create -n comex_env python=3.12
micromamba activate comex_env
micromamba run -n comex_env pip install -r requirements.txt
```

Ou com pip padrão:

```bash
pip install -r requirements.txt
```

### 2. Dados brutos

Faça download do dataset no **Kaggle**:

- URL: https://www.kaggle.com/datasets/daniellecd/dados-de-exportao-e-importao-do-brasil
- Clique em "Download" e extraia o arquivo zip
- Coloque os 8 arquivos CSV em `dados_brutos/`

### 3. Executar o ETL

```bash
# Etapa 1 — dimensões
micromamba run -n comex_env python etl_etapa1_dimensoes.py

# Etapa 2 — tabela fato (~30 min para 30,7 M linhas)
micromamba run -n comex_env python etl_etapa2_fato.py

# Etapa 3 — dCalendario, dUF e validações
micromamba run -n comex_env python etl_etapa3_calendario_uf_validacao.py
```

### 4. Gerar o banco DuckDB

```bash
cd dashboard
micromamba run -n comex_env python - << 'EOF'
import duckdb, glob, os

con = duckdb.connect("dados.duckdb")
tabelas = ["fOperacao","dPais","dNCM","dVia","dURF","dUF","dCalendario","dUnidade"]
for t in tabelas:
    f = f"../dados_limpos/{t}.csv"
    if os.path.exists(f):
        con.execute(f"CREATE OR REPLACE TABLE {t} AS SELECT * FROM read_csv_auto('{f}')")
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {n:,} linhas")
con.close()
print("Banco gerado: dados.duckdb")
EOF
```

### 5. Rodar o dashboard

```bash
cd dashboard
micromamba run -n comex_env streamlit run app.py
```

Acesse: http://localhost:8501

---

## 🚀 Performance

| Métrica | Valor |
|---------|-------|
| Linhas na tabela fato | 30.782.936 |
| Tamanho do banco DuckDB | 634 MB |
| Cold start (Fase 1 — Visão Geral) | < 800 ms |
| Cold start (Fase 4 — Produtos) | < 2.000 ms |
| Warm start (cache quente) | < 100 ms |
| Queries via `@st.cache_data` | Todas as consultas |

---

## 🤝 Autores

| Nome | Matrícula |
|------|-----------|
| Matheus Matoso de Almeida | 2512120034 |
| Pedro Henrique Barbosa Portela | 2512120053 |
| Thiago de Jesus Macedo | 2512120015 |

---

## 📄 Fonte dos Dados

> **Comex Stat** — Base de dados de comércio exterior do Brasil  
> Ministério do Desenvolvimento, Indústria, Comércio e Serviços (MDIC)  
> https://comexstat.mdic.gov.br
