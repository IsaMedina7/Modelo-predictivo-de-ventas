
FROM python:3.12-slim



WORKDIR /app



RUN apt-get update && apt-get install -y \

    build-essential \

    git \

    && rm -rf /var/lib/apt/lists/*



COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt



# 1. Instalamos la herramienta especial para Google Drive

RUN pip install gdown



COPY . .



ARG DRIVE_FILE_ID



# 2. Usamos gdown para saltar la advertencia de virus y descargar el modelo real

RUN gdown "https://drive.google.com/uc?id=${DRIVE_FILE_ID}" -O modelo_demanda.pkl



RUN chmod +x start.sh



EXPOSE 8000

EXPOSE 8501



CMD ["bash", "start.sh"]

