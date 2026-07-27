"""
streamlit_app.py
Interfaz web interactiva y centrada para el Agente de Conocimiento Corporativo.

Ejecutar localmente:
    streamlit run app/streamlit_app.py
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st
from src.agent import load_agent, ask

st.set_page_config(page_title="Agente Corporativo IA", page_icon="🤖")

# Inicialización de estado
if "chain" not in st.session_state:
    with st.spinner("Cargando base de conocimiento..."):
        st.session_state.chain = load_agent()

if "history" not in st.session_state:
    st.session_state.history = []

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

# Encabezado principal centrado
st.title("🤖 Agente de Conocimiento Corporativo")
st.caption("Responde preguntas basadas en los documentos internos de la empresa.")

# Preguntas Frecuentes centradas en el cuerpo principal si no hay historial
if not st.session_state.history:
    st.markdown("##### 💡 Preguntas Frecuentes")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📦 ¿Cuáles son los plazos de devolución?", use_container_width=True):
            st.session_state.pending_question = "¿Cuáles son los plazos para devolver un producto?"
        if st.button("🚚 ¿Quién paga el envío de devolución?", use_container_width=True):
            st.session_state.pending_question = "¿Quién cubre los costos de envío de una devolución?"

    with col2:
        if st.button("💳 ¿Qué métodos de pago aceptan?", use_container_width=True):
            st.session_state.pending_question = "¿Qué métodos de pago son aceptados?"
        if st.button("🛡️ ¿Qué cubre la garantía de un producto?", use_container_width=True):
            st.session_state.pending_question = "¿Qué cubre el manual de garantía de productos?"

    st.markdown("---")

# Mostrar historial de la conversación
for role, msg in st.session_state.history:
    with st.chat_message(role):
        st.markdown(msg)

# Botón discreto para reiniciar chat si ya hay historial
if st.session_state.history:
    st.markdown("---")
    if st.button("🔄 Nueva consulta", help="Limpiar historial de pantalla"):
        st.session_state.history = []
        st.rerun()

# Campo de entrada
user_input = st.chat_input("Escribe tu pregunta sobre las políticas o procesos de la empresa...")
question = user_input or st.session_state.pending_question

if question:
    st.session_state.pending_question = None
    st.session_state.history.append(("user", question))
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Buscando en los documentos..."):
            result = ask(question, st.session_state.chain)
            answer = result["answer"]
            
            if isinstance(answer, list):
                text_parts = [item.get("text", "") for item in answer if isinstance(item, dict) and "text" in item]
                answer_text = "\n".join(text_parts) if text_parts else str(answer)
            else:
                answer_text = str(answer)

            if result["sources"]:
                answer_text += f"\n\n📎 **Fuentes:** {', '.join(result['sources'])}"
            st.markdown(answer_text)

    st.session_state.history.append(("assistant", answer_text))
    st.rerun()
