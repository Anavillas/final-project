from streamlit_option_menu import option_menu
import streamlit as st
import  home, clientes, insights, planos

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