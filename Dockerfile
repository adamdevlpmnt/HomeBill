# ==========================================
# Étape 1 : Build du Frontend (React + Vite)
# ==========================================
FROM node:22-alpine AS frontend-builder
WORKDIR /build

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ==========================================
# Étape 2 : Image Runtime Python 3.12 Slim
# ==========================================
FROM python:3.12-slim AS runner
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/data \
    TZ=Africa/Algiers

# Installation de curl pour le healthcheck et de tzdata pour le fuseau horaire
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copie du backend et de la configuration des tarifs
COPY backend/ ./backend/
COPY config/ ./config/
COPY docs/ ./docs/

# Copie des fichiers statiques compilés du frontend
COPY --from=frontend-builder /build/dist ./frontend/dist

# Création du point de montage pour le volume SQLite /data
RUN mkdir -p /data

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

WORKDIR /app/backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
