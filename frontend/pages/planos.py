# file: pages/dashboard_custom_ui.py

import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from streamlit_option_menu import option_menu
from dateutil.relativedelta import relativedelta
import numpy as np
from backend.data.processed.loading_views import carregar_view
from backend.data.processed.loading_views import carregar_query

# file: pages/dashboard_custom_ui.py

import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from streamlit_option_menu import option_menu
from dateutil.relativedelta import relativedelta
import numpy as np
from backend.data.processed.loading_views import carregar_view
from backend.data.processed.loading_views import carregar_query


    

def render():
    st.markdown("""
        <style>
        body { background-color: #F4F4F5; font-family: 'Segoe UI', sans-serif; }
        .block-container { padding-top: 1rem; }
        .metric-box {
            background-color: #FFFFFF; border-radius: 16px; padding: 20px;
            box-shadow: 0px 2px 8px rgba(0,0,0,0.05); text-align: center;
            display: flex; flex-direction: column; align-items: center; gap: 0.25rem;
        }
        .metric-icon {
            font-size: 26px; color: #3B82F6; margin-bottom: 0.2rem;
        }
        .metric-value { font-size: 22px; font-weight: 600; color: #111827; }
        .metric-label { font-weight: 500; color: #6B7280; font-size: 14px; }
        .main-header { font-size: 26px; color: #111827; font-weight: bold; padding: 1rem 0; }
        .risk-box { background-color: #FFFFFF; border: 2px dashed #C084FC; padding: 1rem; border-radius: 12px; }
        .risk-box h4 { font-size: 16px; margin-bottom: 0.5rem; color: #111827; }
        .risk-button {
            background-color: #F3F4F6; padding: 0.5rem; margin-bottom: 0.5rem;
            border-radius: 8px; cursor: pointer;
        }
        .chart-card {
            background-color: #FFFFFF; border-radius: 16px; padding: 16px;
            box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
            margin-bottom: 1rem;
        }
        .seguro-button {
            padding: 10px 20px; border-radius: 10px;
            background-color: #F4F4F5; color: #3B82F6; border: none; margin-right: 8px;
            font-weight: 500; font-size: 15px; cursor: pointer;
        }
        .seguro-button-active {
            background-color: #3B82F6 !important; color: white !important;
        }
        </style>
    """, unsafe_allow_html=True)
    # --- MENU LATERAL ---
    st.markdown("<div class='main-header'>Visão Geral da Carteira de Seguros</div>", unsafe_allow_html=True)

    # --- BUSCAR TIPOS DE SEGURO ---
    tipos_df = carregar_query("SELECT DISTINCT tipo_seguro_nome FROM v_contratos_detalhados ORDER BY tipo_seguro_nome")
    tipos = tipos_df['tipo_seguro_nome'].tolist() if tipos_df is not None else []

    # --- BARRA DE SELEÇÃO HORIZONTAL ---
    col_btns = st.columns(len(tipos))
    tipo_selecionado = tipos[0] if tipos else None
    for i, tipo in enumerate(tipos):
        if col_btns[i].button(tipo, key=f"seguro_{i}"):
            st.session_state["tipo_atual"] = tipo

    # Valor default ou selecionado
    tipo_ativo = st.session_state.get("tipo_atual", tipo_selecionado)

    # --- FILTROS SQL ---
    where_clause = f"WHERE tipo_seguro_nome = '{tipo_ativo}'"
    df_detalhes = carregar_query(f"SELECT * FROM v_contratos_detalhados {where_clause};")
    df_churn = carregar_query(f"SELECT * FROM v_analise_churn {where_clause};")

    # --- KPIs ---
    if df_detalhes is not None and df_churn is not None:
        contratos_ativos = df_detalhes[df_detalhes['status_contrato'] == 'Ativo'].shape[0]
        clientes_ativos = df_detalhes[df_detalhes['status_contrato'] == 'Ativo']['cliente_id'].nunique()
        faturamento = df_detalhes[df_detalhes['status_contrato'] == 'Ativo']['premio_mensal'].sum()
        cancelados = df_churn.shape[0]
        total = contratos_ativos + cancelados
        churn = (cancelados / total * 100) if total > 0 else 0

        satisf_df = df_detalhes[df_detalhes['nivel_satisfacao_num'].notnull() & (df_detalhes['nivel_satisfacao_num'] > 0)]
        satisfacao = satisf_df['nivel_satisfacao_num'].mean() if not satisf_df.empty else 0

        kpis = [
            ("% de churn", f"{churn:.1f}%", "📉"),
            ("Contratos Ativos", contratos_ativos, "📄"),
            ("Clientes Ativos", clientes_ativos, "👥"),
            ("Satisfação Média", f"{satisfacao:.1f} / 3", "⭐"),
            ("Faturamento Contrato", f"R$ {faturamento:,.2f}", "💰")
        ]

        with st.container():
            col_kpis = st.columns(5)
            for i, (label, value, icon) in enumerate(kpis):
                with col_kpis[i]:
                    st.markdown(f"""
                    <div class='metric-box'>
                        <div class='metric-icon'>{icon}</div>
                        <div class='metric-value'>{value}</div>
                        <div class='metric-label'>{label}</div>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("---")

        col1, col2 = st.columns([2, 1])
        with col1:
            with st.container():
                st.markdown("""
                <div class='chart-card'>
                    <h3 style='margin-bottom: 1rem;'>Motivo de Cancelamento</h3>
                """, unsafe_allow_html=True)

                motivo_df = df_churn['motivo_cancelamento_nome'].value_counts().reset_index()
                motivo_df.columns = ['Motivo', 'Contagem']
                fig = px.bar(motivo_df, y="Motivo", x="Contagem", orientation="h", height=300, color_discrete_sequence=["#3B82F6"])
                st.plotly_chart(fig, use_container_width=True)

                st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            with st.container():
                st.markdown("""
                <div class='chart-card'>
                    <h3 style='margin-bottom: 1rem;'>Duração dos Contratos (meses)</h3>
                """, unsafe_allow_html=True)

                df_duracao = df_detalhes[df_detalhes['data_fim'].notnull() & df_detalhes['data_inicio'].notnull()].copy()
                df_duracao['duracao_meses'] = df_duracao.apply(lambda row: (relativedelta(row['data_fim'], row['data_inicio']).years * 12 + relativedelta(row['data_fim'], row['data_inicio']).months), axis=1)
                fig_duracao = px.histogram(df_duracao, x="duracao_meses", nbins=10, height=300, color_discrete_sequence=["#3B82F6"])
                st.plotly_chart(fig_duracao, use_container_width=True)

                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")

        cl, cr = st.columns([3, 1])
        with cl:
            st.subheader("15 Contratos em Risco")
            st.dataframe(pd.DataFrame({
                "Nome": ["Jane Doe"]*5,
                "Cargo": ["Senior Designer"]*5,
                "Status": ["Em Risco"]*5
            }))

        with cr:
            st.markdown("""
            <div class="risk-box">
                <h4>Situação Contrato</h4>
                <div class="risk-button">Risco Cancelamento</div>
                <div class="risk-button">Contratos a terminar</div>
                <div class="risk-button">Lista Situação Clientes</div>
            </div>
            """, unsafe_allow_html=True)

    else:
        st.warning("Não foi possível carregar os dados para o tipo de seguro selecionado.")
        
render()