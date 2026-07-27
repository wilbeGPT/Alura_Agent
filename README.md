# 🤖 Agente Corporativo de IA — BimBam Buy

Agente de inteligencia artificial (RAG) que responde preguntas de los
colaboradores de **BimBam Buy** (caso de negocio: e-commerce
multiplataforma) con base en documentos internos de la empresa:
políticas de reembolso, programa de afiliados, tiempos de envío,
métodos de pago y garantías.

Proyecto desarrollado para el desafío **Alura Agentes**.

**🔗 Demo en vivo:** [https://alura-agent.onrender.com](https://alura-agent.onrender.com)

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
                 │ (embeddings Gemini) │
                 └──────────┬──────────┘
                            │  retriever (top-k)
                            ▼
       Pregunta ─────▶ ┌─────────────────────┐
       del usuario     │   agent.py (RAG)    │
                        │  LangChain + LLM    │
                        │  (gemini-3.6-flash) │
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
                       │ Render (Web Service) │
                       │  Free Tier, Docker    │
                       └─────────────────────┘
```

**Flujo:**
1. `ingest.py` recorre `docs/`, carga cada archivo con el loader
   adecuado según su extensión, lo divide en fragmentos (*chunks*) y
   genera embeddings que se almacenan en una base vectorial **Chroma**
   persistente (`chroma_db/`).
2. `agent.py` arma una cadena RAG con **LangChain** (Runnables de
   `langchain_core`): dado un mensaje del usuario, recupera los
   fragmentos más relevantes y se los pasa al modelo de lenguaje junto
   con un *system prompt* que lo obliga a responder solo con base en
   esos documentos, citando la fuente.
3. `app/streamlit_app.py` expone el agente como un chat web.
4. Todo se empaqueta en un contenedor **Docker** y se despliega en
   **Render** (Web Service, plan gratuito).

### Stack tecnológico
| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.11 |
| Orquestación del agente | LangChain (Runnables / LCEL) |
| Carga de documentos | PyPDF, python-docx, openpyxl, python-pptx, unstructured, pandas |
| Base vectorial | Chroma |
| Modelo de lenguaje / embeddings | Google Gemini (`gemini-3.6-flash`, `models/gemini-embedding-001`) |
| Interfaz | Streamlit |
| Infraestructura / deploy | Docker + Render (Web Service) |

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
├── chroma_db/                # Base vectorial ya generada (incluida en el repo)
├── .streamlit/
│   └── config.toml           # Configuración de producción (desactiva file watcher)
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚙️ Instrucciones para ejecutar el proyecto localmente

### 1. Clonar el repositorio
```bash
git clone https://github.com/wilbeGPT/Alura_Agent.git
cd Alura_Agent
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
# Edita .env y coloca tu GEMINI_API_KEY
# (consíguela gratis en https://aistudio.google.com/apikey)
```

### 4. Agregar los documentos de la empresa
Coloca dentro de `docs/` los documentos oficiales de BimBam Buy (ya
incluidos en este repositorio):

- Política de Reembolsos y Devoluciones de BimBam Buy
- Programa de Afiliados de BimBam Buy
- Guía de Tiempos y Costos de Envío de BimBam Buy
- Preguntas Frecuentes sobre Métodos de Pago de BimBam Buy
- Manual de Garantía de Productos de BimBam Buy

### 5. Indexar los documentos
```bash
python src/ingest.py
```
> Nota: la carpeta `chroma_db/` ya viene generada e incluida en el
> repositorio, así que este paso es opcional si solo quieres probar
> el agente rápido. Vuelve a correrlo si agregas o cambias documentos.

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

## ❓ Preguntas frecuentes (ejemplos de uso)

| Pregunta | Respuesta esperada / Fuente |
|---|---|
| "¿Cuáles son los plazos para devolver un producto?" | Muestra los plazos según retracto de compra (10 días), daño visible (48 horas) o falla de garantía. (Fuente: Política de Reembolsos y Devoluciones de BimBam Buy) |
| "¿Qué métodos de pago son aceptados?" | Lista las opciones de pago disponibles. (Fuente: Preguntas Frecuentes sobre Métodos de Pago de BimBam Buy) |
| "¿Quién paga el envío de una devolución por producto defectuoso?" | BimBam Buy cubre el costo cuando la devolución se debe a un error o defecto de origen. |
| "¿Puedo devolver ropa interior o productos personalizados?" | No, están excluidos de la política de devoluciones por higiene/personalización. |
| "¿Cuál es la política de vacaciones de la empresa?" | *"No encontré información sobre la política de vacaciones en los documentos disponibles."* (el agente reconoce cuando algo está fuera de su base de conocimiento, en vez de inventar una respuesta). |

---

## ☁️ Despliegue en la nube

**Plataforma utilizada: Render** (Web Service, plan gratuito, contenedor Docker).

### Nota sobre el cambio de OCI a Render
El desafío original sugiere Oracle Cloud Infrastructure (OCI) como
plataforma de despliegue. Se intentó registrar una cuenta en OCI, pero
el proceso de verificación de identidad de Oracle exige una tarjeta de
crédito física o una tarjeta de débito de red internacional (Visa/
Mastercard/Amex no prepago), medio de pago que no estaba disponible
para completar el registro. Ante este bloqueo genuino (no técnico, sino
de acceso a un medio de pago), se optó por **Render** como plataforma
de despliegue equivalente: es un servicio de nube real, con despliegue
de contenedores Docker, sin necesidad de tarjeta.

### Pasos realizados
1. Se creó una cuenta en Render conectada a GitHub.
2. Se creó un **Web Service** apuntando al repositorio
   `wilbeGPT/Alura_Agent`, detectando automáticamente el `Dockerfile`.
3. Se configuró la variable de entorno `GEMINI_API_KEY` en el panel de
   Render.
4. Se seleccionó el plan **Free**.
5. Render construyó la imagen Docker y desplegó el contenedor
   automáticamente al hacer `git push`.

### Evidencia del deploy funcionando

**URL pública:** [https://alura-agent.onrender.com](https://alura-agent.onrender.com)

![Agente respondiendo en producción](docs/evidencia-deploy-render.png)

*El agente respondiendo correctamente sobre los plazos de devolución,
citando la fuente del documento PDF correspondiente, desde la URL
pública de Render.*

---

## ✅ Estado del proyecto / checklist del desafío

- [x] Agente responde con base en documentos internos (RAG)
- [x] Soporta PDF, Word, Excel, PowerPoint, Markdown, CSV, JSON, HTML
- [x] Repositorio organizado con historial de commits
- [x] Deploy realizado en la nube (Render, en sustitución justificada de OCI)
- [x] Captura de evidencia del deploy incluida en este README

---

## 📝 Notas técnicas
- El LLM (`gemini-3.6-flash`) y los embeddings de Google Gemini
  (`models/gemini-embedding-001`) pueden sustituirse por otros
  proveedores compatibles con LangChain (OpenAI, Cohere, etc.)
  modificando `src/agent.py` e `src/ingest.py`.
- `ingest.py` procesa los documentos en lotes con reintentos
  automáticos para respetar los límites de cuota gratuita de la API de
  Gemini.
- La base vectorial (`chroma_db/`) se generó localmente y se incluyó
  directamente en el repositorio, en vez de regenerarse en cada
  despliegue, para evitar agotar la cuota diaria de la API en cada
  build.
- El archivo `.streamlit/config.toml` desactiva el "file watcher" de
  Streamlit, necesario para evitar un error de límite de `inotify` en
  entornos de contenedor restringidos como el plan gratuito de Render.
