"""
agent.py
Define el agente de IA corporativo: recibe una pregunta en lenguaje
natural, recupera los fragmentos más relevantes de la base vectorial
(Chroma) y genera una respuesta fundamentada en los documentos internos,
citando la fuente (nombre del archivo).

Uso directo (modo consola):
    python src/agent.py
"""

from pathlib import Path

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
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


def load_agent():
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectordb = Chroma(
        persist_directory=str(PERSIST_DIR),
        embedding_function=embeddings,
        collection_name="alura_agente_docs",
    )
    retriever = vectordb.as_retriever(search_kwargs={"k": 4})

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", "{input}"),
        ]
    )

    combine_docs_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, combine_docs_chain)
    return rag_chain


def ask(question: str, rag_chain=None) -> dict:
    if rag_chain is None:
        rag_chain = load_agent()
    result = rag_chain.invoke({"input": question})
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
