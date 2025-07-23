import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import altair as alt
from backend.data.processed.loading_views import carregar_view
import time
from frontend.pages.home import kpi_custom

# --- INJEÇÃO DE CSS GLOBAL ---
st.markdown(
    """
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    <style>
    /* Seu CSS existente permanece exatamente igual */
    .stApp {
        background-color: #F0F2F6;
    }
    h3 {
        color: #333333;
        font-weight: 600;
        margin-bottom: 15px;
    }
    .stContainer {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        padding: 20px;
        background-color: white;
    }
    div[data-testid="stSelectbox"] div[role="button"] {
        border-radius: 8px;
        border: 1px solid #ccc;
        padding: 5px 10px;
        background-color: #f9f9f9;
    }
    div[data-testid="stSelectbox"] div[role="button"]::after {
        content: none;
    }
    .plotly-container {
        padding-top: 10px;
    }
    .kpi-box {
        position: relative;
        display: flex;
        align-items: center;
        justify-content: flex-start;
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
        text-align: left;
    }
    .kpi-value {
        font-size: 32px !important;
        font-weight: 700;
        margin: 0;
        color: #111827;
    }
    .kpi-explanation {
        margin-top: 4px;
        font-size: 13px;
        color: #555;
    }
    .chart-container {
        height: 350px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .metric-box {
        background-color: #e0f2f7;
        border-left: 5px solid #64B5F6;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
    }
    .metric-box.inactive-no-risk {
        border-left: 5px solid #1E90FF;
    }
    .metric-box.inactive {
        border-left: 5px solid #1976D2;
    }
    .metric-box.risk {
        border-left: 5px solid #D32F2F;
    }
    .metric-percentage {
        font-size: 1.8em;
        font-weight: bold;
        margin-right: 15px;
        color: #333;
    }
    .metric-label {
        font-size: 1.1em;
        color: #555;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Configuração de caminhos
raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if raiz_projeto not in sys.path:
    sys.path.insert(0, raiz_projeto)

# Função para carregar dados com cache
@st.cache_data(ttl=300)
def load_data():
    """Carrega os dados com cache para evitar recarregamentos"""
    df_perfil = carregar_view('v_perfil_cliente_enriquecido')
    df_detalhados = carregar_view('v_contratos_detalhados')
    return df_perfil, df_detalhados

# Função para aplicar filtros
def apply_filters(df, filtros):
    """Aplica os filtros no DataFrame"""
    df_filtrado = df.copy()
    
    if 'nome' in df_filtrado.columns and filtros['nome']:
        search_term = filtros['nome'].lower()
        df_filtrado = df_filtrado[df_filtrado['nome'].str.lower().str.startswith(search_term)]
    
    if 'genero' in df_filtrado.columns and filtros['genero']:
        df_filtrado = df_filtrado[df_filtrado['genero'].isin(filtros['genero'])]
    
    if 'idade_atual' in df_filtrado.columns:
        df_filtrado = df_filtrado[
            (df_filtrado['idade_atual'] >= filtros['idade_min']) &
            (df_filtrado['idade_atual'] <= filtros['idade_max'])
        ]
    
    if 'nivel_educacional' in df_filtrado.columns and filtros['educacao']:
        df_filtrado = df_filtrado[df_filtrado['nivel_educacional'].isin(filtros['educacao'])]
    
    if 'qtd_dependente' in df_filtrado.columns:
        df_filtrado = df_filtrado[
            (df_filtrado['qtd_dependente'] >= filtros['dependentes_min']) &
            (df_filtrado['qtd_dependente'] <= filtros['dependentes_max'])
        ]
    
    if 'total_contratos' in df_filtrado.columns:
        df_filtrado = df_filtrado[
            (df_filtrado['total_contratos'] >= filtros['contratos_min']) &
            (df_filtrado['total_contratos'] <= filtros['contratos_max'])
        ]

    if 'renda_mensal' in df_filtrado.columns:
        df_filtrado = df_filtrado[
            (df_filtrado['renda_mensal'] >= filtros['renda_min']) &
            (df_filtrado['renda_mensal'] <= filtros['renda_max'])
        ]
    
    return df_filtrado

# Função para resetar filtros
def resetar_filtros(df_perfil):
    """Reseta todos os filtros para seus valores padrão"""
    defaults = {
        'nome': '',
        'genero': list(df_perfil['genero'].unique()) if 'genero' in df_perfil.columns else [],
        'idade_min': int(df_perfil['idade_atual'].min()) if 'idade_atual' in df_perfil.columns else 0,
        'idade_max': int(df_perfil['idade_atual'].max()) if 'idade_atual' in df_perfil.columns else 100,
        'educacao': list(df_perfil['nivel_educacional'].unique()) if 'nivel_educacional' in df_perfil.columns else [],
        'dependentes_min': int(df_perfil['qtd_dependente'].min()) if 'qtd_dependente' in df_perfil.columns else 0,
        'dependentes_max': int(df_perfil['qtd_dependente'].max()) if 'qtd_dependente' in df_perfil.columns else 10,
        'contratos_min': int(df_perfil['total_contratos'].min()) if 'total_contratos' in df_perfil.columns else 0,
        'contratos_max': int(df_perfil['total_contratos'].max()) if 'total_contratos' in df_perfil.columns else 10,
        'renda_min': float(df_perfil['renda_mensal'].min()) if 'renda_mensal' in df_perfil.columns else 0,
        'renda_max': float(df_perfil['renda_mensal'].max()) if 'renda_mensal' in df_perfil.columns else 10000
    }
    
    # Atualiza cada filtro individualmente no session_state
    for key, value in defaults.items():
        st.session_state[f'filter_{key}'] = value
    
    st.session_state.filtros = defaults
    st.toast("Filtros resetados com sucesso!", icon="✅")
    st.rerun()

def render():
    try:
        # Carrega os dados com cache
        df_perfil, df_detalhados = load_data()

        # Inicialização dos filtros
        if 'filtros' not in st.session_state:
            defaults = {
                'nome': '',
                'genero': list(df_perfil['genero'].unique()) if 'genero' in df_perfil.columns else [],
                'idade_min': int(df_perfil['idade_atual'].min()) if 'idade_atual' in df_perfil.columns else 0,
                'idade_max': int(df_perfil['idade_atual'].max()) if 'idade_atual' in df_perfil.columns else 100,
                'educacao': list(df_perfil['nivel_educacional'].unique()) if 'nivel_educacional' in df_perfil.columns else [],
                'dependentes_min': int(df_perfil['qtd_dependente'].min()) if 'qtd_dependente' in df_perfil.columns else 0,
                'dependentes_max': int(df_perfil['qtd_dependente'].max()) if 'qtd_dependente' in df_perfil.columns else 10,
                'contratos_min': int(df_perfil['total_contratos'].min()) if 'total_contratos' in df_perfil.columns else 0,
                'contratos_max': int(df_perfil['total_contratos'].max()) if 'total_contratos' in df_perfil.columns else 10,
                'renda_min': float(df_perfil['renda_mensal'].min()) if 'renda_mensal' in df_perfil.columns else 0,
                'renda_max': float(df_perfil['renda_mensal'].max()) if 'renda_mensal' in df_perfil.columns else 10000
            }
            
            # Inicializa cada filtro individualmente
            for key, value in defaults.items():
                st.session_state[f'filter_{key}'] = value
            
            st.session_state.filtros = defaults

        # ========== SEÇÃO DE KPIS ==========
        st.markdown("## KPIs Principais")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            kpi_custom("fas fa-users", f"{len(df_perfil):,}", "Clientes Totais")

        with col2:
            media_dep = df_perfil['qtd_dependente'].mean()
            kpi_custom("fas fa-child", f"{media_dep:.1f}", "Média Dependentes")

        with col3:
            multi_contr = len(df_perfil[df_perfil['total_contratos'] > 1])
            kpi_custom("fas fa-file-contract", f"{multi_contr}", "Clientes +1 Contrato")

        with col4:
            renda_media = f"R${df_perfil['renda_mensal'].mean():,.2f}"
            kpi_custom("fas fa-money-bill-wave", renda_media, "Renda Média")

        st.markdown("---")

        # ========== SEÇÃO DE GRÁFICOS ==========
        col1_charts, col2_charts = st.columns([2, 1]) 

        with col1_charts:
            # Card 1: Gráfico de Escolaridade
            with st.container(border=True):
                st.markdown("### Escolaridade dos Clientes")
                if 'nivel_educacional' in df_perfil.columns and not df_perfil.empty:
                    df_escolaridade = df_perfil['nivel_educacional'].value_counts().reset_index()
                    df_escolaridade.columns = ['nivel_educacional', 'count']
                    
                    fig = px.bar(
                        df_escolaridade,
                        x='nivel_educacional',
                        y='count',
                        labels={'nivel_educacional': 'Nível Educacional', 'count': 'Quantidade'},
                        color='count',
                        color_continuous_scale='blues',
                        height=350
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Coluna 'nivel_educacional' não encontrada ou DataFrame vazio.")
            
            st.write("")
            
            # Card 2: Gráfico Faixa Etária x Gênero
            with st.container(border=True):
                st.markdown("### Faixa Etária x Gênero")
                if 'idade_atual' in df_perfil.columns and 'genero' in df_perfil.columns and not df_perfil.empty:
                    df_perfil['faixa_etaria'] = pd.cut(
                        df_perfil['idade_atual'],
                        bins=[18, 30, 40, 50, 60, 100],
                        labels=["18-30", "31-40", "41-50", "51-60", "60+"],
                        right=False
                    )
                    df_faixa_genero = df_perfil.groupby(['faixa_etaria', 'genero']).size().reset_index(name='count')
                    
                    color_map = {'F': "#F561AB", 'M': "#5AB6F8", 'O': "#A35AE7"}
                    
                    fig = px.bar(
                        df_faixa_genero,
                        x='faixa_etaria',
                        y='count',
                        color='genero',
                        labels={'count': 'Clientes', 'faixa_etaria': 'Faixa Etária'},
                        barmode='group',
                        color_discrete_map=color_map,
                        height=350
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Colunas 'idade_atual' ou 'genero' não encontradas ou DataFrame vazio.")

        with col2_charts:
            # Card 3: Gráfico de Situação dos Clientes
            with st.container(border=True):
                st.markdown("### Situação Clientes")
                
                total_clientes = len(df_perfil)
                
                if total_clientes == 0:
                    st.warning("Não há dados de clientes para exibir a situação.")
                    ativos_percent = 0
                    inativos_percent = 0
                    em_risco_percent = 0
                    inativos_sem_risco_percent = 0
                else:
                    if 'contratos_ativos' not in df_perfil.columns:
                        st.warning("Coluna 'contratos_ativos' não encontrada. Usando dados mockados para o gráfico de situação.")
                        ativos_percent = 60
                        inativos_percent = 40
                        em_risco_percent = 20
                        inativos_sem_risco_percent = 20
                    else:
                        clientes_ativos = df_perfil[df_perfil['contratos_ativos'] > 0]
                        clientes_inativos = df_perfil[df_perfil['contratos_ativos'] == 0]

                        ativos_percent = round((len(clientes_ativos) / total_clientes) * 100, 1)

                        if 'status_cliente' in df_perfil.columns:
                            total_clientes_situacao = df_perfil['status_cliente'].count() 

                            if total_clientes_situacao > 0:
                                count_ativos = df_perfil[df_perfil['status_cliente'] == 'Ativo'].shape[0]
                                count_inativos = df_perfil[df_perfil['status_cliente'] == 'Inativo'].shape[0]
                                count_em_risco = df_perfil[df_perfil['status_cliente'] == 'Em risco'].shape[0]

                                ativos_percent = round((count_ativos / total_clientes_situacao) * 100, 1)
                                em_risco_percent = round((count_em_risco / total_clientes_situacao) * 100, 1)
                                inativos_sem_risco_percent = round((count_inativos / total_clientes_situacao) * 100, 1)
                                inativos_total_percent_for_indicator = em_risco_percent + inativos_sem_risco_percent
                            else:
                                ativos_percent = 0
                                inativos_sem_risco_percent = 0
                                em_risco_percent = 0
                                inativos_total_percent_for_indicator = 0
                        else:
                            st.warning("Coluna 'status_cliente' não encontrada. Usando valores mockados para o gráfico de situação (60% Ativos, 20% Inativos sem risco, 20% Em risco).")
                            ativos_percent = 60
                            inativos_percent = 40
                            em_risco_percent = 20
                            inativos_sem_risco_percent = 20
                            inativos_total_percent_for_indicator = inativos_percent

                df_chart = pd.DataFrame({
                    'Categoria': ['Clientes Ativos', 'Clientes Inativos (sem risco)', 'Em risco'],
                    'Valor': [ativos_percent, inativos_sem_risco_percent, em_risco_percent]
                })

                color_scale = alt.Scale(domain=['Clientes Ativos', 'Clientes Inativos (sem risco)', 'Em risco'],
                                      range=['#6495ED', '#1E90FF', '#DC143C'])

                chart = alt.Chart(df_chart).mark_arc(outerRadius=120, innerRadius=80).encode(
                    theta=alt.Theta(field="Valor", type="quantitative"),
                    color=alt.Color(field="Categoria", scale=color_scale),
                    order=alt.Order(field="Valor", sort="descending"),
                    tooltip=['Categoria', alt.Tooltip("Valor", format=".1f")]
                ).properties(
                    width=300,
                    height=300
                ).configure_view(
                    strokeWidth=0
                )

                st.altair_chart(chart, use_container_width=True)

                st.markdown(f"""
                    <div class="metric-box">
                        <div class="metric-percentage">{ativos_percent}%</div>
                        <div class="metric-label">Clientes Ativos</div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                    <div class="metric-box inactive">
                        <div class="metric-percentage">{inativos_total_percent_for_indicator}%</div>
                        <div class="metric-label">Clientes Inativos</div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                    <div class="metric-box risk">
                        <div class="metric-percentage">{em_risco_percent}%</div>
                        <div class="metric-label">Em risco</div>
                    </div>
                """, unsafe_allow_html=True)
            
            st.write("")
            
            # Card 4: Gráfico de Renda por Faixa Etária
            with st.container(border=True):
                st.markdown("### Renda por Faixa Etária")
                if 'faixa_etaria' in df_perfil.columns and 'renda_mensal' in df_perfil.columns and not df_perfil.empty:
                    df_renda_idade = df_perfil.groupby('faixa_etaria')['renda_mensal'].mean().reset_index()
                    fig = px.bar(
                        df_renda_idade,
                        x='faixa_etaria',
                        y='renda_mensal',
                        labels={'renda_mensal': 'Renda Média (R$)', 'faixa_etaria': 'Faixa Etária'},
                        color='renda_mensal',
                        color_continuous_scale='blues',
                        height=350
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Dados insuficientes para renda por faixa etária.")

        # ========== SEÇÃO DE FILTROS ==========
        st.markdown("---")
        st.markdown("### Dados dos Clientes")

        # Container para os filtros na sidebar
        filter_container = st.sidebar.container()

        with filter_container:
            st.header("🔍 Filtros Avançados")
            
            with st.form(key='filters_form'):
                # Widgets de filtro - agora usando os valores individuais do session_state
                if 'nome' in df_perfil.columns:
                    st.session_state.filtros['nome'] = st.text_input(
                        "Buscar por nome",
                        value=st.session_state.get('filter_nome', ''),
                        placeholder="Digite o início do nome..."
                    )
                
                if 'genero' in df_perfil.columns:
                    st.session_state.filtros['genero'] = st.multiselect(
                        "Gênero",
                        options=df_perfil['genero'].unique(),
                        default=st.session_state.get('filter_genero', list(df_perfil['genero'].unique()))
                    )
                
                if 'idade_atual' in df_perfil.columns:
                    idade_min, idade_max = st.slider(
                        "Faixa de Idade",
                        min_value=int(df_perfil['idade_atual'].min()),
                        max_value=int(df_perfil['idade_atual'].max()),
                        value=(
                            st.session_state.get('filter_idade_min', int(df_perfil['idade_atual'].min())),
                            st.session_state.get('filter_idade_max', int(df_perfil['idade_atual'].max()))
                        )
                    )
                    st.session_state.filtros.update({
                        'idade_min': idade_min,
                        'idade_max': idade_max
                    })
                
                if 'nivel_educacional' in df_perfil.columns:
                    st.session_state.filtros['educacao'] = st.multiselect(
                        "Nível Educacional",
                        options=df_perfil['nivel_educacional'].unique(),
                        default=st.session_state.get('filter_educacao', list(df_perfil['nivel_educacional'].unique()))
                    )
                
                if 'qtd_dependente' in df_perfil.columns:
                    dep_min, dep_max = st.slider(
                        "Número de Dependentes",
                        min_value=int(df_perfil['qtd_dependente'].min()),
                        max_value=int(df_perfil['qtd_dependente'].max()),
                        value=(
                            st.session_state.get('filter_dependentes_min', int(df_perfil['qtd_dependente'].min())),
                            st.session_state.get('filter_dependentes_max', int(df_perfil['qtd_dependente'].max()))
                        )
                    )
                    st.session_state.filtros.update({
                        'dependentes_min': dep_min,
                        'dependentes_max': dep_max
                    })
                
                if 'total_contratos' in df_perfil.columns:
                    contratos_min, contratos_max = st.slider(
                        "Total de Contratos",
                        min_value=int(df_perfil['total_contratos'].min()),
                        max_value=int(df_perfil['total_contratos'].max()),
                        value=(
                            st.session_state.get('filter_contratos_min', int(df_perfil['total_contratos'].min())),
                            st.session_state.get('filter_contratos_max', int(df_perfil['total_contratos'].max()))
                        )
                    )
                    st.session_state.filtros.update({
                        'contratos_min': contratos_min,
                        'contratos_max': contratos_max
                    })

                if 'renda_mensal' in df_perfil.columns:
                    renda_min, renda_max = st.slider(
                        "Renda Mensal (R$)",
                        min_value=float(df_perfil['renda_mensal'].min()),
                        max_value=float(df_perfil['renda_mensal'].max()),
                        value=(
                            st.session_state.get('filter_renda_min', float(df_perfil['renda_mensal'].min())),
                            st.session_state.get('filter_renda_max', float(df_perfil['renda_mensal'].max()))
                        )
                    )
                    st.session_state.filtros.update({
                        'renda_min': renda_min,
                        'renda_max': renda_max
                    })
                
                # Botões de ação
                col1, col2 = st.columns(2)
                with col1:
                    aplicar_filtros = st.form_submit_button("Aplicar Filtros")
                with col2:
                    if st.form_submit_button("🔄 Resetar"):
                        resetar_filtros(df_perfil)

        # Aplica os filtros
        df_filtrado = apply_filters(df_perfil, st.session_state.filtros)

        # Exibição dos resultados
        st.info(f"📊 {len(df_filtrado)} clientes encontrados")
        
        cols_to_show = [col for col in [
            'nome', 'genero', 'idade_atual', 'nivel_educacional',
            'qtd_dependente', 'total_contratos', 'renda_mensal'
        ] if col in df_filtrado.columns]

        if cols_to_show:
            st.dataframe(df_filtrado[cols_to_show].head(5000), use_container_width=True, height=400)
            st.download_button(
                "📥 Exportar Dados",
                data=df_filtrado[cols_to_show].to_csv(index=False).encode('utf-8'),
                file_name="clientes_filtrados.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"Erro: {str(e)}")

if __name__ == "__main__":
    render()