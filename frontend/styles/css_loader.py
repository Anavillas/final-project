import streamlit as st

# VERSÃO FINAL E MAIS FORTE DO CSS
# Foco total na responsividade e uso de !important para garantir prioridade.
CSS_CODE = """
/* Estilos base para o KPI - sem alterações */
.stApp .kpi-box {
    display: flex;
    align-items: center;
    background-color: white;
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 10px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    min-height: 90px;
}
.stApp .kpi-icon {
    margin-right: 15px;
    font-size: 30px;
    color: #3377ff;
}
.stApp .kpi-content {
    flex-grow: 1;
}
.stApp .kpi-value {
    font-size: 26px !important;
    font-weight: 700;
}
.stApp .kpi-explanation {
    margin-top: 4px;
    font-size: 13px;
    color: #555;
}

/* =======================================================================
--- Media Queries para Responsividade (VERSÃO FINAL) ---
======================================================================= */
@media (max-width: 768px) {
    
    /* 1. Força o CONTAINER das colunas a empilhar na vertical */
    .stApp [data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
    }

    /* 2. Força o CONTEÚDO INTERNO de cada KPI a empilhar também */
    .stApp .kpi-box {
        flex-direction: column !important;
        text-align: center;
    }
    
    /* 3. Ajusta o ícone para o layout vertical */
    .stApp .kpi-icon {
        margin-right: 0;
        margin-bottom: 10px;
    }
}
"""

def load_global_css():
    """
    Injeta o CSS global diretamente como uma string no aplicativo Streamlit.
    """
    st.markdown(f"<style>{CSS_CODE}</style>", unsafe_allow_html=True)