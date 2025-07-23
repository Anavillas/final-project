import streamlit as st
import os

def load_global_css():
    """
    Carrega e injeta o CSS global do arquivo styles/global.css no aplicativo Streamlit.
    """
    current_dir = os.path.dirname(__file__)
    css_file_path = os.path.join(current_dir, "..", "styles", "global.css")

    if os.path.exists(css_file_path):
        with open(css_file_path, "r") as f:
            css_code = f.read()
        st.markdown(f"<style>{css_code}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"Arquivo CSS global não encontrado em: {css_file_path}. Alguns estilos podem estar faltando.")
    
    