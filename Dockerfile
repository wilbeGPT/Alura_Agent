FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema necesarias para unstructured / parsing de office
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmagic1 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# En plataformas con almacenamiento efímero (Render free tier, etc.) el
# disco no persiste entre reinicios del contenedor, así que generamos
# la base vectorial durante el build. La clave de Gemini debe estar
# disponible como variable de entorno en tiempo de build.
ARG GEMINI_API_KEY
ENV GEMINI_API_KEY=${GEMINI_API_KEY}
RUN python src/ingest.py

EXPOSE 8501

# La base vectorial ya se generó arriba durante el build.
# Aquí solo se levanta la app:
CMD ["streamlit", "run", "app/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]