import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
import logging

# --- CONSTANTES ---
BASE_PATH = Path(__file__).resolve().parent / 'data'
FAIXA_ETARIA = ([18, 30, 45, 60, 100], ['18-29', '30-44', '45-59', '60+'])
SATISFACAO_MAP = {'Baixa': 1, 'Média': 2, 'Alta': 3}

# --- CARREGAMENTO ---
@st.cache_data
def load_data():
    """Carrega e pré-processa os dados principais"""
    try:
        dfs = [pd.read_csv(BASE_PATH / f) for f in [
            'P18_clientes.csv', 'P18_contratos.csv', 'P18_cancelamentos.csv']]
        
        # Clientes
        dfs[0]['data_nascimento'] = pd.to_datetime(dfs[0]['data_nascimento'], errors='coerce')
        dfs[0]['idade'] = (pd.Timestamp.now() - dfs[0]['data_nascimento']).dt.days // 365
        dfs[0]['faixa_etaria'] = pd.cut(dfs[0]['idade'], *FAIXA_ETARIA)
        dfs[0]['data_cadastro'] = pd.to_datetime(dfs[0]['data_cadastro'], errors='coerce')
        
        # Contratos
        dfs[1]['data_inicio'] = pd.to_datetime(dfs[1]['data_inicio'], errors='coerce')
        dfs[1]['data_fim'] = pd.to_datetime(dfs[1]['data_fim'], errors='coerce')
        dfs[1]['duracao_contrato'] = (dfs[1]['data_fim'] - dfs[1]['data_inicio']).dt.days
        dfs[1]['satisfacao_numerica'] = dfs[1]['satisfacao_ultima_avaliacao'].map(SATISFACAO_MAP)
        dfs[1]['valor_premio_mensal'] = dfs[1].get('valor_premio_mensal', 100)
        
        # Cancelamentos
        dfs[2]['avaliacao_experiencia_numerica'] = dfs[2][
            'avaliacao_experiencia_cancelamento'].map(SATISFACAO_MAP)
            
        return dfs
        
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        raise

# --- FUNÇÕES ---
def calcular_nps(satisfacao_series):
    """Calcula o NPS a partir de uma série de satisfação numérica (1-3)"""
    satisf = satisfacao_series.dropna()
    detratores = satisf[satisf <= 1.5].count()
    promotores = satisf[satisf > 2.5].count()
    total = detratores + satisf.between(1.5, 2.5).sum() + promotores
    return round((promotores - detratores) / total * 100, 2) if total > 0 else "N/A"

@st.cache_data
def criar_df_completo(df_clientes, df_contratos, df_cancelamentos):
    """Combina todos os DataFrames"""
    df = pd.merge(df_contratos, df_clientes, on='id_cliente', how='left')
    df['cancelado'] = df['id_contrato'].isin(df_cancelamentos['id_contrato'])
    df['faixa_etaria'] = pd.cut(df['idade'], *FAIXA_ETARIA)
    return df

def criar_grafico(tipo='bar', **kwargs):
    """Cria gráficos com estilo padronizado"""
    fig, ax = plt.subplots(figsize=(10, 6))
    {
        'bar': lambda: sns.barplot(**kwargs, ax=ax),
        'line': lambda: sns.lineplot(**kwargs, ax=ax),
        'pie': lambda: ax.pie(**kwargs) or ax.axis('equal')
    }.get(tipo, lambda: None)()
    ax.set_title(kwargs.get('title', ''))
    ax.grid(True, linestyle='--', alpha=0.7)
    return fig

# --- VISÕES ---
def view_visao_geral(df_clientes, df_contratos, df_cancelamentos):
    """Mostra a visão geral da saúde da base de clientes"""
    st.header("🔵 Visão Geral – Saúde da Base")
    
    # Dados calculados
    total_contratos = len(df_contratos)
    cancelamentos = len(df_cancelamentos)
    taxa_churn = (cancelamentos/total_contratos)*100 if total_contratos else 0
    taxa_renovacao = df_contratos['renovado_automaticamente'].mean()*100
    satisfacao_media = df_contratos['satisfacao_numerica'].mean()
    
    # Layout em 3 seções como na imagem de referência
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📊 Série 1")
        st.markdown("**Clientes Ativos**")
        st.metric("", len(df_clientes), help="Total de clientes na base")
        
        st.markdown("**Contratos Ativos**")
        st.metric("", total_contratos - cancelamentos, help="Contratos não cancelados")
        
        st.markdown("**Cancelamentos**")
        st.metric("", cancelamentos, help="Total de cancelamentos")
    
    with col2:
        st.markdown("### 📈 Série 2")
        st.markdown("**Distribuição por Tipo de Seguro**")
        
        # Gráfico de pizza estilizado
        fig = plt.figure(figsize=(6,6))
        tipos = df_contratos['tipo_seguro'].value_counts()
        plt.pie(tipos, labels=tipos.index, autopct='%1.1f%%', 
                startangle=90, colors=['#3498db','#2ecc71','#e74c3c','#f39c12'])
        plt.axis('equal')
        st.pyplot(fig)
        
    with col3:
        st.markdown("### 📊 Indicadores")
        
        # Indicador circular para % Churn
        st.markdown(f"**Churn Rate**")
        st.markdown(f"<div style='font-size:24px;text-align:center;'>{taxa_churn:.1f}%</div>", 
                   unsafe_allow_html=True)
        st.progress(taxa_churn/100)
        
        # Indicador circular para % Renovados
        st.markdown(f"**Renovados Automático**")
        st.markdown(f"<div style='font-size:24px;text-align:center;'>{taxa_renovacao:.1f}%</div>", 
                   unsafe_allow_html=True)
        st.progress(taxa_renovacao/100)
        
        # Indicador de satisfação
        st.markdown(f"**Satisfação Média**")
        st.markdown(f"<div style='font-size:24px;text-align:center;'>{satisfacao_media:.2f}</div>", 
                   unsafe_allow_html=True)
        st.progress(satisfacao_media/3)

def view_perfil_cliente(df_clientes, df_contratos):
    """Mostra análises do perfil dos clientes com layout profissional"""
    st.header("🟡 Perfil do Cliente")
    
    # Dados calculados
    media_dependentes = df_clientes['qtd_dependentes'].mean()
    multiplos_contratos = (df_contratos['id_cliente'].value_counts() > 1).sum()
    
    # Layout em 3 seções principais
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📊 Distribuições Demográficas")
        
        # Gráfico de Faixa Etária
        st.markdown("**Faixa Etária**")
        faixa_counts = df_clientes['faixa_etaria'].value_counts().sort_index()
        faixa_counts.index = faixa_counts.index.astype(str)
        st.bar_chart(faixa_counts, color='#3498db')
        
        # Gráficos em abas
        tab1, tab2, tab3 = st.tabs(["Gênero", "Escolaridade", "Estado"])
        
        with tab1:
            st.markdown("**Distribuição por Gênero**")
            st.bar_chart(df_clientes['genero'].value_counts(), color='#2ecc71')
            
        with tab2:
            st.markdown("**Nível Educacional**")
            st.bar_chart(df_clientes['nivel_educacional'].value_counts(), color='#e74c3c')
            
        with tab3:
            st.markdown("**Estado de Residência**")
            st.bar_chart(df_clientes['estado_residencia'].value_counts(), color='#f39c12')
    
    with col2:
        st.markdown("### 📈 Indicadores-Chave")
        
        # Métricas principais
        st.markdown("**Média de Dependentes**")
        st.markdown(f"<div style='font-size:28px; text-align:center; padding:10px; "
                   f"background-color:#f8f9fa; border-radius:10px;'>{media_dependentes:.2f}</div>",
                   unsafe_allow_html=True)
        
        st.markdown("**Clientes com Múltiplos Contratos**")
        st.markdown(f"<div style='font-size:28px; text-align:center; padding:10px; "
                   f"background-color:#f8f9fa; border-radius:10px;'>{multiplos_contratos}</div>",
                   unsafe_allow_html=True)
        
        st.markdown("### 🔝 Top Profissões")
        top_profissoes = df_clientes['profissao'].value_counts().head(10)
        st.dataframe(
            top_profissoes.reset_index().rename(columns={'index':'Profissão', 'profissao':'Contagem'}),
            height=400,
            hide_index=True
        )

def view_produtos_planos(df_contratos):
    """Mostra análises de produtos e planos com layout profissional"""
    st.header("🔴 Produtos e Planos de Seguro")
    
    # Dados calculados
    tipo_dist = df_contratos['tipo_seguro'].value_counts()
    
    # Layout em 2 colunas principais
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📊 Distribuição de Planos")
        
        # Gráfico de barras horizontal moderno
        st.plotly_chart(px.bar(
            tipo_dist.reset_index(),
            x='count',
            y='tipo_seguro',
            orientation='h',
            color='tipo_seguro',
            color_discrete_sequence=px.colors.qualitative.Pastel,
            labels={'count': 'Número de Contratos', 'tipo_seguro': 'Tipo de Seguro'},
            height=400
        ).update_layout(showlegend=False), use_container_width=True)
        
    with col2:
        st.markdown("### 📈 Satisfação por Plano")
        
        # Gráfico de satisfação
        satisfacao_por_tipo = df_contratos.groupby('tipo_seguro')['satisfacao_numerica'].mean()
        st.plotly_chart(px.bar(
            satisfacao_por_tipo.reset_index(),
            x='tipo_seguro',
            y='satisfacao_numerica',
            color='tipo_seguro',
            color_discrete_sequence=px.colors.qualitative.Pastel,
            labels={'satisfacao_numerica': 'Satisfação Média', 'tipo_seguro': 'Tipo de Seguro'},
            height=400
        ).update_layout(showlegend=False), use_container_width=True)
    
    # Seção de métricas detalhadas
    st.markdown("### 📋 Métricas por Tipo de Seguro")
    
    metricas = {
        'duracao_contrato': 'Duração Média (dias)',
        'satisfacao_numerica': 'Satisfação Média',
        'id_contrato': 'Total Contratos',
        **({'valor_premio_mensal': 'Valor Médio'} if 'valor_premio_mensal' in df_contratos.columns else {})
    }
    
    df_metricas = df_contratos.groupby('tipo_seguro').agg({
        col: 'mean' if col != 'id_contrato' else 'count' for col in metricas
    }).rename(columns=metricas)
    
    # Tabela estilizada
    st.dataframe(
        df_metricas.style
        .format({
            'Duração Média (dias)': '{:.1f}',
            'Satisfação Média': '{:.2f}',
            **({'Valor Médio': 'R$ {:.2f}'} if 'Valor Médio' in df_metricas.columns else {})
        })
        .background_gradient(cmap='Blues', subset=['Satisfação Média'])
        .background_gradient(cmap='Greens', subset=['Duração Média (dias)'])
        .set_properties(**{'text-align': 'center'}),
        height=400,
        use_container_width=True
    )

def view_satisfacao_experiencia(df_contratos, df_cancelamentos):
    """Mostra análises de satisfação com layout profissional"""
    st.header("🟢 Satisfação e Experiência")
    
    # Dados calculados
    satisfacao_por_tipo = df_contratos.groupby('tipo_seguro')['satisfacao_numerica'].mean().sort_values()
    satisfacao_por_canal = df_contratos.groupby('canal_venda')['satisfacao_numerica'].mean().sort_values()
    canais_cancelamento = df_cancelamentos['canal_cancelamento'].value_counts()
    nps = calcular_nps(df_contratos['satisfacao_numerica'])
    
    # Layout em 2 colunas principais
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 😊 Satisfação por Tipo de Seguro")
        st.plotly_chart(px.bar(
            satisfacao_por_tipo.reset_index(),
            x='satisfacao_numerica',
            y='tipo_seguro',
            orientation='h',
            color='satisfacao_numerica',
            color_continuous_scale='Tealgrn',
            labels={'satisfacao_numerica': 'Satisfação Média', 'tipo_seguro': 'Tipo de Seguro'},
            height=400
        ), use_container_width=True)
        
        st.markdown("### 📉 Canais de Cancelamento")
        st.plotly_chart(px.bar(
            canais_cancelamento.reset_index(),
            x='count',
            y='canal_cancelamento',
            orientation='h',
            color='count',
            color_continuous_scale='Reds',
            labels={'count': 'Número de Cancelamentos', 'canal_cancelamento': 'Canal'},
            height=300
        ), use_container_width=True)
    
    with col2:
        st.markdown("### 📞 Satisfação por Canal de Venda")
        st.plotly_chart(px.bar(
            satisfacao_por_canal.reset_index(),
            x='canal_venda',
            y='satisfacao_numerica',
            color='satisfacao_numerica',
            color_continuous_scale='Tealgrn',
            labels={'satisfacao_numerica': 'Satisfação Média', 'canal_venda': 'Canal de Venda'},
            height=400
        ), use_container_width=True)
        
        st.markdown("### 📊 NPS Estimado")
        # Indicador visual do NPS
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=nps if isinstance(nps, (int, float)) else 0,
            number={'suffix': ''},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [-100, 100]},
                'bar': {'color': "#2ecc71"},
                'steps': [
                    {'range': [-100, 0], 'color': "#e74c3c"},
                    {'range': [0, 50], 'color': "#f39c12"},
                    {'range': [50, 100], 'color': "#2ecc71"}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': nps if isinstance(nps, (int, float)) else 0
                }
            }
        ))
        fig.update_layout(height=300, margin=dict(t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)
        
        # Legenda do NPS
        st.markdown("""
        <div style='background-color:#f8f9fa; border-radius:10px; padding:10px; margin-top:10px;'>
            <p style='text-align:center;'>
                <span style='color:#e74c3c;'>●</span> Detratores | 
                <span style='color:#f39c12;'>●</span> Neutros | 
                <span style='color:#2ecc71;'>●</span> Promotores
            </p>
        </div>
        """, unsafe_allow_html=True)

def view_retencao_churn(df_completo):
    """Mostra análises de retenção e churn com layout profissional"""
    st.header("🟣 Retenção e Churn")
    
    # Dados calculados
    canceladores = df_completo[df_completo['cancelado']]
    contratos_por_cliente = df_completo['id_cliente'].value_counts()
    clientes_um_contrato = contratos_por_cliente[contratos_por_cliente == 1].index
    taxa_cancelamento = df_completo[df_completo['id_cliente'].isin(clientes_um_contrato)]['cancelado'].mean()
    relacao_renovacao = df_completo.groupby('renovado_automaticamente')['cancelado'].mean().rename(
        {True: 'Renovaram', False: 'Não Renovaram'})
    risco_churn = df_completo.groupby('duracao_contrato')['cancelado'].mean()
    
    # Layout em 2 colunas principais
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📊 Perfil dos Canceladores")
        
        # CORREÇÃO: Estatísticas descritivas sem tentar estilizar colunas específicas
        desc_stats = canceladores[['idade', 'tipo_seguro', 'satisfacao_numerica']].describe()
        st.dataframe(
            desc_stats.style
            .format('{:.2f}')
            .background_gradient(cmap='Reds')  # Aplica gradiente em todas as colunas numéricas
            .set_properties(**{'text-align': 'center'}),
            height=300
        )
        
        st.markdown("### 📉 Risco de Churn por Duração")
        st.plotly_chart(px.line(
            risco_churn.reset_index(),
            x='duracao_contrato',
            y='cancelado',
            labels={'duracao_contrato': 'Duração do Contrato (dias)', 'cancelado': 'Taxa de Cancelamento'},
            color_discrete_sequence=['#e74c3c'],
            height=300
        ), use_container_width=True)
    
    with col2:
        st.markdown("### 📌 Indicadores-Chave")
        
        # Card de taxa de cancelamento (com tratamento para NaN)
        taxa_display = taxa_cancelamento*100 if not pd.isna(taxa_cancelamento) else 0
        st.markdown("**Cancelamento com 1 Contrato**")
        st.markdown(f"""
        <div style='background-color:#f8f9fa; border-radius:10px; padding:20px; margin-bottom:20px;'>
            <h3 style='color:#e74c3c; text-align:center; margin-top:0;'>
                {taxa_display:.1f}%
            </h3>
            <p style='text-align:center;'>dos clientes com apenas 1 contrato cancelaram</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🔄 Renovação vs Cancelamento")
        st.plotly_chart(px.bar(
            relacao_renovacao.reset_index(),
            x='renovado_automaticamente',
            y='cancelado',
            color='renovado_automaticamente',
            color_discrete_map={'Renovaram': '#2ecc71', 'Não Renovaram': '#e74c3c'},
            labels={'cancelado': 'Taxa de Cancelamento', 'renovado_automaticamente': ''},
            height=300
        ).update_layout(showlegend=False), use_container_width=True)
        
        # Heatmap de risco
        st.markdown("### 🔥 Fatores de Risco")
        try:
            st.plotly_chart(px.density_heatmap(
                canceladores,
                x='idade',
                y='satisfacao_numerica',
                nbinsx=10,
                nbinsy=3,
                color_continuous_scale='reds',
                labels={'idade': 'Idade', 'satisfacao_numerica': 'Satisfação'}
            ), use_container_width=True)
        except Exception as e:
            st.warning("Não foi possível gerar o heatmap de fatores de risco")
            st.error(str(e))
    
def view_insights_acoes(df_completo):
    """Mostra insights acionáveis com layout profissional"""
    st.header("🟤 Insights e Ações")
    
    # Cria e prepara os dados
    df = df_completo.copy()
    df['faixa_etaria'] = df['faixa_etaria'].astype(str)
    
    # Dados calculados
    churn_tipo = df.groupby('tipo_seguro')['cancelado'].mean().sort_values(ascending=False)
    churn_faixa_etaria = df.groupby('faixa_etaria')['cancelado'].mean()
    churn_profissao = df.groupby('profissao')['cancelado'].mean().nlargest(10)
    churn_estado = df.groupby('estado_residencia')['cancelado'].mean().sort_values(ascending=False)
    
    # Layout principal
    st.markdown("### 🔥 Planos com Maior Risco de Churn")
    
    # Gráfico e tabela lado a lado
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.plotly_chart(px.bar(
            churn_tipo.head(5).reset_index(),
            x='tipo_seguro',
            y='cancelado',
            color='tipo_seguro',
            color_discrete_sequence=px.colors.sequential.Reds,
            labels={'cancelado': 'Taxa de Cancelamento', 'tipo_seguro': 'Tipo de Seguro'},
            height=400
        ), use_container_width=True)
    
    with col2:
        st.dataframe(
            churn_tipo.head(5).reset_index().rename(columns={'cancelado': 'Taxa Cancelamento'})
            .style
            .background_gradient(cmap='Reds', subset=['Taxa Cancelamento'])
            .format({'Taxa Cancelamento': '{:.2%}'}),
            height=400,
            use_container_width=True
        )
    
    # Análises segmentadas em abas
    st.markdown("### 📊 Análise Segmentada")
    tab1, tab2, tab3 = st.tabs(["Faixa Etária", "Profissão", "Estado"])
    
    with tab1:
        st.markdown("#### 📉 Taxa de Cancelamento por Faixa Etária")
        st.plotly_chart(px.bar(
            churn_faixa_etaria.reset_index(),
            x='faixa_etaria',
            y='cancelado',
            color='faixa_etaria',
            color_discrete_sequence=px.colors.sequential.Reds,
            labels={'cancelado': 'Taxa de Cancelamento', 'faixa_etaria': 'Faixa Etária'},
            height=400
        ), use_container_width=True)
    
    with tab2:
        st.markdown("#### 👔 Top 10 Profissões com Maior Churn")
        st.dataframe(
            churn_profissao.reset_index().rename(columns={'cancelado': 'Taxa Cancelamento'})
            .style
            .background_gradient(cmap='Reds', subset=['Taxa Cancelamento'])
            .format({'Taxa Cancelamento': '{:.2%}'})
            .set_properties(**{'text-align': 'left'}),
            height=500,
            use_container_width=True
        )
    
    with tab3:
        st.markdown("#### 🗺️ Taxa de Cancelamento por Estado")
        st.plotly_chart(px.bar(
            churn_estado.reset_index(),
            x='cancelado',
            y='estado_residencia',
            orientation='h',
            color='cancelado',
            color_continuous_scale='reds',
            labels={'cancelado': 'Taxa de Cancelamento', 'estado_residencia': 'Estado'},
            height=600
        ), use_container_width=True)
    
    # Recomendações de ações
    st.markdown("### 🚀 Recomendações de Ações")
    cols = st.columns(3)
    
    with cols[0]:
        st.markdown("**Alto Risco**")
        st.markdown("""
        - Contato proativo
        - Oferta de incentivos
        - Planos alternativos
        """)
    
    with cols[1]:
        st.markdown("**Médio Risco**")
        st.markdown("""
        - Monitoramento
        - Campanhas de engajamento
        - Pesquisa de satisfação
        """)
    
    with cols[2]:
        st.markdown("**Baixo Risco**")
        st.markdown("""
        - Programas de fidelização
        - Benefícios exclusivos
        - Upselling
        """)

# --- MAIN ---
def main():
    try:
        df_clientes, df_contratos, df_cancelamentos = load_data()
        df_completo = criar_df_completo(df_clientes, df_contratos, df_cancelamentos)
    except:
        return st.stop()
    
    VIEWS = {
        "🔵 Visão Geral": lambda: view_visao_geral(df_clientes, df_contratos, df_cancelamentos),
        "🟡 Perfil Cliente": lambda: view_perfil_cliente(df_clientes, df_contratos),
        "🔴 Produtos/Planos": lambda: view_produtos_planos(df_contratos),
        "🟢 Satisfação": lambda: view_satisfacao_experiencia(df_contratos, df_cancelamentos),
        "🟣 Retenção/Churn": lambda: view_retencao_churn(df_completo),
        "🟤 Insights": lambda: view_insights_acoes(df_completo)
    }
    
    st.sidebar.title("Navegação")
    view_selecionada = st.sidebar.radio("Escolha uma seção:", list(VIEWS.keys()))
    VIEWS[view_selecionada]()

if __name__ == "__main__":
    main()