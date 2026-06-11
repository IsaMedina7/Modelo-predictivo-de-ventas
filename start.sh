
#!/bin/bash



# 1. Filtro inteligente: Si pegaste la URL completa, el script extrae solo el ID automáticamente

CLEAN_ID="$DRIVE_FILE_ID"

if [[ "$CLEAN_ID" == *"file/d/"* ]]; then

    CLEAN_ID=$(echo "$CLEAN_ID" | sed -E 's|.*/file/d/([^/]+).*|\1|')

fi



echo "Iniciando descarga segura desde Google Drive..."

# 2. Descargar el archivo usando el ID limpio

gdown --id "$CLEAN_ID" -O modelo_demanda.pkl



# 3. Alerta de diagnóstico (Saber si falló por culpa de los permisos de Drive)

if [ ! -f "modelo_demanda.pkl" ]; then

    echo "❌ ALERTA CRÍTICA: El archivo no se pudo descargar. Verifica que el enlace no esté 'Restringido' en Google Drive."

else

    echo "✅ El modelo se descargó con éxito de Google Drive."

fi



# 4. Encender la aplicación

uvicorn main:app --host 0.0.0.0 --port 8000 &

streamlit run app.py --server.port 8501 --server.address 0.0.0.0

