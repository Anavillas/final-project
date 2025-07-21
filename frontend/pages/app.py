from streamlit_option_menu import option_menu
import streamlit as st
import  home, clientes, insights, planos

import streamlit as st

# Configuração da página Streamlit
st.set_page_config(
    page_title="Análise de Clientes",     # Título da aba do navegador
    page_icon="🔬",                         # Ícone que aparece na aba e no header
    layout="wide",                          # Usa todo o espaço horizontal
    initial_sidebar_state="expanded",      # Sidebar começa recolhida
    menu_items={                            # Itens do menu de contexto (canto superior direito)
        'Get help': 'https://github.com/Anavillas/final-project',
        'Report a bug': 'https://github.com/Anavillas/final-project',
        'About': "Aplicativo desenvolvido por Ana Carolina Villas, Emily Gabrielly e Gustavo Lamberty Carranza"
    }
)
with st.sidebar:
    selected = option_menu(
        menu_title="Main Menu",
        options=["Home", "Planos", "Clientes"],
        icons=["house", "clipboard", "people"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {
                "padding": "5!important",
                "background-color": "#3377FF"
            },
            "icon": {
                "color": "#ffffff", 
                "font-size": "20px"
            },
            "nav-link": {
                "font-size": "18px",
                "text-align": "left",
                "margin": "0px",
                "--hover-color": "#031A45"
            },
            "nav-link-selected": {
                "background-color": "#2e7bcf",
                "color": "white"
            },
        }
    )

if selected == "Home":
    home.render()

elif selected == "Planos":
    planos.render()

elif selected == "Clientes":
    clientes.render()