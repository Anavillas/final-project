import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

# Reutilizar kpi_custom de home.py se existir, ou definir localmente se não
try:
    from frontend.pages.home import kpi_custom
except ImportError:
    # Definir uma versão local simplificada de kpi_custom se a importação falhar
    st.warning("kpi_custom não encontrado em home.py. Usando definição local simplificada.")
    def kpi_custom(icon_class, value, explanation):
        html_code = f"""
        <div style="background-color: white; border-radius: 12px; padding: 12px 16px; margin-bottom: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); display: flex; align-items: center; justify-content: flex-start;">
            <div style="width: 55px; height: 55px; margin-right: 14px; display: flex; align-items: center; justify-content: center; font-size: 30px; color: #3377ff; flex-shrink: 0;">
                <i class="{icon_class}"></i>
            </div>
            <div style="flex-grow: 1; text-align: left;">
                <p style="font-size: 24px; font-weight: 700; margin: 0; color: #111827;">{value}</p>
                <div style="margin-top: 4px; font-size: 13px; color: #555;">{explanation}</div>
            </div>
        </div>
        """
        st.markdown(html_code, unsafe_allow_html=True)


# --- INJEÇÃO DE CSS GLOBAL ---
st.markdown(
    """
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    <style>
    body { background-color: #F4F4F5; font-family: 'Segoe UI', sans-serif; }
    .stApp { background-color: #F4F4F5; }
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    
    h3 {
        color: #333333;
        font-weight: 600;
        margin-bottom: 15px;
    }
    .main-header {
        font-size: 26px; color: #111827; font-weight: bold;
        padding: 1rem 0; margin-bottom: 1rem;
    }
    .profile-card {
        background-color: white;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        padding: 20px;
        height: 550px; /* Altura fixa para alinhar os cards */
        display: flex;
        flex-direction: column;
    }
    .profile-card h4 {
        color: #333333;
        font-size: 20px;
        font-weight: 600;
        margin-bottom: 15px;
        text-align: center;
    }
    .profile-metric {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        font-size: 15px;
        color: #555;
    }
    .profile-metric strong {
        color: #111827;
    }
    .profile-chart-placeholder {
        height: 150px; /* Altura para mini-gráficos */
        display: flex;
        justify-content: center;
        align-items: center;
        background-color: #F8FAFC;
        border-radius: 8px;
        margin-top: 10px;
        font-size: 14px;
        color: #6B7280;
        border: 1px dashed #E0E0E0;
    }
    .profile-chart-title {
        font-size: 14px;
        font-weight: 600;
        color: #333;
        margin-top: 15px;
        margin-bottom: 5px;
        text-align: center;
    }
    .chart-card {
        background-color: #FFFFFF;
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
        height: 400px; /* Altura fixa */
        display: flex;
        flex-direction: column;
    }
    .chart-card h3 {
        color: #111827;
        margin-bottom: 1rem;
        font-size: 18px;
        font-weight: 600;
    }
    .chart-card .plotly-empty {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100%;
        color: #6B7280;
        font-size: 16px;
        border: 1px dashed #E0E0E0;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True
)

# --- DADOS MOCKADOS PARA INSIGHTS ---
# Estender MOCK_DF_PERFIL para incluir status de fidelidade/cancelamento
# e dados para LTV e churn ao longo do tempo.

# Geração de dados de perfil mais complexa para simular fiéis/canceladores
np.random.seed(42) # Para reprodutibilidade
num_clientes = 500

mock_data_insights = {
    'cliente_id': range(1, num_clientes + 1),
    'genero': np.random.choice(['M', 'F'], num_clientes, p=[0.55, 0.45]),
    'idade_atual': np.random.randint(20, 65, num_clientes),
    'nivel_educacional': np.random.choice(['Fundamental', 'Médio', 'Superior', 'Pós-graduação'], num_clientes, p=[0.15, 0.3, 0.4, 0.15]),
    'qtd_dependente': np.random.randint(0, 4, num_clientes),
    'renda_mensal': np.random.uniform(2500, 18000, num_clientes),
    'total_contratos': np.random.randint(1, 5, num_clientes),
    'tempo_cliente_meses': np.random.randint(6, 60, num_clientes), # Tempo como cliente
    'satisfacao': np.random.randint(1, 6, num_clientes), # Escala de 1 a 5
    'regiao': np.random.choice(['Sudeste', 'Sul', 'Nordeste', 'Centro-Oeste', 'Norte'], num_clientes, p=[0.4, 0.2, 0.2, 0.1, 0.1]),
}
MOCK_DF_INSIGHTS_PERFIL = pd.DataFrame(mock_data_insights)

# Simular status de churn baseado em algumas características
# Ex: Clientes com baixa satisfação ou tempo de cliente curto/muito longo, ou muitos contratos cancelam mais
MOCK_DF_INSIGHTS_PERFIL['is_churning'] = 0
MOCK_DF_INSIGHTS_PERFIL.loc[(MOCK_DF_INSIGHTS_PERFIL['satisfacao'] <= 2) |
                             (MOCK_DF_INSIGHTS_PERFIL['tempo_cliente_meses'] < 12) |
                             (MOCK_DF_INSIGHTS_PERFIL['total_contratos'] == 1), 'is_churning'] = np.random.choice([0, 1], size=len(MOCK_DF_INSIGHTS_PERFIL[(MOCK_DF_INSIGHTS_PERFIL['satisfacao'] <= 2) | (MOCK_DF_INSIGHTS_PERFIL['tempo_cliente_meses'] < 12) | (MOCK_DF_INSIGHTS_PERFIL['total_contratos'] == 1)]), p=[0.3, 0.7])

# Clientes fiéis: não são churners e têm pelo menos 1 contrato
MOCK_DF_INSIGHTS_PERFIL['is_loyal'] = ((MOCK_DF_INSIGHTS_PERFIL['is_churning'] == 0) & (MOCK_DF_INSIGHTS_PERFIL['total_contratos'] >= 1)).astype(int)

# Para LTV (simples: renda * tempo_cliente_meses * fator de ajuste)
MOCK_DF_INSIGHTS_PERFIL['ltv'] = MOCK_DF_INSIGHTS_PERFIL['renda_mensal'] * MOCK_DF_INSIGHTS_PERFIL['tempo_cliente_meses'] * np.random.uniform(0.5, 1.5, num_clientes)


# Mock de dados para Análise de Churn ao longo do tempo
start_date_churn_trend = datetime(2023, 1, 1)
dates_churn_trend = [start_date_churn_trend + timedelta(days=x*30) for x in range(18)] # 18 meses
MOCK_CHURN_TREND_DATA = pd.DataFrame({
    'Data': dates_churn_trend,
    'Taxa de Churn': np.random.uniform(5, 15, len(dates_churn_trend)) # Taxa de 5% a 15%
})

# Mock de dados para Motivos de Cancelamento
MOCK_MOTIVOS_CANCELAMENTO = pd.DataFrame({
    'Motivo': ['Preço Alto', 'Má Experiência', 'Atendimento Ruim', 'Concorrência', 'Mudança de Necessidade'],
    'Contagem': [120, 80, 60, 45, 30]
})


# --- FUNÇÕES MOCKADAS (substituindo carregar_view/query) ---
@st.cache_data
def get_mock_data(data_type):
    if data_type == 'perfil_insights':
        return MOCK_DF_INSIGHTS_PERFIL.copy()
    elif data_type == 'churn_trend':
        return MOCK_CHURN_TREND_DATA.copy()
    elif data_type == 'motivos_cancelamento':
        return MOCK_MOTIVOS_CANCELAMENTO.copy()
    return pd.DataFrame()


# --- RENDERIZAÇÃO DA PÁGINA ---
def render():
    st.markdown("<div class='main-header'>Insights e Análises Estratégicas</div>", unsafe_allow_html=True)

    df_insights = get_mock_data('perfil_insights')

    # Separar clientes fiéis e canceladores
    df_fieis = df_insights[df_insights['is_loyal'] == 1].copy()
    df_canceladores = df_insights[df_insights['is_churning'] == 1].copy()

    # ========== SEÇÃO DE COMPARATIVO DE PERFIS ==========
    st.markdown("## Comparativo de Perfis: Fiéis vs. Canceladores")
    col_loyal, col_churn = st.columns(2)

    # --- CARD: PERFIL DE CLIENTES FIÉIS ---
    with col_loyal:
        with st.container():
            st.markdown("<div class='profile-card'>", unsafe_allow_html=True)
            st.markdown("<h4>Perfil de Clientes Fiéis</h4>", unsafe_allow_html=True)

            if not df_fieis.empty:
                st.markdown(f"<div class='profile-metric'>Total de Clientes: <strong>{len(df_fieis):,}</strong></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='profile-metric'>Idade Média: <strong>{df_fieis['idade_atual'].mean():.1f}</strong></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='profile-metric'>Rendimento Médio: <strong>R$ {df_fieis['renda_mensal'].mean():,.2f}</strong></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='profile-metric'>Média Dependentes: <strong>{df_fieis['qtd_dependente'].mean():.1f}</strong></div>", unsafe_allow_html=True)
                
                # Gênero
                st.markdown("<div class='profile-chart-title'>Gênero</div>", unsafe_allow_html=True)
                df_genero_fieis = df_fieis['genero'].value_counts().reset_index()
                df_genero_fieis.columns = ['Gênero', 'Contagem']
                if not df_genero_fieis.empty:
                    fig_genero_fieis = px.pie(df_genero_fieis, values='Contagem', names='Gênero', hole=0.5, height=180)
                    fig_genero_fieis.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=True)
                    st.plotly_chart(fig_genero_fieis, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.markdown("<div class='profile-chart-placeholder'>Sem dados de gênero</div>", unsafe_allow_html=True)

                # Nível Educacional
                st.markdown("<div class='profile-chart-title'>Nível Educacional</div>", unsafe_allow_html=True)
                df_educ_fieis = df_fieis['nivel_educacional'].value_counts().reset_index()
                df_educ_fieis.columns = ['Nível Educacional', 'Contagem']
                if not df_educ_fieis.empty:
                    fig_educ_fieis = px.bar(df_educ_fieis, x='Nível Educacional', y='Contagem', height=180)
                    fig_educ_fieis.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
                    st.plotly_chart(fig_educ_fieis, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.markdown("<div class='profile-chart-placeholder'>Sem dados de educação</div>", unsafe_allow_html=True)

            else:
                st.info("Não há clientes fiéis nos dados mockados.")
            st.markdown("</div>", unsafe_allow_html=True) # Fecha profile-card

    # --- CARD: PERFIL DE CLIENTES CANCELADORES ---
    with col_churn:
        with st.container():
            st.markdown("<div class='profile-card'>", unsafe_allow_html=True)
            st.markdown("<h4>Perfil de Clientes Canceladores</h4>", unsafe_allow_html=True)

            if not df_canceladores.empty:
                st.markdown(f"<div class='profile-metric'>Total de Clientes: <strong>{len(df_canceladores):,}</strong></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='profile-metric'>Idade Média: <strong>{df_canceladores['idade_atual'].mean():.1f}</strong></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='profile-metric'>Rendimento Médio: <strong>R$ {df_canceladores['renda_mensal'].mean():,.2f}</strong></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='profile-metric'>Média Dependentes: <strong>{df_canceladores['qtd_dependente'].mean():.1f}</strong></div>", unsafe_allow_html=True)
                
                # Gênero
                st.markdown("<div class='profile-chart-title'>Gênero</div>", unsafe_allow_html=True)
                df_genero_canceladores = df_canceladores['genero'].value_counts().reset_index()
                df_genero_canceladores.columns = ['Gênero', 'Contagem']
                if not df_genero_canceladores.empty:
                    fig_genero_canceladores = px.pie(df_genero_canceladores, values='Contagem', names='Gênero', hole=0.5, height=180)
                    fig_genero_canceladores.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=True)
                    st.plotly_chart(fig_genero_canceladores, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.markdown("<div class='profile-chart-placeholder'>Sem dados de gênero</div>", unsafe_allow_html=True)

                # Nível Educacional
                st.markdown("<div class='profile-chart-title'>Nível Educacional</div>", unsafe_allow_html=True)
                df_educ_canceladores = df_canceladores['nivel_educacional'].value_counts().reset_index()
                df_educ_canceladores.columns = ['Nível Educacional', 'Contagem']
                if not df_educ_canceladores.empty:
                    fig_educ_canceladores = px.bar(df_educ_canceladores, x='Nível Educacional', y='Contagem', height=180)
                    fig_educ_canceladores.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
                    st.plotly_chart(fig_educ_canceladores, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.markdown("<div class='profile-chart-placeholder'>Sem dados de educação</div>", unsafe_allow_html=True)

            else:
                st.info("Não há clientes canceladores nos dados mockados.")
            st.markdown("</div>", unsafe_allow_html=True) # Fecha profile-card

    st.markdown("---")

    # ========== SEÇÃO DE ANÁLISE DE CHURN ==========
    st.markdown("## Análise de Churn")
    col_churn_trend, col_churn_reasons = st.columns([2, 1])

    with col_churn_trend:
        st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
        st.markdown("<h3>Tendência de Churn ao Longo do Tempo</h3>", unsafe_allow_html=True)
        churn_trend_data = get_mock_data('churn_trend')
        if not churn_trend_data.empty:
            fig_churn_trend = px.line(churn_trend_data, x='Data', y='Taxa de Churn',
                                      title='Taxa de Churn Mensal', height=350)
            fig_churn_trend.update_traces(mode='lines+markers', line=dict(color='#FF4B4B', width=2), marker=dict(size=6, color='#FF4B4B'))
            st.plotly_chart(fig_churn_trend, use_container_width=True)
        else:
            st.markdown("<div class='plotly-empty'>Sem dados de tendência de churn.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_churn_reasons:
        st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
        st.markdown("<h3>Principais Motivos de Cancelamento</h3>", unsafe_allow_html=True)
        motivos_cancelamento_data = get_mock_data('motivos_cancelamento')
        if not motivos_cancelamento_data.empty:
            fig_motivos = px.bar(motivos_cancelamento_data, x='Contagem', y='Motivo', orientation='h',
                                 title='Top Motivos', height=350, color_discrete_sequence=['#3B82F6'])
            fig_motivos.update_layout(yaxis={'categoryorder':'total ascending'}) # Ordena do menor para o maior
            st.plotly_chart(fig_motivos, use_container_width=True)
        else:
            st.markdown("<div class='plotly-empty'>Sem dados de motivos de cancelamento.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # ========== SEÇÃO DE ANÁLISE DE VALOR DO CLIENTE ==========
    st.markdown("## Análise de Valor do Cliente")
    col_ltv = st.columns(1)[0] # Usar uma única coluna para o gráfico LTV

    with col_ltv:
        st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
        st.markdown("<h3>Valor de Vida do Cliente (LTV): Fiéis vs. Canceladores</h3>", unsafe_allow_html=True)
        if not df_fieis.empty and not df_canceladores.empty:
            ltv_data = pd.DataFrame({
                'Grupo': ['Fiéis', 'Canceladores'],
                'LTV Médio': [df_fieis['ltv'].mean(), df_canceladores['ltv'].mean()]
            })
            fig_ltv = px.bar(ltv_data, x='Grupo', y='LTV Médio',
                             title='LTV Médio por Grupo de Clientes', height=350,
                             color='Grupo', color_discrete_map={'Fiéis': '#4CAF50', 'Canceladores': '#FF4B4B'})
            st.plotly_chart(fig_ltv, use_container_width=True)
        else:
            st.markdown("<div class='plotly-empty'>Sem dados suficientes para comparar LTV.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    # A seção de filtros e tabela de clientes foi removida para focar na página de Insights
    # Se precisar dela, pode copiá-la de volta do seu código anterior.


# --- PONTO DE ENTRADA DA PÁGINA ---
if __name__ == '__main__':
    render()