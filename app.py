"""
app.py — StormWatch SP
Arquivo principal de inicialização do sistema
"""

import streamlit as st
from frontend import render_app

# Configuração da página
st.set_page_config(
    page_title="StormWatch SP",
    page_icon="⛈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Renderiza toda a aplicação
if __name__ == "__main__":
    render_app()