"""
streamlit_app.py
Interfaz web sencilla para el Agente de Conocimiento Corporativo.

Ejecutar localmente:
    streamlit run app/streamlit_app.py

En OCI Compute, este mismo comando se ejecuta dentro del contenedor
Docker (ver Dockerfile) y se expone en el puerto 8501.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st
from src.agent import load_agent, ask

st.set_page_config(page_title="Agente Corporativo IA", page_icon="🤖")
st.title("🤖 Agente de Conocimiento Corporativo")
st.caption("Responde preguntas basadas en los documentos internos de la empresa.")

if "chain" not in st.session_state:
    with st.spinner("Cargando base de conocimiento..."):
        st.session_state.chain = load_agent()

if "history" not in st.session_state:
    st.session_state.history = []

for role, msg in st.session_state.history:
    with st.chat_message(role):
        st.markdown(msg)

question = st.chat_input("Escribe tu pregunta sobre las políticas o procesos de la empresa...")

if question:
    st.session_state.history.append(("user", question))
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Buscando en los documentos..."):
            result = ask(question, st.session_state.chain)
            answer = result["answer"]
            if result["sources"]:
                answer += f"\n\n📎 **Fuentes:** {', '.join(result['sources'])}"
            st.markdown(answer)
    st.session_state.history.append(("assistant", answer))
