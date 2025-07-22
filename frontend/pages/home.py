

import pandas as pd
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

def carregar_dados_predicao():
    caminho_csv = "backend/models/clientes_ativos_com_predicao.csv"
    df = pd.read_csv(caminho_csv)
    return df

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
df_predicoes = carregar_dados_predicao()

# Filtra só os contratos com cancelamento previsto (exemplo: valor 1)
clientes_em_risco = df_predicoes[df_predicoes['cancelamento_previsto'] == 1]['cliente_id'].nunique()
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
        kpi_custom("📈", clientes_em_risco, "Clientes em Risco")   
    with col4:
        kpi_custom("📉", avl_avg, "Satisfação Média")
    with col5:
        kpi_custom("👥", clientes_ativos, "Clientes Ativos")
        
    st.markdown('---')
    categorias = ['Automotivo', 'Residencial', 'Saúde', 'Vida', 'Empresarial']
    ativos = [100, 32, 231, 231, 231]
    risco = [54, 31, 42, 431, 543]

    df_card1 = pd.DataFrame({
        'Contratos Ativos': ativos,
        'Contratos em Risco': risco
    }, index=categorias)

    # Dados do card 2 (Faturamento Mensal)
    meses = list(range(1,13))
    faturamento = [200, 400, 300, 600, 700, 500, 800, 900, 700, 650, 600, 620]
    df_card2 = pd.DataFrame({'Mês': meses, 'Faturamento': faturamento}).set_index('Mês')

    # Layout com duas colunas
    card1, card2 = st.columns([2, 3])

    with card1:
        with st.container():
            st.markdown("### Contratos ativos X Contratos em Risco")
            st.bar_chart(df_card1)
            for categoria in categorias:
                st.write(f"**{categoria}**: {df_card1.loc[categoria, 'Contratos Ativos']} × {df_card1.loc[categoria, 'Contratos em Risco']}")

    # Card 2
    with card2:
        with st.container():
            st.markdown("### Faturamento Mensal")
            st.write("Faturamento baseado na filtragem escolhida")
            st.metric(label="Indicators", value=f"{df_card2['Faturamento'].sum():,.2f}", delta="-11.2% per year")
            st.line_chart(df_card2)

    col1, col2 = st.columns(2)
        
    col1.title("Clientes em Risco")
        
    if st.button("Exportar CSV"):
            st.download_button(
                label="Download CSV",
                data=df_predicoes.to_csv(index=False).encode('utf-8'),
                file_name='clientes_com_risco_cancelamento.csv',
                mime='text/csv'
            )
    st.dataframe(df_predicoes)
        

if __name__ == "__main__":
    render()
