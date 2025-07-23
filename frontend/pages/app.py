import streamlit as st
import sys
import os
from streamlit import config as _config

# --- Configuração do Caminho Raiz do Projeto (MAIS ROBUSTA) ---
# Encontra a raiz do projeto 'final-project'
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root_indicator = "final-project"
parts = current_dir.split(os.sep)

# Tenta encontrar o índice do diretório 'final-project' no caminho
try:
    project_root_index = len(parts) - 1 - parts[::-1].index(project_root_indicator)
    PROJECT_ROOT = os.sep.join(parts[:project_root_index + 1])
except ValueError:
    # Fallback se 'final-project' não for encontrado (ex: rodando de um nível acima ou renomeou a pasta)
    # Assume que a raiz do projeto está 2 níveis acima de 'frontend/pages'
    PROJECT_ROOT = os.path.abspath(os.path.join(current_dir, '..', '..'))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# --- Importação da função de carregamento de CSS global (AGORA FUNCIONARÁ) ---
# Importante que esta linha venha DEPOIS da configuração do sys.path
from frontend.styles.css_loader import load_global_css 

# --- Configurações de Tema ---
_config.set_option("theme.base", "light")
_config.set_option("theme.primaryColor", "#ff4b4b")
_config.set_option("theme.backgroundColor", "#ffffff")
_config.set_option("theme.secondaryBackgroundColor", "#f0f2f6")
_config.set_option("theme.textColor", "#31333F")

def main():
    st.set_page_config(
        page_title="Gestão de Seguros e Clientes",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    # --- CHAME O CSS GLOBAL AQUI PARA APLICAR OS ESTILOS DA SIDEBAR ---
    load_global_css()

    home_page = st.Page("home.py", title="Home", url_path="/")
    perfil_cliente_page = st.Page("clientes.py", title="Análise Cliente", url_path="/perfil_cliente")
    seguros_contratos_page = st.Page("planos.py", title="Seguros", url_path="/seguros_e_contratos")
    insights_page = st.Page("insights.py", title="Insights", url_path="/insights")

    # --- Navegação ---
    pg = st.navigation([
        home_page,
        perfil_cliente_page,
        seguros_contratos_page,
        insights_page
    ])

    pg.run()

if __name__ == "__main__":
    main()