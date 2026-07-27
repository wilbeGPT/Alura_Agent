"""
streamlit_app.py
Interfaz web interactiva para el Agente de Conocimiento Corporativo (BimBam Buy).

Ejecutar localmente:
    streamlit run app/streamlit_app.py
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st
from src.agent import load_agent, ask

st.set_page_config(page_title="Agente Corporativo IA — BimBam Buy", page_icon="🤖", layout="wide")

# Inicialización de estado
if "chain" not in st.session_state:
    with st.spinner("Cargando base de conocimiento corporativo..."):
        st.session_state.chain = load_agent()

if "history" not in st.session_state:
    st.session_state.history = []

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

# Sidebar con Preguntas Frecuentes (FAQ)
with st.sidebar:
    st.title("💡 Preguntas Frecuentes")
    st.caption("Haz clic en una pregunta rápida para consultar al agente:")
    
    faqs = [
        "📦 ¿Cuáles son los plazos para devolver un producto?",
        "💳 ¿Qué métodos de pago son aceptados en la plataforma?",
        "🚚 ¿Quién cubre los costos de envío de una devolución?",
        "🛡️ ¿Qué cubre el manual de garantía de productos?",
        "🤝 ¿Cómo funciona el programa de afiliados de BimBam Buy?"
    ]
    
    for faq in faqs:
        clean_faq = faq.split(" ", 1)[1] if " " in faq else faq
        if st.button(faq, use_container_width=True):
            st.session_state.pending_question = clean_faq

    st.markdown("---")
    if st.button("🗑️ Limpiar historial de chat", use_container_width=True):
        st.session_state.history = []
        st.rerun()

# Área principal
st.title("🤖 Agente de Conocimiento Corporativo")
st.caption("Responde preguntas basadas exclusivamente en las políticas y documentos internos de BimBam Buy.")

# Mostrar historial de mensajes
for role, msg in st.session_state.history:
    with st.chat_message(role):
        st.markdown(msg)

# Sugerencias rápidas si no hay historial
if not st.session_state.history:
    st.info("💡 **Consejo:** Puedes escribir cualquier duda en el campo de texto inferior o seleccionar una de las **Preguntas Frecuentes** en el menú lateral izquierdo.")

# Procesar entrada del usuario o selección del FAQ
user_input = st.chat_input("Escribe tu pregunta sobre las políticas o procesos de la empresa...")
question = user_input or st.session_state.pending_question

if question:
    st.session_state.pending_question = None
    st.session_state.history.append(("user", question))
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Buscando en los documentos corporativos..."):
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
