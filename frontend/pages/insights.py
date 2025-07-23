import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np # Adicionado, pois pode ser útil em manipulações de dados
import altair as alt
# import time # 'time' não está sendo usado, pode ser removido se não for necessário

# --- Importação da função de carregamento de CSS global ---
from frontend.styles.css_loader import load_global_css # Importante!
from frontend.utils.components import kpi_custom

# --- Importação da função kpi_custom (CONSIDERE MOVER PARA frontend/utils/components.py) ---



# --- Configuração de Caminhos ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# --- Importações reais do backend ---
# Adicionado try-except para as importações do backend, consistente com outras páginas
from backend.data.processed.loading_views import carregar_view, carregar_query



def render():
    st.set_page_config(layout="wide", page_title="Análise de Clientes")

    # --- CHAME A FUNÇÃO PARA CARREGAR O CSS GLOBAL AQUI ---
    load_global_css()

    # --- Dados Mockados (Prontos para serem substituídos por dados do banco) ---

    # Dados para o filtro de Tipo de Seguro
    tipos_seguro_mock = ["Automóvel", "Residencial", "Vida", "Saúde", "Viagem"]

    # Dados para Perfil Cliente Fiel
    cliente_fiel_mock = {
        "faixa_etaria": "30-45 anos",
        "media_dependentes": 2,
        "media_renda_mensal": "R$ 5.000 - R$ 8.000",
        "duracao_contrato_ideal": "5+ anos",
        "genero_distribuicao": pd.DataFrame({
            "categoria": ["Feminino", "Masculino", "Outro"],
            "valor": [700, 500, 100] # Exemplo de valores
        }),
        "escolaridade_distribuicao": pd.DataFrame({
            "categoria": ["Ensino Médio", "Graduação", "Pós-Graduação", "Mestrado", "Doutorado"],
            "valor": [400, 800, 600, 300, 150] # Exemplo de valores
        })
    }

    # Dados para Perfil Cliente Cancelador
    cliente_cancelador_mock = {
        "faixa_etaria": "18-29 anos",
        "media_dependentes": 0,
        "media_renda_mensal": "Até R$ 3.000",
        "duracao_contrato_ideal": "Menos de 1 ano",
        "genero_distribuicao": pd.DataFrame({
            "categoria": ["Feminino", "Masculino", "Outro"],
            "valor": [550, 750, 50] # Exemplo de valores
        }),
        "escolaridade_distribuicao": pd.DataFrame({
            "categoria": ["Ensino Médio", "Graduação", "Pós-Graduação", "Mestrado", "Doutorado"],
            "valor": [700, 500, 200, 50, 10] # Exemplo de valores
        })
    }

    # Dados para Motivos de Cancelamento
    motivos_cancelamento_mock = pd.DataFrame({
        "motivo": ["Preço Alto", "Atendimento Ruim", "Concorrência", "Mudança de Necessidade", "Outros"],
        "percentual": [60, 40, 20, 40, 20] # Exemplo de percentuais
    })

    # --- Funções para carregar dados do banco (placeholder) ---
    @st.cache_data(ttl=300) # Adicionando cache para estas funções também
    def get_tipos_seguro_from_db():
        # Substitua por carregar_query ou carregar_view real do seu backend
        # Exemplo: df_tipos = carregar_query("SELECT DISTINCT tipo_seguro_nome FROM tabela_de_seguros;")
        # return df_tipos['tipo_seguro_nome'].tolist()
        return tipos_seguro_mock

    @st.cache_data(ttl=300)
    def get_perfil_cliente_fiel_from_db(tipo_seguro):
        # Substitua pela lógica real do banco de dados
        return cliente_fiel_mock

    @st.cache_data(ttl=300)
    def get_perfil_cliente_cancelador_from_db(tipo_seguro):
        # Substitua pela lógica real do banco de dados
        return cliente_cancelador_mock

    @st.cache_data(ttl=300)
    def get_motivos_cancelamento_from_db(tipo_seguro):
        # Substitua pela lógica real do banco de dados
        return motivos_cancelamento_mock

    # --- Definição da paleta de cores azuis (se ainda for usada diretamente no Python para gráficos) ---
    # Nota: Cores para CSS devem estar no global.css
    BLUE_PALETTE = [
        '#007bff', # Azul primário
        '#6c8cd9', # Azul mais claro
        '#4682B4', # Azul aço
        '#1E90FF', # Azul Dodger
        '#87CEFA', # Azul céu
        '#ADD8E6'  # Azul claro
    ]
    PRIMARY_BLUE = '#007bff'
    TEXT_COLOR_MEDIUM = '#6c757d'


    # --- ATENÇÃO: ESTE BLOCO st.markdown FOI REMOVIDO! ---
    # O CSS global agora será carregado pela função load_global_css().


    # Título principal da página
    st.markdown(f"<h1 style='color: {PRIMARY_BLUE}; text-align: center; margin-bottom: 20px;'>Análise de Clientes</h1>", unsafe_allow_html=True)

    # Dropdown de seleção de tipo de seguro
    tipos_seguro = get_tipos_seguro_from_db()
    selected_seguro = st.selectbox("Tipo de Seguro", tipos_seguro)

    # Contêiner principal para os cards
    col1, col2, col3 = st.columns([1, 1, 0.6]) # Proporções ajustadas

    # --- Card: Perfil Cliente Fiel ---
    with col1:
        # Usando a classe global .stContainer para o card
        with st.container(border=True): # border=True já adiciona a classe stContainer
            st.markdown(f"<h3>Perfil Cliente Fiel</h3>", unsafe_allow_html=True)
            st.markdown(f"""
                <p style="font-size: 0.95em; color: {TEXT_COLOR_MEDIUM}; margin-bottom: 15px;">Características comuns:</p>
                <div class="icon-group">
                    <svg viewBox="0 0 24 24">
                        <path d="M16 17a3 3 0 0 0-3-3h-2a3 3 0 0 0-3 3v3h8M12 11a4 4 0 1 0-4-4 4 4 0 0 0 4 4m0-6a2 2 0 1 1-2 2 2 2 0 0 1 2-2m6 10a3 3 0 0 0 3-3v-2a3 3 0 0 0-3-3h-2.17a5.95 5.95 0 0 1 .17 2v2a3 3 0 0 0 3 3m-6 0a3 3 0 0 0-3-3h-2a3 3 0 0 0-3 3v3h8M6 10a4 4 0 1 0-4-4 4 4 0 0 0 4 4m0-6a2 2 0 1 1-2 2 2 2 0 0 1 2-2m-3 9a3 3 0 0 0-3-3v-2a3 3 0 0 0-3-3h-2.17a5.95 5.95 0 0 1 .17 2v2a3 3 0 0 0 3 3" />
                    </svg>
                </div>
                <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                    <div class="metric-item">
                        <span class="metric-label">Faixa Etária:</span>
                        <span class="metric-value">{get_perfil_cliente_fiel_from_db(selected_seguro)['faixa_etaria']}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Média Dependentes:</span>
                        <span class="metric-value">{get_perfil_cliente_fiel_from_db(selected_seguro)['media_dependentes']}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Média Renda Mensal:</span>
                        <span class="metric-value">{get_perfil_cliente_fiel_from_db(selected_seguro)['media_renda_mensal']}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Duração de Contrato Ideal:</span>
                        <span class="metric-value">{get_perfil_cliente_fiel_from_db(selected_seguro)['duracao_contrato_ideal']}</span>
                    </div>
                </div>
                <h4 class="chart-header">Gênero</h4>
                """, unsafe_allow_html=True)
            
            # Gráfico de Gênero para Cliente Fiel
            df_genero_fiel = get_perfil_cliente_fiel_from_db(selected_seguro)['genero_distribuicao']
            fig_genero_fiel = px.bar(df_genero_fiel, x="categoria", y="valor",
                                     labels={"categoria": "", "valor": ""},
                                     color_discrete_sequence=[PRIMARY_BLUE])
            fig_genero_fiel.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                height=200,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            fig_genero_fiel.update_xaxes(showgrid=False, tickfont=dict(size=10))
            fig_genero_fiel.update_yaxes(showgrid=True, zeroline=True, tickfont=dict(size=10))
            st.plotly_chart(fig_genero_fiel, use_container_width=True)

            st.markdown(f"""<h4 class="chart-header">Escolaridade</h4>""", unsafe_allow_html=True)
            # Gráfico de Escolaridade para Cliente Fiel
            df_escolaridade_fiel = get_perfil_cliente_fiel_from_db(selected_seguro)['escolaridade_distribuicao']
            fig_escolaridade_fiel = px.bar(df_escolaridade_fiel, x="categoria", y="valor",
                                            labels={"categoria": "", "valor": ""},
                                            color_discrete_sequence=[PRIMARY_BLUE])
            fig_escolaridade_fiel.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                height=200,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            fig_escolaridade_fiel.update_xaxes(showgrid=False, tickfont=dict(size=10))
            fig_escolaridade_fiel.update_yaxes(showgrid=True, zeroline=True, tickfont=dict(size=10))
            st.plotly_chart(fig_escolaridade_fiel, use_container_width=True)


    # --- Card: Perfil Cliente Cancelador ---
    with col2:
        # Usando a classe global .stContainer para o card
        with st.container(border=True):
            st.markdown(f"<h3>Perfil Cliente Cancelador</h3>", unsafe_allow_html=True)
            st.markdown(f"""
                <p style="font-size: 0.95em; color: {TEXT_COLOR_MEDIUM}; margin-bottom: 15px;">Características comuns:</p>
                <div class="icon-group">
                    <svg viewBox="0 0 24 24">
                        <path d="M16 17a3 3 0 0 0-3-3h-2a3 3 0 0 0-3 3v3h8M12 11a4 4 0 1 0-4-4 4 4 0 0 0 4 4m0-6a2 2 0 1 1-2 2 2 2 0 0 1 2-2m6 10a3 3 0 0 0 3-3v-2a3 3 0 0 0-3-3h-2.17a5.95 5.95 0 0 1 .17 2v2a3 3 0 0 0 3 3m-6 0a3 3 0 0 0-3-3h-2a3 3 0 0 0-3 3v3h8M6 10a4 4 0 1 0-4-4 4 4 0 0 0 4 4m0-6a2 2 0 1 1-2 2 2 2 0 0 1 2-2m-3 9a3 3 0 0 0-3-3v-2a3 3 0 0 0-3-3h-2.17a5.95 5.95 0 0 1 .17 2v2a3 3 0 0 0 3 3" />
                    </svg>
                </div>
                <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                    <div class="metric-item">
                        <span class="metric-label">Faixa Etária:</span>
                        <span class="metric-value">{get_perfil_cliente_cancelador_from_db(selected_seguro)['faixa_etaria']}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Média Dependentes:</span>
                        <span class="metric-value">{get_perfil_cliente_cancelador_from_db(selected_seguro)['media_dependentes']}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Média Renda Mensal:</span>
                        <span class="metric-value">{get_perfil_cliente_cancelador_from_db(selected_seguro)['media_renda_mensal']}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Duração de Contrato Ideal:</span>
                        <span class="metric-value">{get_perfil_cliente_cancelador_from_db(selected_seguro)['duracao_contrato_ideal']}</span>
                    </div>
                </div>
                <h4 class="chart-header">Gênero</h4>
                """, unsafe_allow_html=True)
            
            # Gráfico de Gênero para Cliente Cancelador
            df_genero_cancelador = get_perfil_cliente_cancelador_from_db(selected_seguro)['genero_distribuicao']
            fig_genero_cancelador = px.bar(df_genero_cancelador, x="categoria", y="valor",
                                            labels={"categoria": "", "valor": ""},
                                            color_discrete_sequence=[PRIMARY_BLUE])
            fig_genero_cancelador.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                height=200,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            fig_genero_cancelador.update_xaxes(showgrid=False, tickfont=dict(size=10))
            fig_genero_cancelador.update_yaxes(showgrid=True, zeroline=True, tickfont=dict(size=10))
            st.plotly_chart(fig_genero_cancelador, use_container_width=True)

            st.markdown(f"""<h4 class="chart-header">Escolaridade</h4>""", unsafe_allow_html=True)
            # Gráfico de Escolaridade para Cliente Cancelador
            df_escolaridade_cancelador = get_perfil_cliente_cancelador_from_db(selected_seguro)['escolaridade_distribuicao']
            fig_escolaridade_cancelador = px.bar(df_escolaridade_cancelador, x="categoria", y="valor",
                                                 labels={"categoria": "", "valor": ""},
                                                 color_discrete_sequence=[PRIMARY_BLUE])
            fig_escolaridade_cancelador.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                height=200,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            fig_escolaridade_cancelador.update_xaxes(showgrid=False, tickfont=dict(size=10))
            fig_escolaridade_cancelador.update_yaxes(showgrid=True, zeroline=True, tickfont=dict(size=10))
            st.plotly_chart(fig_escolaridade_cancelador, use_container_width=True)

    # --- Card: Motivos de Cancelamento ---
    with col3:
        # Usando a classe global .stContainer para o card
        with st.container(border=True):
            st.markdown(f"<h3>Motivos de Cancelamento</h3>", unsafe_allow_html=True)
            
            # Gráfico de Rosca para Motivos de Cancelamento
            df_motivos = get_motivos_cancelamento_from_db(selected_seguro)
            
            # Criar o gráfico de rosca com a paleta de azuis
            fig_motivos = go.Figure(data=[go.Pie(labels=df_motivos["motivo"],
                                                 values=df_motivos["percentual"],
                                                 hole=.7,
                                                 marker_colors=BLUE_PALETTE,
                                                 hoverinfo='label+percent',
                                                 textinfo='none'
                                                 )])
            
            fig_motivos.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                height=250,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_motivos, use_container_width=True)

            # Lista de percentuais abaixo do gráfico de rosca
            st.markdown("""
                <div style="margin-top: 20px;">
            """, unsafe_allow_html=True)
            for index, row in df_motivos.iterrows():
                st.markdown(f"""
                    <div class="percentage-list-item">
                        <span class="percentage-value">{row['percentual']}%</span>
                        <span class="percentage-text">{row['motivo']}</span>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

# Para rodar a aplicação no Streamlit, chame a função render()
if __name__ == '__main__':
    render()