"""
agent.py
Define el agente de IA corporativo: recibe una pregunta en lenguaje
natural, recupera los fragmentos más relevantes de la base vectorial
(Chroma) y genera una respuesta fundamentada en los documentos internos,
citando la fuente (nombre del archivo).

Construido con los bloques básicos de LangChain (Runnables de
langchain_core) en vez de las cadenas de alto nivel (create_retrieval_chain,
etc.), que a partir de LangChain 1.0 se movieron al paquete separado
`langchain_classic` y cambian con frecuencia entre versiones.

Uso directo (modo consola):
    python src/agent.py
"""

import os
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from dotenv import load_dotenv

load_dotenv()

PERSIST_DIR = Path(__file__).resolve().parent.parent / "chroma_db"

SYSTEM_PROMPT = """Eres el Agente de Conocimiento Corporativo de la empresa.
Respondes preguntas de los colaboradores basándote ÚNICAMENTE en el
contexto de documentos internos que se te entrega a continuación.

Reglas:
- Si la respuesta no está en el contexto, di claramente que no
  encontraste esa información en los documentos disponibles.
- Sé preciso, breve y profesional.
- Cuando sea posible, menciona de qué documento proviene la información
  (usa el campo 'source' de los metadatos).

Contexto:
{context}
"""


def format_docs(docs) -> str:
    return "\n\n".join(
        f"[Fuente: {d.metadata.get('source', 'desconocido')}]\n{d.page_content}"
        for d in docs
    )

def extract_text(content) -> str:
    """Extrae solo el texto de la respuesta del LLM.

    Modelos recientes de Gemini devuelven `response.content` como una
    lista de bloques estructurados (texto, firmas internas, etc.) en
    vez de un string plano. Esta función toma únicamente los bloques
    de tipo 'text' y descarta el resto.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    return str(content)

def load_agent():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=api_key
    )
    vectordb = Chroma(
        persist_directory=str(PERSIST_DIR),
        embedding_function=embeddings,
        collection_name="alura_agente_docs",
    )
    retriever = vectordb.as_retriever(search_kwargs={"k": 4})

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.6-flash",
        temperature=0,
        google_api_key=api_key
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", "{input}"),
        ]
    )

    def generate_answer(inputs: dict) -> dict:
        docs = inputs["context"]
        messages = prompt.invoke({"context": format_docs(docs), "input": inputs["input"]})
        response = llm.invoke(messages)
        return {"answer": extract_text(response.content), "context": docs}

    # 1) En paralelo: recupera documentos relevantes y conserva la pregunta original
    # 2) Genera la respuesta con el LLM usando ese contexto
    rag_chain = (
        RunnableParallel(context=retriever, input=RunnablePassthrough())
        | RunnableLambda(generate_answer)
    )
    return rag_chain


def ask(question: str, rag_chain=None) -> dict:
    if rag_chain is None:
        rag_chain = load_agent()
    try:
        result = rag_chain.invoke(question)
    except Exception as e:
        error_text = str(e)
        if "RESOURCE_EXHAUSTED" in error_text or "429" in error_text:
            return {
                "answer": (
                    "⚠️ Se alcanzó el límite gratuito diario de consultas a Gemini. "
                    "Este límite se reinicia automáticamente cada 24 horas "
                    "(medianoche hora del Pacífico). Por favor intenta de nuevo "
                    "más tarde."
                ),
                "sources": [],
            }
        return {
            "answer": (
                "⚠️ Ocurrió un error inesperado al consultar el agente. "
                "Por favor intenta de nuevo en unos momentos."
            ),
            "sources": [],
        }
    sources = sorted(
        {doc.metadata.get("source", "desconocido") for doc in result.get("context", [])}
    )
    return {"answer": result["answer"], "sources": sources}


if __name__ == "__main__":
    chain = load_agent()
    print("🤖 Agente de Conocimiento Corporativo — escribe 'salir' para terminar.\n")
    while True:
        question = input("Tú: ")
        if question.strip().lower() in {"salir", "exit", "quit"}:
            break
        result = ask(question, chain)
        print(f"\nAgente: {result['answer']}")
        if result["sources"]:
            print(f"📎 Fuentes: {', '.join(result['sources'])}\n")
