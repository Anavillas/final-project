import pandas as pd
import sqlite3

# Conexão com o banco SQLite (ou cria um novo)
conn = sqlite3.connect('seguros.db')
cursor = conn.cursor()

# 1. Criar tabela de clientes
cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes (
    id_cliente TEXT PRIMARY KEY,
    nome TEXT,
    data_nascimento DATE,
    genero TEXT,
    cidade_residencia TEXT,
    estado_residencia TEXT,
    profissao TEXT,
    renda_mensal REAL,
    nivel_educacional TEXT,
    qtd_dependentes INTEGER,
    data_cadastro DATE
);
""")

# 2. Criar tabela de contratos
cursor.execute("""
CREATE TABLE IF NOT EXISTS contratos (
    id_contrato TEXT PRIMARY KEY,
    id_cliente TEXT,
    tipo_seguro TEXT,
    data_inicio DATE,
    data_fim DATE,
    valor_premio_mensal REAL,
    satisfacao_ultima_avaliacao TEXT,
    canal_venda TEXT,
    renovado_automaticamente BOOLEAN,
    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
);
""")

# 3. Criar tabela de cancelamentos
cursor.execute("""
CREATE TABLE IF NOT EXISTS cancelamentos (
    id_contrato TEXT PRIMARY KEY,
    data_cancelamento DATE,
    motivo_cancelamento TEXT,
    canal_cancelamento TEXT,
    avaliacao_experiencia_cancelamento TEXT,
    FOREIGN KEY (id_contrato) REFERENCES contratos(id_contrato)
);
""")

conn.commit()