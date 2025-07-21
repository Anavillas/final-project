# backend/data_loading/load_views.py
import pandas as pd
from .data_acess import get_engine

def carregar_view(nome_view):
    engine = get_engine()
    query = f"SELECT * FROM {nome_view}"
    df = pd.read_sql_query(query, con=engine)
    return df


def carregar_query(sql_query: str) -> pd.DataFrame:
    engine = get_engine()
    df = pd.read_sql_query(sql_query, con=engine)
    return df