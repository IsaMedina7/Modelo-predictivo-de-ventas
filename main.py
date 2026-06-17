from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import joblib
import sqlite3
import os
import gdown  # ¡Importante para descargar de Drive!
from datetime import timedelta
import numpy as np

app = FastAPI(title="Core de Retail con DB Real - Modelo Robusto")

# 1. DEFINICIÓN ESTRICTA DE VARIABLES GLOBALES DE CONTROL
modelo_ia = None
columnas_modelo = None

print("⏳ Verificando archivos del modelo...")

# ID del archivo en Google Drive (El del modelo ROBUSTO)
# Usa os.getenv para que Render le pase el ID, o usa uno por defecto
DRIVE_FILE_ID = os.getenv("DRIVE_FILE_ID", "14NVsKTgFKLQJdlEOF1VxKTw9Drg1WOjs")
MODELO_PATH = "modelo_demanda_robusto.pkl"
FEATURES_PATH = "features_modelo_robusto.pkl"

try:
    # Si el modelo pesado no existe (ej. en Render), lo descargamos de Drive
    if not os.path.exists(MODELO_PATH):
        print(f"☁️ Modelo no encontrado localmente. Descargando desde Google Drive...")
        url = f"https://drive.google.com/uc?id={DRIVE_FILE_ID}"
        gdown.download(url, MODELO_PATH, quiet=False)
        print("✅ Descarga completada.")

    # Ahora sí, cargamos ambos archivos
    if os.path.exists(MODELO_PATH) and os.path.exists(FEATURES_PATH):
        print("⏳ Cargando el PIPELINE en memoria...")
        modelo_ia = joblib.load(MODELO_PATH)
        columnas_modelo = joblib.load(FEATURES_PATH)
        print("✅ ¡Pipeline ROBUSTO y variables cargados con éxito!")
    else:
        print(
            f"❌ ERROR: Aún faltan archivos. Asegúrate de que {FEATURES_PATH} esté subido a GitHub."
        )

except Exception as e:
    print(f"❌ ERROR CRÍTICO AL CARGAR LOS ARCHIVOS PKL: {e}")


# Función auxiliar para conectar a la DB
def conectar_db():
    conn = sqlite3.connect("sistema_retail.db")
    conn.row_factory = sqlite3.Row
    return conn


# --- MODELOS DE ENTRADA PYDANTIC ---
class RegistroUsuario(BaseModel):
    usuario: str
    contrasena: str


class ConsultaDemanda(BaseModel):
    store_nbr: int
    family: str
    fecha_inicio: str
    dias_prediccion: int


class ItemInventario(BaseModel):
    store_nbr: int
    family: str
    cantidad: int


# ==========================================
# ENDPOINTS DE AUTENTICACIÓN E INVENTARIO (Sin cambios)
# ==========================================
@app.post("/api/auth/register")
def registrar_usuario(datos: RegistroUsuario):
    conn = conectar_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO usuarios (usuario, contrasena) VALUES (?, ?)",
            (datos.usuario, datos.contrasena),
        )
        conn.commit()
        return {"status": "success", "message": "Usuario registrado correctamente"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="El usuario ya existe.")
    finally:
        conn.close()


@app.post("/api/auth/login")
def login_usuario(datos: RegistroUsuario):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM usuarios WHERE usuario = ? AND contrasena = ?",
        (datos.usuario, datos.contrasena),
    )
    usuario_encontrado = cursor.fetchone()
    conn.close()

    if not usuario_encontrado:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos.")
    return {"status": "success", "usuario": datos.usuario}


@app.get("/api/inventory")
def obtener_inventario():
    conn = conectar_db()
    df = pd.read_sql_query("SELECT store_nbr, family, stock FROM inventario", conn)
    conn.close()
    return df.to_dict(orient="records")


@app.post("/api/inventory/add")
def agregar_inventario(item: ItemInventario):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO inventario (store_nbr, family, stock) 
        VALUES (?, ?, ?)
        ON CONFLICT(store_nbr, family) 
        DO UPDATE SET stock = stock + excluded.stock
    """,
        (item.store_nbr, item.family, item.cantidad),
    )
    conn.commit()
    conn.close()
    return {"status": "success"}


@app.post("/api/inventory/sell")
def vender_inventario(item: ItemInventario):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT stock FROM inventario WHERE store_nbr = ? AND family = ?",
        (item.store_nbr, item.family),
    )
    resultado = cursor.fetchone()

    if not resultado or resultado["stock"] < item.cantidad:
        conn.close()
        raise HTTPException(status_code=400, detail="Stock insuficiente para la venta.")

    cursor.execute(
        "UPDATE inventario SET stock = stock - ? WHERE store_nbr = ? AND family = ?",
        (item.cantidad, item.store_nbr, item.family),
    )
    conn.commit()
    conn.close()
    return {"status": "success"}


# ==========================================
# ENDPOINT DE HISTÓRICO Y PREDICCIÓN ROBUSTA
# ==========================================
@app.post("/api/predict/demand")
def predecir_demanda(consulta: ConsultaDemanda):
    global modelo_ia, columnas_modelo  # Le decimos a Python que use las variables globales

    # --- FALLBACK DE EMERGENCIA (La solución al problema de Render) ---
    # Si este 'worker' específico tiene la memoria vacía, recarga el archivo
    if modelo_ia is None or columnas_modelo is None:
        print("⚠️ Memoria RAM vacía en este Worker. Recargando modelo en caliente...")
        try:
            if os.path.exists("modelo_demanda_robusto.pkl"):
                modelo_ia = joblib.load("modelo_demanda_robusto.pkl")
                columnas_modelo = joblib.load("features_modelo_robusto.pkl")
                print("✅ Modelo recargado con éxito para esta petición.")
            else:
                raise Exception(
                    "El archivo .pkl no existe en el disco duro del servidor."
                )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Fallo en el Backend: No se pudo recargar el modelo. Error: {e}",
            )

    try:
        conn = conectar_db()
        cursor = conn.cursor()

        # 1. Traer ventas históricas (Útil para calcular los Lags)
        df_hist = pd.read_sql_query(
            """
            SELECT date, sales FROM ventas_historicas 
            WHERE store_nbr = ? AND family = ? 
            ORDER BY date DESC LIMIT 30
        """,
            conn,
            params=(consulta.store_nbr, consulta.family),
        )

        # 2. Traer el stock
        cursor.execute(
            "SELECT stock FROM inventario WHERE store_nbr = ? AND family = ?",
            (consulta.store_nbr, consulta.family),
        )
        res_stock = cursor.fetchone()
        stock_actual = res_stock["stock"] if res_stock else 0
        conn.close()

        # Calcular el promedio histórico reciente para alimentar las variables de Lag del modelo
        promedio_ventas_recientes = (
            df_hist["sales"].mean() if not df_hist.empty else 0.0
        )

        # 3. Preparar variables para predecir en bloque
        fecha_inicial = pd.to_datetime(consulta.fecha_inicio)
        prediccion_ventas_total = 0.0

        filas_para_predecir = []

        for i in range(consulta.dias_prediccion):
            fecha_actual = fecha_inicial + timedelta(days=i)
            valores_fila = {}

            for col in columnas_modelo:
                # -- CATEGÓRICAS (Obligatorio que sean TEXTO / STR) --
                if col == "family":
                    valores_fila[col] = str(consulta.family.upper())
                elif col == "city":
                    valores_fila[col] = "Quito"
                elif col == "state":
                    valores_fila[col] = "Pichincha"
                elif col == "store_type":
                    valores_fila[col] = "A"
                elif col == "cluster":
                    valores_fila[col] = "1"  # <-- ¡Cambiado a texto!
                elif col == "store_nbr":
                    valores_fila[col] = str(
                        consulta.store_nbr
                    )  # <-- ¡Cambiado a texto!

                # -- FECHAS AVANZADAS (Obligatorio que sean NÚMEROS / FLOAT) --
                elif col == "year":
                    valores_fila[col] = float(fecha_actual.year)
                elif col == "month":
                    valores_fila[col] = float(fecha_actual.month)
                elif col == "day":
                    valores_fila[col] = float(fecha_actual.day)
                elif col == "dayofweek":
                    valores_fila[col] = float(fecha_actual.dayofweek)
                elif col == "weekofyear":
                    valores_fila[col] = float(fecha_actual.isocalendar().week)
                elif col == "dayofyear":
                    valores_fila[col] = float(fecha_actual.timetuple().tm_yday)
                elif col == "is_weekend":
                    valores_fila[col] = 1.0 if fecha_actual.dayofweek >= 5 else 0.0

                # -- VARIABLES EXTERNAS Y FERIADOS --
                elif col == "dcoilwtico":
                    valores_fila[col] = 50.0  # Petróleo
                elif col == "onpromotion":
                    valores_fila[col] = 0.0
                elif "holiday" in col:
                    valores_fila[col] = 0.0

                # -- LAGS Y MÉTRICAS DE NEGOCIO --
                elif "lag" in col or "rolling_mean" in col:
                    valores_fila[col] = float(promedio_ventas_recientes)

                # -- SALVAVIDAS --
                else:
                    valores_fila[col] = 0.0

            filas_para_predecir.append(valores_fila)

        # Convertimos todo a un DataFrame respetando el orden estricto de las columnas
        datos_entrada = pd.DataFrame(filas_para_predecir)[columnas_modelo]

        # Ejecución del predict para todos los días a la vez (Mucho más rápido)
        try:
            predicciones = modelo_ia.predict(datos_entrada)
            # Sumamos las predicciones evitando números negativos
            prediccion_ventas_total = sum(
                max(0.0, float(valor)) for valor in predicciones
            )

        except Exception as e_predict:
            raise ValueError(
                f"Fallo en .predict(): {e_predict}. Asegúrate de instalar xgboost/lightgbm."
            )

        # 4. LÓGICA DE NEGOCIO
        balance_real = stock_actual - prediccion_ventas_total
        reposicion = max(0, round(prediccion_ventas_total - stock_actual))

        if balance_real > 0:
            alerta = f"SOBREINVENTARIO DETECTADO: Tienes un exceso de {round(balance_real, 2)} unidades."
        elif balance_real < 0:
            alerta = (
                f"DÉFICIT CRÍTICO: Te faltan {round(abs(balance_real), 2)} unidades."
            )
        else:
            alerta = "BALANCE PERFECTO: Tu inventario actual cubre con precisión la demanda estimada."

        return {
            "ventas_estimadas": round(prediccion_ventas_total, 2),
            "reposicion_sugerida": reposicion,
            "alerta_inventario": alerta,
            "stock_actual_db": stock_actual,
            "balance_real": round(balance_real, 2),
            "historico": df_hist.head(7).to_dict(orient="records"),
        }

    except Exception as e_interna:
        raise HTTPException(
            status_code=500, detail=f"Fallo en el Backend: {str(e_interna)}"
        )
