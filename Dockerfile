
FROM python:3.12-slim



WORKDIR /app



RUN apt-get update && apt-get install -y \

    build-essential \

    git \

    wget \

    && rm -rf /var/lib/apt/lists/*



COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt



COPY . .



# Recibimos la variable de entorno

ARG DRIVE_FILE_ID



# Descarga automática del modelo

RUN wget --no-check-certificate "https://docs.google.com/uc?export=download&id=${DRIVE_FILE_ID}" -O modelo_demanda.pkl



# Le damos permisos al script

RUN chmod +x start.sh



EXPOSE 8000

EXPOSE 8501



# LA SOLUCIÓN: Forzamos a bash a ejecutar el archivo

CMD ["bash", "start.sh"]

