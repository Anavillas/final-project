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
# Se a importação falhar, o aplicativo irá parar, como você solicitou (sem mocks).
try:
    from backend.data.processed.loading_views import carregar_view, carregar_query
except ImportError as e:
    st.error(f"Erro CRÍTICO ao carregar módulos do backend: {e}. O aplicativo não pode continuar sem conexão aos dados reais.")
    st.info("Por favor, verifique se a pasta 'backend' está configurada corretamente, se contém '__init__.py's e se o banco de dados está acessível.")
    st.stop()

# --- Função para carregar dados de predição (assume que o CSV existe e é válido) ---
@st.cache_data
def carregar_dados_predicao():
    caminho_csv = os.path.join(PROJECT_ROOT, "frontend", "pages", "clientes_com_risco_cancelamento.csv")
    # Não há try-except ou verificação de existência/colunas aqui.
    # Se o CSV não existir ou não tiver as colunas esperadas, o erro será lançado diretamente.
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

    query_churn_rate = """
    SELECT
        ROUND(
            100.0 * SUM(CASE WHEN status_contrato = 'Cancelado' THEN 1 ELSE 0 END) /
            NULLIF(COUNT(DISTINCT contrato_id), 0)
        , 2) AS churn_global
    FROM v_contratos_detalhados
    WHERE status_contrato IN ('Ativo', 'Cancelado', 'Encerrado');
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
    WHERE nivel_satisfacao_num IS NOT NULL;
    """

    # Carrega os dados para os KPIs - Sem try-except ou verificações de empty DataFrame
    df_total_contratos_ativos = carregar_query(query_total_contratos_ativos)
    total_contratos = df_total_contratos_ativos['total_contratos_ativos'].iloc[0]

    df_churn_rate = carregar_query(query_churn_rate)
    churn_rate = df_churn_rate['churn_global'].iloc[0]

    df_predicoes = carregar_dados_predicao()
    # KPI 'Contratos em Risco' - Conta o número de contratos previstos como em risco diretamente de df_predicoes
    contratos_em_risco = len(df_predicoes[df_predicoes['tende_cancelar'] == 1])

    df_clientes_ativos = carregar_query(query_clientes_ativos)
    clientes_ativos = df_clientes_ativos['total_clientes_ativos'].iloc[0]

    df_avl_avg = carregar_query(query_avaliacao)
    avl_avg = df_avl_avg['satisfacao_media'].iloc[0]

    # Exibe os KPIs
    kpi_cols = st.columns(5)
    with kpi_cols[0]:
        kpi_custom(icon_class="fas fa-chart-line", value=f"{churn_rate}%", explanation="Taxa de Churn Global")
    with kpi_cols[1]:
        kpi_custom(icon_class="fas fa-file-contract", value=f"{total_contratos:,}", explanation="Contratos Ativos")
    with kpi_cols[2]:
        kpi_custom(icon_class="fas fa-exclamation-triangle", value=f"{contratos_em_risco:,}", explanation="Contratos em Risco (Modelo)")
    with kpi_cols[3]:
        kpi_custom(icon_class="fas fa-star", value=f"{avl_avg}", explanation="Satisfação Média (Contratos)")
    with kpi_cols[4]:
        kpi_custom(icon_class="fas fa-users", value=f"{clientes_ativos:,}", explanation="Clientes Ativos")

    st.markdown('---')

    # --- Dados dos Cards de Gráficos ---
    df_contratos_detalhados_para_grafico = carregar_view('v_contratos_detalhados')

    # Contratos Ativos por Categoria
    active_contracts_by_type = df_contratos_detalhados_para_grafico[
        df_contratos_detalhados_para_grafico['status_contrato'] == 'Ativo'
    ]['tipo_seguro_nome'].value_counts().reset_index()
    active_contracts_by_type.columns = ['Categoria', 'Contratos Ativos']

    # Contratos em Risco por Categoria - OBTIDOS DIRETAMENTE DE DF_PREDICOES (DATASET DE CONTRATOS)
    risky_contracts_from_predicoes = df_predicoes[df_predicoes['tende_cancelar'] == 1]
    risk_contracts_by_type = risky_contracts_from_predicoes['tipo_seguro'].value_counts().reset_index()
    risk_contracts_by_type.columns = ['Categoria', 'Contratos em Risco']

    # Unimos os dados de contratos ativos com os de contratos em risco
    df_card1_data = pd.merge(active_contracts_by_type, risk_contracts_by_type, on='Categoria', how='outer').fillna(0)
    df_card1_data = df_card1_data.sort_values(by='Contratos Ativos', ascending=False)
    categories_order = df_card1_data['Categoria'].tolist()

    # --- CARREGAMENTO PARA O CARD 2: FATURAMENTO MENSAL REAL E CENÁRIO DE CANCELAMENTO ---
    query_faturamento_mensal_real = """
    WITH meses_projetados AS (
        SELECT generate_series(
            DATE_TRUNC('month', MIN(data_inicio)),
            DATE_TRUNC('month', MAX(data_fim) + INTERVAL '1 year'), -- Projeção de 1 ano após o último fim de contrato
            '1 month'::interval
        ) AS mes_vigencia
        FROM v_contratos_detalhados
    ),
    faturamento_por_contrato_mes AS (
        SELECT
            c.contrato_id,
            c.premio_mensal,
            c.data_inicio,
            c.data_fim,
            mp.mes_vigencia
        FROM
            v_contratos_detalhados c
        JOIN
            meses_projetados mp ON mp.mes_vigencia >= DATE_TRUNC('month', c.data_inicio)
                               AND mp.mes_vigencia <= DATE_TRUNC('month', c.data_fim)
        WHERE
            c.status_contrato IN ('Ativo', 'Encerrado')
    )
    SELECT
        mes_vigencia AS "Data",
        SUM(premio_mensal) AS "Faturamento"
    FROM
        faturamento_por_contrato_mes
    GROUP BY
        mes_vigencia
    ORDER BY
        mes_vigencia;
    """

    df_faturamento_real = carregar_query(query_faturamento_mensal_real)
    df_faturamento_real['Data'] = pd.to_datetime(df_faturamento_real['Data']).dt.tz_localize(None)


    # --- CRIANDO O CENÁRIO "SE TIVESSEM CANCELADO" NO PYTHON (AJUSTADO PARA df_predicoes sem contrato_id) ---
    # --- CRIANDO O CENÁRIO "SE TIVESSEM CANCELADO" NO PYTHON (AJUSTADO PARA df_predicoes sem contrato_id) ---
    df_contratos_detalhados_para_cenario = carregar_view('v_contratos_detalhados')
    df_contratos_detalhados_para_cenario['data_inicio'] = pd.to_datetime(df_contratos_detalhados_para_cenario['data_inicio']).dt.tz_localize(None)
    df_contratos_detalhados_para_cenario['data_fim'] = pd.to_datetime(df_contratos_detalhados_para_cenario['data_fim']).dt.tz_localize(None)

    # Renomear colunas em df_predicoes para facilitar o merge
    df_predicoes_para_merge = df_predicoes[['id_cliente', 'tipo_seguro', 'tende_cancelar']].copy()
    df_predicoes_para_merge.rename(columns={'id_cliente': 'cliente_id', 'tipo_seguro': 'tipo_seguro_nome'}, inplace=True)

    # Criar um DataFrame simples com apenas os identificadores e a flag de cancelamento para merge
    contratos_previstos_para_cancelar_flags = df_predicoes_para_merge[df_predicoes_para_merge['tende_cancelar'] == 1].copy()
    contratos_previstos_para_cancelar_flags = contratos_previstos_para_cancelar_flags[['cliente_id', 'tipo_seguro_nome']]
    # Adiciona uma coluna auxiliar que será True para os contratos que tendem a cancelar
    contratos_previstos_para_cancelar_flags['previsto_para_cancelar_flag'] = True

    # Fazer um LEFT MERGE para adicionar essa flag aos seus contratos detalhados
    contratos_com_predicao = pd.merge(
        df_contratos_detalhados_para_cenario,
        contratos_previstos_para_cancelar_flags,
        on=['cliente_id', 'tipo_seguro_nome'],
        how='left'
    )

    # A coluna 'previsto_para_cancelar_flag' agora existe no df_contratos_com_predicao.
    # Ela será True se houve match, e NaN se não houve match.
    # Criar a coluna final 'is_predicted_to_cancel' preenchendo NaN com False.
    contratos_com_predicao['is_predicted_to_cancel'] = contratos_com_predicao['previsto_para_cancelar_flag'].fillna(False)

    # Remover a coluna auxiliar se não for mais necessária
    contratos_com_predicao.drop(columns=['previsto_para_cancelar_flag'], inplace=True)

    # Aviso sobre a limitação da estimativa (mantido)
    st.warning("Aviso: O cenário de faturamento por cancelamento previsto é uma estimativa. Devido à ausência de 'contrato_id' em 'df_predicoes', contratos são correspondidos por 'id_cliente' e 'tipo_seguro'. Se um cliente tem vários contratos do mesmo tipo, e um é previsto para cancelar, todos do mesmo tipo para aquele cliente serão considerados cancelados no cenário.")

    current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    all_months_in_range = pd.date_range(start=df_faturamento_real['Data'].min(),
                                        end=df_faturamento_real['Data'].max(),
                                        freq='MS').tz_localize(None)

    faturamento_cenario_list = []
    for month_start in all_months_in_range:
        month_end = month_start + pd.offsets.MonthEnd(0)
        
        current_month_contracts_active = contratos_com_predicao[
            (contratos_com_predicao['data_inicio'] <= month_end) &
            (contratos_com_predicao['data_fim'] >= month_start) &
            (contratos_com_predicao['status_contrato'] == 'Ativo')
        ].copy()

        faturamento_real_mes = current_month_contracts_active['premio_mensal'].sum()

        faturamento_cenario_cancelamento_mes = 0
        if month_start >= current_month:
            faturamento_cenario_cancelamento_mes = current_month_contracts_active[
                current_month_contracts_active['is_predicted_to_cancel'] == False
            ]['premio_mensal'].sum()
        else:
            faturamento_cenario_cancelamento_mes = faturamento_real_mes

        faturamento_cenario_list.append({
            'Data': month_start,
            'Faturamento Real': faturamento_real_mes,
            'Faturamento Cenário Cancelamento': faturamento_cenario_cancelamento_mes
        })

    df_card2_data = pd.DataFrame(faturamento_cenario_list)
    df_card2_data['Data'] = pd.to_datetime(df_card2_data['Data']).dt.tz_localize(None)
    df_card2_data['Mês'] = df_card2_data['Data'].dt.month

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
                                             legend=dict(x=0.01, y=0.99, xanchor="left", yanchor="top", font=dict(color="#333")))
                fig_contracts.update_xaxes(showgrid=False, tickfont=dict(color="#333"))
                fig_contracts.update_yaxes(showgrid=False, showticklabels=False, tickfont=dict(color="#333"))
                st.plotly_chart(fig_contracts, use_container_width=True, config={'displayModeBar': False})

            with col_values:
                valores_html_content = ""
                for idx, row in df_card1_data.iterrows():
                    categoria = row['Categoria']
                    ativo = int(row['Contratos Ativos'])
                    risco = int(row['Contratos em Risco'])
                    valores_html_content += f"<p class='valores-item'><strong>{categoria}:</strong> <span>{ativo} × {risco}</span></p>"
                st.markdown(f"<div class='valores-card'>{valores_html_content}</div>", unsafe_allow_html=True)


    # Card 2: Faturamento Mensal
    with main_col2:
        st.markdown("### Faturamento Mensal")
        with st.container(border=True, height=400):
            col_date_start, col_date_end = st.columns(2)

            start_date_value = df_card2_data['Data'].min().date()
            end_date_value = df_card2_data['Data'].max().date()

            with col_date_start:
                start_date = st.date_input(
                    "Data Início",
                    value=start_date_value,
                    min_value=df_card2_data['Data'].min().date(),
                    max_value=df_card2_data['Data'].max().date(),
                    label_visibility="collapsed",
                    key="faturamento_start_date"
                )
            with col_date_end:
                end_date = st.date_input(
                    "Data Fim",
                    value=end_date_value,
                    min_value=df_card2_data['Data'].min().date(),
                    max_value=df_card2_data['Data'].max().date(),
                    label_visibility="collapsed",
                    key="faturamento_end_date"
                )

            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())

            df_filtered_revenue = df_card2_data[
                (df_card2_data['Data'] >= start_datetime) &
                (df_card2_data['Data'] <= end_datetime)
            ]

            st.markdown(f"<p style='font-size: 13px; color: #555; margin-bottom: 5px; font-weight: bold;'>Faturamento de {start_datetime.strftime('%d/%m/%Y')} a {end_datetime.strftime('%d/%m/%Y')}</p>", unsafe_allow_html=True)

            top_row_cols = st.columns([0.7, 0.3])
            with top_row_cols[0]:
                pass
            with top_row_cols[1]:
                current_revenue_real = df_filtered_revenue['Faturamento Real'].sum()
                st.markdown(f"""
                    <div style='text-align: right;'>
                        <p style='font-size: 13px; color: #555; margin-bottom: 5px; font-weight: bold;'>Faturamento Real</p>
                        <p style='font-size: 26px; font-weight: bold; margin-top: 0px; color: #333;'>
                            {current_revenue_real:,.2f}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                current_revenue_scenario = df_filtered_revenue['Faturamento Cenário Cancelamento'].sum()
                st.markdown(f"""
                    <div style='text-align: right; margin-top: 10px;'>
                        <p style='font-size: 13px; color: #555; margin-bottom: 5px; font-weight: bold;'>Cenário de Cancelamento</p>
                        <p style='font-size: 26px; font-weight: bold; margin-top: 0px; color: red;'>
                            {current_revenue_scenario:,.2f}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)


            st.markdown("#### Faturamento do mês")
            df_plot = df_filtered_revenue.melt(id_vars='Data', value_vars=['Faturamento Real', 'Faturamento Cenário Cancelamento'],
                                                var_name='Tipo de Faturamento', value_name='Valor')

            fig_revenue = px.line(df_plot, x='Data', y='Valor', color='Tipo de Faturamento',
                                     height=250,
                                     labels={'Valor': 'Faturamento'})
            fig_revenue.update_traces(mode='lines+markers', line=dict(width=2), marker=dict(size=6))
            fig_revenue.update_layout(xaxis_title='', yaxis_title='', showlegend=True,
                                         margin=dict(l=20, r=20, t=20, b=20),
                                         plot_bgcolor='rgba(0,0,0,0)',
                                         paper_bgcolor='rgba(0,0,0,0)',
                                         font_color="#333",
                                         legend=dict(x=0.01, y=0.99, xanchor="left", yanchor="top", font=dict(color="#333")))
            fig_revenue.update_xaxes(showgrid=False, tickformat="%b %Y")
            fig_revenue.update_yaxes(showgrid=True, gridcolor='#E0E0E0', showticklabels=True)
            st.plotly_chart(fig_revenue, use_container_width=True, config={'displayModeBar': False})

    st.markdown('---')

    st.title("Contratos em Risco (Detalhes)")
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

# --- Ponto de Entrada da Aplicação ---
if __name__ == '__main__':
    render()