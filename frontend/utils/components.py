import streamlit as st 

def kpi_custom(icon_class, value, explanation):
    st.markdown(f"""
    <div class="kpi-box">
        <div class="kpi-icon"><i class="{icon_class}"></i></div>
        <div class="kpi-content">
            <p class="kpi-value">{value}</p>
            <div class="kpi-explanation">{explanation}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
