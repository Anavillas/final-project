import sys
import os

# Caminho da raiz do projeto (duas pastas acima de frontend/pages)
    
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

def get_engine():
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASS")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT", 5432)
    db = os.getenv("DB_NAME")

    conn_str = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    engine = create_engine(conn_str)
    return create_engine(f"postgresql://{user}:{password}@{host}:{port}/{db}")
