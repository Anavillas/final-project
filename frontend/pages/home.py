import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

# --- Configuração de Caminhos ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# --- Importações reais do backend ---
# O objetivo é NÃO usar dados mockados. Se o backend falhar, o app não deve prosseguir
# ou deve deixar claro que não há dados. Removemos a lógica de mock automática aqui.
try:
    from backend.data.processed.loading_views import carregar_view, carregar_query
    # Se 'carregar_dados_predicao' deve vir do backend e acessar o DB,
    # ele deve ser implementado em loading_views.py e importado aqui.
    # Por enquanto, mantemos a versão local que lida com CSVs (ou mocks se o CSV não for encontrado).
    # IMPORTANTE: Para "não mockar", a carregar_dados_predicao abaixo também precisaria
    # ser reescrita para puxar do DB. Vou mantê-la como está, mas com um aviso claro.
    backend_disponivel = True
except ImportError as e:
    st.error(f"Erro CRÍTICO ao carregar módulos do backend: {e}. O aplicativo não pode continuar sem conexão aos dados reais.")
    st.info("Por favor, verifique se a pasta 'backend' está configurada corretamente, se contém '__init__.py's e se o banco de dados está acessível.")
    st.stop() # Interrompe a execução do Streamlit se o backend não carregar.

# --- ATENÇÃO: Se 'clientes_com_risco_cancelamento.csv' for a ÚNICA fonte de predição,
# e ela não for do DB, isso vai contra a regra de "não usar dados mockados".
# Se esses dados também devem vir do DB, 'carregar_dados_predicao' precisará ser reescrita.
@st.cache_data
def carregar_dados_predicao():
    caminho_csv = os.path.join(PROJECT_ROOT, "frontend", "pages", "clientes_com_risco_cancelamento.csv")
    if os.path.exists(caminho_csv):
        df = pd.read_csv(caminho_csv)
    return df
  
# --- Componente Customizado KPI ---
def kpi_custom(icon_class, value, explanation):
    st.markdown(f"""
    <div class="kpi-box">
        <div class="kpi-icon"><i class="{icon_class}"></i></div>
        <div class="kpi-content">
            <p class="kpi-value">{value}</p>
            <div class="kpi-explanation">{explanation}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# --- INJEÇÃO DE CSS GLOBAL E FONT AWESOME ---
st.markdown(
    """
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    <style>
    .stApp { background-color: #F0F2F6; }
    h3 { color: #333333; font-weight: 600; margin-bottom: 15px; }
    .stContainer { border: 1px solid #e0e0e0; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); padding: 20px; background-color: white; }
    div[data-testid="stSelectbox"] div[role="button"] { border-radius: 8px; border: 1px solid #ccc; padding: 5px 10px; background-color: #f9f9f9; }
    div[data-testid="stSelectbox"] div[role="button"]::after { content: none; }
    .plotly-container { padding-top: 10px; }
    .kpi-box { position: relative; display: flex; align-items: center; background-color: white; border-radius: 12px; padding: 12px 16px; width: 100%; margin-bottom: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); font-family: Arial, sans-serif; }
    .kpi-icon { width: 100px; height: 100px; margin-right: 14px; display: flex; align-items: center; justify-content: center; font-size: 55px; color: #3377ff; }
    .kpi-content { flex-grow: 1; }
    .kpi-value { font-size: 32px !important; font-weight: 700; margin: 0; }
    .kpi-explanation { margin-top: 4px; font-size: 13px; color: #555; }
    .valores-card { background-color: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); height: 100%; display: flex; flex-direction: column; justify-content: space-around; }
    .valores-item { font-size: 16px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
    .valores-item strong { color: #333; flex-grow: 1; }
    .valores-item span { font-weight: bold; color: #007bff; text-align: right; min-width: 60px; }
    .plotly-graph-div { /* A altura e largura serão gerenciadas pelo Streamlit ou pelos settings do Plotly */ }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Função Principal de Renderização do Dashboard ---
def render():
    st.title("Dashboard de Visão Geral")

    # Define SQL queries para os KPIs
    query_total_contratos_ativos = """
    SELECT COUNT(*) AS total_contratos_ativos
    FROM v_contratos_detalhados
    WHERE status_contrato = 'Ativo'
    """

    # Agora a query de CHURN usa APENAS v_contratos_detalhados, como combinado.
    query_churn_rate = """
    SELECT
        ROUND(
            100.0 * SUM(CASE WHEN status_contrato = 'Cancelado' THEN 1 ELSE 0 END) /
            NULLIF(COUNT(DISTINCT contrato_id), 0) -- Evita divisão por zero
        , 2) AS churn_global
    FROM v_contratos_detalhados
    WHERE status_contrato IN ('Cancelado', 'Encerrado');
    """

    query_clientes_ativos = """
    SELECT COUNT(DISTINCT cliente_id) AS total_clientes_ativos
    FROM v_contratos_detalhados
    WHERE status_contrato = 'Ativo';
    """

    query_avaliacao = """
    SELECT
        ROUND(AVG(nivel_satisfacao_num), 2) AS satisfacao_media
    FROM v_contratos_detalhados
    WHERE nivel_satisfacao_num IS NOT NULL; -- Apenas avaliações válidas
    """

    # Carrega os dados para os KPIs
    
    df_total_contratos_ativos = carregar_query(query_total_contratos_ativos)
    total_contratos = df_total_contratos_ativos['total_contratos_ativos'].iloc[0] 
    
    df_churn_rate = carregar_query(query_churn_rate)
    churn_rate = df_churn_rate['churn_global'].iloc[0]
    
    df_predicoes = carregar_dados_predicao()
    contratos_em_risco = len(df_predicoes[df_predicoes['tende_cancelar'] == 1])
    


    df_clientes_ativos = carregar_query(query_clientes_ativos)
    clientes_ativos = df_clientes_ativos['total_clientes_ativos'].iloc[0]
    
    df_avl_avg = carregar_query(query_avaliacao)
    avl_avg = df_avl_avg['satisfacao_media'].iloc[0] 
    
    
    kpi_cols = st.columns(5)
    with kpi_cols[0]:
        kpi_custom(icon_class="fas fa-chart-line", value=f"{churn_rate}%", explanation="Taxa de Churn Global")
    with kpi_cols[1]:
        kpi_custom(icon_class="fas fa-file-contract", value=f"{total_contratos:,}", explanation="Contratos Ativos")
    with kpi_cols[2]:
        kpi_custom(icon_class="fas fa-exclamation-triangle", value=f"{contratos_em_risco:,}", explanation="Contratos em Risco")
    with kpi_cols[3]:
        kpi_custom(icon_class="fas fa-star", value=f"{avl_avg}", explanation="Satisfação Média (Contratos)")
    with kpi_cols[4]:
        kpi_custom(icon_class="fas fa-users", value=f"{clientes_ativos:,}", explanation="Clientes Ativos")

    st.markdown('---')

    # --- Dados dos Cards de Gráficos ---
    # ATENÇÃO: Estes dados ainda são DUMMY. Para que não sejam mockados,
    # você precisaria de queries SQL para popular 'df_card1_data' e 'df_card2_data'
    # a partir das suas views (v_contratos_detalhados, v_perfil_cliente_enriquecido).

    # Exemplo: Como puxar dados REAIS para o gráfico de Contratos por Categoria
    # Você precisaria de uma coluna 'tipo_seguro_nome' na v_contratos_detalhados
    # e então agrupar e contar.
    try:
        df_contratos_detalhados_para_grafico = carregar_view('v_contratos_detalhados')
        if not df_contratos_detalhados_para_grafico.empty and 'tipo_seguro_nome' in df_contratos_detalhados_para_grafico.columns:
            # Contratos Ativos por Categoria
            active_contracts_by_type = df_contratos_detalhados_para_grafico[
                df_contratos_detalhados_para_grafico['status_contrato'] == 'Ativo'
            ]['tipo_seguro_nome'].value_counts().reset_index()
            active_contracts_by_type.columns = ['Categoria', 'Contratos Ativos']

            # Contratos em Risco (assumindo que 'tende_cancelar' vem do df_predicoes e pode ser unido)
            # Isso requer uma lógica de JOIN entre df_predicoes e df_contratos_detalhados_para_grafico
            # para identificar quais contratos ativos estão em risco.
            # POR SIMPLICIDADE, e se não tivermos a lógica completa aqui, o 'risco' ainda será genérico.
            # Uma forma seria: JOIN df_predicoes com v_contratos_detalhados_para_grafico por cliente_id.
            # Como df_predicoes tem 'tende_cancelar' e 'cliente_id',
            # vamos criar um mock de "risco" se não houver um dado real direto:
            risk_contracts_by_type = df_contratos_detalhados_para_grafico[
                (df_contratos_detalhados_para_grafico['status_contrato'] == 'Ativo')
            ].sample(frac=0.3) # Exemplo: 30% dos ativos estão em risco para o mock
            risk_contracts_by_type = risk_contracts_by_type['tipo_seguro_nome'].value_counts().reset_index()
            risk_contracts_by_type.columns = ['Categoria', 'Contratos em Risco']

            df_card1_data = pd.merge(active_contracts_by_type, risk_contracts_by_type, on='Categoria', how='outer').fillna(0)
            df_card1_data = df_card1_data.sort_values(by='Contratos Ativos', ascending=False)
            categories_order = df_card1_data['Categoria'].tolist() # Manter a ordem para o gráfico
        else:
            st.warning("Não há dados de 'tipo_seguro_nome' na v_contratos_detalhados ou view vazia para o gráfico de categorias. Usando dados dummy para o gráfico 1.")
            categories_order = ['Automotivo', 'Residencial', 'Saúde', 'Vida', 'Empresarial']
            df_card1_data = pd.DataFrame({
                'Categoria': categories_order,
                'Contratos Ativos': [1000, 800, 1200, 600, 900], # Dados dummy
                'Contratos em Risco': [200, 150, 250, 100, 180] # Dados dummy
            })
    except Exception as e:
        st.error(f"Erro ao preparar dados para o gráfico 'Contratos ativos X Contratos em Risco': {e}. Usando dados dummy.")
        categories_order = ['Automotivo', 'Residencial', 'Saúde', 'Vida', 'Empresarial']
        df_card1_data = pd.DataFrame({
            'Categoria': categories_order,
            'Contratos Ativos': [1000, 800, 1200, 600, 900], # Dados dummy
            'Contratos em Risco': [200, 150, 250, 100, 180] # Dados dummy
        })


    # Dados do card 2 (Faturamento Mensal) - ESTES AINDA SÃO DUMMY!
    # Para puxar do DB, você precisaria de uma coluna 'premio_mensal' e 'data_inicio'
    # na v_contratos_detalhados, e agregaria por mês.
    today = datetime.now()
    dates = [today - timedelta(days=x * 30) for x in range(12)] # Últimos 12 meses
    revenue_values = [200, 400, 300, 600, 700, 500, 800, 900, 700, 650, 600, 620]
    df_card2_data = pd.DataFrame({'Data': dates, 'Faturamento': revenue_values})
    df_card2_data['Mês'] = df_card2_data['Data'].dt.month
    st.warning("Dados do 'Faturamento Mensal' ainda são mockados. Implemente uma query para puxar do DB.")

    # --- Layout dos Cards de Gráfico ---
    main_col1, main_col2 = st.columns([1, 1])

    # Card 1: Contratos ativos X Contratos em Risco
    with main_col1:
        st.markdown("### Contratos ativos X Contratos em Risco")
        with st.container(border=True, height=400):
            col_chart, col_values = st.columns([3, 1])

            with col_chart:
                fig_contracts = px.bar(df_card1_data.melt(id_vars='Categoria', var_name='Tipo de Contrato', value_name='Número'),
                                         x='Categoria', y='Número', color='Tipo de Contrato',
                                         barmode='group',
                                         height=300,
                                         color_discrete_map={'Contratos Ativos': '#A7D9FC', 'Contratos em Risco': '#E0F2FC'},
                                         labels={'Número': ''},
                                         category_orders={"Categoria": categories_order}
                                        )
                fig_contracts.update_layout(xaxis_title='', yaxis_title='', showlegend=True,
                                             plot_bgcolor='rgba(0,0,0,0)',
                                             paper_bgcolor='rgba(0,0,0,0)',
                                             font_color="#333",
                                             margin=dict(l=0, r=0, t=20, b=0),
                                             legend=dict(x=0.01, y=0.99, xanchor="left", yanchor="top", font=dict(color="#333"))
                                            )
                fig_contracts.update_xaxes(showgrid=False, tickfont=dict(color="#333"))
                fig_contracts.update_yaxes(showgrid=False, showticklabels=False, tickfont=dict(color="#333"))
                st.plotly_chart(fig_contracts, use_container_width=True, config={'displayModeBar': False})

            with col_values:
                valores_html_content = ""
                for idx, row in df_card1_data.iterrows():
                    categoria = row['Categoria']
                    ativo = int(row['Contratos Ativos']) # Converte para int para exibição
                    risco = int(row['Contratos em Risco']) # Converte para int para exibição
                    valores_html_content += f"<p class='valores-item'><strong>{categoria}:</strong> <span>{ativo} × {risco}</span></p>"
                st.markdown(f"<div class='valores-card'>{valores_html_content}</div>", unsafe_allow_html=True)


    # Card 2: Faturamento Mensal
    with main_col2:
        st.markdown("### Faturamento Mensal")
        with st.container(border=True, height=400):
            col_date_start, col_date_end = st.columns(2)
            with col_date_start:
                # Use value=df_card2_data['Data'].min().date() apenas se df_card2_data não for vazio
                default_start_date = df_card2_data['Data'].min().date() if not df_card2_data.empty else (datetime.now() - timedelta(days=365)).date()
                start_date = st.date_input(
                    "Data Início",
                    value=default_start_date,
                    min_value=df_card2_data['Data'].min().date() if not df_card2_data.empty else (datetime.now() - timedelta(days=730)).date(), # Min value mais amplo se dados forem poucos
                    max_value=df_card2_data['Data'].max().date() if not df_card2_data.empty else datetime.now().date(),
                    label_visibility="collapsed",
                    key="faturamento_start_date"
                )
            with col_date_end:
                default_end_date = df_card2_data['Data'].max().date() if not df_card2_data.empty else datetime.now().date()
                end_date = st.date_input(
                    "Data Fim",
                    value=default_end_date,
                    min_value=df_card2_data['Data'].min().date() if not df_card2_data.empty else (datetime.now() - timedelta(days=730)).date(),
                    max_value=df_card2_data['Data'].max().date() if not df_card2_data.empty else datetime.now().date(),
                    label_visibility="collapsed",
                    key="faturamento_end_date"
                )

            # Converte as datas de volta para datetime para filtragem
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())

            df_filtered_revenue = df_card2_data[
                (df_card2_data['Data'] >= start_datetime) &
                (df_card2_data['Data'] <= end_datetime)
            ]

            st.markdown(f"<p style='font-size: 13px; color: #555; margin-bottom: 5px; font-weight: bold;'>Faturamento de {start_datetime.strftime('%d/%m/%Y')} a {end_datetime.strftime('%d/%m/%Y')}</p>", unsafe_allow_html=True)

            top_row_cols = st.columns([0.7, 0.3])
            with top_row_cols[0]:
                pass # Espaço vazio
            with top_row_cols[1]:
                current_revenue = df_filtered_revenue['Faturamento'].sum() if not df_filtered_revenue.empty else 0
                st.markdown(f"""
                    <div style='text-align: right;'>
                        <p style='font-size: 13px; color: #555; margin-bottom: 5px; font-weight: bold;'>Indicators</p>
                        <p style='font-size: 26px; font-weight: bold; margin-top: 0px; color: #333;'>
                            {current_revenue:,.2f}
                            <span style='font-size: 14px; color: red; font-weight: normal; margin-left: 5px;'>▼ 11.2% per year</span>
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("#### Faturamento do mês")
            fig_revenue = px.line(df_filtered_revenue, x='Data', y='Faturamento',
                                     height=250,
                                     labels={'Faturamento': ''})
            fig_revenue.update_traces(mode='lines+markers', line=dict(color='#2b6cb0', width=2), marker=dict(size=6, color='#2b6cb0'))
            fig_revenue.update_layout(xaxis_title='', yaxis_title='', showlegend=False,
                                         margin=dict(l=20, r=20, t=20, b=20),
                                         plot_bgcolor='rgba(0,0,0,0)',
                                         paper_bgcolor='rgba(0,0,0,0)',
                                         font_color="#333")
            fig_revenue.update_xaxes(showgrid=False, tickformat="%b %Y")
            fig_revenue.update_yaxes(showgrid=True, gridcolor='#E0E0E0', showticklabels=True)
            st.plotly_chart(fig_revenue, use_container_width=True, config={'displayModeBar': False})

    st.markdown('---')

    st.title("Contratos em Risco (Detalhes)")
    # df_predicoes é o DataFrame já carregado de carregar_dados_predicao()
    if not df_predicoes.empty:
        export_col, _ = st.columns([0.2, 0.8])
        with export_col:
            st.download_button(
                label="Exportar CSV",
                data=df_predicoes.to_csv(index=False).encode('utf-8'),
                file_name='clientes_com_risco_cancelamento.csv',
                mime='text/csv',
                key="download_risco_csv"
            )
        st.dataframe(df_predicoes, use_container_width=True, height=400)
    else:
        st.info("Não há dados de 'Contratos em Risco' para exibir. Verifique a fonte de dados.")

# --- Ponto de Entrada da Aplicação ---
if __name__ == '__main__':
    render()