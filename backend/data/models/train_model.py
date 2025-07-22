import sys
import os

# Caminho da raiz do projeto (duas pastas acima de frontend/pages)
raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if raiz_projeto not in sys.path:
    sys.path.insert(0, raiz_projeto)

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from imblearn.over_sampling import SMOTE
from catboost import CatBoostClassifier
from data.processed.loading_views import carregar_query

# QUERY SQL
query = """
SELECT
  c.cliente_id,

  -- Idade com base na data de nascimento
  DATE_PART('year', CURRENT_DATE) - DATE_PART('year', c.cliente_data_nascimento) AS idade,

  c.cliente_renda_mensal AS renda_mensal,
  c.tipo_seguro_nome AS tipo_seguro,
  c.premio_mensal,
  c.nivel_satisfacao_num AS satisfacao_ultima_avaliacao,
  c.renovacao_automatica,
  DATE(c.data_inicio) AS inicio,
  DATE(c.data_fim) AS fim,

  -- Duração do contrato em dias
  (c.data_fim - c.data_inicio) AS duracao_dias,

  -- Identifica se foi cancelado
  CASE WHEN c.status_contrato = 'Cancelado' THEN 1 ELSE 0 END AS cancelado

FROM v_contratos_detalhados c;
"""

# Carrega os dados
df = carregar_query(query)

# Define X e y
X = df.drop(["cancelado", "inicio", "fim"], axis=1)
y = df["cancelado"]

# OneHotEncoder para variáveis categóricas
categorical_features = ["tipo_seguro"]
encoder = ColumnTransformer(
    [("onehot", OneHotEncoder(drop=None, sparse_output=False), categorical_features)],
    remainder="passthrough"
)
X_encoded = encoder.fit_transform(X)

# SMOTE para balancear as classes
smote = SMOTE(random_state=42)
X_resampled, y_resampled = smote.fit_resample(X_encoded, y)

# Divide em treino e teste
X_train, _, y_train, _ = train_test_split(
    X_resampled, y_resampled, test_size=0.2, random_state=42
)

# Treina modelo final com todas as variáveis
final_model = CatBoostClassifier(random_seed=42, verbose=0, eval_metric='F1')
final_model.fit(X_train, y_train)

# Salva os objetos com joblib
output_dir = "backend/models"
os.makedirs(output_dir, exist_ok=True)

joblib.dump({
    "encoder": encoder,
    "model": final_model
}, os.path.join(output_dir, "modelo_completo.pkl"))

print("✅ Modelo salvo com sucesso em backend/models/modelo_completo.pkl")
