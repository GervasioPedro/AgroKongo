# Usamos uma imagem leve de Python
FROM python:3.11-slim

# Instala dependências do sistema para WeasyPrint e Pillow
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-cffi \
    python3-brotli \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho
WORKDIR /app

# Copia e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do código
COPY . .

# Cria as pastas de storage e dá permissões
RUN mkdir -p /app/data_storage/public /app/data_storage/private
RUN chmod -R 755 /app/data_storage

# Porta padrão do Flask
EXPOSE 5000

# Comando para iniciar com Gunicorn (4 workers para performance)
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "run:app"]