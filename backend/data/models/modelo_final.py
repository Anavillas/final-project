import os
import joblib

# Define caminho para o modelo salvo
caminho = os.path.dirname(__file__)
modelo_path = os.path.join(caminho, "modelo_completo.pkl")

# Carrega os objetos
modelo = joblib.load(modelo_path)

encoder = modelo["encoder"]
final_model = modelo["model"]
selected_indices = modelo["selected_indices"]