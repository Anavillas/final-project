import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dateutil.relativedelta import relativedelta
import numpy as np
from datetime import datetime, timedelta
import re # Necessário para o regex na função mock carregar_query

# --- Configuração de Caminhos ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# --- Importações reais do backend (com mocks para fallback, conforme seu último código) ---
try:
    from backend.data.processed.loading_views import carregar_view, carregar_query
except ImportError as e:
    st.error(f"Erro ao carregar módulos do backend: {e}. Verifique se a pasta 'backend' está configurada corretamente e se contém '__init__.py's.")
    st.info("O aplicativo será executado com dados mockados para demonstração.")

    # --- Mocks para funções do backend se a importação falhar ---
    @st.cache_data
    def carregar_view(view_name):
        st.warning(f"Dummy carregar_view called for {view_name}. No data loaded.")
        if view_name == 'v_perfil_cliente_enriquecido':
            return pd.DataFrame({
                'cliente_id': range(1, 101),
                'nome': [f'Cliente {i}' for i in range(1, 101)],
                'genero': np.random.choice(['M', 'F', 'O'], 100),
                'idade_atual': np.random.randint(18, 70, 100),
                'nivel_educacional': np.random.choice(['Fundamental', 'Médio', 'Superior', 'Pós-graduação'], 100),
                'qtd_dependente': np.random.randint(0, 5, 100),
                'total_contratos': np.random.randint(1, 4, 100),
                'renda_mensal': np.random.uniform(2000, 15000, 100),
                'contratos_cancelados': np.random.choice([0, 1, 2], 100, p=[0.8, 0.15, 0.05]),
                'contratos_ativos': np.random.randint(0, 3, 100)
            })
        elif view_name == 'v_contratos_detalhados':
            data = {
                'contrato_id': [],
                'cliente_id': [],
                'status_contrato': [],
                'nivel_satisfacao_num': [],
                'tipo_seguro_nome': [],
                'data_inicio': [],
                'data_fim': [],
                'premio_mensal': [],
                'motivo_cancelamento_nome': []
            }
            contract_types = ['Automotivo', 'Residencial', 'Saúde', 'Vida', 'Empresarial']
            for client_id in range(1, 51):
                num_contracts = np.random.randint(1, 4)
                current_date = datetime(2023, 1, 1)

                for i in range(num_contracts):
                    contract_id = len(data['contrato_id']) + 1
                    status = np.random.choice(['Ativo', 'Cancelado', 'Encerrado'], p=[0.7, 0.2, 0.1])
                    satisfaction = np.random.randint(1, 6)
                    contract_type = np.random.choice(contract_types)
                    start_date = current_date + timedelta(days=np.random.randint(0, 90))
                    end_date = start_date + timedelta(days=np.random.randint(180, 720))
                    premium = np.random.uniform(50, 500)
                    
                    cancellation_reason = None
                    if status == 'Cancelado':
                        cancellation_reason = np.random.choice(['Preço', 'Atendimento', 'Concorrente', 'Necessidade Mudou'])

                    data['contrato_id'].append(contract_id)
                    data['cliente_id'].append(client_id)
                    data['status_contrato'].append(status)
                    data['nivel_satisfacao_num'].append(satisfaction)
                    data['tipo_seguro_nome'].append(contract_type)
                    data['data_inicio'].append(start_date)
                    data['data_fim'].append(end_date)
                    data['premio_mensal'].append(premium)
                    data['motivo_cancelamento_nome'].append(cancellation_reason)

                    current_date = end_date

            return pd.DataFrame(data)
        return pd.DataFrame()

    @st.cache_data
    def carregar_query(query_string):
        st.warning(f"Dummy carregar_query called for query: {query_string}. No data loaded.")
        
        # Mocks para queries filtradas por tipo_seguro_nome (dentro das abas)
        if "COUNT(*) AS total_contratos_ativos" in query_string and "WHERE tipo_seguro_nome = " in query_string:
            return pd.DataFrame({'total_contratos_ativos': [np.random.randint(100, 500)]})
        elif "COUNT(DISTINCT cliente_id) AS total_clientes_ativos" in query_string and "WHERE tipo_seguro_nome = " in query_string:
            return pd.DataFrame({'total_clientes_ativos': [np.random.randint(50, 300)]})
        elif "AVG(premio_mensal)" in query_string and "WHERE tipo_seguro_nome = " in query_string:
            return pd.DataFrame({'faturamento_medio': [round(np.random.uniform(50, 250), 2)]})
        elif "AVG(nivel_satisfacao_num)" in query_string and "WHERE tipo_seguro_nome = " in query_string:
            return pd.DataFrame({'satisfacao_media': [round(np.random.uniform(2.5, 4.5), 2)]})
        elif "FROM v_analise_churn WHERE tipo_seguro_nome = " in query_string:
            df_full = carregar_view('v_contratos_detalhados')
            contract_type_filter = re.search(r"tipo_seguro_nome = '([^']+)'", query_string)
            if contract_type_filter:
                df_full = df_full[df_full['tipo_seguro_nome'] == contract_type_filter.group(1)]
            return df_full[df_full['status_contrato'] == 'Cancelado'].copy()
        
        # Mock para df_all_detalhes no gráfico de transição
        elif "v_contratos_detalhados" in query_string and "SELECT cliente_id, data_inicio, tipo_seguro_nome FROM" in query_string:
            return carregar_view('v_contratos_detalhados')[['cliente_id', 'data_inicio', 'tipo_seguro_nome']]
        
        # Mock para df_detalhes_tab (SELECT * da view detalhada filtrada)
        elif "v_contratos_detalhados" in query_string and "SELECT *" in query_string and "WHERE tipo_seguro_nome = " in query_string:
            df_full = carregar_view('v_contratos_detalhados')
            contract_type_filter = re.search(r"tipo_seguro_nome = '([^']+)'", query_string)
            if contract_type_filter:
                df_full = df_full[df_full['tipo_seguro_nome'] == contract_type_filter.group(1)]
            return df_full
        
        # Fallback para v_contratos_em_risco (se ainda for usado em algum lugar, embora a sugestão seja usar df_predicoes)
        elif "v_contratos_em_risco" in query_string:
            categories = ['Automotivo', 'Residencial', 'Saúde', 'Vida', 'Empresarial']
            mock_risk_data = {
                'cliente_id': [101, 105, 112],
                'cliente_nome': ['Roberto', 'Mariana', 'Lucas'],
                'status_risco': ['Alto', 'Médio', 'Alto'],
                'data_fim_contrato_previsao': [
                    (datetime.now() + timedelta(days=np.random.randint(1, 60))).strftime('%Y-%m-%d') for _ in range(3)
                ],
                'tipo_seguro_nome': np.random.choice(categories, 3).tolist()
            }
            df_risk = pd.DataFrame(mock_risk_data)
            contract_type_filter = re.search(r"tipo_seguro_nome = '([^']+)'", query_string)
            if contract_type_filter:
                df_risk = df_risk[df_risk['tipo_seguro_nome'] == contract_type_filter.group(1)]
            return df_risk
        
        # Mocks para queries globais (se ainda houver alguma parte do código que as chame e não foi removida)
        elif "SELECT DISTINCT tipo_seguro_nome FROM v_contratos_detalhados" in query_string:
             categories = ['Automotivo', 'Empresarial', 'Vida', 'Saúde', 'Residencial']
             return pd.DataFrame({'tipo_seguro_nome': categories})

        return pd.DataFrame()


# A função `carregar_dados_predicao` é fornecida no seu prompt original e lida com CSV local.
# Mocks adicionados para colunas ausentes no CSV, se o arquivo existir mas faltar dados.
@st.cache_data
def carregar_dados_predicao():
    caminho_csv = os.path.join(PROJECT_ROOT, "frontend", "pages", "clientes_com_risco_cancelamento.csv")
    contract_types = ['Automotivo', 'Residencial', 'Saúde', 'Vida', 'Empresarial'] 

    if os.path.exists(caminho_csv):
        df = pd.read_csv(caminho_csv)
        # Adiciona colunas mock se ausentes. AVISO: Isso é um mock de dados, não um tratamento real de erro de dados.
        if 'cancelamento_previsto' not in df.columns:
            df['cancelamento_previsto'] = np.random.choice([0, 1], len(df), p=[0.8, 0.2])
        if 'cliente_id' not in df.columns:
            df['cliente_id'] = range(1, len(df) + 1)
        if 'cliente_nome' not in df.columns:
             df['cliente_nome'] = [f'Cliente {i}' for i in df['cliente_id']]
        if 'status_risco' not in df.columns:
            df['status_risco'] = np.random.choice(['Alto', 'Médio', 'Baixo'], len(df))
        if 'data_fim_contrato_previsao' not in df.columns:
            df['data_fim_contrato_previsao'] = (datetime.now() + pd.to_timedelta(np.random.randint(1, 365, len(df)), unit='days')).strftime('%Y-%m-%d')
        if 'tipo_seguro_nome' not in df.columns:
            df['tipo_seguro_nome'] = np.random.choice(contract_types, len(df))
        return df
    else:
        st.warning(f"Arquivo CSV de predição não encontrado em: {caminho_csv}. Usando dados de predição mockados.")
        # Este mock será ativado apenas se o arquivo CSV não for encontrado.
        mock_data = {
            'cliente_id': range(1, 101),
            'cliente_nome': [f'Cliente Risco {i}' for i in range(1, 101)],
            'cancelamento_previsto': np.random.choice([0, 1], 100, p=[0.8, 0.2]),
            'status_risco': np.random.choice(['Alto', 'Médio', 'Baixo'], 100),
            'data_fim_contrato_previsao': [(datetime.now() + timedelta(days=np.random.randint(1, 90))).strftime('%Y-%m-%d') for _ in range(100)],
            'tipo_seguro_nome': np.random.choice(contract_types, 100)
        }
        return pd.DataFrame(mock_data)

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
    /* Cor de fundo da aplicação */
    .stApp {
        background-color: #F0F2F6;
    }
    /* Estilo para os títulos dos cards */
    h3 {
        color: #333333; /* Cor mais escura para títulos */
        font-weight: 600;
        margin-bottom: 15px;
    }
    /* Estilo para containers com borda (usado para os cards grandes) */
    .stContainer {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); /* Sombra mais sutil */
        padding: 20px;
        background-color: white; /* Cor de fundo padrão dos cards do Streamlit */
    }
    /* Estilo para o seletor (selectbox) de período */
    div[data-testid="stSelectbox"] div[role="button"] {
        border-radius: 8px; /* Borda arredondada */
        border: 1px solid #ccc; /* Borda sutil */
        padding: 5px 10px;
        background-color: #f9f9f9;
    }
    /* Esconder o triângulo do selectbox, se desejar */
    div[data-testid="stSelectbox"] div[role="button"]::after {
        content: none;
    }
    /* Ajustes para o gráfico de linha (Faturamento) */
    .plotly-container {
        padding-top: 10px;
    }
    .kpi-box {
        position: relative;
        display: flex;
        align-items: center;
        background-color: white;
        border-radius: 12px;
        padding: 12px 16px;
        width: 100%;
        margin-bottom: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        font-family: Arial, sans-serif;
    }
    .kpi-icon {
        width: 100px;
        height: 100px;
        margin-right: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 55px;
        color: #3377ff;
    }
    .kpi-content {
        flex-grow: 1;
    }
    .kpi-value {
        font-size: 32px !important;
        font-weight: 700;
        margin: 0;
    }
    .kpi-explanation {
        margin-top: 4px;
        font-size: 13px;
        color: #555;
    }
    /* Estilos para a seção de valores dentro do card de Contratos */
    .valores-card {
        background-color: white; /* Corrigido para branco ou transparente se o pai for manipulado */
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05); /* Sombra mais leve */
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-around;
    }
    .valores-item {
        font-size: 16px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .valores-item strong {
        color: #333; /* Corrigido para a cor padrão de texto */
        flex-grow: 1;
    }
    .valores-item span {
        font-weight: bold;
        color: #007bff; /* Corrigido para a cor padrão de link/valor */
        text-align: right;
        min-width: 60px;
    }
    /* Estilos para o gráfico Plotly */
    .plotly-graph-div {
        /* A altura e largura serão gerenciadas pelo Streamlit ou pelos settings do Plotly */
    }
    /* Estilo para as abas */
    .stTabs [data-baseweb="tab-list"] button {
        background-color: white;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        margin-right: 5px;
        border: 1px solid #e0e0e0;
        border-bottom: none;
        color: #555;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: #007bff;
        color: white;
        border-color: #007bff;
    }
    .stTabs [data-baseweb="tab-panel"] {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 0 0 12px 12px;
        padding: 20px;
        margin-top: -1px; /* Overlap with tab list border */
    }
    </style>
    """,
    unsafe_allow_html=True
)


# --- Função para criar gráfico de barras de motivos de cancelamento ---
def create_cancellation_reasons_chart(df_cancellation):
    # This function now assumes df_cancellation will be a valid DataFrame
    # with 'motivo_cancelamento_nome' column if it's not empty.
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
    # Assumes df_detalhes will be a valid DataFrame
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
    # Removendo try-except, assume que os dados estão corretos ou o erro será propagado
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

    # --- BUSCAR TIPOS DE SEGURO PARA AS ABAS ---
    tipos_df = carregar_query("SELECT DISTINCT tipo_seguro_nome FROM v_contratos_detalhados ORDER BY tipo_seguro_nome")
    tab_names = tipos_df['tipo_seguro_nome'].tolist() if not tipos_df.empty else ["Automotivo", "Empresarial", "Vida", "Saúde", "Residencial"]

    tabs = st.tabs(tab_names)

    # Carrega TODOS os dados detalhados de contratos UMA VEZ para o gráfico de transição.
    # Isso precisa ser global para a lógica de transição funcionar entre diferentes tipos.
    df_all_detalhes_for_transitions = carregar_query("SELECT cliente_id, data_inicio, tipo_seguro_nome FROM v_contratos_detalhados;")
    
    # Carrega TODOS os dados de predição de risco UMA VEZ. Será filtrado por aba.
    df_predicoes_global = carregar_dados_predicao()


    for i, tab in enumerate(tabs):
        with tab:
            contract_type = tab_names[i]
            st.markdown(f"## Visão Geral - {contract_type}")

            # --- TAB-SPECIFIC DATA LOADING ---
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
            SELECT SUM(premio_mensal) AS faturamento_total
            FROM v_contratos_detalhados
            {where_clause} AND status_contrato = 'Ativo';
            """
            query_churn_tab_calc = f"""
            SELECT
                CAST(COUNT(CASE WHEN status_contrato = 'Cancelado' THEN 1 ELSE NULL END) AS REAL) * 100 /
                NULLIF(COUNT(CASE WHEN status_contrato IN ('Ativo', 'Cancelado') THEN 1 ELSE NULL END), 0) AS churn_rate
            FROM v_contratos_detalhados
            {where_clause};
            """
            query_satisfacao_tab = f"""
            SELECT ROUND(AVG(nivel_satisfacao_num), 2) AS satisfacao_media
            FROM v_contratos_detalhados
            {where_clause} AND nivel_satisfacao_num IS NOT NULL AND nivel_satisfacao_num > 0;
            """

            # Load dataframes for the current tab
            df_detalhes_tab = carregar_query(f"SELECT * FROM v_contratos_detalhados {where_clause};")
            df_churn_reasons_tab = carregar_query(f"SELECT * FROM v_analise_churn {where_clause};") # Used for cancellation reasons chart
            
            # Filter the globally loaded prediction data for the current tab's contract type
            df_predicoes_filtered_tab = df_predicoes_global[df_predicoes_global['tipo_seguro_nome'] == contract_type].copy()

            # --- Calculate Tab-Specific KPIs ---
            contratos_ativos_tab = carregar_query(query_contratos_ativos_tab)['total_contratos_ativos'].iloc[0] if not carregar_query(query_contratos_ativos_tab).empty else 0
            clientes_ativos_tab = carregar_query(query_clientes_ativos_tab)['total_clientes_ativos'].iloc[0] if not carregar_query(query_clientes_ativos_tab).empty else 0
            faturamento_tab = carregar_query(query_faturamento_tab)['faturamento_total'].iloc[0] if not carregar_query(query_faturamento_tab).empty else 0.0
            churn_rate_tab = carregar_query(query_churn_tab_calc)['churn_rate'].iloc[0] if not carregar_query(query_churn_tab_calc).empty else 0.0
            satisfacao_media_tab = carregar_query(query_satisfacao_tab)['satisfacao_media'].iloc[0] if not carregar_query(query_satisfacao_tab).empty else 0.0
            
            # KPI de Clientes em Risco para a aba atual, vindo de df_predicoes_global filtrado
            at_risk_clients_tab = df_predicoes_filtered_tab[df_predicoes_filtered_tab['cancelamento_previsto'] == 1]['cliente_id'].nunique() if not df_predicoes_filtered_tab.empty else 0


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
                st.container(border=True).write(f"### Contratos em Risco para {contract_type}")
                df_risk_display_tab = df_predicoes_filtered_tab[df_predicoes_filtered_tab['cancelamento_previsto'] == 1].copy()
                
                expected_risk_cols = ['cliente_nome', 'status_risco', 'data_fim_contrato_previsao']
                
                if not df_risk_display_tab.empty and all(col in df_risk_display_tab.columns for col in expected_risk_cols):
                    display_df_tab = df_risk_display_tab[expected_risk_cols]
                    display_df_tab.columns = ['Cliente', 'Status Risco', 'Previsão Fim']
                    st.dataframe(display_df_tab, use_container_width=True, hide_index=True, key=f"risk_contracts_table_{contract_type}")
                else:
                    st.info(f"Nenhum contrato em risco encontrado para {contract_type}.")
                    st.dataframe(pd.DataFrame(), use_container_width=True, hide_index=True, key=f"risk_contracts_table_empty_{contract_type}")


            with bottom_cols_tab[1]:
                st.container(border=True).write("### Situação Contrato")
                st.markdown(f"""
                <div class="valores-card">
                    <div class="valores-item"><strong>Risco Cancelamento</strong> <span></span></div>
                    <div class="valores-item"><strong>Contratos a terminar</strong> <span></span></div>
                    <div class="valores-item"><strong>Lista Situação Clientes</strong> <span></span></div>
                </div>
                """, unsafe_allow_html=True)


    # NENHUM CÓDIGO RELACIONADO À "PÁGINA HOME" ABAIXO.
    # Se você tiver uma página home separada, ela deve ter sua própria função render()
    # e ser chamada em seu próprio arquivo ou em uma estrutura de múltiplos arquivos.

if __name__ == '__main__':
    render()