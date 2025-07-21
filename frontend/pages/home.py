

import sys
import os

# Caminho da raiz do projeto (duas pastas acima de frontend/pages)
raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if raiz_projeto not in sys.path:
    sys.path.insert(0, raiz_projeto)
    
    
import streamlit as st
from streamlit_card import card
from backend.data.processed.loading_views import carregar_view


def kpi_custom(icon, value, explanation):
    st.markdown(f"""
    <style>
    .kpi-box {{
        position: relative;
        display: flex;
        align-items: center;
        background-color: white;
        border-radius: 12px;
        padding: 12px 16px;
        width: 100%;
        margin-bottom: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        font-family: 'Arial', sans-serif;
    }}
    .kpi-icon {{
        font-size: 28px;
        margin-right: 14px;
    }}
    .kpi-content {{
        flex-grow: 1;
    }}
    .kpi-value {{
        font-size: 26px;
        font-weight: 700;
        margin: 0;
    }}
    .kpi-explanation {{
        margin-top: 4px;
        font-size: 13px;
        color: #555;
    }}
    .tooltip {{
        position: absolute;
        top: 10px;
        right: 10px;
        cursor: pointer;
        color: #999;
        font-weight: bold;
        font-size: 16px;
        border-radius: 50%;
        width: 20px;
        height: 20px;
        line-height: 20px;
        text-align: center;
        user-select: none;
        transition: color 0.3s;
    }}
    .tooltip:hover {{
        color: #333;
    }}
    .tooltip .tooltiptext {{
        visibility: hidden;
        width: 180px;
        background-color: #333;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 6px 8px;
        position: absolute;
        z-index: 1;
        top: 28px;
        right: 0;
        opacity: 0;
        transition: opacity 0.3s;
        font-size: 12px;
    }}
    .tooltip:hover .tooltiptext {{
        visibility: visible;
        opacity: 1;
    }}
    </style>

    <div class="kpi-box">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-content">
            <p class="kpi-value">{value}</p>
            <div class="kpi-explanation">{explanation}</div>
        </div>
        <div class="tooltip">i
            <span class="tooltiptext">Mais informações sobre este KPI</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

## DADOS TRATADOS PARA PASSAR PARA O FRONTEND
sql = "SELECT AVG(satisfacao) AS satisfacao_media FROM clientes"

def render():
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        kpi_custom("🚀", "4.5%", "% Churn")
    with col2:
        kpi_custom("💰", "R$ 250,00", "Contratos Ativos")   
    with col3:
        kpi_custom("📈", "7.8%", "Clientes em Risco")   
    with col4:
        kpi_custom("📉", "2.1%", "Satisfação Média")
    with col5:
        kpi_custom("👥", "1.200", "Clientes Ativos")

    col1, col2 = st.columns(2)
    
    col1.title("Clientes em Risco")
    col2.button("Exportar CSV")
    df_ativos = carregar_view('v_perfil_cliente_enriquecido')
    st.dataframe(df_ativos)
    st.dataframe()
if __name__ == "__main__":
    render()
