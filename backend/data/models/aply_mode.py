import sys
import os

# Caminho da raiz do projeto
raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if raiz_projeto not in sys.path:
    sys.path.insert(0, raiz_projeto)

import joblib
import pandas as pd
from data.processed.loading_views import carregar_query

# 1. Carrega o modelo salvo
modelo = joblib.load("backend/models/modelo_completo.pkl")
encoder = modelo["encoder"]
clf = modelo["model"]

# 2. Carrega os dados reais (clientes ativos)
query = """
SELECT
  c.cliente_id,

  -- Idade com base na data de nascimento
  -- ATENÇÃO: Verifique se DATE_PART e CURRENT_DATE são compatíveis com seu banco de dados.
  -- Para SQLite, use: CAST(strftime('%Y', 'now') AS INTEGER) - CAST(strftime('%Y', c.cliente_data_nascimento) AS INTEGER) AS idade,
  DATE_PART('year', CURRENT_DATE) - DATE_PART('year', c.cliente_data_nascimento) AS idade,

  c.cliente_renda_mensal AS renda_mensal,
  c.tipo_seguro_nome AS tipo_seguro,
  c.premio_mensal AS valor_premio_mensal, -- Renomeado para 'valor_premio_mensal' para consistência
  
  -- Nova Feature: satisfacao_score (assumindo que nivel_satisfacao_num já é numérica)
  c.nivel_satisfacao_num AS satisfacao_score, -- Renomeado para 'satisfacao_score'
  
  c.renovacao_automatica AS renovado_automaticamente, -- Renomeado para 'renovado_automaticamente'
  DATE(c.data_inicio) AS inicio,
  DATE(c.data_fim) AS fim,

  -- Duração do contrato em dias
  -- ATENÇÃO: Verifique se (c.data_fim - c.data_inicio) funciona para seu banco de dados para calcular dias.
  -- Para SQLite, use: julianday(c.data_fim) - julianday(c.data_inicio) AS duracao_dias,
  (c.data_fim - c.data_inicio) AS duracao_dias,

  -- **Novas Features Derivadas:**
  -- Valor do prêmio mensal sobre a renda mensal
  (c.premio_mensal / c.cliente_renda_mensal) AS valor_premio_sobre_renda,

  -- Interação entre idade e renda mensal
  ((DATE_PART('year', CURRENT_DATE) - DATE_PART('year', c.cliente_data_nascimento)) * c.cliente_renda_mensal) AS interacao_idade_renda

FROM v_contratos_detalhados c
WHERE c.status_contrato = 'Ativo';
"""
df = carregar_query(query)

# 3. Guarda cliente_id para depois (mantém na cópia original)

# 4. Remove colunas não usadas pelo modelo antes do encode
X = df.drop(columns=["inicio", "fim"], errors="ignore")

# 5. Aplica a transformação usando o encoder salvo
X_encoded = encoder.transform(X)

# 6. Faz a predição com o modelo
y_pred = clf.predict(X_encoded)

# 7. Junta as previsões com os dados originais
df_resultado = df.copy()
df_resultado["cancelamento_previsto"] = y_pred

# 8. Salva o resultado em CSV
df_resultado.to_csv("backend/models/clientes_ativos_com_predicao.csv", index=False)

print("✅ Previsões geradas e salvas com sucesso!")
