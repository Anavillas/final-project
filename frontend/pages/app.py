import streamlit as st
import sys
import os
from streamlit import config as _config

# --- Configurações de Tema (devem vir antes de st.set_page_config) ---
_config.set_option("theme.base", "light")
_config.set_option("theme.primaryColor", "#ff4b4b")
_config.set_option("theme.backgroundColor", "#ffffff")
_config.set_option("theme.secondaryBackgroundColor", "#f0f2f6")
_config.set_option("theme.textColor", "#31333F")

# Adicionar o diretório raiz do projeto ao sys.path para imports de backend (se houver)
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, os.path.join(PROJECT_ROOT, '..', '..')) # Adiciona a raiz do projeto (final-project)
    sys.path.insert(0, PROJECT_ROOT) # Adiciona o diretório atual de app.py

# Se você não tem criarTable, remova essas linhas.
# try:
#     from data.CriacaoBD import criarTable
# except ImportError:
#     st.error("Erro: Não foi possível importar 'criarTable'. Verifique o caminho 'data.CriacaoBD'.")
#     st.stop()

def main():
    st.set_page_config(
        page_title="Gestão de Seguros e Clientes",
        page_icon="📄", # Ícone de página/documento
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Se você não tem criarTable, remova essa linha.
    # criarTable()

    # --- Injeção de CSS para a barra lateral ---
    st.markdown("""
        <style>
            /* Cor de fundo da barra lateral */
            [data-testid="stSidebar"] {
                background-color: #3377FF; /* Azul forte */
                padding-top: 20px; /* Adiciona padding no topo do sidebar */
            }

            /* Esconde o elemento que cria um pequeno espaço no topo da sidebar */
            /* Seletor dinâmico - pode precisar de ajuste em futuras versões do Streamlit */

            /* Esconde o título/label do sidebar gerado pelo Streamlit nativo */
            /* Seletor dinâmico - pode precisar de ajuste em futuras versões do Streamlit */


            /* Estilo para os links de navegação nativos no sidebar */
            .stSidebarNavLink {
                color: white; /* Cor do texto padrão dos links */
                background-color: transparent; /* Fundo transparente */
                padding: 12px 15px 12px 20px; /* Topo, direita, baixo, esquerda para espaçamento dos itens */
                margin-bottom: 5px; /* Espaço entre os itens do menu */
                border-radius: 5px; /* Bordas arredondadas */
                transition: all 0.2s ease-in-out; /* Transição suave para hover/ativo */
                display: flex; /* Para alinhar ícone e texto */
                align-items: center; /* Alinha verticalmente */
            }

            .stSidebarNavLink:hover {
                background-color: #2e7bcf; /* Cor de hover */
                color: white;
            }

            /* Estilo para o link de navegação ativo (selecionado) */
            .stSidebarNavLink[data-active="true"] { /* Streamlit adiciona data-active="true" */
                background-color: #2e7bcf; /* Fundo do item selecionado */
                color: white; /* Cor do texto do item selecionado */
                font-weight: bold; /* Deixa o texto selecionado em negrito */
            }

            /* Ajustar o texto do link */
            .stSidebarNavLink p {
                color: white !important; /* Garante que o texto seja branco */
                font-size: 18px; /* Tamanho da fonte dos links */
                margin: 0; /* Remove margem padrão do parágrafo */
            }

            /* Estilo para o emoji do ícone (o que realmente aparece) */
            /* Adicionado !important para tentar forçar o tamanho */
            .stSidebarNavLink .streamlit-expander span div:first-child,
            .stSidebarNavLink span[data-testid="stSidebarNavLink-icon"] {
                font-size: 100px !important; /* <--- ALTERADO AQUI: Adicionado !important */
                margin-right: 15px; /* Espaço entre o emoji e o texto */
            }


            /* Remover bordas e sombras de containers que possam afetar o sidebar */
            /* Seletor dinâmico - pode precisar de ajuste em futuras versões do Streamlit */
            .css-1lcbmhc.e1fqkh3o3 {
                box-shadow: none !important;
                border-radius: 0 !important;
            }

            /* Ajuste para o padding do conteúdo principal */
            .block-container {
                padding-left: 2rem;
                padding-right: 2rem;
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
        </style>
    """, unsafe_allow_html=True)

    # --- Definição das Páginas para a Navegação Nativa do Streamlit ---
    # Usando emojis simples de um único caractere
    home_page = st.Page("home.py", title="Home", icon="🏠", url_path="/")
    perfil_cliente_page = st.Page("clientes.py", title="Perfil Cliente", icon="👤", url_path="/perfil_cliente")
    seguros_contratos_page = st.Page("planos.py", title="Seguros e contratos", icon="📝", url_path="/seguros_e_contratos")
    insights_page = st.Page("insights.py", title="Insights", icon="💡", url_path="/insights")

    # --- Configuração da Navegação ---
    pg = st.navigation([
        home_page,
        perfil_cliente_page,
        seguros_contratos_page,
        insights_page
    ])

    # --- Executa a Navegação ---
    pg.run()

if __name__ == "__main__":
    main()