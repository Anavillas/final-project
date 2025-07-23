import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

# Importar funções de acesso a dados
# Alterado de importação relativa para absoluta para resolver ImportError
from frontend.data_acess import carregar_view, carregar_query

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

# --- PONTO DE ENTRADA DA PÁGINA DE INSIGHTS ---
def render(): # Renomeado de page_insights() para render()
    st.markdown("<div class='main-header'>Insights e Análises Estratégicas</div>", unsafe_allow_html=True)

    st.markdown("""
        Bem-vindo à página de insights! Aqui, exploramos dados agregados e analisamos tendências
        importantes sobre nossos contratos, clientes e cancelamentos, utilizando as views
        pré-processadas do nosso banco de dados.
    """)

    st.sidebar.header("Navegação de Insights")
    insight_option = st.sidebar.radio(
        "Selecione o tipo de Insight:",
        ("Visão Geral de Contratos", "Perfis de Clientes", "Análise de Cancelamentos (Churn)", "Comparativo de Perfis", "Análise de Valor do Cliente")
    )

    if insight_option == "Visão Geral de Contratos":
        display_contract_insights()
    elif insight_option == "Perfis de Clientes":
        display_client_profile_insights()
    elif insight_option == "Análise de Cancelamentos (Churn)":
        display_churn_analysis_insights()
    elif insight_option == "Comparativo de Perfis":
        display_profile_comparison_insights()
    elif insight_option == "Análise de Valor do Cliente":
        display_customer_value_insights()

def display_contract_insights():
    st.header("Visão Geral de Contratos")
    st.write("Explorando dados detalhados de todos os contratos de seguro.")

    # Carregar a view v_contratos_detalhados
    with st.spinner("Carregando dados de contratos..."):
        df_contratos = carregar_view("v_contratos_detalhados")

    if not df_contratos.empty:
        st.success(f"Dados carregados com sucesso! Total de {len(df_contratos)} contratos.")

        st.subheader("Distribuição de Status de Contrato")
        status_counts = df_contratos['status_contrato'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Quantidade']
        fig_status = px.bar(status_counts, x='Status', y='Quantidade', color='Status',
                            title='Contratos por Status', height=350)
        st.plotly_chart(fig_status, use_container_width=True)

        st.subheader("Prêmio Mensal Médio por Tipo de Seguro")
        avg_premio_tipo_seguro = df_contratos.groupby('tipo_seguro_nome')['premio_mensal'].mean().reset_index()
        avg_premio_tipo_seguro.columns = ['Tipo de Seguro', 'Prêmio Mensal Médio']
        fig_premio = px.bar(avg_premio_tipo_seguro, x='Tipo de Seguro', y='Prêmio Mensal Médio',
                            title='Prêmio Mensal Médio por Tipo de Seguro', height=350)
        st.plotly_chart(fig_premio, use_container_width=True)

        st.subheader("Contratos por Canal de Venda")
        canal_venda_counts = df_contratos['canal_venda_nome'].value_counts().reset_index()
        canal_venda_counts.columns = ['Canal de Venda', 'Quantidade']
        fig_canal = px.pie(canal_venda_counts, values='Quantidade', names='Canal de Venda',
                           title='Contratos por Canal de Venda', hole=0.3, height=350)
        st.plotly_chart(fig_canal, use_container_width=True)

        st.subheader("Últimos 10 Contratos Detalhados (Amostra)")
        st.dataframe(df_contratos.head(10))
    else:
        st.warning("Não foi possível carregar os dados de contratos detalhados ou a view está vazia.")

def display_client_profile_insights():
    st.header("Perfis de Clientes")
    st.write("Analisando o perfil e o comportamento dos nossos clientes.")

    # Carregar a view v_perfil_cliente_enriquecido
    with st.spinner("Carregando dados de perfis de clientes..."):
        df_clientes = carregar_view("v_perfil_cliente_enriquecido")

    if not df_clientes.empty:
        st.success(f"Dados carregados com sucesso! Total de {len(df_clientes)} clientes.")

        st.subheader("Distribuição Etária dos Clientes")
        # Criar faixas etárias
        bins = [0, 18, 25, 35, 45, 55, 65, 100]
        labels = ['<18', '18-24', '25-34', '35-44', '45-54', '55-64', '65+']
        df_clientes['faixa_etaria'] = pd.cut(df_clientes['idade_atual'], bins=bins, labels=labels, right=False)
        fig_idade = px.bar(df_clientes['faixa_etaria'].value_counts().sort_index().reset_index(),
                           x='index', y='faixa_etaria', title='Distribuição Etária', height=350)
        fig_idade.update_layout(xaxis_title="Faixa Etária", yaxis_title="Contagem de Clientes")
        st.plotly_chart(fig_idade, use_container_width=True)

        st.subheader("Top 10 Clientes por Gasto Mensal Total")
        top_clientes_gasto = df_clientes.sort_values(by='gasto_mensal_total', ascending=False).head(10)
        st.dataframe(top_clientes_gasto[['nome', 'gasto_mensal_total', 'total_contratos', 'contratos_ativos']])

        st.subheader("Distribuição de Clientes por Gênero")
        genero_counts = df_clientes['cliente_genero'].value_counts().reset_index()
        genero_counts.columns = ['Gênero', 'Quantidade']
        fig_genero = px.pie(genero_counts, values='Quantidade', names='Gênero',
                            title='Clientes por Gênero', hole=0.3, height=350)
        st.plotly_chart(fig_genero, use_container_width=True)

        st.subheader("Distribuição de Clientes por Nível Educacional")
        educ_counts = df_clientes['cliente_nivel_educacional'].value_counts().reset_index()
        educ_counts.columns = ['Nível Educacional', 'Quantidade']
        fig_educ = px.bar(educ_counts, x='Nível Educacional', y='Quantidade',
                          title='Clientes por Nível Educacional', height=350)
        st.plotly_chart(fig_educ, use_container_width=True)

    else:
        st.warning("Não foi possível carregar os dados de perfil de clientes ou a view está vazia.")

def display_churn_analysis_insights():
    st.header("Análise de Cancelamentos (Churn)")
    st.write("Foco nos contratos que foram cancelados para identificar padrões e motivos.")

    # Carregar a view v_analise_churn
    with st.spinner("Carregando dados de cancelamentos..."):
        df_churn = carregar_view("v_analise_churn")

    if not df_churn.empty:
        st.success(f"Dados carregados com sucesso! Total de {len(df_churn)} contratos cancelados.")

        st.subheader("Principais Motivos de Cancelamento")
        motivo_counts = df_churn['motivo_cancelamento_nome'].value_counts().reset_index()
        motivo_counts.columns = ['Motivo de Cancelamento', 'Quantidade']
        fig_motivos = px.bar(motivo_counts, x='Quantidade', y='Motivo de Cancelamento', orientation='h',
                             title='Principais Motivos de Cancelamento', height=350, color_discrete_sequence=['#FF4B4B'])
        fig_motivos.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_motivos, use_container_width=True)

        st.subheader("Cancelamentos por Tipo de Seguro")
        churn_tipo_seguro = df_churn['tipo_seguro_nome'].value_counts().reset_index()
        churn_tipo_seguro.columns = ['Tipo de Seguro', 'Quantidade de Cancelamentos']
        fig_churn_tipo = px.bar(churn_tipo_seguro, x='Tipo de Seguro', y='Quantidade de Cancelamentos',
                                title='Cancelamentos por Tipo de Seguro', height=350)
        st.plotly_chart(fig_churn_tipo, use_container_width=True)

        st.subheader("Cancelamentos por Canal de Cancelamento")
        canal_cancelamento_counts = df_churn['canal_cancelamento_nome'].value_counts().reset_index()
        canal_cancelamento_counts.columns = ['Canal de Cancelamento', 'Quantidade']
        fig_canal_churn = px.pie(canal_cancelamento_counts, values='Quantidade', names='Canal de Cancelamento',
                                 title='Cancelamentos por Canal de Cancelamento', hole=0.3, height=350)
        st.plotly_chart(fig_canal_churn, use_container_width=True)

        st.subheader("Taxa de Satisfação dos Clientes que Cancelaram")
        # Excluir N/A (0) para esta análise
        satisfaction_churn = df_churn[df_churn['nivel_satisfacao_num'] != 0]['nivel_satisfacao_num'].value_counts().sort_index().reset_index()
        satisfaction_churn.columns = ['Nível de Satisfação', 'Quantidade']
        fig_satisfacao_churn = px.bar(satisfaction_churn, x='Nível de Satisfação', y='Quantidade',
                                      title='Nível de Satisfação dos Clientes Cancelados', height=350)
        st.plotly_chart(fig_satisfacao_churn, use_container_width=True)

        st.subheader("Tendência de Cancelamentos ao Longo do Tempo")
        # Assegurar que 'cancelado_em' é do tipo datetime
        df_churn['cancelado_em'] = pd.to_datetime(df_churn['cancelado_em'])
        # Agrupar por mês e contar cancelamentos
        churn_trend = df_churn.set_index('cancelado_em').resample('M').size().reset_index(name='Contagem')
        churn_trend.columns = ['Data', 'Contagem de Cancelamentos']
        fig_churn_trend = px.line(churn_trend, x='Data', y='Contagem de Cancelamentos',
                                  title='Contagem de Cancelamentos Mensais', height=350)
        fig_churn_trend.update_traces(mode='lines+markers', line=dict(color='#FF4B4B', width=2), marker=dict(size=6, color='#FF4B4B'))
        st.plotly_chart(fig_churn_trend, use_container_width=True)

        st.subheader("Últimos 10 Cancelamentos (Amostra)")
        st.dataframe(df_churn.head(10))
    else:
        st.warning("Não foi possível carregar os dados de análise de churn ou a view está vazia.")

def display_profile_comparison_insights():
    st.header("Comparativo de Perfis: Fiéis vs. Canceladores")
    st.write("Compare as características demográficas e comportamentais de clientes fiéis e aqueles que cancelaram contratos.")

    with st.spinner("Carregando dados para comparação de perfis..."):
        df_perfil_cliente = carregar_view("v_perfil_cliente_enriquecido")
        df_contratos_detalhados = carregar_view("v_contratos_detalhados") # Para obter nível de satisfação se necessário

    if not df_perfil_cliente.empty:
        # Definir clientes fiéis e canceladores com base em v_perfil_cliente_enriquecido
        df_fieis = df_perfil_cliente[(df_perfil_cliente['contratos_ativos'] > 0) & (df_perfil_cliente['contratos_cancelados'] == 0)].copy()
        df_canceladores = df_perfil_cliente[df_perfil_cliente['contratos_cancelados'] > 0].copy()

        col_loyal, col_churn = st.columns(2)

        # --- CARD: PERFIL DE CLIENTES FIÉIS ---
        with col_loyal:
            with st.container():
                st.markdown("<div class='profile-card'>", unsafe_allow_html=True)
                st.markdown("<h4>Perfil de Clientes Fiéis</h4>", unsafe_allow_html=True)

                if not df_fieis.empty:
                    st.markdown(f"<div class='profile-metric'>Total de Clientes: <strong>{len(df_fieis):,}</strong></div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='profile-metric'>Idade Média: <strong>{df_fieis['idade_atual'].mean():.1f}</strong></div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='profile-metric'>Rendimento Médio: <strong>R$ {df_fieis['cliente_renda_mensal'].mean():,.2f}</strong></div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='profile-metric'>Contratos Ativos Médios: <strong>{df_fieis['contratos_ativos'].mean():.1f}</strong></div>", unsafe_allow_html=True)
                    
                    # Gênero
                    st.markdown("<div class='profile-chart-title'>Gênero</div>", unsafe_allow_html=True)
                    df_genero_fieis = df_fieis['cliente_genero'].value_counts().reset_index()
                    df_genero_fieis.columns = ['Gênero', 'Contagem']
                    if not df_genero_fieis.empty:
                        fig_genero_fieis = px.pie(df_genero_fieis, values='Contagem', names='Gênero', hole=0.5, height=180)
                        fig_genero_fieis.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=True)
                        st.plotly_chart(fig_genero_fieis, use_container_width=True, config={'displayModeBar': False})
                    else:
                        st.markdown("<div class='profile-chart-placeholder'>Sem dados de gênero</div>", unsafe_allow_html=True)

                    # Nível Educacional
                    st.markdown("<div class='profile-chart-title'>Nível Educacional</div>", unsafe_allow_html=True)
                    df_educ_fieis = df_fieis['cliente_nivel_educacional'].value_counts().reset_index()
                    df_educ_fieis.columns = ['Nível Educacional', 'Contagem']
                    if not df_educ_fieis.empty:
                        fig_educ_fieis = px.bar(df_educ_fieis, x='Nível Educacional', y='Contagem', height=180)
                        fig_educ_fieis.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
                        st.plotly_chart(fig_educ_fieis, use_container_width=True, config={'displayModeBar': False})
                    else:
                        st.markdown("<div class='profile-chart-placeholder'>Sem dados de educação</div>", unsafe_allow_html=True)

                else:
                    st.info("Não há clientes fiéis nos dados.")
                st.markdown("</div>", unsafe_allow_html=True) # Fecha profile-card

        # --- CARD: PERFIL DE CLIENTES CANCELADORES ---
        with col_churn:
            with st.container():
                st.markdown("<div class='profile-card'>", unsafe_allow_html=True)
                st.markdown("<h4>Perfil de Clientes Canceladores</h4>", unsafe_allow_html=True)

                if not df_canceladores.empty:
                    st.markdown(f"<div class='profile-metric'>Total de Clientes: <strong>{len(df_canceladores):,}</strong></div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='profile-metric'>Idade Média: <strong>{df_canceladores['idade_atual'].mean():.1f}</strong></div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='profile-metric'>Rendimento Médio: <strong>R$ {df_canceladores['cliente_renda_mensal'].mean():,.2f}</strong></div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='profile-metric'>Contratos Cancelados Médios: <strong>{df_canceladores['contratos_cancelados'].mean():.1f}</strong></div>", unsafe_allow_html=True)
                    
                    # Gênero
                    st.markdown("<div class='profile-chart-title'>Gênero</div>", unsafe_allow_html=True)
                    df_genero_canceladores = df_canceladores['cliente_genero'].value_counts().reset_index()
                    df_genero_canceladores.columns = ['Gênero', 'Contagem']
                    if not df_genero_canceladores.empty:
                        fig_genero_canceladores = px.pie(df_genero_canceladores, values='Contagem', names='Gênero', hole=0.5, height=180)
                        fig_genero_canceladores.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=True)
                        st.plotly_chart(fig_genero_canceladores, use_container_width=True, config={'displayModeBar': False})
                    else:
                        st.markdown("<div class='profile-chart-placeholder'>Sem dados de gênero</div>", unsafe_allow_html=True)

                    # Nível Educacional
                    st.markdown("<div class='profile-chart-title'>Nível Educacional</div>", unsafe_allow_html=True)
                    df_educ_canceladores = df_canceladores['cliente_nivel_educacional'].value_counts().reset_index()
                    df_educ_canceladores.columns = ['Nível Educacional', 'Contagem']
                    if not df_educ_canceladores.empty:
                        fig_educ_canceladores = px.bar(df_educ_canceladores, x='Nível Educacional', y='Contagem', height=180)
                        fig_educ_canceladores.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
                        st.plotly_chart(fig_educ_canceladores, use_container_width=True, config={'displayModeBar': False})
                    else:
                        st.markdown("<div class='profile-chart-placeholder'>Sem dados de educação</div>", unsafe_allow_html=True)

                else:
                    st.info("Não há clientes canceladores nos dados.")
                st.markdown("</div>", unsafe_allow_html=True) # Fecha profile-card
    else:
        st.warning("Não foi possível carregar os dados de perfil de clientes para comparação ou a view está vazia.")

def display_customer_value_insights():
    st.header("Análise de Valor do Cliente (LTV)")
    st.write("Compare o valor médio de vida do cliente (LTV) entre clientes fiéis e canceladores, utilizando o gasto mensal total como proxy.")

    with st.spinner("Carregando dados de valor do cliente..."):
        df_perfil_cliente = carregar_view("v_perfil_cliente_enriquecido")

    if not df_perfil_cliente.empty:
        df_fieis_ltv = df_perfil_cliente[(df_perfil_cliente['contratos_ativos'] > 0) & (df_perfil_cliente['contratos_cancelados'] == 0)].copy()
        df_canceladores_ltv = df_perfil_cliente[df_perfil_cliente['contratos_cancelados'] > 0].copy()

        col_ltv = st.columns(1)[0]

        with col_ltv:
            st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
            st.markdown("<h3>Valor de Vida do Cliente (LTV) Médio: Fiéis vs. Canceladores</h3>", unsafe_allow_html=True)
            
            ltv_fieis_mean = df_fieis_ltv['gasto_mensal_total'].mean() if not df_fieis_ltv.empty else 0
            ltv_canceladores_mean = df_canceladores_ltv['gasto_mensal_total'].mean() if not df_canceladores_ltv.empty else 0

            if ltv_fieis_mean > 0 or ltv_canceladores_mean > 0:
                ltv_data = pd.DataFrame({
                    'Grupo': ['Fiéis', 'Canceladores'],
                    'LTV Médio': [ltv_fieis_mean, ltv_canceladores_mean]
                })
                fig_ltv = px.bar(ltv_data, x='Grupo', y='LTV Médio',
                                 title='LTV Médio por Grupo de Clientes', height=350,
                                 color='Grupo', color_discrete_map={'Fiéis': '#4CAF50', 'Canceladores': '#FF4B4B'})
                st.plotly_chart(fig_ltv, use_container_width=True)
            else:
                st.markdown("<div class='plotly-empty'>Sem dados suficientes para comparar LTV.</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("Não foi possível carregar os dados de perfil de clientes para análise de LTV ou a view está vazia.")


# --- PONTO DE ENTRADA PRINCIPAL (para execução direta do script) ---
if __name__ == '__main__':
    render()
