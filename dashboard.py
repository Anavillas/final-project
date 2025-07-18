import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import logging

# --- CONSTANTES E CONFIGURAÇÕES ---
BASE_PATH = Path(r'C:\Users\Aluno\Documents\GitHub\final-project\data')
FAIXA_ETARIA_BINS = [18, 30, 45, 60, 100]
FAIXA_ETARIA_LABELS = ['18-29', '30-44', '45-59', '60+']
SATISFACAO_MAP = {'Baixa': 1, 'Média': 2, 'Alta': 3}

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CARREGAMENTO DE DADOS ---
@st.cache_data
def load_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Carrega e pré-processa os dados principais
    
    Returns:
        Tuple contendo (df_clientes, df_contratos, df_cancelamentos)
    """
    try:
        with st.spinner('Carregando dados...'):
            df_clientes = pd.read_csv(BASE_PATH / 'P18_clientes.csv')
            df_contratos = pd.read_csv(BASE_PATH / 'P18_contratos.csv')
            df_cancelamentos = pd.read_csv(BASE_PATH / 'P18_cancelamentos.csv')
            
            # Pré-processamento de clientes
            df_clientes['data_nascimento'] = pd.to_datetime(df_clientes['data_nascimento'], errors='coerce')
            df_clientes['idade'] = (pd.Timestamp.now() - df_clientes['data_nascimento']).dt.days // 365
            df_clientes['faixa_etaria'] = pd.cut(df_clientes['idade'], bins=FAIXA_ETARIA_BINS, 
                                                labels=FAIXA_ETARIA_LABELS, right=False)
            df_clientes['data_cadastro'] = pd.to_datetime(df_clientes['data_cadastro'], errors='coerce')
            
            # Pré-processamento de contratos
            df_contratos['data_inicio'] = pd.to_datetime(df_contratos['data_inicio'], errors='coerce')
            df_contratos['data_fim'] = pd.to_datetime(df_contratos['data_fim'], errors='coerce')
            df_contratos['duracao_contrato'] = (df_contratos['data_fim'] - df_contratos['data_inicio']).dt.days
            df_contratos['satisfacao_numerica'] = df_contratos['satisfacao_ultima_avaliacao'].map(SATISFACAO_MAP)
            
            # Verifica se a coluna valor_mensal existe, caso contrário cria com valores padrão
            if 'valor_mensal' not in df_contratos.columns:
                df_contratos['valor_mensal'] = 100  # Valor padrão para demonstração
            
            # Pré-processamento de cancelamentos
            df_cancelamentos['avaliacao_experiencia_numerica'] = (
                df_cancelamentos['avaliacao_experiencia_cancelamento'].map(SATISFACAO_MAP)
            )
            
            logger.info("Dados carregados e pré-processados com sucesso")
            return df_clientes, df_contratos, df_cancelamentos
    except Exception as e:
        logger.error(f"Erro ao carregar dados: {str(e)}")
        st.error("Erro ao carregar os dados. Verifique os arquivos de entrada.")
        raise

# Carrega os dados
try:
    df_clientes, df_contratos, df_cancelamentos = load_data()
except:
    st.stop()

# --- FUNÇÕES AUXILIARES ---
def calcular_nps(satisfacao_series: pd.Series) -> float:
    """Calcula o NPS a partir de uma série de satisfação numérica (1-3)
    
    Args:
        satisfacao_series: Série pandas com valores de satisfação (1-3)
        
    Returns:
        Valor do NPS calculado ou "N/A" se não houver dados
    """
    try:
        satisf = satisfacao_series.dropna()
        
        # Definindo os limites corretos para NPS em escala 1-3
        detratores = satisf[satisf <= 1.5].count()  # 1.0-1.5: Detratores (1)
        promotores = satisf[satisf > 2.5].count()   # 2.5-3.0: Promotores (3)
        neutros = satisf[(satisf > 1.5) & (satisf <= 2.5)].count()  # 1.5-2.5: Neutros (2)
        
        total_respostas = detratores + neutros + promotores
        
        if total_respostas > 0:
            nps = ((promotores - detratores) / total_respostas) * 100
            return round(nps, 2)
        return "N/A"
    except Exception as e:
        logger.error(f"Erro ao calcular NPS: {str(e)}")
        return "N/A"

def criar_df_completo() -> pd.DataFrame:
    """Cria um DataFrame combinado com todas as informações
    
    Returns:
        DataFrame combinado com informações de clientes, contratos e cancelamentos
    """
    try:
        with st.spinner('Combinando dados...'):
            df_all = pd.merge(df_contratos, df_clientes, on='id_cliente', how='left')
            df_all['cancelado'] = df_all['id_contrato'].isin(df_cancelamentos['id_contrato'])
            df_all['faixa_etaria'] = pd.cut(df_all['idade'], bins=FAIXA_ETARIA_BINS, 
                                           labels=FAIXA_ETARIA_LABELS, right=False)
            return df_all
    except Exception as e:
        logger.error(f"Erro ao criar DataFrame completo: {str(e)}")
        st.error("Erro ao processar os dados. Tente recarregar a página.")
        raise

def criar_grafico_padrao(tipo: str = 'bar', **kwargs) -> plt.Figure:
    """Cria gráficos com estilo padronizado
    
    Args:
        tipo: Tipo de gráfico ('bar', 'line', 'pie')
        **kwargs: Argumentos específicos para cada tipo de gráfico
        
    Returns:
        Figura matplotlib configurada
    """
    try:
        plt.style.use('seaborn')
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if tipo == 'bar':
            sns.barplot(**kwargs, ax=ax)
            ax.set_xlabel(kwargs.get('xlabel', ''))
            ax.set_ylabel(kwargs.get('ylabel', ''))
        elif tipo == 'line':
            sns.lineplot(**kwargs, ax=ax)
        elif tipo == 'pie':
            ax.pie(**kwargs)
            ax.axis('equal')
        
        ax.set_title(kwargs.get('title', ''))
        ax.grid(True, linestyle='--', alpha=0.7)
        return fig
    except Exception as e:
        logger.error(f"Erro ao criar gráfico: {str(e)}")
        raise

# --- VISÕES ---
def view_visao_geral():
    """Mostra a visão geral da saúde da base de clientes"""
    st.header("🔵 Visão Geral – Saúde da Base")

    total_clientes = df_clientes['id_cliente'].nunique()
    total_contratos = df_contratos['id_contrato'].nunique()
    total_cancelamentos = df_cancelamentos['id_contrato'].nunique()
    contratos_ativos = total_contratos - total_cancelamentos
    churn_rate = total_cancelamentos / total_contratos if total_contratos > 0 else 0
    renovados = df_contratos['renovado_automaticamente'].value_counts(normalize=True).get(True, 0)
    satisfacao_media = df_contratos['satisfacao_numerica'].mean()
    tipos_seguro = df_contratos['tipo_seguro'].value_counts()

    # Métricas
    col1, col2, col3 = st.columns(3)
    col1.metric("Clientes", total_clientes)
    col2.metric("Contratos Ativos", contratos_ativos)
    col3.metric("Cancelamentos", total_cancelamentos)

    col4, col5, col6 = st.columns(3)
    col4.metric("% Churn", f"{churn_rate*100:.2f}%")
    col5.metric("% Renovados", f"{renovados*100:.1f}%")
    col6.metric("Satisfação Média", f"{satisfacao_media:.2f}")

    # Gráfico de tipos de seguro
    st.subheader("Distribuição por Tipo de Seguro")
    fig, ax = plt.subplots()
    ax.pie(tipos_seguro, labels=tipos_seguro.index, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    st.pyplot(fig)

def view_perfil_cliente():
    """Mostra análises do perfil dos clientes"""
    st.header("🟡 Perfil do Cliente")

    # Gráficos de distribuição
    st.subheader("Distribuição por Faixa Etária")
    st.bar_chart(df_clientes['faixa_etaria'].value_counts().sort_index())

    st.subheader("Distribuição por Gênero")
    st.bar_chart(df_clientes['genero'].value_counts())

    st.subheader("Distribuição por Escolaridade")
    st.bar_chart(df_clientes['nivel_educacional'].value_counts())

    st.subheader("Distribuição por Profissão (Top 10)")
    st.dataframe(df_clientes['profissao'].value_counts().head(10))

    st.subheader("Distribuição por Estado")
    st.bar_chart(df_clientes['estado_residencia'].value_counts())

    # Métricas
    col1, col2 = st.columns(2)
    col1.metric("Média de Dependentes", f"{df_clientes['qtd_dependentes'].mean():.2f}")
    
    contratos_por_cliente = df_contratos['id_cliente'].value_counts()
    multiplos = contratos_por_cliente[contratos_por_cliente > 1].count()
    col2.metric("Clientes com múltiplos contratos", multiplos)

    # Filtros dinâmicos
    st.subheader("Filtros Dinâmicos")
    genero_sel = st.multiselect("Gênero", df_clientes['genero'].unique())
    tipo_sel = st.multiselect("Tipo de Seguro", df_contratos['tipo_seguro'].unique())

    df_filtrado = pd.merge(df_clientes, df_contratos, on='id_cliente')
    if genero_sel:
        df_filtrado = df_filtrado[df_filtrado['genero'].isin(genero_sel)]
    if tipo_sel:
        df_filtrado = df_filtrado[df_filtrado['tipo_seguro'].isin(tipo_sel)]

    st.dataframe(df_filtrado[['id_cliente', 'genero', 'idade', 'tipo_seguro', 'renda_mensal']].head())

def view_produtos_planos():
    """Mostra análises específicas de produtos e planos de seguro"""
    st.header("🔴 Produtos e Planos de Seguro")
    
    # Análise de tipos de seguro
    st.subheader("Distribuição de Planos por Tipo")
    tipo_dist = df_contratos['tipo_seguro'].value_counts()
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=tipo_dist.values, y=tipo_dist.index, palette='viridis', ax=ax)
    ax.set_xlabel('Quantidade de Contratos')
    ax.set_ylabel('Tipo de Seguro')
    st.pyplot(fig)
    
    # Métricas por tipo de seguro - versão segura
    st.subheader("Métricas por Tipo de Seguro")
    
    # Cria um dicionário com as colunas disponíveis
    metricas = {
        'duracao_contrato': 'Duração Média (dias)',
        'satisfacao_numerica': 'Satisfação Média',
        'id_contrato': 'Total Contratos'
    }
    
    # Adiciona valor_mensal apenas se existir no DataFrame
    if 'valor_mensal' in df_contratos.columns:
        metricas['valor_mensal'] = 'Valor Médio'
    
    metricas_seguro = df_contratos.groupby('tipo_seguro').agg({
        col: 'mean' if col != 'id_contrato' else 'count' 
        for col in metricas.keys()
    }).rename(columns=metricas).sort_values('Total Contratos', ascending=False)
    
    # Formatação condicional
    format_dict = {
        'Duração Média (dias)': '{:.1f}',
        'Satisfação Média': '{:.2f}'
    }
    
    if 'Valor Médio' in metricas_seguro.columns:
        format_dict['Valor Médio'] = 'R$ {:.2f}'
    
    st.dataframe(metricas_seguro.style.format(format_dict))

def view_satisfacao_experiencia():
    """Mostra análises de satisfação e experiência do cliente"""
    st.header("🟢 Satisfação e Experiência")

    # Análise de satisfação por tipo de seguro
    st.subheader("Satisfação × Tipo de Seguro")
    media_satisf = df_contratos.groupby('tipo_seguro')['satisfacao_numerica'].mean().sort_values()
    st.bar_chart(media_satisf)

    # Análise por canal
    st.subheader("Nota Média por Canal de Venda")
    canal_venda_media = df_contratos.groupby('canal_venda')['satisfacao_numerica'].mean().sort_values()
    st.bar_chart(canal_venda_media)

    st.subheader("Canais de Cancelamento mais Frequentes")
    st.bar_chart(df_cancelamentos['canal_cancelamento'].value_counts())

    # NPS com cálculo revisado
    st.subheader("NPS Estimado (Escala 1-3)")
    nps = calcular_nps(df_contratos['satisfacao_numerica'])
    
    # Explicação do cálculo
    with st.expander("Como interpretar este NPS?"):
        st.markdown("""
        **NPS em escala 1-3:**
        - **1 (Baixa satisfação)**: Detratores
        - **2 (Média satisfação)**: Neutros  
        - **3 (Alta satisfação)**: Promotores
        
        **Fórmula:**  
        `NPS = (% Promotores) - (% Detratores)`  
        *Valores podem variar entre -100 (todos detratores) e +100 (todos promotores)*
        
        **Seu resultado:** {}
        """.format(nps))
    
    st.metric("NPS Estimado", f"{nps}")

def view_retencao_churn():
    """Mostra análises de retenção e churn"""
    st.header("🟣 Retenção e Churn (Prevenção)")
    df_all = criar_df_completo()

    # Perfil dos canceladores
    st.subheader("Perfil dos Canceladores")
    df_cancel = df_all[df_all['cancelado']]
    perfil = df_cancel[['idade', 'tipo_seguro', 'satisfacao_numerica']]
    st.dataframe(perfil.describe(include='all'))

    # Taxa de cancelamento para clientes com 1 contrato
    st.subheader("Cancelamento em Clientes com 1 Contrato")
    qtd_contratos = df_contratos['id_cliente'].value_counts()
    um_contrato = qtd_contratos[qtd_contratos == 1].index
    cancelaram = df_all[df_all['id_cliente'].isin(um_contrato)]['cancelado'].sum()
    taxa = cancelaram / len(um_contrato) if len(um_contrato) > 0 else 0
    st.metric("% Cancelaram com 1 contrato", f"{taxa*100:.2f}%")

    # Renovação vs Cancelamento
    st.subheader("Renovação × Cancelamento")
    taxa_renovacao = df_all.groupby('renovado_automaticamente')['cancelado'].mean()
    st.bar_chart(taxa_renovacao.rename(index={True: 'Renovaram', False: 'Não Renovaram'}))

    # Duração do contrato vs Churn
    st.subheader("Duração do Contrato × Risco de Churn")
    st.line_chart(df_all.groupby('duracao_contrato')['cancelado'].mean())

    # Identificação de clientes em risco
    st.subheader("Ranking de Clientes em Risco")
    df_all['risco'] = 'Baixo'
    df_all.loc[(df_all['satisfacao_numerica'] == 1) & (df_all['duracao_contrato'] < 365), 'risco'] = 'Médio'
    df_all.loc[(df_all['satisfacao_numerica'] == 1) & (df_all['duracao_contrato'] < 250), 'risco'] = 'Alto'
    st.dataframe(
        df_all[['id_cliente', 'tipo_seguro', 'satisfacao_numerica', 'duracao_contrato', 'risco']]
        .sort_values(by='risco', ascending=False)
        .head(10)
    )

    # Recomendações
    st.subheader("Ações Recomendadas para Retenção")
    st.markdown("""
    - **Alto risco**: Contato proativo, oferta de incentivos ou planos alternativos
    - **Médio risco**: Monitoramento com campanhas de engajamento
    - **Baixo risco**: Estratégias de fidelização e programas de benefícios
    """)

def view_insights_acoes():
    """Mostra insights acionáveis"""
    st.header("🟤 Insights e Ações")
    df_all = criar_df_completo()

    # Análises de churn
    st.subheader("Planos com Maior e Menor Churn")
    churn_tipo = df_all.groupby('tipo_seguro')['cancelado'].mean().sort_values(ascending=False)
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Piores planos (maior churn)**")
        st.dataframe(churn_tipo.head(5).reset_index().rename(columns={'cancelado': 'Taxa de Cancelamento'}))
    
    with col2:
        st.write("**Melhores planos (menor churn)**")
        st.dataframe(churn_tipo.tail(5).reset_index().rename(columns={'cancelado': 'Taxa de Cancelamento'}))

    # Análises demográficas
    st.subheader("Análise Demográfica do Churn")
    
    tab1, tab2, tab3 = st.tabs(["Faixa Etária", "Profissão", "Estado"])
    
    with tab1:
        st.bar_chart(df_all.groupby('faixa_etaria')['cancelado'].mean())
    
    with tab2:
        st.dataframe(
            df_all.groupby('profissao')['cancelado']
            .mean().sort_values(ascending=False)
            .head(10)
            .reset_index()
            .rename(columns={'cancelado': 'Taxa de Cancelamento'})
        )
    
    with tab3:
        st.bar_chart(df_all.groupby('estado_residencia')['cancelado'].mean().sort_values(ascending=False))

    # Perfil ideal
    st.subheader("Perfil do Cliente Fidelizado")
    st.dataframe(
        df_all[~df_all['cancelado']]
        [['idade', 'renda_mensal', 'qtd_dependentes', 'duracao_contrato']]
        .mean()
        .to_frame('Média')
        .T
    )

# --- NAVEGAÇÃO ---
VIEWS = {
    "🔵 Visão Geral – Saúde da Base": view_visao_geral,
    "🟡 Perfil do Cliente": view_perfil_cliente,
    "🔴 Produtos e Planos de Seguro": view_produtos_planos,
    "🟢 Satisfação e Experiência": view_satisfacao_experiencia,
    "🟣 Retenção e Churn (Prevenção)": view_retencao_churn,
    "🟤 Insights e Ações": view_insights_acoes
}

def main():
    """Função principal que controla a navegação"""
    st.sidebar.title("Navegação")
    view_selecionada = st.sidebar.radio("Escolha uma seção:", list(VIEWS.keys()))
    
    # Executa a view selecionada
    VIEWS[view_selecionada]()

if __name__ == "__main__":
    main()