import sys
import os
from frontend.styles.css_loader import load_global_css # Importante!
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dateutil.relativedelta import relativedelta
import numpy as np
from datetime import datetime, timedelta

# --- Configuração de Caminhos ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# --- Importações reais do backend ---

from backend.data.processed.loading_views import carregar_view, carregar_query
from frontend.utils.components import kpi_custom


# --- Importação da função de carregamento de CSS global ---

# --- Função para carregar dados de predição (SÓ CSV, SEM GERAÇÃO DE MOCKS) ---
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
    
    return df

# --- Componente Customizado KPI ---



# --- ATENÇÃO: REMOVA O BLOCO st.markdown COM O CSS AQUI! ---
# O CSS será carregado pela função load_global_css() agora.
# st.markdown(""" ... CSS antigo ... """, unsafe_allow_html=True)


# --- Função para criar gráfico de barras de motivos de cancelamento ---
def create_cancellation_reasons_chart(df_cancellation):
    if df_cancellation.empty or 'motivo_cancelamento_nome' not in df_cancellation.columns:
        fig = go.Figure()
        fig.add_annotation(text="Nenhum dado de cancelamento disponível ou coluna 'motivo_cancelamento_nome' ausente.",
                           xref="paper", yref="paper", showarrow=False,
                           font=dict(size=14, color="gray"))
        fig.update_layout(height=250, margin=dict(l=10, r=10, t=50, b=10))
        return fig

    motivo_df = df_cancellation['motivo_cancelamento_nome'].value_counts().reset_index()
    motivo_df.columns = ['Motivo', 'Contagem']

    fig = px.bar(motivo_df, x="Contagem", y="Motivo", orientation="h",
                     title='Motivo de Cancelamento',
                     labels={'Contagem': 'Número de Cancelamentos', 'Motivo': 'Motivo'},
                     color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="", yaxis_title="", showlegend=False, height=250)
    return fig

# --- Função para criar gráfico de histograma de duração de contrato ---
def create_contract_duration_chart(df_detalhes):
    if df_detalhes.empty:
        fig = go.Figure()
        fig.add_annotation(text="Nenhum dado de duração de contrato disponível",
                           xref="paper", yref="paper", showarrow=False,
                           font=dict(size=16, color="gray"))
        fig.update_layout(height=250, margin=dict(l=10, r=10, t=50, b=10))
        return fig

    required_cols = ['data_fim', 'data_inicio']
    if not all(col in df_detalhes.columns for col in required_cols):
        fig = go.Figure()
        fig.add_annotation(text=f"Colunas necessárias para duração ({', '.join(required_cols)}) ausentes no df_detalhes.",
                           xref="paper", yref="paper", showarrow=False,
                           font=dict(size=14, color="gray"))
        fig.update_layout(height=250, margin=dict(l=10, r=10, t=50, b=10))
        return fig

    df_duracao = df_detalhes[df_detalhes['data_fim'].notnull() & df_detalhes['data_inicio'].notnull()].copy()
    if df_duracao.empty:
        fig = go.Figure()
        fig.add_annotation(text="Nenhum dado válido para cálculo de duração (datas nulas)",
                           xref="paper", yref="paper", showarrow=False,
                           font=dict(size=16, color="gray"))
        fig.update_layout(height=250, margin=dict(l=10, r=10, t=50, b=10))
        return fig

    df_duracao['data_fim'] = pd.to_datetime(df_duracao['data_fim'])
    df_duracao['data_inicio'] = pd.to_datetime(df_duracao['data_inicio'])

    df_duracao['duracao_meses'] = df_duracao.apply(
        lambda row: (relativedelta(row['data_fim'], row['data_inicio']).years * 12 +
                     relativedelta(row['data_fim'], row['data_inicio']).months), axis=1
    )

    fig = px.histogram(df_duracao, x="duracao_meses", nbins=10,
                         title='Melhor Duração de Contrato',
                         labels={'duracao_meses': 'Duração (Meses)', 'count': 'Número de Contratos'},
                         color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_layout(xaxis_title="", yaxis_title="", showlegend=False, height=250)
    return fig

# --- Nova Função para Gráfico de Transição de Contratos ---
def create_contract_transition_chart(df_all_detalhes, current_contract_type):
    if df_all_detalhes.empty or \
       not all(col in df_all_detalhes.columns for col in ['cliente_id', 'data_inicio', 'tipo_seguro_nome']):
        fig = go.Figure()
        fig.add_annotation(text="Dados insuficientes para o gráfico de transição de contratos.",
                           xref="paper", yref="paper", showarrow=False,
                           font=dict(size=14, color="gray"))
        fig.update_layout(height=350, margin=dict(l=10, r=10, t=50, b=10))
        return fig

    df_detalhes_copy = df_all_detalhes.copy()
    df_detalhes_copy['data_inicio'] = pd.to_datetime(df_detalhes_copy['data_inicio'])

    df_sorted = df_detalhes_copy.sort_values(by=['cliente_id', 'data_inicio'])

    transitions = []
    for client_id in df_sorted['cliente_id'].unique():
        client_contracts = df_sorted[df_sorted['cliente_id'] == client_id]
        if len(client_contracts) > 1:
            for i in range(len(client_contracts) - 1):
                from_type = client_contracts.iloc[i]['tipo_seguro_nome']
                to_type = client_contracts.iloc[i+1]['tipo_seguro_nome']
                if from_type == current_contract_type and from_type != to_type:
                    transitions.append({'From': from_type, 'To': to_type})

    if not transitions:
        fig = go.Figure()
        fig.add_annotation(text=f"Nenhuma transição de '{current_contract_type}' para outros tipos de contrato encontrada.",
                           xref="paper", yref="paper", showarrow=False,
                           font=dict(size=14, color="gray"))
        fig.update_layout(height=350, margin=dict(l=10, r=10, t=50, b=10))
        return fig

    df_transitions = pd.DataFrame(transitions)
    
    # Count transitions
    transition_counts = df_transitions.groupby(['From', 'To']).size().reset_index(name='Count')

    # Prepare data for Sankey
    all_nodes = pd.concat([transition_counts['From'], transition_counts['To']]).unique()
    label_map = {label: i for i, label in enumerate(all_nodes)}

    source = [label_map[s] for s in transition_counts['From']]
    target = [label_map[t] for t in transition_counts['To']]
    value = transition_counts['Count']

    # Create Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=list(all_nodes),
            color="#3377ff"
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color="rgba(51, 119, 255, 0.4)"
        )
    )])

    fig.update_layout(
        title_text=f"Fluxo de Troca de Contrato a partir de '{current_contract_type}'",
        font_size=10,
        height=350,
        margin=dict(l=10, r=10, t=50, b=10)
    )
    return fig


def render():
    st.title("Detalhes por Tipo de Contrato") # Título da página de Planos

    # --- CHAME A FUNÇÃO PARA CARREGAR O CSS GLOBAL AQUI ---
    load_global_css()

    # --- BUSCAR TIPOS DE SEGURO PARA AS ABAS ---
    tipos_df = carregar_query("""
        SELECT DISTINCT tipo_seguro_nome
        FROM v_contratos_detalhados
        ORDER BY tipo_seguro_nome;
    """)
    
    if tipos_df.empty:
        st.warning("Não foi possível carregar os tipos de seguro do banco de dados. Verifique a conexão e os dados em 'v_contratos_detalhados'.")
        st.info("A aplicação não pode exibir detalhes por tipo de contrato sem dados de tipos de seguro.")
        return # Sai da função render se não houver tipos para exibir.
    
    tab_names = tipos_df['tipo_seguro_nome'].tolist()

    tabs = st.tabs(tab_names)

    # Carrega TODOS os dados detalhados de contratos UMA VEZ para o gráfico de transição.
    df_all_detalhes_for_transitions = carregar_query("""
        SELECT cliente_id, data_inicio, tipo_seguro_nome
        FROM v_contratos_detalhados;
    """)
    
    # Carrega TODOS os dados de predição de risco UMA VEZ. Será filtrado por aba.
    df_predicoes_global = carregar_dados_predicao()


    for i, tab in enumerate(tabs):
        with tab:
            contract_type = tab_names[i]
            st.markdown(f"## Visão Geral - {contract_type}")
            # --- CARREGAMENTO DE DADOS ESPECÍFICOS DA ABA ---
            where_clause = f"WHERE tipo_seguro_nome = '{contract_type}'"

            # Queries para KPIs e gráficos específicos da aba
            query_contratos_ativos_tab = f"""
            SELECT COUNT(*) AS total_contratos_ativos
            FROM v_contratos_detalhados
            {where_clause} AND status_contrato = 'Ativo';
            """
            query_clientes_ativos_tab = f"""
            SELECT COUNT(DISTINCT cliente_id) AS total_clientes_ativos
            FROM v_contratos_detalhados
            {where_clause} AND status_contrato = 'Ativo';
            """
            query_faturamento_tab = f"""
            SELECT COALESCE(SUM(premio_mensal), 0) AS faturamento_total
            FROM v_contratos_detalhados
            {where_clause} AND status_contrato = 'Ativo';
            """
            query_churn_tab_calc = f"""
            SELECT
                CAST(COUNT(CASE WHEN status_contrato = 'Cancelado' THEN 1 ELSE NULL END) AS REAL) * 100 /
                NULLIF(COUNT(CASE WHEN status_contrato IN ('Ativo', 'Cancelado', 'Encerrado') THEN 1 ELSE NULL END), 0) AS churn_rate
            FROM v_contratos_detalhados
            {where_clause};
            """
            query_satisfacao_tab = f"""
            SELECT COALESCE(ROUND(AVG(nivel_satisfacao_num), 2), 0) AS satisfacao_media
            FROM v_contratos_detalhados
            {where_clause} AND nivel_satisfacao_num IS NOT NULL AND nivel_satisfacao_num > 0;
            """

            # Carrega DataFrames para a aba atual
            df_detalhes_tab = carregar_query(f"SELECT * FROM v_contratos_detalhados {where_clause};")
            df_churn_reasons_tab = carregar_query(f"SELECT * FROM v_analise_churn {where_clause};")
            
            # Filtra os dados de predição global para o tipo de contrato atual da aba
            # Usa 'tende_cancelar' e 'tipo_seguro_nome' (que é o 'tipo_seguro' renomeado do CSV)
            df_predicoes_filtered_tab = df_predicoes_global[df_predicoes_global['tipo_seguro_nome'] == contract_type].copy() if not df_predicoes_global.empty else pd.DataFrame()


            # --- Calcular KPIs Específicos da Aba ---
            # Uso de .iloc[0] após checar se não está vazio para segurança
            contratos_ativos_tab = carregar_query(query_contratos_ativos_tab)['total_contratos_ativos'].iloc[0] if not carregar_query(query_contratos_ativos_tab).empty else 0
            clientes_ativos_tab = carregar_query(query_clientes_ativos_tab)['total_clientes_ativos'].iloc[0] if not carregar_query(query_clientes_ativos_tab).empty else 0
            faturamento_tab = carregar_query(query_faturamento_tab)['faturamento_total'].iloc[0] if not carregar_query(query_faturamento_tab).empty else 0.0
            churn_rate_tab = carregar_query(query_churn_tab_calc)['churn_rate'].iloc[0] if not carregar_query(query_churn_tab_calc).empty else 0.0
            satisfacao_media_tab = carregar_query(query_satisfacao_tab)['satisfacao_media'].iloc[0] if not carregar_query(query_satisfacao_tab).empty else 0.0
            
            # KPI de Clientes em Risco para a aba atual, usando 'tende_cancelar' do CSV
            # O status_risco não pode ser usado sem a coluna no CSV, então focamos em 'tende_cancelar'
            at_risk_clients_tab = df_predicoes_filtered_tab[df_predicoes_filtered_tab['tende_cancelar'] == 1]['cliente_id'].nunique() if not df_predicoes_filtered_tab.empty else 0


            kpi_cols_tab = st.columns(5)
            with kpi_cols_tab[0]:
                kpi_custom(icon_class="fas fa-chart-line", value=f"{churn_rate_tab:.1f}%", explanation="% Churn")
            with kpi_cols_tab[1]:
                kpi_custom(icon_class="fas fa-file-contract", value=f"{contratos_ativos_tab:,}", explanation="Contratos Ativos")
            with kpi_cols_tab[2]:
                kpi_custom(icon_class="fas fa-user-times", value=f"{at_risk_clients_tab:,}", explanation="Clientes em Risco")
            with kpi_cols_tab[3]:
                kpi_custom(icon_class="fas fa-star", value=f"{satisfacao_media_tab:.1f}", explanation="Satisfação Média")
            with kpi_cols_tab[4]:
                kpi_custom(icon_class="fas fa-money-check", value=f"R$ {faturamento_tab:,.2f}", explanation="Faturamento Contrato")

            st.markdown("---")

            # Gráficos (Tab-specific)
            chart_cols_tab = st.columns(2)

            with chart_cols_tab[0]:
                with st.container(border=True):
                    st.write("### Motivo de Cancelamento")
                    st.plotly_chart(create_cancellation_reasons_chart(df_churn_reasons_tab), use_container_width=True, key=f"churn_chart_{contract_type}")

            with chart_cols_tab[1]:
                with st.container(border=True):
                    st.write("### Melhor Duração de Contrato")
                    st.plotly_chart(create_contract_duration_chart(df_detalhes_tab), use_container_width=True, key=f"duration_chart_{contract_type}")

            st.markdown("---")

            # Gráfico de Transição de Contratos (Tab-specific)
            st.markdown("### Transição de Contratos por Cliente")
            with st.container(border=True):
                st.plotly_chart(create_contract_transition_chart(df_all_detalhes_for_transitions, contract_type), use_container_width=True, key=f"transition_chart_{contract_type}")

            st.markdown("---")

            # Contratos em Risco (Table - Tab-specific, using filtered df_predicoes_global)
            bottom_cols_tab = st.columns([0.7, 0.3])
            with bottom_cols_tab[0]:
                st.container(border=True).write(f"### Clientes em Risco para {contract_type}")
                # Filtra apenas clientes que tendem a cancelar
                df_risk_display_tab = df_predicoes_filtered_tab[df_predicoes_filtered_tab['tende_cancelar'] == 1].copy()
                
                # As colunas agora são 'cliente_id' e 'prob_cancelamento', pois 'cliente_nome', 'status_risco', 'data_fim_contrato_previsao' não estão no CSV.
                expected_risk_cols = ['cliente_id', 'prob_cancelamento'] # Ajustado para as colunas do CSV
                
                if not df_risk_display_tab.empty and all(col in df_risk_display_tab.columns for col in expected_risk_cols):
                    display_df_tab = df_risk_display_tab[expected_risk_cols]
                    display_df_tab.columns = ['ID Cliente', 'Prob. Cancelamento'] # Nomes mais amigáveis
                    
                    # Formatar a probabilidade para percentual
                    display_df_tab['Prob. Cancelamento'] = display_df_tab['Prob. Cancelamento'].apply(lambda x: f"{x:.2%}")

                    st.dataframe(display_df_tab, use_container_width=True, hide_index=True, key=f"risk_clients_table_{contract_type}")
                else:
                    st.info(f"Nenhum cliente em risco encontrado para {contract_type} ou colunas necessárias ausentes no CSV.")
                    st.dataframe(pd.DataFrame(), use_container_width=True, hide_index=True, key=f"risk_clients_table_empty_{contract_type}")


            with bottom_cols_tab[1]:
                # --- Preenchimento do card 'Situação Contrato' ---
                # Agora, contamos clientes que 'tende_cancelar' sem um status_risco
                clients_predicted_to_cancel_count = 0
                # O KPI "Contratos a Terminar" foi removido pois 'data_fim_contrato_previsao' não está no CSV.

                if not df_predicoes_filtered_tab.empty:
                    clients_predicted_to_cancel_count = df_predicoes_filtered_tab[df_predicoes_filtered_tab['tende_cancelar'] == 1].shape[0]

                st.container(border=True).write("### Situação Contrato")
                st.markdown(f"""
                <div class="valores-card">
                    <div class="valores-item"><strong>Clientes a Cancelar (Previsto)</strong> <span>{clients_predicted_to_cancel_count}</span></div>
                    <div class="valores-item"><strong>Contratos a Terminar</strong> <span>N/A</span></div>
                    <div class="valores-item"><strong>Ver Detalhes Risco</strong> <span><i class="fas fa-arrow-right"></i></span></div>
                </div>
                """, unsafe_allow_html=True)


if __name__ == '__main__':
    render()