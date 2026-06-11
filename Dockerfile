
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



# 1. Declaramos que Render nos pasará el ID como un argumento de construcción

ARG DRIVE_FILE_ID



# 2. Usamos la variable ${DRIVE_FILE_ID} en el comando wget

RUN wget --no-check-certificate "https://docs.google.com/uc?export=download&id=${DRIVE_FILE_ID}" -O modelo_demanda.pkl



RUN chmod +x start.sh



EXPOSE 8000

EXPOSE 8501



CMD ["./start.sh"]

