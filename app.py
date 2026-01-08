import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime, timedelta
import calendar
import numpy as np

# Configuração da página
st.set_page_config(page_title="Metas 2026 SJ Consulting", layout="wide", page_icon="🎯")

# Estilos CSS customizados
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    .main {
        background-color: #000000;
    }
    .stApp {
        background-color: #000000;
    }
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown {
        color: #d7d4cb !important;
    }
    .stSelectbox label, .stDateInput label, .stNumberInput label, .stTextInput label {
        color: #d7d4cb !important;
    }
    [data-testid="stMetricValue"] {
        color: #d7d4cb !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #1a1a1a;
        border-color: #42644b;
    }
    input {
        background-color: #1a1a1a !important;
        color: #d7d4cb !important;
        border-color: #42644b !important;
    }
    .stButton button {
        background-color: #42644b;
        color: #d7d4cb;
        font-weight: bold;
        border: none;
    }
    .stButton button:hover {
        background-color: #354d38;
    }
    .icon-card {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
        border-radius: 10px;
        border: 2px solid #42644b;
        margin: 10px 0;
    }
    .icon-card i {
        font-size: 3em;
        color: #42644b;
        margin-bottom: 10px;
    }
    .metric-icon {
        display: inline-block;
        margin-right: 10px;
        color: #42644b;
    }
</style>
""", unsafe_allow_html=True)

# Configurar estilo do matplotlib
plt.style.use('dark_background')

# Conexão com banco de dados
def init_db():
    conn = sqlite3.connect('metas.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS metas
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nome TEXT NOT NULL,
                  meta_mensal INTEGER NOT NULL,
                  realizado INTEGER NOT NULL,
                  data DATE NOT NULL)''')
    conn.commit()
    return conn

# Funções do banco de dados
def adicionar_meta(conn, nome, meta_mensal, realizado, data):
    c = conn.cursor()
    c.execute("INSERT INTO metas (nome, meta_mensal, realizado, data) VALUES (?, ?, ?, ?)",
              (nome, meta_mensal, realizado, data))
    conn.commit()

def obter_metas(conn, data_inicio=None, data_fim=None):
    c = conn.cursor()
    if data_inicio and data_fim:
        c.execute("SELECT * FROM metas WHERE data BETWEEN ? AND ?", (data_inicio, data_fim))
    else:
        c.execute("SELECT * FROM metas")
    return c.fetchall()

def obter_ultimas_metas_por_tipo(conn, data_inicio, data_fim):
    c = conn.cursor()
    query = """
        SELECT nome, meta_mensal, SUM(realizado) as total_realizado
        FROM metas
        WHERE data BETWEEN ? AND ?
        GROUP BY nome, meta_mensal
    """
    c.execute(query, (data_inicio, data_fim))
    return c.fetchall()

def obter_dados_mensais(conn, ano):
    c = conn.cursor()
    query = """
        SELECT nome, strftime('%m', data) as mes, SUM(realizado) as total
        FROM metas
        WHERE strftime('%Y', data) = ?
        GROUP BY nome, mes
        ORDER BY nome, mes
    """
    c.execute(query, (str(ano),))
    return c.fetchall()

# Função para criar gráfico de rosca
def criar_grafico_rosca(realizado, faltam, cor, nome, meta_mensal):
    fig, ax = plt.subplots(figsize=(5, 5), facecolor='#000000')
    ax.set_facecolor('#000000')
    
    valores = [realizado, faltam]
    cores_grafico = [cor, '#1a1a1a']
    percentual = (realizado / meta_mensal * 100) if meta_mensal > 0 else 0
    
    # Criar gráfico de rosca
    wedges, texts = ax.pie(valores, colors=cores_grafico, startangle=90, 
                            wedgeprops=dict(width=0.4, edgecolor='#000000', linewidth=2))
    
    # Adicionar texto no centro
    ax.text(0, 0.1, f'{percentual:.0f}%', ha='center', va='center', 
            fontsize=32, color='#d7d4cb', weight='bold')
    ax.text(0, -0.15, f'Faltam: {faltam}', ha='center', va='center', 
            fontsize=12, color='#d7d4cb')
    ax.text(0, 0.6, f'{realizado}/{meta_mensal}', ha='center', va='center', 
            fontsize=14, color='#d7d4cb', weight='bold')
    
    plt.tight_layout()
    return fig

# Inicializar banco de dados
conn = init_db()

# Título
st.markdown("""
<h1 style='text-align: center; font-size: 3em;'>
    <i class='fas fa-chart-line' style='color: #42644b;'></i> 
    Metas 2026 SJ Consulting 
    <i class='fas fa-trophy' style='color: #42644b;'></i>
</h1>
""", unsafe_allow_html=True)
st.markdown("---")

# Sidebar para adicionar novas metas
with st.sidebar:
    st.markdown("## <i class='fas fa-plus-circle'></i> Adicionar Nova Meta", unsafe_allow_html=True)
    
    # Dicionário com ícones Font Awesome
    tipos_meta_display = {
        "Sites": "<i class='fas fa-globe'></i> Sites",
        "Delivery": "<i class='fas fa-truck'></i> Delivery",
        "Ecommerce": "<i class='fas fa-shopping-cart'></i> Ecommerce",
        "Tráfego": "<i class='fas fa-chart-bar'></i> Tráfego",
        "Celina IA": "<i class='fas fa-robot'></i> Celina IA"
    }
    
    # Criar lista de opções sem HTML para o selectbox
    tipos_meta_options = list(tipos_meta_display.keys())
    
    # Mostrar os ícones acima do selectbox
    st.markdown("<p style='font-size: 14px;'><i class='fas fa-list'></i> Tipo de Meta:</p>", unsafe_allow_html=True)
    nome_meta = st.selectbox("Tipo de Meta:", tipos_meta_options, label_visibility="collapsed")
    
    # Metas mensais padrão
    metas_padrao = {
        "Sites": 5,
        "Delivery": 2,
        "Ecommerce": 10,
        "Tráfego": 5,
        "Celina IA": 50
    }
    
    st.markdown("<p style='font-size: 14px;'><i class='fas fa-bullseye'></i> Meta Mensal:</p>", unsafe_allow_html=True)
    meta_mensal = st.number_input("Meta Mensal:", min_value=1, value=metas_padrao.get(nome_meta, 1), step=1, label_visibility="collapsed")
    
    st.markdown("<p style='font-size: 14px;'><i class='fas fa-check-circle'></i> Realizado:</p>", unsafe_allow_html=True)
    realizado = st.number_input("Realizado:", min_value=0, value=0, step=1, label_visibility="collapsed")
    
    st.markdown("<p style='font-size: 14px;'><i class='fas fa-calendar-alt'></i> Data:</p>", unsafe_allow_html=True)
    data_meta = st.date_input("Data:", value=datetime.now(), label_visibility="collapsed")
    
    if st.button("💾 Salvar Meta", use_container_width=True):
        adicionar_meta(conn, nome_meta, meta_mensal, realizado, data_meta)
        st.success(f"✅ Meta '{nome_meta}' adicionada!")
        st.rerun()

# Filtro de período
st.markdown("<h3><i class='fas fa-filter' style='color: #42644b;'></i> Filtro de Período</h3>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    st.markdown("<p style='font-size: 14px;'><i class='fas fa-calendar-check'></i> Data Início:</p>", unsafe_allow_html=True)
    data_inicio = st.date_input("Data Início:", value=datetime(2026, 1, 1), label_visibility="collapsed")
with col2:
    st.markdown("<p style='font-size: 14px;'><i class='fas fa-calendar-times'></i> Data Fim:</p>", unsafe_allow_html=True)
    data_fim = st.date_input("Data Fim:", value=datetime(2026, 12, 31), label_visibility="collapsed")

st.markdown("---")

# Obter dados do período selecionado
metas_periodo = obter_ultimas_metas_por_tipo(conn, data_inicio, data_fim)

# Gráficos de rosca (donut charts)
if metas_periodo:
    st.markdown("<h2><i class='fas fa-chart-pie' style='color: #42644b;'></i> Metas do Período</h2>", unsafe_allow_html=True)
    
    cores = ["#9333ea", "#f97316", "#eab308", "#06b6d4", "#ec4899"]
    
    # Criar colunas para os gráficos
    num_metas = len(metas_periodo)
    cols = st.columns(min(num_metas, 5))
    
    for idx, (nome, meta_mensal, realizado) in enumerate(metas_periodo):
        faltam = max(meta_mensal - realizado, 0)
        
        # Ícones Font Awesome por categoria
        icones_fa = {
            "Sites": "fa-globe",
            "Delivery": "fa-truck",
            "Ecommerce": "fa-shopping-cart",
            "Tráfego": "fa-chart-bar",
            "Celina IA": "fa-robot"
        }
        icone_class = icones_fa.get(nome, "fa-chart-line")
        
        with cols[idx % 5]:
            # Card com ícone
            st.markdown(f"""
            <div style='text-align: center; margin-bottom: 10px;'>
                <i class='fas {icone_class}' style='font-size: 2em; color: {cores[idx % len(cores)]};'></i>
                <h3 style='margin: 5px 0; color: #d7d4cb;'>{nome}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Criar e exibir gráfico de rosca
            fig = criar_grafico_rosca(realizado, faltam, cores[idx % len(cores)], nome, meta_mensal)
            st.pyplot(fig)
            plt.close(fig)
else:
    st.info("📝 Nenhuma meta registrada para o período selecionado.")

st.markdown("---")

# Gráfico de linha anual
st.markdown("<h2><i class='fas fa-chart-line' style='color: #42644b;'></i> Projeção Anual de Metas</h2>", unsafe_allow_html=True)

# Obter dados do ano selecionado
ano_selecionado = data_inicio.year
dados_mensais = obter_dados_mensais(conn, ano_selecionado)

# Preparar dados para o gráfico
df_dados = pd.DataFrame(dados_mensais, columns=['nome', 'mes', 'total'])

# Criar o gráfico de linhas com matplotlib
fig_linha, ax = plt.subplots(figsize=(14, 6), facecolor='#000000')
ax.set_facecolor('#000000')

cores_linha = {
    "Sites": "#9333ea",
    "Delivery": "#f97316",
    "Ecommerce": "#eab308",
    "Tráfego": "#06b6d4",
    "Celina IA": "#ec4899"
}

# Meses do ano
meses = [f'{i:02d}' for i in range(1, 13)]
nomes_meses = [calendar.month_abbr[i] for i in range(1, 13)]

# Adicionar linha para cada tipo de meta
for tipo_meta in ["Sites", "Delivery", "Ecommerce", "Tráfego", "Celina IA"]:
    meta_mensal = metas_padrao.get(tipo_meta, 0)
    meta_anual = meta_mensal * 12
    
    # Dados realizados
    dados_tipo = df_dados[df_dados['nome'] == tipo_meta]
    valores_mensais = []
    acumulado = 0
    
    for mes in meses:
        valor_mes = dados_tipo[dados_tipo['mes'] == mes]['total'].sum()
        acumulado += valor_mes
        valores_mensais.append(acumulado)
    
    cor = cores_linha.get(tipo_meta, '#d7d4cb')
    
    # Linha de realizado
    ax.plot(nomes_meses, valores_mensais, 
            color=cor, linewidth=3, marker='o', markersize=8, 
            label=f'{tipo_meta} (Realizado)')
    
    # Linha de meta (linha pontilhada)
    metas_linha = [meta_mensal * (i+1) for i in range(12)]
    ax.plot(nomes_meses, metas_linha, 
            color=cor, linewidth=2, linestyle='--', alpha=0.6,
            label=f'{tipo_meta} (Meta: {meta_anual})')

# Configurar o gráfico
ax.set_title(f'Acompanhamento de Metas Anuais - {ano_selecionado}', 
             fontsize=20, color='#d7d4cb', weight='bold', pad=20)
ax.set_xlabel('Mês', fontsize=14, color='#d7d4cb')
ax.set_ylabel('Quantidade Acumulada', fontsize=14, color='#d7d4cb')
ax.tick_params(colors='#d7d4cb')
ax.grid(True, alpha=0.2, color='#1a1a1a')
ax.legend(loc='upper left', fontsize=10, facecolor='#1a1a1a', 
          edgecolor='#42644b', framealpha=0.9, labelcolor='#d7d4cb')

# Remover bordas superiores e direitas
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#42644b')
ax.spines['bottom'].set_color('#42644b')

plt.tight_layout()
st.pyplot(fig_linha)
plt.close(fig_linha)

# Tabela de resumo
st.markdown("---")
st.markdown("<h2><i class='fas fa-table' style='color: #42644b;'></i> Resumo das Metas</h2>", unsafe_allow_html=True)

if metas_periodo:
    resumo_data = []
    icones_fa_resumo = {
        "Sites": "fa-globe",
        "Delivery": "fa-truck",
        "Ecommerce": "fa-shopping-cart",
        "Tráfego": "fa-chart-bar",
        "Celina IA": "fa-robot"
    }
    
    for nome, meta_mensal, realizado in metas_periodo:
        faltam = max(meta_mensal - realizado, 0)
        percentual = (realizado / meta_mensal * 100) if meta_mensal > 0 else 0
        meta_anual = meta_mensal * 12
        
        resumo_data.append({
            "Meta": nome,
            "Meta Mensal": meta_mensal,
            "Meta Anual": meta_anual,
            "Realizado": realizado,
            "Faltam": faltam,
            "% Concluído": f"{percentual:.1f}%"
        })
    
    df_resumo = pd.DataFrame(resumo_data)
    
    # Adicionar cards visuais acima da tabela
    st.markdown("<div style='margin: 20px 0;'>", unsafe_allow_html=True)
    cols_resumo = st.columns(len(metas_periodo))
    
    for idx, (col, row) in enumerate(zip(cols_resumo, resumo_data)):
        with col:
            nome = row["Meta"]
            icone_class = icones_fa_resumo.get(nome, "fa-chart-line")
            cor = cores[idx % len(cores)]
            
            st.markdown(f"""
            <div style='text-align: center; padding: 15px; background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%); 
                        border-radius: 10px; border: 2px solid {cor}; margin: 5px;'>
                <i class='fas {icone_class}' style='font-size: 2.5em; color: {cor};'></i>
                <h4 style='margin: 10px 0 5px 0; color: #d7d4cb;'>{nome}</h4>
                <p style='font-size: 1.5em; font-weight: bold; color: {cor}; margin: 5px 0;'>{row['% Concluído']}</p>
                <p style='font-size: 0.9em; color: #d7d4cb; margin: 0;'>{row['Realizado']}/{row['Meta Mensal']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.dataframe(df_resumo, use_container_width=True, hide_index=True)

# Fechar conexão
conn.close()