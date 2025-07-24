import sys
import os
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from imblearn.over_sampling import SMOTE
from catboost import CatBoostClassifier
from sklearn.metrics import classification_report, confusion_matrix

# --- Configuração do Caminho ---
raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if raiz_projeto not in sys.path:
    sys.path.insert(0, raiz_projeto)

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from data.processed.loading_views import carregar_query

# --- QUERY SQL (Ver acima - copiada para o script) ---
query = """
SELECT
    c.cliente_id,
    c.contrato_id AS id_contrato_legado,
    c.cliente_id AS id_cliente_legado,

    c.cliente_genero AS genero,
    c.cliente_nivel_educacional AS nivel_educacional,
    c.canal_venda_nome AS canal_venda,
    pce.qtd_dependente,

    DATE_PART('year', CURRENT_DATE) - DATE_PART('year', c.cliente_data_nascimento) AS idade,
    c.cliente_renda_mensal AS renda_mensal,
    c.tipo_seguro_nome AS tipo_seguro,
    c.premio_mensal AS valor_premio_mensal,
    c.nivel_satisfacao_num AS satisfacao_score, -- JÁ NUMÉRICO (1, 2, 3)
    c.renovacao_automatica AS renovado_automaticamente,
    DATE(c.data_inicio) AS inicio,
    DATE(c.data_fim) AS fim,
    (c.data_fim - c.data_inicio) AS duracao_dias,

    (c.premio_mensal / NULLIF(c.cliente_renda_mensal, 0)) AS valor_premio_sobre_renda,
    ((DATE_PART('year', CURRENT_DATE) - DATE_PART('year', c.cliente_data_nascimento)) * c.cliente_renda_mensal) AS interacao_idade_renda,


    CASE WHEN c.status_contrato = 'Cancelado' THEN 1 ELSE 0 END AS cancelado

FROM v_contratos_detalhados c
JOIN v_perfil_cliente_enriquecido pce ON c.cliente_id = pce.cliente_id
WHERE c.status_contrato IN ('Ativo', 'Cancelado');
"""

# --- Carrega os dados ---
df = carregar_query(query)

# --- ENGENHARIA DE FEATURES (Apenas o que NÃO foi possível fazer na query) ---
df_att = df.copy()

# O mapeamento de satisfação foi removido, pois 'satisfacao_score' já vem numérico (1, 2, 3)
# df_att['satisfacao_score'] = df_att['satisfacao_ultima_avaliacao'].map(mapa_satisfacao)

# A feature 'seguro_alto_risco' foi removida, e 'tipo_seguro' será usada diretamente

# --- Prepara X e y com as colunas finais ---
# Dropar todas as colunas que NÃO são features (IDs, datas auxiliares, target)
# e as colunas originais que foram usadas para criar novas features
# e agora são redundantes ou não mais desejadas.
columns_to_drop_from_X = [
    "cancelado",
    "inicio",
    "fim",
    "cliente_id", # ID interno
    "id_contrato_legado", # ID legado
    "id_cliente_legado",  # ID legado
    "idade",              # Original, pode ser usada para interações
    "qtd_dependente",    # Usada para criar 'renda_por_dependente'
]

# Remover colunas que não existem no df_att para evitar erros
columns_to_drop_from_X = [col for col in columns_to_drop_from_X if col in df_att.columns]

X = df_att.drop(columns=columns_to_drop_from_X, axis=1)
y = df_att["cancelado"]

# --- DIVIDE OS DATOS EM TREINO E TESTE PRIMEIRO! ---
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# --- OneHotEncoder (Fit APENAS no Treino, Transformar Treino e Teste) ---
# Atualize esta lista com as novas features categóricas.
# 'faixa_etaria' e 'seguro_alto_risco' removidas.
# 'tipo_seguro' adicionada como categórica.
categorical_features = [
    "genero",
    "nivel_educacional",
    "canal_venda",
    "tipo_seguro" # Tipo de seguro agora é uma feature categórica
]

encoder = ColumnTransformer(
    [("onehot", OneHotEncoder(drop=None, handle_unknown='ignore', sparse_output=False), categorical_features)],
    remainder="passthrough"
)

X_train_encoded = encoder.fit_transform(X_train)
X_test_encoded = encoder.transform(X_test)

# --- SMOTE (Aplicar APENAS no Conjunto de TREINO) ---
smote = SMOTE(random_state=42)
X_train_resampled, y_train_resampled = smote.fit_resample(X_train_encoded, y_train)

# --- Treina modelo final ---
final_model = CatBoostClassifier(random_seed=42, verbose=0, eval_metric='F1')
final_model.fit(X_train_resampled, y_train_resampled)

# --- Avalia o Modelo no conjunto de teste com diferentes thresholds ---
print("\n--- Avaliação do Modelo no Conjunto de Teste com Diferentes Thresholds ---")

y_pred_proba = final_model.predict_proba(X_test_encoded)[:, 1]

thresholds = [0.5, 0.4, 0.3, 0.2, 0.1, 0.05] # Você pode ajustar os thresholds aqui

for threshold in thresholds:
    print(f"\n--- Threshold: {threshold} ---")
    y_pred_threshold = (y_pred_proba >= threshold).astype(int)

    print("\n📊 Relatório de Classificação:")
    print(classification_report(y_test, y_pred_threshold))

    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred_threshold))
    print("--------------------------------------------------")

# --- Salva os objetos com joblib ---
output_dir = "backend/models"
os.makedirs(output_dir, exist_ok=True)

joblib.dump({
    "encoder": encoder,
    "model": final_model,
    "X_test_encoded": X_test_encoded,
    "y_test": y_test
}, os.path.join(output_dir, "modelo_completo.pkl"))

print("\n✅ Modelo e objetos auxiliares salvos com sucesso em backend/models/modelo_completo.pkl")