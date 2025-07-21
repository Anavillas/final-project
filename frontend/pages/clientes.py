import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from backend.data.processed.loading_views import carregar_view
from home import kpi_custom

# Configuração de caminhos
raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if raiz_projeto not in sys.path:
    sys.path.insert(0, raiz_projeto)

def render():
    st.set_page_config(layout="wide")
    
    try:
        # Carrega os dados
        df_perfil = carregar_view('v_perfil_cliente_enriquecido')
        df_detalhados = carregar_view('v_contratos_detalhados')
        
        # ========== SEÇÃO DE KPIs ==========
        st.markdown("## KPIs Principais")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            kpi_custom("👥", f"{len(df_perfil):,}", "Clientes Totais")
        
        with col2:
            media_dep = df_perfil['qtd_dependente'].mean()
            kpi_custom("👨‍👩‍👧‍👦", f"{media_dep:.1f}", "Média Dependentes")
        
        with col3:
            multi_contr = len(df_perfil[df_perfil['total_contratos'] > 1])
            kpi_custom("📑", f"{multi_contr}", "Clientes +1 Contrato")
        
        with col4:
            renda_media = f"R${df_perfil['renda_mensal'].mean():,.2f}"
            kpi_custom("💰", renda_media, "Renda Média")
        
        with col5:
            cancelamentos = df_perfil['contratos_cancelados'].sum()
            kpi_custom("❌", f"{cancelamentos}", "Cancelamentos")

        st.markdown("---")
        
        # ========== SEÇÃO DE GRÁFICOS ==========
        col1, col2 = st.columns(2)

        with col1:
            # Card 1: Gráfico de Escolaridade
            with st.container(border=True):  # Novo no Streamlit 1.29.0+
                st.markdown("### Escolaridade dos Clientes")
                if 'nivel_educacional' in df_perfil.columns:
                    df_escolaridade = df_perfil['nivel_educacional'].value_counts().reset_index()
                    df_escolaridade.columns = ['nivel_educacional', 'count']
                    
                    fig = px.bar(
                        df_escolaridade,
                        x='nivel_educacional',
                        y='count',
                        labels={'nivel_educacional': 'Nível Educacional', 'count': 'Quantidade'},
                        color='count',
                        color_continuous_scale='blues'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Coluna 'nivel_educacional' não encontrada")
            
            # Espaçamento entre cards
            st.write("")  
            
            # Card 2: Gráfico Faixa Etária x Gênero
            with st.container(border=True):
                st.markdown("### Faixa Etária x Gênero")
                df_perfil['faixa_etaria'] = pd.cut(
                    df_perfil['idade_atual'],
                    bins=[18, 30, 40, 50, 60, 100],
                    labels=["18-30", "31-40", "41-50", "51-60", "60+"]
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
                    color_discrete_map=color_map
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Card 3: Gráfico de Situação dos Clientes
            with st.container(border=True):
                st.markdown("### Situação dos Clientes")
                if all(col in df_perfil.columns for col in ['contratos_ativos', 'contratos_cancelados']):
                    conditions = [
                        (df_perfil['contratos_ativos'] > 0),
                        (df_perfil['contratos_cancelados'] > 0),
                        (df_perfil['contratos_ativos'] == 0) & (df_perfil['contratos_cancelados'] == 0)
                    ]
                    choices = ['Ativo', 'Cancelado', 'Inativo']
                    df_perfil['status'] = np.select(conditions, choices, default='Desconhecido')
                    
                    df_status = df_perfil['status'].value_counts().reset_index()
                    df_status.columns = ['status', 'count']
                    
                    color_map_status = {
                        'Ativo': "#9AE751",
                        'Cancelado': "#FD4242",
                        'Inativo': "#FFDE21"
                    }
                    
                    fig = px.pie(
                        df_status,
                        values='count',
                        names='status',
                        hole=0.3,
                        labels={'status': 'Status', 'count': 'Clientes'},
                        color='status',
                        color_discrete_map=color_map_status
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Dados insuficientes para status")
            
            # Espaçamento entre cards
            st.write("")  
            
            # Card 4: Gráfico de Renda por Faixa Etária
            with st.container(border=True):
                st.markdown("### Renda por Faixa Etária")
                if 'faixa_etaria' in df_perfil.columns and 'renda_mensal' in df_perfil.columns:
                    df_renda_idade = df_perfil.groupby('faixa_etaria')['renda_mensal'].mean().reset_index()
                    fig = px.bar(
                        df_renda_idade,
                        x='faixa_etaria',
                        y='renda_mensal',
                        labels={'renda_mensal': 'Renda Média (R$)', 'faixa_etaria': 'Faixa Etária'},
                        color='renda_mensal',
                        color_continuous_scale='blues'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Dados insuficientes para renda por faixa etária")

        # ========== SEÇÃO DE DADOS COM FILTROS ==========
        st.markdown("---")
        st.markdown("### Dados dos Clientes")

        # Inicializar session_state para filtros
        if 'filtros' not in st.session_state:
            st.session_state.filtros = {
                'genero': df_perfil['genero'].unique() if 'genero' in df_perfil.columns else [],
                'idade_min': int(df_perfil['idade_atual'].min()) if 'idade_atual' in df_perfil.columns else 0,
                'idade_max': int(df_perfil['idade_atual'].max()) if 'idade_atual' in df_perfil.columns else 100,
                'educacao': df_perfil['nivel_educacional'].unique() if 'nivel_educacional' in df_perfil.columns else [],
                'dependentes_min': int(df_perfil['qtd_dependente'].min()) if 'qtd_dependente' in df_perfil.columns else 0,
                'dependentes_max': int(df_perfil['qtd_dependente'].max()) if 'qtd_dependente' in df_perfil.columns else 10,
                'renda_min': float(df_perfil['renda_mensal'].min()) if 'renda_mensal' in df_perfil.columns else 0,
                'renda_max': float(df_perfil['renda_mensal'].max()) if 'renda_mensal' in df_perfil.columns else 10000
            }

        # Função para resetar filtros
        def resetar_filtros():
            defaults = {
                'genero': df_perfil['genero'].unique() if 'genero' in df_perfil.columns else [],
                'idade_min': int(df_perfil['idade_atual'].min()) if 'idade_atual' in df_perfil.columns else 0,
                'idade_max': int(df_perfil['idade_atual'].max()) if 'idade_atual' in df_perfil.columns else 100,
                'educacao': df_perfil['nivel_educacional'].unique() if 'nivel_educacional' in df_perfil.columns else [],
                'dependentes_min': int(df_perfil['qtd_dependente'].min()) if 'qtd_dependente' in df_perfil.columns else 0,
                'dependentes_max': int(df_perfil['qtd_dependente'].max()) if 'qtd_dependente' in df_perfil.columns else 10,
                'renda_min': float(df_perfil['renda_mensal'].min()) if 'renda_mensal' in df_perfil.columns else 0,
                'renda_max': float(df_perfil['renda_mensal'].max()) if 'renda_mensal' in df_perfil.columns else 10000
            }
            
            for key in defaults:
                st.session_state.filtros[key] = defaults[key]
            
            st.toast("Filtros resetados com sucesso!", icon="✅")

        # Filtros na sidebar
        with st.sidebar:
            st.header("🔍 Filtros Avançados")
            
            if st.button("🔄 Resetar Todos os Filtros"):
                resetar_filtros()
            
            # 1. Filtro por Gênero
            generos = df_perfil['genero'].unique() if 'genero' in df_perfil.columns else []
            genero_selecionado = st.multiselect(
                "Gênero",
                options=generos,
                default=st.session_state.filtros['genero']
            )
            st.session_state.filtros['genero'] = genero_selecionado
            
            # 2. Filtro por Faixa Etária
            if 'idade_atual' in df_perfil.columns:
                idade_min, idade_max = st.slider(
                    "Faixa de Idade",
                    min_value=int(df_perfil['idade_atual'].min()),
                    max_value=int(df_perfil['idade_atual'].max()),
                    value=(st.session_state.filtros['idade_min'], st.session_state.filtros['idade_max'])  # Corrigido: usando parênteses
                )
                st.session_state.filtros['idade_min'] = idade_min
                st.session_state.filtros['idade_max'] = idade_max
            
            # 3. Filtro por Nível Educacional
            if 'nivel_educacional' in df_perfil.columns:
                educacao_selecionada = st.multiselect(
                    "Nível Educacional",
                    options=df_perfil['nivel_educacional'].unique(),
                    default=st.session_state.filtros['educacao']
                )
                st.session_state.filtros['educacao'] = educacao_selecionada
            
            # 4. Filtro por Quantidade de Dependentes
            if 'qtd_dependente' in df_perfil.columns:
                dependentes_min, dependentes_max = st.slider(
                    "Número de Dependentes",
                    min_value=int(df_perfil['qtd_dependente'].min()),
                    max_value=int(df_perfil['qtd_dependente'].max()),
                    value=(st.session_state.filtros['dependentes_min'], st.session_state.filtros['dependentes_max'])  # Corrigido: usando parênteses
                )
                st.session_state.filtros['dependentes_min'] = dependentes_min
                st.session_state.filtros['dependentes_max'] = dependentes_max
            
            # 5. Filtro por Renda Mensal
            if 'renda_mensal' in df_perfil.columns:
                renda_min, renda_max = st.slider(
                    "Faixa de Renda Mensal (R$)",
                    min_value=float(df_perfil['renda_mensal'].min()),
                    max_value=float(df_perfil['renda_mensal'].max()),
                    value=(st.session_state.filtros['renda_min'], st.session_state.filtros['renda_max'])  # Corrigido: usando parênteses
                )
                st.session_state.filtros['renda_min'] = renda_min
                st.session_state.filtros['renda_max'] = renda_max

        # Aplicar filtros usando os valores do session_state
        df_filtrado = df_perfil.copy()

        if 'genero' in df_filtrado.columns and st.session_state.filtros['genero']:
            df_filtrado = df_filtrado[df_filtrado['genero'].isin(st.session_state.filtros['genero'])]

        if 'idade_atual' in df_filtrado.columns:
            df_filtrado = df_filtrado[
                (df_filtrado['idade_atual'] >= st.session_state.filtros['idade_min']) & 
                (df_filtrado['idade_atual'] <= st.session_state.filtros['idade_max'])
            ]

        if 'nivel_educacional' in df_filtrado.columns and st.session_state.filtros['educacao']:
            df_filtrado = df_filtrado[df_filtrado['nivel_educacional'].isin(st.session_state.filtros['educacao'])]

        if 'qtd_dependente' in df_filtrado.columns:
            df_filtrado = df_filtrado[
                (df_filtrado['qtd_dependente'] >= st.session_state.filtros['dependentes_min']) & 
                (df_filtrado['qtd_dependente'] <= st.session_state.filtros['dependentes_max'])
            ]

        if 'renda_mensal' in df_filtrado.columns:
            df_filtrado = df_filtrado[
                (df_filtrado['renda_mensal'] >= st.session_state.filtros['renda_min']) & 
                (df_filtrado['renda_mensal'] <= st.session_state.filtros['renda_max'])
            ]

        # Mostrar contagem de resultados
        st.info(f"📊 {len(df_filtrado)} clientes encontrados com os filtros selecionados")

        # Colunas para mostrar
        cols_to_show = [
            'nome', 'genero', 'idade_atual', 'nivel_educacional',
            'qtd_dependente', 'total_contratos', 'renda_mensal'
        ]
        cols_to_show = [col for col in cols_to_show if col in df_filtrado.columns]

        # Exibir tabela filtrada
        if cols_to_show:
            st.dataframe(
                df_filtrado[cols_to_show].head(5000),
                use_container_width=True,
                height=400
            )
            
            # Botão de exportação dos dados filtrados
            st.download_button(
                "📥 Exportar Dados Filtrados",
                data=df_filtrado[cols_to_show].to_csv(index=False).encode('utf-8'),
                file_name="clientes_filtrados.csv",
                mime="text/csv"
            )
        else:
            st.warning("Nenhuma coluna disponível para exibição")
    
    except Exception as e:
        st.error(f"Erro ao processar dados: {str(e)}")

if __name__ == "__main__":
    render()