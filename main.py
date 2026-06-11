from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import joblib

import sqlite3
import os
from datetime import timedelta
import numpy as np

app = FastAPI(title="Core de Retail con DB Real")

# 1. DEFINICIÓN ESTRICTA DE VARIABLES GLOBALES DE CONTROL
modelo_ia = None

print("⏳ Cargando el PIPELINE REAL de Scikit-Learn con Joblib...")

try:
    if os.path.exists("modelo_demanda.pkl"):

        modelo_ia = joblib.load("modelo_demanda.pkl")
        print("✅ ¡Pipeline REAL de Scikit-Learn cargado con éxito!")
    else:
        print("❌ ERROR DE INICIO: El archivo 'modelo_demanda.pkl' no existe.")

except Exception as e:
    print(f"❌ ERROR CRÍTICO AL CARGAR EL ARCHIVO PKL: {e}")


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
# ENDPOINTS DE AUTENTICACIÓN
# ==========================================
@app.post("/api/auth/register")
def registrar_usuario(datos: RegistroUsuario):
    conn = conectar_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (usuario, contrasena) VALUES (?, ?)", (datos.usuario, datos.contrasena))
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
    cursor.execute("SELECT * FROM usuarios WHERE usuario = ? AND contrasena = ?", (datos.usuario, datos.contrasena))
    usuario_encontrado = cursor.fetchone()
    conn.close()
    
    if not usuario_encontrado:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos.")
    return {"status": "success", "usuario": datos.usuario}

# ==========================================
# ENDPOINTS DEL CRUD DE INVENTARIO
# ==========================================
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

    cursor.execute("""
        INSERT INTO inventario (store_nbr, family, stock) 
        VALUES (?, ?, ?)
        ON CONFLICT(store_nbr, family) 
        DO UPDATE SET stock = stock + excluded.stock
    """, (item.store_nbr, item.family, item.cantidad))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.post("/api/inventory/sell")

def vender_inventario(item: ItemInventario):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT stock FROM inventario WHERE store_nbr = ? AND family = ?", (item.store_nbr, item.family))
    resultado = cursor.fetchone()
    
    if not resultado or resultado['stock'] < item.cantidad:
        conn.close()
        raise HTTPException(status_code=400, detail="Stock insuficiente para la venta.")
        
    cursor.execute("UPDATE inventario SET stock = stock - ? WHERE store_nbr = ? AND family = ?", (item.cantidad, item.store_nbr, item.family))
    conn.commit()
    conn.close()
    return {"status": "success"}

# ==========================================
# ENDPOINT DE HISTÓRICO Y PREDICCIÓN REAL
# ==========================================
@app.post("/api/predict/demand")
def predecir_demanda(consulta: ConsultaDemanda):
    if modelo_ia is None:
        raise HTTPException(status_code=500, detail="Fallo en el Backend: Pipeline no cargado.")

    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        # 1. Traer ventas históricas
        df_hist = pd.read_sql_query("""
            SELECT date, sales FROM ventas_historicas 
            WHERE store_nbr = ? AND family = ? 
            ORDER BY date DESC LIMIT 7
        """, conn, params=(consulta.store_nbr, consulta.family))
        
        # 2. Traer el stock
        cursor.execute("SELECT stock FROM inventario WHERE store_nbr = ? AND family = ?", (consulta.store_nbr, consulta.family))
        res_stock = cursor.fetchone()
        stock_actual = res_stock['stock'] if res_stock else 0
        conn.close()


        # 3. Preparar variables
        fecha_inicial = pd.to_datetime(consulta.fecha_inicio)
        prediccion_ventas_total = 0.0

        # Inspección de columnas
        columnas_modelo = None
        if hasattr(modelo_ia, "feature_names_in_"):

            columnas_modelo = list(modelo_ia.feature_names_in_)
        elif hasattr(modelo_ia, "feature_names"):
            columnas_modelo = list(modelo_ia.feature_names)

        for i in range(consulta.dias_prediccion):
            fecha_actual = fecha_inicial + timedelta(days=i)

            if columnas_modelo is not None:
                valores_fila = {}
                for col in columnas_modelo:
                    col_lower = col.lower()
                    
                    # --- CATEGÓRICAS (Obligatorio TEXTO) ---
                    if col_lower in ['family', 'familia']:

                        valores_fila[col] = str(consulta.family.upper())
                    elif col_lower in ['city', 'ciudad']:
                        valores_fila[col] = "Quito"

                    elif col_lower in ['state', 'estado']:
                        valores_fila[col] = "Pichincha"
                    elif col_lower in ['store_type', 'type', 'tipo']:
                        valores_fila[col] = "A"

                        
                    # --- NUMÉRICAS Y TEMPORALES (Obligatorio FLOTANTE) ---

                    elif 'store' in col_lower:
                        valores_fila[col] = float(consulta.store_nbr)
                    elif 'month' in col_lower or col_lower == 'mes':
                        valores_fila[col] = float(fecha_actual.month)
                    elif 'dayofweek' in col_lower or 'dia_semana' in col_lower:
                        valores_fila[col] = float(fecha_actual.dayofweek)
                    elif 'day' in col_lower and 'week' not in col_lower and 'year' not in col_lower:
                        valores_fila[col] = float(fecha_actual.day)
                    elif 'year' in col_lower or 'anio' in col_lower or 'año' in col_lower:
                        valores_fila[col] = float(fecha_actual.year)
                    elif 'dcoilwtico' in col_lower or 'oil' in col_lower:
                        valores_fila[col] = 50.0  # Precio seguro del crudo
                    else:
                        valores_fila[col] = 0.0   # Ceros para feriados y clusters

                
                datos_entrada = pd.DataFrame([valores_fila])
                
            else:
                # Respaldo de seguridad plano
                datos_entrada = pd.DataFrame([{
                    'store_nbr': float(consulta.store_nbr), 
                    'family': str(consulta.family.upper()), 
                    'mes': float(fecha_actual.month), 
                    'dia_semana': float(fecha_actual.dayofweek)
                }])

            # Ejecución matemática del predict real
            try:
                prediccion_dia = modelo_ia.predict(datos_entrada)
                # Extraemos limpiamente el número de la matriz numpy
                if isinstance(prediccion_dia, np.ndarray):
                    valor = float(prediccion_dia[0])
                else:
                    valor = float(prediccion_dia)
                    
                prediccion_ventas_total += max(0.0, valor) # Evitar predicciones negativas
                
            except Exception as e_predict:

                raise ValueError(f"Fallo en .predict(): {e_predict}. Datos intentados: {valores_fila}")

        # 4. LÓGICA DE NEGOCIO
        balance_real = stock_actual - prediccion_ventas_total

        reposicion = max(0, round(prediccion_ventas_total - stock_actual))
        
        if balance_real > 0:
            alerta = f"SOBREINVENTARIO DETECTADO: Tienes un exceso de {round(balance_real, 2)} unidades."
        elif balance_real < 0:
            alerta = f"DÉFICIT CRÍTICO: Te faltan {round(abs(balance_real), 2)} unidades."
        else:
            alerta = "BALANCE PERFECTO: Tu inventario actual cubre con precisión la demanda estimada."

        return {

            "ventas_estimadas": round(prediccion_ventas_total, 2),
            "reposicion_sugerida": reposicion,
            "alerta_inventario": alerta,
            "stock_actual_db": stock_actual,
            "balance_real": round(balance_real, 2),
            "historico": df_hist.to_dict(orient="records")
        }

    except Exception as e_interna:
        raise HTTPException(status_code=500, detail=f"Fallo en el Backend: {str(e_interna)}")
