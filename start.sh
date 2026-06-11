
#!/bin/bash



# 1. Descargar el modelo al encender la app (usando la variable segura de Render)

echo "Descargando modelo desde Google Drive..."

gdown "https://drive.google.com/uc?id=${DRIVE_FILE_ID}" -O modelo_demanda.pkl



# 2. Encender la aplicación

uvicorn main:app --host 0.0.0.0 --port 8000 &

streamlit run app.py --server.port 8501 --server.address 0.0.0.0

