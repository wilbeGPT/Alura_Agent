# 🤖 Agente Corporativo de IA — BimBam Buy

Agente de inteligencia artificial (RAG) que responde preguntas de los
colaboradores de **BimBam Buy** (caso de negocio: e-commerce
multiplataforma) con base en documentos internos de la empresa:
políticas de reembolso, programa de afiliados, tiempos de envío,
métodos de pago y garantías.

Proyecto desarrollado para el desafío **Alura Agentes**.

---

## 🏗️ Arquitectura

```
                ┌─────────────────────┐
                │   docs/ (PDF, Word, │
                │  Excel, PPTX, MD,   │
                │   CSV, JSON, HTML)  │
                └──────────┬──────────┘
                           │  ingest.py
                           │  (loaders + splitter)
                           ▼
                ┌─────────────────────┐
                │  Chroma Vector DB   │
                │  (embeddings OpenAI)│
                └──────────┬──────────┘
                           │  retriever (top-k)
                           ▼
      Pregunta ─────▶ ┌─────────────────────┐
      del usuario     │   agent.py (RAG)    │
                       │  LangChain + LLM    │
                       │   (gpt-4o-mini)     │
                       └──────────┬──────────┘
                                  │ respuesta + fuentes
                                  ▼
                       ┌─────────────────────┐
                       │  Streamlit UI       │
                       │  (app/streamlit_app)│
                       └──────────┬──────────┘
                                  │ Docker container
                                  ▼
                       ┌─────────────────────┐
                       │  OCI Compute        │
                       │  (VM.Standard.E4)   │
                       └─────────────────────┘
```

**Flujo:**
1. `ingest.py` recorre `docs/`, carga cada archivo con el loader
   adecuado según su extensión, lo divide en fragmentos (*chunks*) y
   genera embeddings que se almacenan en una base vectorial **Chroma**
   persistente.
2. `agent.py` arma una cadena RAG con **LangChain**: dado un mensaje
   del usuario, recupera los fragmentos más relevantes y se los pasa al
   modelo de lenguaje junto con un *system prompt* que lo obliga a
   responder solo con base en esos documentos, citando la fuente.
3. `app/streamlit_app.py` expone el agente como un chat web simple.
4. Todo se empaqueta en un contenedor **Docker** y se despliega en una
   instancia de **OCI Compute** (Oracle Cloud Infrastructure).

### Stack tecnológico
| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.11 |
| Orquestación del agente | LangChain |
| Carga de documentos | PyPDF, python-docx, openpyxl, python-pptx, unstructured, pandas |
| Base vectorial | Chroma |
| Modelo de lenguaje / embeddings | OpenAI (`gpt-4o-mini`, `text-embedding-3-small`) — intercambiable por Cohere/Gemma |
| Interfaz | Streamlit |
| Infraestructura / deploy | Docker + OCI Compute |

---

## 📂 Estructura del repositorio

```
alura-agente/
├── docs/                    # Documentos internos de la empresa (PDF, Word, etc.)
├── src/
│   ├── ingest.py            # Ingesta y vectorización de documentos
│   └── agent.py             # Agente RAG (lógica conversacional)
├── app/
│   └── streamlit_app.py     # Interfaz web de chat
├── chroma_db/                # Base vectorial generada (no se sube a git)
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚙️ Instrucciones para ejecutar el proyecto

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/alura-agente.git
cd alura-agente
```

### 2. Crear entorno virtual e instalar dependencias
```bash
python -m venv venv
source venv/bin/activate      # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configurar la clave de API
```bash
cp .env.example .env
# Edita .env y coloca tu OPENAI_API_KEY
```

### 4. Agregar los documentos de la empresa
Descarga los documentos oficiales de BimBam Buy (o los de tu propio
caso de negocio) y colócalos dentro de `docs/`:

- Política de Reembolsos y Devoluciones de BimBam Buy
- Programa de Afiliados de BimBam Buy
- Guía de Tiempos y Costos de Envío de BimBam Buy
- Preguntas Frecuentes sobre Métodos de Pago de BimBam Buy
- Manual de Garantía de Productos de BimBam Buy

> Se incluye `docs/ejemplo_politica_reembolsos.md` como documento de
> muestra para poder probar el pipeline de inmediato.

### 5. Indexar los documentos
```bash
python src/ingest.py
```

### 6. Ejecutar el agente
- **Modo consola:**
  ```bash
  python src/agent.py
  ```
- **Modo web (Streamlit):**
  ```bash
  streamlit run app/streamlit_app.py
  ```

---

## 💬 Ejemplos de preguntas y respuestas

| Pregunta | Respuesta esperada |
|---|---|
| "¿Cuántos días tengo para devolver un producto?" | "30 días calendario desde la entrega, con el empaque original y sin uso. (Fuente: Política de Reembolsos y Devoluciones de BimBam Buy)" |
| "¿Quién paga el envío de una devolución por producto defectuoso?" | "BimBam Buy cubre el costo cuando la devolución se debe a un error de la empresa." |
| "¿Puedo devolver ropa interior?" | "No, los artículos de ropa interior y productos personalizados están excluidos de la política de devoluciones." |
| "¿Cuál es la política de vacaciones de la empresa?" | "No encontré esa información en los documentos disponibles." (el agente reconoce cuando algo no está en el contexto) |

---

## ☁️ Deploy en Oracle Cloud Infrastructure (OCI)

Servicio utilizado: **OCI Compute** (instancia VM con Docker).

### Pasos sugeridos
1. Crear una instancia **VM.Standard.E4.Flex** (Ubuntu 22.04) en OCI,
   con un *Security List* que abra el puerto **8501**.
2. Conectarse por SSH e instalar Docker:
   ```bash
   sudo apt update && sudo apt install -y docker.io
   sudo systemctl enable --now docker
   ```
3. Clonar el repositorio dentro de la instancia y configurar `.env`.
4. Construir y ejecutar el contenedor:
   ```bash
   sudo docker build -t alura-agente .
   sudo docker run -d --env-file .env -p 8501:8501 alura-agente
   ```
5. Ejecutar la ingesta una vez dentro del contenedor (o antes de
   construir la imagen) para generar `chroma_db/`:
   ```bash
   sudo docker exec -it <container_id> python src/ingest.py
   ```
6. Acceder desde el navegador a `http://<IP_PUBLICA_OCI>:8501`.

> 📸 **Evidencia del deploy:** agrega aquí una captura de pantalla o
> video corto del agente respondiendo preguntas mientras corre en la
> instancia de OCI.
>
> `![Agente corriendo en OCI](docs/screenshot-oci.png)`

---

## ✅ Estado del proyecto / checklist del desafío

- [x] Agente responde con base en documentos internos (RAG)
- [x] Soporta PDF, Word, Excel, PowerPoint, Markdown, CSV, JSON, HTML
- [x] Repositorio organizado con historial de commits
- [ ] Deploy realizado en OCI (agregar evidencia)
- [ ] Captura/video del deploy insertada en este README

---

## 📝 Notas
- El LLM (`gpt-4o-mini`) y los embeddings de OpenAI pueden sustituirse
  libremente por Cohere, Gemma (vía Ollama) u otro proveedor; solo hay
  que cambiar `src/agent.py` e `src/ingest.py`.
- Para producción, considera mover `chroma_db/` a un volumen persistente
  de OCI Block Storage para no perder el índice al reiniciar el contenedor.
