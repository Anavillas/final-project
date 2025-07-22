import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from backend.data.processed.loading_views import carregar_view
from home import kpi_custom
import time  # Adicionado para o time.sleep()

# Configuração inicial única (removida a duplicação)
st.set_page_config(layout="wide", initial_sidebar_state="expanded")

# CSS otimizado
st.markdown("""
<style>
    .stApp [data-testid="stDecoration"] { display: none; }
    div[data-testid="stVerticalBlock"] > div:has(> .element-container) {
        transition: opacity 200ms ease-in-out;
    }
    .stSlider { min-height: 50px; }
    .stDataFrame { margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# Configuração de caminhos
raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if raiz_projeto not in sys.path:
    sys.path.insert(0, raiz_projeto)

# Cache para carregamento de dados
@st.cache_data
def load_data():
    return (
        carregar_view('v_perfil_cliente_enriquecido'),
        carregar_view('v_contratos_detalhados')
    )

def render():
    try:
        # Carrega os dados com cache
        df_perfil, df_detalhados = load_data()
        
        # ========== SEÇÃO DE KPIs ==========
        st.markdown("## KPIs Principais")
        cols = st.columns(5)
        metrics = [
            ("👥", f"{len(df_perfil):,}", "Clientes Totais"),
            ("👨‍👩‍👧‍👦", f"{df_perfil['qtd_dependente'].mean():.1f}", "Média Dependentes"),
            ("📑", f"{len(df_perfil[df_perfil['total_contratos'] > 1])}", "Clientes +1 Contrato"),
            ("💰", f"R${df_perfil['renda_mensal'].mean():,.2f}", "Renda Média"),
            ("❌", f"{df_perfil['contratos_cancelados'].sum()}", "Cancelamentos")
        ]
        
        for col, (emoji, value, label) in zip(cols, metrics):
            with col:
                kpi_custom(emoji, value, label)

        st.markdown("---")
        
        # ========== SEÇÃO DE GRÁFICOS ==========
        col1, col2 = st.columns(2)

        with col1:
            # Gráfico de Escolaridade
            with st.container(border=True):
                st.markdown("### Escolaridade dos Clientes")
                if 'nivel_educacional' in df_perfil.columns:
                    df_escolaridade = df_perfil['nivel_educacional'].value_counts().reset_index()
                    fig = px.bar(
                        df_escolaridade,
                        x='nivel_educacional',
                        y='count',
                        labels={'nivel_educacional': 'Nível Educacional', 'count': 'Quantidade'},
                        color='count',
                        color_continuous_scale='blues'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            st.write("")
            
            # Gráfico Faixa Etária x Gênero
            with st.container(border=True):
                st.markdown("### Faixa Etária x Gênero")
                df_perfil['faixa_etaria'] = pd.cut(
                    df_perfil['idade_atual'],
                    bins=[18, 30, 40, 50, 60, 100],
                    labels=["18-30", "31-40", "41-50", "51-60", "60+"]
                )
                fig = px.bar(
                    df_perfil.groupby(['faixa_etaria', 'genero']).size().reset_index(name='count'),
                    x='faixa_etaria',
                    y='count',
                    color='genero',
                    barmode='group',
                    color_discrete_map={'F': "#F561AB", 'M': "#5AB6F8", 'O': "#A35AE7"}
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
        # Gráfico de Situação dos Clientes
            with st.container(border=True):
                st.markdown("### Situação dos Clientes")
                if all(col in df_perfil.columns for col in ['contratos_ativos', 'contratos_cancelados']):
                    df_perfil['status'] = np.select(
                        [
                            (df_perfil['contratos_ativos'] > 0),
                            (df_perfil['contratos_cancelados'] > 0),
                            (df_perfil['contratos_ativos'] == 0) & (df_perfil['contratos_cancelados'] == 0)
                        ],
                        ['Ativo', 'Cancelado', 'Inativo'],
                        default='Desconhecido'
                    )
                    
                    # Criar um dataframe com a contagem
                    status_counts = df_perfil['status'].value_counts().reset_index()
                    status_counts.columns = ['status', 'count']
                    
                    # Definir a paleta de cores
                    cores = {
                        'Ativo': "#9AE751",
                        'Cancelado': "#FD4242", 
                        'Inativo': "#FFDE21",
                        'Desconhecido': "#CCCCCC"  # cor padrão para outros status
                    }
                    
                    fig = px.pie(
                        status_counts,
                        values='count',
                        names='status',
                        hole=0.3,
                        color='status',
                        color_discrete_map=cores
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            st.write("")
            
            # Gráfico de Renda por Faixa Etária
            with st.container(border=True):
                st.markdown("### Renda por Faixa Etária")
                if 'faixa_etaria' in df_perfil.columns and 'renda_mensal' in df_perfil.columns:
                    fig = px.bar(
                        df_perfil.groupby('faixa_etaria')['renda_mensal'].mean().reset_index(),
                        x='faixa_etaria',
                        y='renda_mensal',
                        color='renda_mensal',
                        color_continuous_scale='blues'
                    )
                    st.plotly_chart(fig, use_container_width=True)

        # ========== SEÇÃO DE FILTROS ==========
        st.markdown("---")
        st.markdown("### Dados dos Clientes")

        # Inicialização dos filtros
        if 'filtros' not in st.session_state:
            st.session_state.filtros = {
                'nome': '',
                'genero': df_perfil['genero'].unique() if 'genero' in df_perfil.columns else [],
                'idade_min': int(df_perfil['idade_atual'].min()) if 'idade_atual' in df_perfil.columns else 0,
                'idade_max': int(df_perfil['idade_atual'].max()) if 'idade_atual' in df_perfil.columns else 100,
                'educacao': df_perfil['nivel_educacional'].unique() if 'nivel_educacional' in df_perfil.columns else [],
                'dependentes_min': int(df_perfil['qtd_dependente'].min()) if 'qtd_dependente' in df_perfil.columns else 0,
                'dependentes_max': int(df_perfil['qtd_dependente'].max()) if 'qtd_dependente' in df_perfil.columns else 10,
                'contratos_min': int(df_perfil['total_contratos'].min()) if 'total_contratos' in df_perfil.columns else 0,
                'contratos_max': int(df_perfil['total_contratos'].max()) if 'total_contratos' in df_perfil.columns else 10,
                'renda_min': float(df_perfil['renda_mensal'].min()) if 'renda_mensal' in df_perfil.columns else 0,
                'renda_max': float(df_perfil['renda_mensal'].max()) if 'renda_mensal' in df_perfil.columns else 10000
            }
            st.session_state['reset_counter'] = 0

        def resetar_filtros():
            defaults = {
                'nome': '',
                'genero': df_perfil['genero'].unique() if 'genero' in df_perfil.columns else [],
                'idade_min': int(df_perfil['idade_atual'].min()) if 'idade_atual' in df_perfil.columns else 0,
                'idade_max': int(df_perfil['idade_atual'].max()) if 'idade_atual' in df_perfil.columns else 100,
                'educacao': df_perfil['nivel_educacional'].unique() if 'nivel_educacional' in df_perfil.columns else [],
                'dependentes_min': int(df_perfil['qtd_dependente'].min()) if 'qtd_dependente' in df_perfil.columns else 0,
                'dependentes_max': int(df_perfil['qtd_dependente'].max()) if 'qtd_dependente' in df_perfil.columns else 10,
                'contratos_min': int(df_perfil['total_contratos'].min()) if 'total_contratos' in df_perfil.columns else 0,
                'contratos_max': int(df_perfil['total_contratos'].max()) if 'total_contratos' in df_perfil.columns else 10,
                'renda_min': float(df_perfil['renda_mensal'].min()) if 'renda_mensal' in df_perfil.columns else 0,
                'renda_max': float(df_perfil['renda_mensal'].max()) if 'renda_mensal' in df_perfil.columns else 10000
            }
            st.session_state.filtros.update(defaults)
            st.session_state['reset_counter'] += 1
            st.toast("Filtros resetados!", icon="✅")

        with st.sidebar:
            st.header("🔍 Filtros Avançados")
            
            if st.button("🔄 Resetar Filtros", key="reset_btn"):
                resetar_filtros()
                time.sleep(0.3)
                st.rerun()
            
            # Widgets de filtro com keys dinâmicas
            reset_counter = st.session_state.get('reset_counter', 0)
            
            if 'nome' in df_perfil.columns:
                st.session_state.filtros['nome'] = st.text_input(
                    "Buscar por nome",
                    value=st.session_state.filtros['nome'],
                    placeholder="Digite o início do nome...",
                    key=f"nome_{reset_counter}"
    )
            if 'genero' in df_perfil.columns:
                st.session_state.filtros['genero'] = st.multiselect(
                    "Gênero",
                    options=df_perfil['genero'].unique(),
                    default=st.session_state.filtros['genero'],
                    key=f"genero_{reset_counter}"
                )
            
            if 'idade_atual' in df_perfil.columns:
                idade_min, idade_max = st.slider(
                    "Faixa de Idade",
                    min_value=int(df_perfil['idade_atual'].min()),
                    max_value=int(df_perfil['idade_atual'].max()),
                    value=(st.session_state.filtros['idade_min'], st.session_state.filtros['idade_max']),
                    key=f"idade_{reset_counter}"
                )
                st.session_state.filtros.update({'idade_min': idade_min, 'idade_max': idade_max})
            
            if 'nivel_educacional' in df_perfil.columns:
                st.session_state.filtros['educacao'] = st.multiselect(
                    "Nível Educacional",
                    options=df_perfil['nivel_educacional'].unique(),
                    default=st.session_state.filtros['educacao'],
                    key=f"educacao_{reset_counter}"
                )
            
            if 'qtd_dependente' in df_perfil.columns:
                dep_min, dep_max = st.slider(
                    "Número de Dependentes",
                    min_value=int(df_perfil['qtd_dependente'].min()),
                    max_value=int(df_perfil['qtd_dependente'].max()),
                    value=(st.session_state.filtros['dependentes_min'], st.session_state.filtros['dependentes_max']),
                    key=f"dependentes_{reset_counter}"
                )
                st.session_state.filtros.update({'dependentes_min': dep_min, 'dependentes_max': dep_max})
            
                    # NOVO FILTRO - TOTAL DE CONTRATOS
            if 'total_contratos' in df_perfil.columns:
                contratos_min, contratos_max = st.slider(
                    "Total de Contratos",
                    min_value=int(df_perfil['total_contratos'].min()),
                    max_value=int(df_perfil['total_contratos'].max()),
                    value=(st.session_state.filtros['contratos_min'], st.session_state.filtros['contratos_max']),
                    key=f"contratos_{reset_counter}"
                )
                st.session_state.filtros['contratos_min'] = contratos_min
                st.session_state.filtros['contratos_max'] = contratos_max

            if 'renda_mensal' in df_perfil.columns:
                renda_min, renda_max = st.slider(
                    "Renda Mensal (R$)",
                    min_value=float(df_perfil['renda_mensal'].min()),
                    max_value=float(df_perfil['renda_mensal'].max()),
                    value=(st.session_state.filtros['renda_min'], st.session_state.filtros['renda_max']),
                    key=f"renda_{reset_counter}"
                )
                st.session_state.filtros.update({'renda_min': renda_min, 'renda_max': renda_max})

        # Aplicação dos filtros
        df_filtrado = df_perfil.copy()
        filtros = st.session_state.filtros
        
        if 'nome' in df_filtrado.columns and st.session_state.filtros['nome']:
                search_term = st.session_state.filtros['nome'].lower()
                df_filtrado = df_filtrado[
                df_filtrado['nome'].str.lower().str.startswith(search_term)
            ]

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
                (df_filtrado['total_contratos'] >= st.session_state.filtros['contratos_min']) & 
                (df_filtrado['total_contratos'] <= st.session_state.filtros['contratos_max'])
            ]

        if 'renda_mensal' in df_filtrado.columns:
            df_filtrado = df_filtrado[
                (df_filtrado['renda_mensal'] >= filtros['renda_min']) & 
                (df_filtrado['renda_mensal'] <= filtros['renda_max'])
            ]

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