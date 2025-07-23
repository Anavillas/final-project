import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import altair as alt # Certifique-se de que altair está importado
from backend.data.processed.loading_views import carregar_view

# Importa a função kpi_custom de frontend.pages.home
# Certifique-se de que frontend/pages/home.py contém a definição de kpi_custom
from frontend.pages.home import kpi_custom

# --- INJEÇÃO DE CSS GLOBAL ---
# Este CSS é essencial para estilizar os KPIs e containers.
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
        color: #333333;
        font-weight: 600;
        margin-bottom: 15px;
    }
    /* Estilo para containers com borda (usado para os cards grandes) */
    .stContainer {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        padding: 20px;
        background-color: white;
    }
    /* Estilo para o seletor (selectbox) de período */
    div[data-testid="stSelectbox"] div[role="button"] {
        border-radius: 8px;
        border: 1px solid #ccc;
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
    /* Estilo para os KPIs (caixas de métricas) - ATUALIZADO PARA LAYOUT HORIZONTAL */
    .kpi-box {
        position: relative;
        display: flex; /* ATUALIZADO: Usar flexbox */
        align-items: center; /* ATUALIZADO: Alinha itens verticalmente no centro */
        justify-content: flex-start; /* ATUALIZADO: Alinha itens ao início (esquerda) */
        background-color: white;
        border-radius: 12px;
        padding: 12px 16px;
        width: 100%;
        margin-bottom: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        font-family: Arial, sans-serif;
        /* Removido: flex-direction: column; e text-align: center; gap: 5px; */
    }
    .kpi-icon {
        width: 100px; /* Largura fixa para o ícone */
        height: 100px; /* Altura fixa para o ícone */
        margin-right: 14px; /* Espaço à direita do ícone */
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 55px; /* Tamanho do ícone */
        color: #3377ff;
    }
    .kpi-content {
        flex-grow: 1; /* Permite que o conteúdo de texto ocupe o espaço restante */
        text-align: left; /* ATUALIZADO: Alinha o texto à esquerda */
    }
    .kpi-value {
        font-size: 32px !important; /* ATUALIZADO: Tamanho do valor do KPI */
        font-weight: 700;
        margin: 0;
        color: #111827;
    }
    .kpi-explanation {
        margin-top: 4px;
        font-size: 13px;
        color: #555;
    }
    /* Ajustes para gráficos Plotly dentro de containers */
    .chart-container {
        height: 350px; /* Altura padrão para os gráficos */
        display: flex;
        align-items: center;
        justify-content: center;
    }
        .metric-box {
        background-color: #e0f2f7; /* Cor de fundo suave */
        border-left: 5px solid #64B5F6; /* Borda esquerda azul para 'Ativos' */
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
    }
    .metric-box.inactive-no-risk { /* Nova classe para inativos sem risco */
        border-left: 5px solid #1E90FF; /* Borda esquerda azul escuro */
    }
    .metric-box.inactive { /* Original para inativos, pode ser usado para o total de inativos */
        border-left: 5px solid #1976D2; /* Borda esquerda azul escuro para 'Inativos' */
    }
    .metric-box.risk {
        border-left: 5px solid #D32F2F; /* Borda esquerda vermelha para 'Em risco' */
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

# Configuração de caminhos (mantida)
raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if raiz_projeto not in sys.path:
    sys.path.insert(0, raiz_projeto)


def render():
    try:
        # Carrega os dados (agora mockados)
        df_perfil = carregar_view('v_perfil_cliente_enriquecido')
        df_detalhados = carregar_view('v_contratos_detalhados') # Mantido, mas não usado diretamente para os KPIs aqui

        # ========== SEÇÃO DE KPIS ==========
        st.markdown("## KPIs Principais")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            # Ícones Font Awesome são preferíveis para kpi_custom se a classe for passada
            # O kpi_custom de home.py espera icon_class (string para classe FA)
            kpi_custom("fas fa-users", f"{len(df_perfil):,}", "Clientes Totais")

        with col2:
            media_dep = df_perfil['qtd_dependente'].mean()
            kpi_custom("fas fa-child", f"{media_dep:.1f}", "Média Dependentes") # Ícone ajustado

        with col3:
            multi_contr = len(df_perfil[df_perfil['total_contratos'] > 1])
            kpi_custom("fas fa-file-contract", f"{multi_contr}", "Clientes +1 Contrato") # Ícone ajustado

        with col4:
            renda_media = f"R${df_perfil['renda_mensal'].mean():,.2f}"
            kpi_custom("fas fa-money-bill-wave", renda_media, "Renda Média") # Ícone ajustado

        st.markdown("---")

        # ========== SEÇÃO DE GRÁFICOS ==========
        # AJUSTE AQUI: Colunas com proporções [2, 1] - Esquerda maior, Direita menor
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
                        height=350 # Altura fixa para o gráfico
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Coluna 'nivel_educacional' não encontrada ou DataFrame vazio.")
            
            st.write("") # Espaçamento entre cards
            
            # Card 2: Gráfico Faixa Etária x Gênero
            with st.container(border=True):
                st.markdown("### Faixa Etária x Gênero")
                if 'idade_atual' in df_perfil.columns and 'genero' in df_perfil.columns and not df_perfil.empty:
                    df_perfil['faixa_etaria'] = pd.cut(
                        df_perfil['idade_atual'],
                        bins=[18, 30, 40, 50, 60, 100],
                        labels=["18-30", "31-40", "41-50", "51-60", "60+"],
                        right=False # Inclui o limite inferior, exclui o superior
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
                        height=350 # Altura fixa para o gráfico
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Colunas 'idade_atual' ou 'genero' não encontradas ou DataFrame vazio.")

        with col2_charts: # Usando col2_charts para evitar conflito
            # Card 3: Gráfico de Situação dos Clientes (GRÁFICO DE DONUT COM ALTAIR E INDICADORES)
            with st.container(border=True):
                st.markdown("### Situação Clientes") # Título do gráfico

                # --- Lógica para calcular porcentagens dinamicamente ---
                total_clientes = len(df_perfil)
                
                # Tratamento para evitar divisão por zero se df_perfil estiver vazio
                if total_clientes == 0:
                    st.warning("Não há dados de clientes para exibir a situação.")
                    # Define valores padrão ou sai da função se não houver dados
                    ativos_percent = 0
                    inativos_percent = 0
                    em_risco_percent = 0
                    inativos_sem_risco_percent = 0
                else:
                    # Assumindo que 'contratos_ativos' e 'status_risco' (ou similar) existem
                    # Mockando 'em_risco' se não existir para demonstração
                    if 'contratos_ativos' not in df_perfil.columns:
                        st.warning("Coluna 'contratos_ativos' não encontrada. Usando dados mockados para o gráfico de situação.")
                        # Usar dados mockados da imagem original se as colunas não existirem
                        ativos_percent = 60
                        inativos_percent = 40
                        em_risco_percent = 20
                        inativos_sem_risco_percent = 20 # 40 - 20
                    else:
                        # Cálculos dinâmicos
                        clientes_ativos = df_perfil[df_perfil['contratos_ativos'] > 0]
                        clientes_inativos = df_perfil[df_perfil['contratos_ativos'] == 0]

                        ativos_percent = round((len(clientes_ativos) / total_clientes) * 100, 1)

                        # Se 'v_perfil_cliente_enriquecido' tiver uma coluna 'status_cliente' com 'Ativo', 'Inativo', 'Em Risco':
                        if 'status_cliente' in df_perfil.columns:
                            # Calcular as porcentagens com base na coluna 'status_cliente'
                            total_clientes_situacao = df_perfil['status_cliente'].count() 

                            # Evitar divisão por zero
                            if total_clientes_situacao > 0:
                                count_ativos = df_perfil[df_perfil['status_cliente'] == 'Ativo'].shape[0]
                                count_inativos = df_perfil[df_perfil['status_cliente'] == 'Inativo'].shape[0] # Este é o "Inativo (sem risco)" se 'Em risco' é uma categoria separada
                                count_em_risco = df_perfil[df_perfil['status_cliente'] == 'Em risco'].shape[0]

                                ativos_percent = round((count_ativos / total_clientes_situacao) * 100, 1)
                                em_risco_percent = round((count_em_risco / total_clientes_situacao) * 100, 1)
                                inativos_sem_risco_percent = round((count_inativos / total_clientes_situacao) * 100, 1)
                                
                                # O total de inativos para o indicador seria em_risco_percent + inativos_sem_risco_percent
                                inativos_total_percent_for_indicator = em_risco_percent + inativos_sem_risco_percent
                            else:
                                ativos_percent = 0
                                inativos_sem_risco_percent = 0
                                em_risco_percent = 0
                                inativos_total_percent_for_indicator = 0
                        else:
                            # Se não há coluna 'status_cliente', usamos os valores da imagem
                            # e um aviso para o usuário.
                            st.warning("Coluna 'status_cliente' não encontrada. Usando valores mockados para o gráfico de situação (60% Ativos, 20% Inativos sem risco, 20% Em risco).")
                            ativos_percent = 60
                            inativos_percent = 40 # Este é o total de inativos para o indicador de texto (60 + 40 = 100)
                            em_risco_percent = 20
                            inativos_sem_risco_percent = 20 # 40% (inativos total) - 20% (em risco)
                            inativos_total_percent_for_indicator = inativos_percent


                # Dados para o gráfico de donut (usando os valores calculados/mockados)
                df_chart = pd.DataFrame({
                    'Categoria': ['Clientes Ativos', 'Clientes Inativos (sem risco)', 'Em risco'],
                    'Valor': [ativos_percent, inativos_sem_risco_percent, em_risco_percent]
                })

                # Cores para as categorias (mantidas do seu exemplo)
                color_scale = alt.Scale(domain=['Clientes Ativos', 'Clientes Inativos (sem risco)', 'Em risco'],
                                        range=['#6495ED', '#1E90FF', '#DC143C'])

                # Criando o gráfico de donut com Altair
                chart = alt.Chart(df_chart).mark_arc(outerRadius=120, innerRadius=80).encode(
                    theta=alt.Theta(field="Valor", type="quantitative"),
                    color=alt.Color(field="Categoria", scale=color_scale),
                    order=alt.Order(field="Valor", sort="descending"),
                    tooltip=['Categoria', alt.Tooltip("Valor", format=".1f") # Formata a porcentagem
                    ]
                ).properties(
                    # Ajusta a largura e altura do gráfico dentro do container
                    width=300, # Reduz a largura para caber no espaço menor da coluna
                    height=300 # Reduz a altura também
                ).configure_view(
                    strokeWidth=0 # Remove a borda do gráfico
                )

                # Exibindo o gráfico
                st.altair_chart(chart, use_container_width=True) # use_container_width=True para flexibilidade

                # Indicadores de porcentagem com caixas de destaque
                # As clases CSS '.metric-box', etc., já estão no cabeçalho CSS global
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
            
            st.write("") # Espaçamento entre cards
            
            # Card 4: Gráfico de Renda por Faixa Etária (permanece aqui)
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
                        height=350 # Altura fixa para o gráfico
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Dados insuficientes para renda por faixa etária.")

        # ========== SEÇÃO DE DADOS COM FILTROS ==========
        st.markdown("---")
        st.markdown("### Dados dos Clientes")

        # Inicializar session_state para filtros
        if 'filtros' not in st.session_state:
            st.session_state.filtros = {
                'genero': df_perfil['genero'].unique().tolist() if 'genero' in df_perfil.columns and not df_perfil.empty else [],
                'idade_min': int(df_perfil['idade_atual'].min()) if 'idade_atual' in df_perfil.columns and not df_perfil.empty else 0,
                'idade_max': int(df_perfil['idade_atual'].max()) if 'idade_atual' in df_perfil.columns and not df_perfil.empty else 100,
                'educacao': df_perfil['nivel_educacional'].unique().tolist() if 'nivel_educacional' in df_perfil.columns and not df_perfil.empty else [],
                'dependentes_min': int(df_perfil['qtd_dependente'].min()) if 'qtd_dependente' in df_perfil.columns and not df_perfil.empty else 0,
                'dependentes_max': int(df_perfil['qtd_dependente'].max()) if 'qtd_dependente' in df_perfil.columns and not df_perfil.empty else 10,
                'renda_min': float(df_perfil['renda_mensal'].min()) if 'renda_mensal' in df_perfil.columns and not df_perfil.empty else 0,
                'renda_max': float(df_perfil['renda_mensal'].max()) if 'renda_mensal' in df_perfil.columns and not df_perfil.empty else 10000
            }

        # Função para resetar filtros
        def resetar_filtros():
            defaults = {
                'genero': df_perfil['genero'].unique().tolist() if 'genero' in df_perfil.columns and not df_perfil.empty else [],
                'idade_min': int(df_perfil['idade_atual'].min()) if 'idade_atual' in df_perfil.columns and not df_perfil.empty else 0,
                'idade_max': int(df_perfil['idade_atual'].max()) if 'idade_atual' in df_perfil.columns and not df_perfil.empty else 100,
                'educacao': df_perfil['nivel_educacional'].unique().tolist() if 'nivel_educacional' in df_perfil.columns and not df_perfil.empty else [],
                'dependentes_min': int(df_perfil['qtd_dependente'].min()) if 'qtd_dependente' in df_perfil.columns and not df_perfil.empty else 0,
                'dependentes_max': int(df_perfil['qtd_dependente'].max()) if 'qtd_dependente' in df_perfil.columns and not df_perfil.empty else 10,
                'renda_min': float(df_perfil['renda_mensal'].min()) if 'renda_mensal' in df_perfil.columns and not df_perfil.empty else 0,
                'renda_max': float(df_perfil['renda_mensal'].max()) if 'renda_mensal' in df_perfil.columns and not df_perfil.empty else 10000
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
            generos = df_perfil['genero'].unique().tolist() if 'genero' in df_perfil.columns and not df_perfil.empty else []
            genero_selecionado = st.multiselect(
                "Gênero",
                options=generos,
                default=st.session_state.filtros['genero']
            )
            st.session_state.filtros['genero'] = genero_selecionado
            
            # 2. Filtro por Faixa Etária
            if 'idade_atual' in df_perfil.columns and not df_perfil.empty:
                idade_min_default = int(df_perfil['idade_atual'].min())
                idade_max_default = int(df_perfil['idade_atual'].max())
                idade_min, idade_max = st.slider(
                    "Faixa de Idade",
                    min_value=idade_min_default,
                    max_value=idade_max_default,
                    value=(st.session_state.filtros['idade_min'], st.session_state.filtros['idade_max'])
                )
                st.session_state.filtros['idade_min'] = idade_min
                st.session_state.filtros['idade_max'] = idade_max
            
            # 3. Filtro por Nível Educacional
            if 'nivel_educacional' in df_perfil.columns and not df_perfil.empty:
                educacao_options = df_perfil['nivel_educacional'].unique().tolist()
                educacao_selecionada = st.multiselect(
                    "Nível Educacional",
                    options=educacao_options,
                    default=st.session_state.filtros['educacao']
                )
                st.session_state.filtros['educacao'] = educacao_selecionada
            
            # 4. Filtro por Quantidade de Dependentes
            if 'qtd_dependente' in df_perfil.columns and not df_perfil.empty:
                dep_min_default = int(df_perfil['qtd_dependente'].min())
                dep_max_default = int(df_perfil['qtd_dependente'].max())
                dependentes_min, dependentes_max = st.slider(
                    "Número de Dependentes",
                    min_value=dep_min_default,
                    max_value=dep_max_default,
                    value=(st.session_state.filtros['dependentes_min'], st.session_state.filtros['dependentes_max'])
                )
                st.session_state.filtros['dependentes_min'] = dependentes_min
                st.session_state.filtros['dependentes_max'] = dependentes_max
            
            # 5. Filtro por Renda Mensal
            if 'renda_mensal' in df_perfil.columns and not df_perfil.empty:
                renda_min_default = float(df_perfil['renda_mensal'].min())
                renda_max_default = float(df_perfil['renda_mensal'].max())
                renda_min, renda_max = st.slider(
                    "Faixa de Renda Mensal (R$)",
                    min_value=renda_min_default,
                    max_value=renda_max_default,
                    value=(st.session_state.filtros['renda_min'], st.session_state.filtros['renda_max'])
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
        if cols_to_show and not df_filtrado.empty:
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
            st.warning("Nenhuma coluna disponível para exibição ou DataFrame vazio após filtros.")
    
    except Exception as e:
        st.error(f"Erro ao processar dados: {str(e)}")
        # No caso de erro na carga de dados, exibir o gráfico mockado como fallback
        st.title("Situação Clientes (Dados indisponíveis - Exibindo mock)")

        # Dados para o gráfico de donut (mockados para fallback)
        df_chart_fallback = pd.DataFrame({
            'Categoria': ['Clientes Ativos', 'Clientes Inativos (sem risco)', 'Em risco'],
            'Valor': [60, 20, 20] # 60% Ativos, 20% Inativos (sem risco), 20% Em Risco
        })

        # Cores para as categorias (ajuste conforme a imagem)
        color_scale_fallback = alt.Scale(domain=['Clientes Ativos', 'Clientes Inativos (sem risco)', 'Em risco'],
                                range=['#6495ED', '#1E90FF', '#DC143C'])

        chart_fallback = alt.Chart(df_chart_fallback).mark_arc(outerRadius=120, innerRadius=80).encode(
            theta=alt.Theta(field="Valor", type="quantitative"),
            color=alt.Color(field="Categoria", scale=color_scale_fallback),
            order=alt.Order(field="Valor", sort="descending"),
            tooltip=['Categoria', 'Valor']
        ).properties(
            width=400,
            height=400
        )
        st.altair_chart(chart_fallback, use_container_width=True)

        st.markdown("---")
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-percentage">60%</div>
                <div class="metric-label">Clientes Ativos</div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
            <div class="metric-box inactive">
                <div class="metric-percentage">40%</div>
                <div class="metric-label">Clientes Inativos</div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
            <div class="metric-box risk">
                <div class="metric-percentage">20%</div>
                <div class="metric-label">Em risco</div>
            </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    render()