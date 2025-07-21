

import sys
import os

# Caminho da raiz do projeto (duas pastas acima de frontend/pages)
raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if raiz_projeto not in sys.path:
    sys.path.insert(0, raiz_projeto)
    
    
import streamlit as st
from streamlit_card import card
from backend.data.processed.loading_views import carregar_view
from backend.data.processed.loading_views import carregar_query


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
query_total_contratos_ativos = """
SELECT COUNT(*) AS total_contratos_ativos
FROM v_contratos_detalhados
WHERE status_contrato = 'Ativo'
"""
df_total_contratos_ativos = carregar_query(query_total_contratos_ativos)
total_contratos = df_total_contratos_ativos['total_contratos_ativos'].iloc[0]

#---------------------------------------------------------
#KPI CHURN
query = """
SELECT 
  ROUND(
    100.0 * SUM(CASE WHEN status_contrato = 'Cancelado' THEN 1 ELSE 0 END) / 
            SUM(CASE WHEN status_contrato IN ('Cancelado', 'Encerrado') THEN 1 ELSE 0 END)
  , 2) AS churn_global
FROM v_contratos_detalhados;

"""
df_churn = carregar_query(query)
churn = df_churn['churn_global'].iloc[0]
#----------------------------------------------------------
#KPI CLIENTES EM RISCO

#--------------------------------------------------------------------

#KPI CLIENTES ATIVOS
query = """
SELECT COUNT(DISTINCT cliente_id) AS total_clientes_ativos
FROM v_contratos_detalhados
WHERE status_contrato = 'Ativo';
"""
df_clientes_ativos = carregar_query(query)
clientes_ativos = df_clientes_ativos['total_clientes_ativos'].iloc[0]
#---------------------------------
#KPI AVALIAÇÃO
query= """
SELECT 
  ROUND(AVG(nivel_satisfacao_num), 2) AS satisfacao_media
FROM v_contratos_detalhados
"""
df_avl_avg = carregar_query(query)
avl_avg = df_avl_avg['satisfacao_media'].iloc[0]
def render():
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        kpi_custom("🚀", churn, "% Churn")
    with col2:
        kpi_custom("💰", total_contratos, "Contratos Ativos")   
    with col3:
        kpi_custom("📈", "7.8%", "Clientes em Risco")   
    with col4:
        kpi_custom("📉", avl_avg, "Satisfação Média")
    with col5:
        kpi_custom("👥", clientes_ativos, "Clientes Ativos")

    st.markdown("### 👥 Clientes em Risco")

    # Layout com duas colunas, mas bem próximo
    col1, col2 = st.columns([6, 1])  # 6:1 para colar mais o botão no título

    with col1:
        st.markdown("Visualize e exporte os clientes com maior risco de cancelamento:")

    with col2:
        st.button("📤 Exportar CSV")

    # Carrega os dados da view
    df_ativos = carregar_view('v_contratos_detalhados')

    # Mostra a tabela
    st.dataframe(df_ativos, use_container_width=True)
if __name__ == "__main__":
    render()
