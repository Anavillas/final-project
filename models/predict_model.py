# === backend/model/predict_model.py ===
import pandas as pd
import joblib
#from database.connection import get_conn
#from database.queries.view_query import get_view_query
#from backend.features.transformacoes import aplicar_transformacoes

# Carrega modelo e encoder
final_model = joblib.load("backend/model/modelo_churn.joblib")
encoder = joblib.load("backend/encoding/encoder.joblib")
selected_indices = joblib.load("backend/encoding/selected_indices.joblib")  # RFE

def carregar_dados_clientes_em_risco(threshold=0.4):
    conn = get_conn()
    query = get_view_query("view_clientes_ativos")
    df = pd.read_sql_query(query, conn)
    df = aplicar_transformacoes(df)

    X_encoded = encoder.transform(df)
    X_rfe = X_encoded[:, selected_indices]

    probas = final_model.predict_proba(X_rfe)[:, 1]
    df["prob_cancelamento"] = probas
    df["tende_cancelar"] = (df["prob_cancelamento"] >= threshold).astype(int)

    return df[df["tende_cancelar"] == 1].sort_values("prob_cancelamento", ascending=False)


# === database/connection.py ===
import psycopg2
import os

def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port=5432
    )


# === database/queries/view_query.py ===
from pathlib import Path

def get_view_query(view_name):
    path = Path(f"database/queries/{view_name}.sql")
    return path.read_text()


# === backend/features/transformacoes.py ===
def aplicar_transformacoes(df):
    mapa_satisfacao = {'Baixa': 0, 'Média': 1, 'Alta': 2}
    df['satisfacao_score'] = df['satisfacao_ultima_avaliacao'].map(mapa_satisfacao)
    df['valor_premio_sobre_renda'] = df['valor_premio_mensal'] / df['renda_mensal']
    df['interacao_idade_renda'] = df['idade'] * df['renda_mensal']
    df.drop(columns=[
        'satisfacao_ultima_avaliacao', 'qtd_dependentes', 'renda_mensal',
        'tipo_duracao', 'genero', 'nivel_educacional', 'canal_venda'
    ], inplace=True)
    return df


# === frontend/pages/clientes_risco.py ===
import streamlit as st
import pandas as pd
#from backend.model.predict_model import carregar_dados_clientes_em_risco

def exibir_clientes_em_risco():
    st.title("🔍 Clientes com risco de cancelamento")

    threshold = st.slider("Probabilidade mínima para alerta", 0.0, 1.0, 0.4, 0.05)
    df_risco = carregar_dados_clientes_em_risco(threshold=threshold)

    st.metric("Clientes em risco", df_risco.shape[0])
    st.dataframe(df_risco.head(10))

# (Na app.py, chame exibir_clientes_em_risco() quando a página for essa)
