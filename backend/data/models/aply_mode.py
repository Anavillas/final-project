import sys
import os

# Caminho da raiz do projeto
raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if raiz_projeto not in sys.path:
    sys.path.insert(0, raiz_projeto)

import joblib
import pandas as pd
from data.processed.loading_views import carregar_view

# 1. Carrega o modelo salvo
modelo_completo = joblib.load("backend/models/modelo_completo.pkl")
encoder = modelo_completo["encoder"]
clf = modelo_completo["model"]

# 2. Carrega os dados reais (clientes ativos)
df = carregar_view('v_clientes_para_predicao_final')

# 3. Guarda cliente_id para depois (mantém na cópia original)
# Não é necessário fazer nada aqui, pois o df original será usado para juntar o resultado.

# --- AJUSTE AQUI: Listar APENAS as colunas que foram de fato para o modelo no treino ---
columns_for_model_input = [
    "genero",
    "nivel_educacional",
    "canal_venda",
    "tipo_seguro",
    "renda_mensal",
    "valor_premio_mensal",
    "satisfacao_score",
    "renovado_automaticamente",
    "duracao_dias",
    "valor_premio_sobre_renda",
    "interacao_idade_renda"
]

# Filtra o dataframe para ter apenas as colunas que o modelo espera
X_inferencia = df[columns_for_model_input]

# 5. Aplica a transformação usando o encoder salvo
X_encoded_inferencia = encoder.transform(X_inferencia)

# 6. Faz a predição com o modelo
y_pred_proba = clf.predict_proba(X_encoded_inferencia)[:, 1]
threshold = 0.3
y_pred_com_threshold = (y_pred_proba >= threshold).astype(int)

# 7. Junta as previsões com os dados originais
df_resultado = df.copy()
df_resultado["probabilidade_cancelamento"] = y_pred_proba
df_resultado["cancelamento_previsto"] = y_pred_com_threshold

# 8. Salva o resultado em CSV
df_resultado.to_csv("backend/models/clientes_ativos_com_predicao.csv", index=False)

print("✅ Previsões geradas e salvas com sucesso!")