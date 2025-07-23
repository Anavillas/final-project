import streamlit as st
import pandas as pd
from .data_acess import get_engine

def carregar_view(nome_view):
    engine = get_engine()
    if engine is None: # Adiciona verificação para o mock
        return pd.DataFrame() # Retorna DataFrame vazio se o engine for None
    query = f"SELECT * FROM {nome_view}"
    # Explicitly pass an empty dictionary for params
    df = pd.read_sql_query(query, con=engine, params={}) # Adicione params={} aqui também
    return df

def carregar_query(sql_query):
    print("SQL sendo executado:\n", sql_query)
    engine = get_engine()
    with engine.connect() as conn:
        # Teste com uma query super simples primeiro
        if "v_contratos_detalhados" not in sql_query: # Apenas para testar se é a query complexa
            df = pd.read_sql_query("SELECT 1 as test_column;", con=conn)
        else:
            df = pd.read_sql_query(sql_query, con=conn)
    return df