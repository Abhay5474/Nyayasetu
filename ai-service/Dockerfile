FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    FASTEMBED_CACHE_PATH=/opt/models

# Tesseract OCR with English, Marathi and Hindi language packs
RUN apt-get update \
 && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng tesseract-ocr-mar tesseract-ocr-hin curl \
 && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/models
WORKDIR /app

# Heaviest, rarely-changing layers first, so editing requirements.txt or the code never re-downloads ~1 GB of models:
# 1) the ML libraries (keep these two lines in sync with requirements.txt), 2) the models, 3) everything else.
RUN pip install "fastembed>=0.5,<1" "numpy>=1.26"

# Bake the multilingual embedding + reranker models into the image so start-up is fast and offline-safe.
# Build with --build-arg PRELOAD_MODELS=false to skip (models are then downloaded on first start).
ARG PRELOAD_MODELS=true
ARG EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
ARG RERANKER_MODEL=jinaai/jina-reranker-v2-base-multilingual
RUN if [ "$PRELOAD_MODELS" = "true" ]; then python -c "\
from fastembed import TextEmbedding; \
from fastembed.rerank.cross_encoder import TextCrossEncoder; \
TextEmbedding('${EMBEDDING_MODEL}'); \
TextCrossEncoder('${RERANKER_MODEL}')"; fi

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app
COPY knowledge_base ./knowledge_base
COPY eval ./eval

RUN useradd --create-home --uid 10001 appuser && chown -R appuser /app /opt/models
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=5 \
  CMD curl -fsS http://localhost:8000/health || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
