# ---------- Stage 1: builder ----------
FROM python:3.12-slim AS builder

WORKDIR /build

# Dipendenze di sistema necessarie solo in fase di build (se servissero pacchetti compilati)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Installiamo le dipendenze in una directory isolata, da copiare poi nello stage finale
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt


# ---------- Stage 2: runtime ----------
FROM python:3.12-slim

# Metadati immagine (buona pratica per tracciabilità)
LABEL org.opencontainers.image.title="api-platform-demo"
LABEL org.opencontainers.image.description="FastAPI demo service per pipeline CI/CD + Kubernetes"

# Utente non-root
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Copiamo solo le dipendenze già installate dallo stage builder (niente compilatori nell'immagine finale)
COPY --from=builder /install /usr/local

COPY main.py .

# Argomento build-time per taggare la versione dentro l'app (passato dalla pipeline Jenkins, Capitolo 12)
ARG APP_VERSION=0.1.0
ENV APP_VERSION=${APP_VERSION}

# Permessi corretti per l'utente non-root
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Healthcheck nativo Docker (indipendente dalle probe K8s, utile anche in docker run standalone)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz/live')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
