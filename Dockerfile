FROM python:3.11-slim

WORKDIR /app


# Instalar dependencias del sistema para Chromium
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libnss3 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    libx11-6 \
    && rm -rf /var/lib/apt/lists/*

# Instalar Python deps
RUN pip install playwright fuzzywuzzy python-Levenshtein colorama

# Instalar navegador
RUN playwright install chromium

COPY . .
CMD ["python", "main.py"]
