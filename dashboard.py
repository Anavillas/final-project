import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Caminhos
BASE_PATH = r'C:\Users\Aluno\Documents\GitHub\final-project\data'
df_clientes = pd.read_csv(f'{BASE_PATH}\P18_clientes.csv')
df_contratos = pd.read_csv(f'{BASE_PATH}\P18_contratos.csv')
df_cancelamentos = pd.read_csv(f'{BASE_PATH}\P18_cancelamentos.csv')

# --- PRÉ-PROCESSAMENTO GLOBAL ---
df_clientes['data_nascimento'] = pd.to_datetime(df_clientes['data_nascimento'], errors='coerce')
df_clientes['idade'] = (pd.Timestamp.now() - df_clientes['data_nascimento']).dt.days // 365
bins = [0, 18, 30, 45, 60, 100]
labels = ['0-17', '18-29', '30-44', '45-59', '60+']
df_clientes['faixa_etaria'] = pd.cut(df_clientes['idade'], bins=bins, labels=labels, right=False)
df_clientes = df_clientes[df_clientes['faixa_etaria'] != '0-17']
df_clientes['data_cadastro'] = pd.to_datetime(df_clientes['data_cadastro'], errors='coerce')
df_contratos['data_inicio'] = pd.to_datetime(df_contratos['data_inicio'], errors='coerce')
df_contratos['data_fim'] = pd.to_datetime(df_contratos['data_fim'], errors='coerce')
df_contratos['duracao_contrato'] = (df_contratos['data_fim'] - df_contratos['data_inicio']).dt.days
dict_satisfacao = {'Baixa': 1, 'Média': 2, 'Alta': 3}
df_contratos['satisfacao_numerica'] = df_contratos['satisfacao_ultima_avaliacao'].map(dict_satisfacao)

# Conversão de avaliações textuais
dict_satisfacao = {'Baixa': 1, 'Média': 2, 'Alta': 3}
df_contratos['satisfacao_numerica'] = df_contratos['satisfacao_ultima_avaliacao'].map(dict_satisfacao)
df_cancelamentos['avaliacao_experiencia_numerica'] = df_cancelamentos['avaliacao_experiencia_cancelamento'].map(dict_satisfacao)

# --- VISÕES ---
def view_visao_geral():
    st.header("🔵 Visão Geral – Saúde da Base")

    total_clientes = df_clientes['id_cliente'].nunique()
    total_contratos = df_contratos['id_contrato'].nunique()
    total_cancelamentos = df_cancelamentos['id_contrato'].nunique()
    contratos_ativos = total_contratos - total_cancelamentos
    contratos_inativos = total_cancelamentos
    churn_rate = total_cancelamentos / total_contratos
    renovados = df_contratos['renovado_automaticamente'].value_counts(normalize=True).get(True, 0)
    satisfacao_media = df_contratos['satisfacao_numerica'].mean()
    tipos_seguro = df_contratos['tipo_seguro'].value_counts()

    col1, col2, col3 = st.columns(3)
    col1.metric("Clientes", total_clientes)
    col2.metric("Contratos Ativos", contratos_ativos)
    col3.metric("Cancelamentos", contratos_inativos)

    col4, col5, col6 = st.columns(3)
    col4.metric("% Churn", f"{churn_rate*100:.2f}%")
    col5.metric("% Renovados", f"{renovados*100:.1f}%")
    col6.metric("Satisfação Média", f"{satisfacao_media:.2f}")

    st.subheader("Distribuição por Tipo de Seguro")
    fig, ax = plt.subplots()
    ax.pie(tipos_seguro, labels=tipos_seguro.index, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    st.pyplot(fig)

def view_perfil_cliente():
    st.header("🟡 Perfil do Cliente")

    st.subheader("Distribuição por Faixa Etária")
    st.bar_chart(df_clientes['faixa_etaria'].value_counts().sort_index())

    st.subheader("Distribuição por Gênero")
    st.bar_chart(df_clientes['genero'].value_counts())

    st.subheader("Distribuição por Escolaridade")
    st.bar_chart(df_clientes['nivel_educacional'].value_counts())

    st.subheader("Distribuição por Profissão")
    st.dataframe(df_clientes['profissao'].value_counts().head(10))

    st.subheader("Distribuição por Estado")
    st.bar_chart(df_clientes['estado_residencia'].value_counts())

    st.subheader("Nº médio de dependentes")
    st.metric("Média de Dependentes", f"{df_clientes['qtd_dependentes'].mean():.2f}")

    contratos_por_cliente = df_contratos['id_cliente'].value_counts()
    multiplos = contratos_por_cliente[contratos_por_cliente > 1].count()
    st.metric("Clientes com múltiplos contratos", multiplos)

    st.subheader("Filtros Dinâmicos")
    genero_sel = st.multiselect("Gênero", df_clientes['genero'].unique())
    tipo_sel = st.multiselect("Tipo de Seguro", df_contratos['tipo_seguro'].unique())

    df_merge = pd.merge(df_clientes, df_contratos, on='id_cliente')
    if genero_sel:
        df_merge = df_merge[df_merge['genero'].isin(genero_sel)]
    if tipo_sel:
        df_merge = df_merge[df_merge['tipo_seguro'].isin(tipo_sel)]

    st.dataframe(df_merge[['id_cliente', 'genero', 'idade', 'tipo_seguro', 'renda_mensal']].head())

def view_produtos_planos():
    st.header("🔴 Produtos e Planos de Seguro")

    st.subheader("Avaliação média por tipo de seguro")
    media_avaliacao = df_contratos.groupby('tipo_seguro')['satisfacao_numerica'].mean().sort_values()
    st.bar_chart(media_avaliacao)

    st.subheader("Churn por tipo de seguro")
    df_churn = df_contratos.copy()
    df_churn['cancelado'] = df_churn['id_contrato'].isin(df_cancelamentos['id_contrato'])
    churn_tipo = df_churn.groupby('tipo_seguro')['cancelado'].mean().sort_values()
    st.bar_chart(churn_tipo)

    st.subheader("Tempo médio de contrato por tipo de seguro")
    duracao_media = df_contratos.groupby('tipo_seguro')['duracao_contrato'].mean().sort_values()
    st.bar_chart(duracao_media)

    st.subheader("Receita média por cliente (renda × valor seguro)")
    df_receita = pd.merge(df_clientes[['id_cliente', 'renda_mensal']], df_contratos[['id_cliente', 'valor_premio_mensal', 'tipo_seguro']], on='id_cliente')
    df_receita['indice_receita'] = df_receita['renda_mensal'] * df_receita['valor_premio_mensal']
    receita_media = df_receita.groupby('tipo_seguro')['indice_receita'].mean().sort_values()
    st.bar_chart(receita_media)

    st.subheader("Contratos mais cancelados × tipo")
    df_canc = pd.merge(df_contratos[['id_contrato', 'tipo_seguro']], df_cancelamentos[['id_contrato']], on='id_contrato')
    st.dataframe(df_canc['tipo_seguro'].value_counts().reset_index().rename(columns={'index': 'Tipo de Seguro', 'tipo_seguro': 'Total Cancelamentos'}))

    st.subheader("Contratos mais duradouros × tipo")
    duraveis = df_contratos.groupby('tipo_seguro')['duracao_contrato'].mean().sort_values(ascending=False)
    st.dataframe(duraveis.reset_index().rename(columns={'duracao_contrato': 'Duração Média (dias)'}))

def view_satisfacao_experiencia():
    st.header("🟢 Satisfação e Experiência")

    # Satisfação por tipo de seguro
    st.subheader("Satisfação da última avaliação × Tipo de Seguro")
    media_satisf = df_contratos.groupby('tipo_seguro')['satisfacao_numerica'].mean().sort_values()
    st.bar_chart(media_satisf)

    # Experiência de cancelamento por motivo
    st.subheader("Experiência de Cancelamento × Motivo")
    df_cancelamentos['avaliacao_experiencia_cancelamento'] = pd.to_numeric(df_cancelamentos['avaliacao_experiencia_cancelamento'], errors='coerce')
    experiencia = df_cancelamentos.groupby('motivo_cancelamento')['avaliacao_experiencia_cancelamento'].mean().sort_values()
    st.bar_chart(experiencia)

    # Nota média por canal de venda
    st.subheader("Nota Média por Canal de Venda")
    canal_venda_media = df_contratos.groupby('canal_venda')['satisfacao_numerica'].mean().sort_values()
    st.bar_chart(canal_venda_media)

    # Canais de cancelamento mais frequentes
    st.subheader("Canais de Cancelamento mais Frequentes")
    canal_cancel_freq = df_cancelamentos['canal_cancelamento'].value_counts()
    st.bar_chart(canal_cancel_freq)

    # NPS aproximado (baseado em nota)
    st.subheader("NPS Estimado (Baseado na Satisfação da Última Avaliação)")
    satisf = df_contratos['satisfacao_numerica'].dropna()
    detratores = satisf[satisf <= 1.6].count()
    neutros = satisf[(satisf > 1.6) & (satisf <= 2.3)].count()
    promotores = satisf[satisf > 2.3].count()
    total_respostas = detratores + neutros + promotores

    if total_respostas > 0:
        nps = round(((promotores - detratores) / total_respostas) * 100, 2)
    else:
        nps = 'N/A'

    st.metric("NPS Estimado", f"{nps}")

def view_retencao_churn():
    st.header("🟣 Retenção e Churn (Prevenção)")

    # Perfil dos canceladores
    st.subheader("Perfil dos Canceladores")
    df_cancel = pd.merge(df_cancelamentos, df_contratos, on='id_contrato')
    df_cancel = pd.merge(df_cancel, df_clientes, on='id_cliente')
    perfil = df_cancel[['idade', 'tipo_seguro', 'satisfacao_numerica']]
    st.dataframe(perfil.describe(include='all'))

    # Clientes com 1 contrato × cancelaram?
    st.subheader("Clientes com 1 Contrato × Cancelaram?")
    qtd_contratos = df_contratos['id_cliente'].value_counts()
    df_clientes['qtd_contratos'] = df_clientes['id_cliente'].map(qtd_contratos)
    um_contrato = df_clientes[df_clientes['qtd_contratos'] == 1]['id_cliente']
    cancelaram = df_cancelamentos['id_contrato'].isin(df_contratos[df_contratos['id_cliente'].isin(um_contrato)]['id_contrato']).sum()
    taxa_cancelamento = cancelaram / len(um_contrato)
    st.metric("% Cancelaram com 1 contrato", f"{taxa_cancelamento*100:.2f}%")

    # Clientes que renovam × cancelam menos?
    st.subheader("Clientes que Renovam Cancelam Menos?")
    df_contratos['cancelado'] = df_contratos['id_contrato'].isin(df_cancelamentos['id_contrato'])
    taxa = df_contratos.groupby('renovado_automaticamente')['cancelado'].mean()
    st.write(taxa.rename(index={True: 'Renovaram', False: 'Não Renovaram'}))

    # Tamanho do contrato × risco de churn
    st.subheader("Duração do Contrato × Risco de Churn")
    df_churn_dur = df_contratos.copy()
    df_churn_dur['churn'] = df_churn_dur['id_contrato'].isin(df_cancelamentos['id_contrato'])
    st.line_chart(df_churn_dur.groupby('duracao_contrato')['churn'].mean())

    # Predição com modelo: (simples classificação baseada em regras)
    st.subheader("Ranking de Clientes em Risco")
    df_pred = pd.merge(df_contratos, df_clientes, on='id_cliente')
    df_pred['risco'] = 'Baixo'
    df_pred.loc[(df_pred['satisfacao_numerica'] == 1) & (df_pred['duracao_contrato'] < 365), 'risco'] = 'Médio'
    df_pred.loc[(df_pred['satisfacao_numerica'] == 1) & (df_pred['duracao_contrato'] < 250), 'risco'] = 'Alto'
    ranking = df_pred[['id_cliente', 'tipo_seguro', 'satisfacao_numerica', 'duracao_contrato', 'risco']].sort_values(by='risco', ascending=False)
    st.dataframe(ranking.head(10))

    # Ações recomendadas
    st.subheader("Ações Recomendadas para Retenção")
    st.markdown("""
    - Clientes com risco **Alto**: Contatar proativamente, oferecer incentivos ou planos alternativos.
    - Clientes com risco **Médio**: Monitoramento com campanhas de engajamento.
    - Clientes com risco **Baixo**: Estratégias de fidelização, upgrades, e programas de benefícios.
    """)

def view_insights_acoes():
    st.header("🟤 Insights e Ações")

    # Merge bases
    df_all = pd.merge(df_contratos, df_clientes, on='id_cliente', how='left')
    df_all['cancelado'] = df_all['id_contrato'].isin(df_cancelamentos['id_contrato'])

    st.subheader("Plano com pior retenção")
    churn_tipo = df_all.groupby('tipo_seguro')['cancelado'].mean().sort_values(ascending=False)
    st.dataframe(churn_tipo.reset_index().rename(columns={'cancelado': 'Taxa de Cancelamento'}))

    st.subheader("Faixa etária com mais churn")
    df_all['faixa_etaria'] = pd.cut(df_all['idade'], bins=[0, 18, 30, 45, 60, 100], labels=labels, right=False)
    churn_faixa = df_all.groupby('faixa_etaria')['cancelado'].mean()
    st.bar_chart(churn_faixa)

    st.subheader("Profissões com mais churn")
    churn_profissao = df_all.groupby('profissao')['cancelado'].mean()
    churn_profissao = churn_profissao[churn_profissao > 0].sort_values(ascending=False).head(10)
    st.dataframe(churn_profissao.reset_index().rename(columns={'cancelado': 'Taxa de Cancelamento'}))

    st.subheader("Estados com mais churn")
    churn_estado = df_all.groupby('estado_residencia')['cancelado'].mean().sort_values(ascending=False)
    st.bar_chart(churn_estado)

    st.subheader("Planos com melhor performance para expandir")
    melhor_expansao = churn_tipo.sort_values().head(5)
    st.dataframe(melhor_expansao.reset_index().rename(columns={'cancelado': 'Menor Churn'}))

    st.subheader("Perfil ideal de cliente fidelizado")
    fidelizados = df_all[df_all['cancelado'] == False]
    perfil = fidelizados[['idade', 'renda_mensal', 'qtd_dependentes', 'duracao_contrato']].mean()
    st.write(perfil)

# --- SIDEBAR ---
st.sidebar.title("Navegação")
view = st.sidebar.radio("Escolha uma seção:", [
    "🔵 Visão Geral – Saúde da Base",
    "🟡 Perfil do Cliente",
    "🔴 Produtos e Planos de Seguro",
    "🟢 Satisfação e Experiência",
    "🟣 Retenção e Churn (Prevenção)",
    "🟤 Insights e Ações"
])

if view == "🔵 Visão Geral – Saúde da Base":
    view_visao_geral()
elif view == "🟡 Perfil do Cliente":
    view_perfil_cliente()
elif view == "🔴 Produtos e Planos de Seguro":
    view_produtos_planos()
elif view == "🟢 Satisfação e Experiência":
    view_satisfacao_experiencia()
elif view == "🟣 Retenção e Churn (Prevenção)":
    view_retencao_churn()
elif view == "🟤 Insights e Ações":
    view_insights_acoes()