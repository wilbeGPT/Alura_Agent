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
    TextLoader,
    CSVLoader,
    BSHTMLLoader,
)
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
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
    ".md": TextLoader,
    ".txt": TextLoader,
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
        print(f"[!] No hay archivos en {DOCS_DIR}. Agrega documentos antes de indexar.")

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
                print(f"[Omitido] Formato no soportado: {file_path.name}")
        except Exception as e:
            print(f"[Error] Carga fallida {file_path.name}: {e}")

    print(f"[OK] Documentos cargados: {len(documents)} fragmentos de origen")
    return documents


import time

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
    print(f"[OK] Documentos divididos en {len(chunks)} chunks")

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=api_key
    )

    batch_size = 30
    total_batches = (len(chunks) - 1) // batch_size + 1
    vectordb = None

    for idx, i in enumerate(range(0, len(chunks), batch_size), start=1):
        batch = chunks[i : i + batch_size]
        print(f"[...] Indexando lote {idx}/{total_batches} ({len(batch)} fragmentos)...")
        
        for attempt in range(1, 6):
            try:
                if vectordb is None:
                    vectordb = Chroma.from_documents(
                        documents=batch,
                        embedding=embeddings,
                        persist_directory=str(PERSIST_DIR),
                        collection_name="alura_agente_docs",
                    )
                else:
                    vectordb.add_documents(batch)
                break
            except Exception as e:
                err_msg = str(e)
                if "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg:
                    print(f"    [Pausa de cuota] Esperando 15s antes de reintentar (intento {attempt}/5)...")
                    time.sleep(15)
                else:
                    raise e

        if idx < total_batches:
            time.sleep(5)

    print(f"[OK] Base vectorial creada/actualizada en {PERSIST_DIR}")
    return vectordb


if __name__ == "__main__":
    build_vectorstore()
