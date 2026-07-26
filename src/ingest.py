"""
ingest.py
Carga documentos de la carpeta `docs/` en múltiples formatos
(PDF, Word, Excel, PowerPoint, Markdown, CSV, JSON, HTML), los
divide en fragmentos (chunks) y los indexa en una base vectorial
Chroma persistente para su posterior consulta por el agente RAG.

Uso:
    python src/ingest.py
"""

import os
import json
from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader,
    UnstructuredPowerPointLoader,
    UnstructuredMarkdownLoader,
    CSVLoader,
    BSHTMLLoader,
)
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
PERSIST_DIR = Path(__file__).resolve().parent.parent / "chroma_db"

LOADER_MAP = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".xlsx": UnstructuredExcelLoader,
    ".xls": UnstructuredExcelLoader,
    ".pptx": UnstructuredPowerPointLoader,
    ".md": UnstructuredMarkdownLoader,
    ".csv": CSVLoader,
    ".html": BSHTMLLoader,
    ".htm": BSHTMLLoader,
}


def load_json(path: Path) -> list[Document]:
    """JSON no tiene loader nativo simple en LangChain community para
    texto libre, así que lo aplanamos a texto legible."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    text = json.dumps(data, ensure_ascii=False, indent=2)
    return [Document(page_content=text, metadata={"source": str(path)})]


def load_all_documents() -> list[Document]:
    documents: list[Document] = []

    if not DOCS_DIR.exists():
        raise FileNotFoundError(
            f"No se encontró la carpeta {DOCS_DIR}. Crea 'docs/' y coloca "
            "ahí los documentos de la empresa."
        )

    files = [f for f in DOCS_DIR.rglob("*") if f.is_file()]
    if not files:
        print(f"⚠️  No hay archivos en {DOCS_DIR}. Agrega documentos antes de indexar.")

    for file_path in files:
        suffix = file_path.suffix.lower()
        try:
            if suffix == ".json":
                documents.extend(load_json(file_path))
            elif suffix in LOADER_MAP:
                loader_cls = LOADER_MAP[suffix]
                loader = loader_cls(str(file_path))
                docs = loader.load()
                for d in docs:
                    d.metadata["source"] = file_path.name
                documents.extend(docs)
            else:
                print(f"⏭️  Formato no soportado, se omite: {file_path.name}")
        except Exception as e:
            print(f"❌ Error cargando {file_path.name}: {e}")

    print(f"✅ Documentos cargados: {len(documents)} fragmentos de origen")
    return documents


def build_vectorstore():
    documents = load_all_documents()

    if not documents:
        print("No hay documentos para indexar. Abortando.")
        return

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    print(f"✂️  Documentos divididos en {len(chunks)} chunks")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(PERSIST_DIR),
        collection_name="alura_agente_docs",
    )
    print(f"💾 Base vectorial creada/actualizada en {PERSIST_DIR}")
    return vectordb


if __name__ == "__main__":
    build_vectorstore()
