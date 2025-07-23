import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

# --- Importação da função de carregamento de CSS global ---

# --- Configuração de Caminhos ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# --- Importações reais do backend ---

from backend.data.processed.loading_views import carregar_view, carregar_query
from frontend.styles.css_loader import load_global_css # Importante!
from frontend.utils.components import kpi_custom

# --- Função para carregar dados de predição (assume que o CSV existe e é válido) ---
@st.cache_data
def carregar_dados_predicao():
    caminho_csv = os.path.join(PROJECT_ROOT, "frontend", "pages", "clientes_com_risco_cancelamento.csv")
    
    if not os.path.exists(caminho_csv):
        st.error(f"Erro: Arquivo CSV de predição não encontrado em: {caminho_csv}. Sem este arquivo, os dados de predição não podem ser carregados.")
        return pd.DataFrame() # Retorna DataFrame vazio se o arquivo não existir.

    df = pd.read_csv(caminho_csv)
    # Validar a presença das colunas críticas do CSV
    required_cols_csv = ['id_cliente', 'tende_cancelar', 'tipo_seguro']
    if not all(col in df.columns for col in required_cols_csv):
        st.error(f"O arquivo CSV '{os.path.basename(caminho_csv)}' não contém todas as colunas necessárias para o dashboard: {', '.join(required_cols_csv)}. Verifique o arquivo.")
        return pd.DataFrame() # Retorna DataFrame vazio se colunas essenciais estiverem faltando.
    
    # Renomear colunas para consistência com o restante do código (se necessário para joins ou lógica)
    df.rename(columns={'id_cliente': 'cliente_id', 'tipo_seguro': 'tipo_seguro_nome'}, inplace=True)
    
    # Certificar que 'tende_cancelar' é numérica (0 ou 1)
    if 'tende_cancelar' in df.columns:
        df['tende_cancelar'] = pd.to_numeric(df['tende_cancelar'], errors='coerce').fillna(0).astype(int)
    
    # Adicionar 'prob_cancelamento' se não existir (para evitar erro no display_df_tab se o CSV não tiver essa coluna)
    # No seu CSV, você tem 'prob_cancelamento', mas é bom garantir.
    if 'prob_cancelamento' not in df.columns:
        df['prob_cancelamento'] = np.nan # Ou um valor padrão razoável, se souber
        st.warning("Coluna 'prob_cancelamento' não encontrada no CSV. Exibindo como NaN.")

    return df


# --- Componente Customizado KPI ---



# --- ATENÇÃO: ESTE BLOCO st.markdown FOI REMOVIDO! ---
# O CSS global agora será carregado pela função load_global_css().


# --- Função Principal de Renderização do Dashboard ---
def render():
    # --- CHAME A FUNÇÃO PARA CARREGAR O CSS GLOBAL AQUI ---
    load_global_css()

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

    # Carrega os dados para os KPIs - Adicionado mais checagens para robustez
    df_total_contratos_ativos = carregar_query(query_total_contratos_ativos)
    total_contratos = df_total_contratos_ativos['total_contratos_ativos'].iloc[0] if not df_total_contratos_ativos.empty else 0

    df_churn_rate = carregar_query(query_churn_rate)
    churn_rate = df_churn_rate['churn_global'].iloc[0] if not df_churn_rate.empty else 0.0

    df_predicoes = carregar_dados_predicao()
    # KPI 'Contratos em Risco' - Conta o número de contratos previstos como em risco diretamente de df_predicoes
    contratos_em_risco = len(df_predicoes[df_predicoes['tende_cancelar'] == 1]) if not df_predicoes.empty else 0

    df_clientes_ativos = carregar_query(query_clientes_ativos)
    clientes_ativos = df_clientes_ativos['total_clientes_ativos'].iloc[0] if not df_clientes_ativos.empty else 0

    df_avl_avg = carregar_query(query_avaliacao)
    avl_avg = df_avl_avg['satisfacao_media'].iloc[0] if not df_avl_avg.empty else 0.0

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
    ]['tipo_seguro_nome'].value_counts().reset_index() if not df_contratos_detalhados_para_grafico.empty else pd.DataFrame(columns=['tipo_seguro_nome', 'count'])
    active_contracts_by_type.columns = ['Categoria', 'Contratos Ativos']

    # Contratos em Risco por Categoria - OBTIDOS DIRETAMENTE DE DF_PREDICOES (DATASET DE CONTRATOS)
    risky_contracts_from_predicoes = df_predicoes[df_predicoes['tende_cancelar'] == 1] if not df_predicoes.empty else pd.DataFrame()
    risk_contracts_by_type = risky_contracts_from_predicoes['tipo_seguro_nome'].value_counts().reset_index() if not risky_contracts_from_predicoes.empty else pd.DataFrame(columns=['tipo_seguro_nome', 'count'])
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
    df_faturamento_real['Data'] = pd.to_datetime(df_faturamento_real['Data']).dt.tz_localize(None) if not df_faturamento_real.empty else pd.Series(dtype='datetime64[ns]')


    # --- CRIANDO O CENÁRIO "SE TIVESSEM CANCELADO" NO PYTHON (AJUSTADO PARA df_predicoes sem contrato_id) ---
    df_contratos_detalhados_para_cenario = carregar_view('v_contratos_detalhados')
    if not df_contratos_detalhados_para_cenario.empty:
        df_contratos_detalhados_para_cenario['data_inicio'] = pd.to_datetime(df_contratos_detalhados_para_cenario['data_inicio']).dt.tz_localize(None)
        df_contratos_detalhados_para_cenario['data_fim'] = pd.to_datetime(df_contratos_detalhados_para_cenario['data_fim']).dt.tz_localize(None)

        # Renomear colunas em df_predicoes para facilitar o merge
        df_predicoes_para_merge = df_predicoes[['cliente_id', 'tipo_seguro_nome', 'tende_cancelar']].copy()
        
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
    else:
        contratos_com_predicao = pd.DataFrame()


    # Aviso sobre a limitação da estimativa (mantido)
    st.warning("Aviso: O cenário de faturamento por cancelamento previsto é uma estimativa. Devido à ausência de 'contrato_id' em 'df_predicoes', contratos são correspondidos por 'id_cliente' e 'tipo_seguro'. Se um cliente tem vários contratos do mesmo tipo, e um é previsto para cancelar, todos do mesmo tipo para aquele cliente serão considerados cancelados no cenário.")

    current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if not df_faturamento_real.empty:
        all_months_in_range = pd.date_range(start=df_faturamento_real['Data'].min(),
                                            end=df_faturamento_real['Data'].max(),
                                            freq='MS').tz_localize(None)
    else:
        # Se não houver dados, crie um range de um mês para evitar erro
        all_months_in_range = pd.date_range(start=current_month, end=current_month + timedelta(days=30), freq='MS').tz_localize(None)


    faturamento_cenario_list = []
    for month_start in all_months_in_range:
        month_end = month_start + pd.offsets.MonthEnd(0)
        
        # Garante que contratos_com_predicao não esteja vazio antes de filtrar
        if not contratos_com_predicao.empty:
            current_month_contracts_active = contratos_com_predicao[
                (contratos_com_predicao['data_inicio'] <= month_end) &
                (contratos_com_predicao['data_fim'] >= month_start) &
                (contratos_com_predicao['status_contrato'] == 'Ativo')
            ].copy()
        else:
            current_month_contracts_active = pd.DataFrame()

        faturamento_real_mes = current_month_contracts_active['premio_mensal'].sum() if not current_month_contracts_active.empty else 0

        faturamento_cenario_cancelamento_mes = 0
        if month_start >= current_month and not current_month_contracts_active.empty:
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
    if not df_card2_data.empty:
        df_card2_data['Data'] = pd.to_datetime(df_card2_data['Data']).dt.tz_localize(None)
        df_card2_data['Mês'] = df_card2_data['Data'].dt.month
    else:
        st.info("Não há dados para calcular o Faturamento Mensal. Gráfico não será exibido.")


    # --- Layout dos Cards de Gráfico ---
    main_col1, main_col2 = st.columns([1, 1])

    # Card 1: Contratos ativos X Contratos em Risco
    with main_col1:
        st.markdown("### Contratos ativos X Contratos em Risco")
        with st.container(border=True, height=400):
            col_chart, col_values = st.columns([3, 1])

            with col_chart:
                if not df_card1_data.empty:
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
                else:
                    st.info("Não há dados de contratos ativos ou em risco para exibir este gráfico.")

            with col_values:
                st.markdown(f"<div class='valores-card'>", unsafe_allow_html=True)
                if not df_card1_data.empty:
                    valores_html_content = ""
                    for idx, row in df_card1_data.iterrows():
                        categoria = row['Categoria']
                        ativo = int(row['Contratos Ativos'])
                        risco = int(row['Contratos em Risco'])
                        valores_html_content += f"<p class='valores-item'><strong>{categoria}:</strong> <span>{ativo} × {risco}</span></p>"
                    st.markdown(valores_html_content, unsafe_allow_html=True)
                else:
                    st.info("Nenhum detalhe de categoria disponível.")
                st.markdown(f"</div>", unsafe_allow_html=True)


    # Card 2: Faturamento Mensal
    with main_col2:
        st.markdown("### Faturamento Mensal")
        with st.container(border=True, height=400):
            col_date_start, col_date_end = st.columns(2)

            start_date_value = df_card2_data['Data'].min().date() if not df_card2_data.empty else datetime.now().date()
            end_date_value = df_card2_data['Data'].max().date() if not df_card2_data.empty else datetime.now().date() + timedelta(days=30)

            with col_date_start:
                start_date = st.date_input(
                    "Data Início",
                    value=start_date_value,
                    min_value=df_card2_data['Data'].min().date() if not df_card2_data.empty else datetime.now().date() - timedelta(days=365),
                    max_value=df_card2_data['Data'].max().date() if not df_card2_data.empty else datetime.now().date() + timedelta(days=365),
                    label_visibility="collapsed",
                    key="faturamento_start_date"
                )
            with col_date_end:
                end_date = st.date_input(
                    "Data Fim",
                    value=end_date_value,
                    min_value=df_card2_data['Data'].min().date() if not df_card2_data.empty else datetime.now().date() - timedelta(days=365),
                    max_value=df_card2_data['Data'].max().date() if not df_card2_data.empty else datetime.now().date() + timedelta(days=365),
                    label_visibility="collapsed",
                    key="faturamento_end_date"
                )

            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())

            df_filtered_revenue = df_card2_data[
                (df_card2_data['Data'] >= start_datetime) &
                (df_card2_data['Data'] <= end_datetime)
            ] if not df_card2_data.empty else pd.DataFrame(columns=['Data', 'Faturamento Real', 'Faturamento Cenário Cancelamento'])


            st.markdown(f"<p style='font-size: 13px; color: #555; margin-bottom: 5px; font-weight: bold;'>Faturamento de {start_datetime.strftime('%d/%m/%Y')} a {end_datetime.strftime('%d/%m/%Y')}</p>", unsafe_allow_html=True)

            # Usando st.columns para organizar os valores de faturamento
            top_row_cols = st.columns([0.7, 0.3]) # Proporção para alinhar com o gráfico
            with top_row_cols[0]:
                pass # Este espaço pode ser usado para um título menor ou para alinhar
            with top_row_cols[1]:
                current_revenue_real = df_filtered_revenue['Faturamento Real'].sum() if not df_filtered_revenue.empty else 0.0
                st.markdown(f"""
                    <div style='text-align: right;'>
                        <p style='font-size: 13px; color: #555; margin-bottom: 5px; font-weight: bold;'>Faturamento Real</p>
                        <p style='font-size: 26px; font-weight: bold; margin-top: 0px; color: #333;'>
                            R$ {current_revenue_real:,.2f}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                current_revenue_scenario = df_filtered_revenue['Faturamento Cenário Cancelamento'].sum() if not df_filtered_revenue.empty else 0.0
                st.markdown(f"""
                    <div style='text-align: right; margin-top: 10px;'>
                        <p style='font-size: 13px; color: #555; margin-bottom: 5px; font-weight: bold;'>Cenário de Cancelamento</p>
                        <p style='font-size: 26px; font-weight: bold; margin-top: 0px; color: red;'>
                            R$ {current_revenue_scenario:,.2f}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)


            st.markdown("#### Faturamento do mês")
            if not df_filtered_revenue.empty:
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
            else:
                st.info("Nenhum dado de faturamento disponível no período selecionado para exibir o gráfico.")

    st.markdown('---')

    st.title("Contratos em Risco (Detalhes)")
    export_col, _ = st.columns([0.2, 0.8])
    with export_col:
        # Verifica se df_predicoes não está vazio antes de tentar exportar
        if not df_predicoes.empty:
            st.download_button(
                label="Exportar CSV",
                data=df_predicoes.to_csv(index=False).encode('utf-8'),
                file_name='clientes_com_risco_cancelamento.csv',
                mime='text/csv',
                key="download_risco_csv"
            )
        else:
            st.info("Nenhum dado de predição para exportar.")

    if not df_predicoes.empty:
        # Colunas a serem exibidas na tabela
        cols_to_display = ['cliente_id', 'prob_cancelamento', 'tipo_seguro_nome', 'tende_cancelar']
        display_df = df_predicoes[cols_to_display].copy()
        
        # Formatar a probabilidade para percentual
        if 'prob_cancelamento' in display_df.columns:
            display_df['prob_cancelamento'] = display_df['prob_cancelamento'].apply(lambda x: f"{x:.2%}" if pd.notnull(x) else "N/A")
        
        # Renomear colunas para exibição amigável
        display_df.columns = ['ID Cliente', 'Prob. Cancelamento', 'Tipo de Seguro', 'Tende a Cancelar']

        st.dataframe(display_df, use_container_width=True, height=400)
    else:
        st.info("Nenhum dado de predição de risco disponível para exibir.")

# --- Ponto de Entrada da Aplicação ---
if __name__ == '__main__':
    render()