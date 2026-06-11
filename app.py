import streamlit as st
import requests
import pandas as pd
import time

from datetime import datetime, timedelta

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Sistema Retail Inteligente", page_icon="🏢", layout="wide")

URL_API = "http://127.0.0.1:8000/api"


# Inicializar memoria de sesión para el usuario
if 'usuario_actual' not in st.session_state:
    st.session_state['usuario_actual'] = None

# --- BARRA LATERAL ---
st.sidebar.title("🏢 Menú Principal")

if st.session_state['usuario_actual'] is None:
    menu = ["Login / Registro"]

else:
    st.sidebar.write(f"👤 Usuario: **{st.session_state['usuario_actual']}**")
    menu = ["Gestión de Inventario", "Dashboard de Predicción", "Cerrar Sesión"]

seleccion = st.sidebar.radio("Ir a:", menu)

# ==========================================
# PANTALLA 1: LOGIN Y REGISTRO
# ==========================================
if seleccion == "Login / Registro":
    st.title("🔐 Acceso al Sistema")
    
    tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse como Usuario Nuevo"])
    
    with tab1:
        u_login = st.text_input("Usuario", key="u_log")
        c_login = st.text_input("Contraseña", type="password", key="c_log")
        if st.button("Ingresar Sistema", type="primary"):
            try:

                res = requests.post(f"{URL_API}/auth/login", json={"usuario": u_login, "contrasena": c_login})

                if res.status_code == 200:
                    st.session_state['usuario_actual'] = res.json()["usuario"]
                    st.rerun()

                else:
                    st.error("Credenciales inválidas. Revisa o regístrate.")
            except requests.exceptions.ConnectionError:
                st.error("🚨 El motor FastAPI está apagado. Enciéndelo con 'uvicorn main:app --reload'")
                
    with tab2:
        st.subheader("Crear Cuenta Multi-Tienda")
        u_reg = st.text_input("Elige un Nombre de Usuario", key="u_reg")
        c_reg = st.text_input("Elige una Contraseña", type="password", key="c_reg")

        if st.button("Guardar en Base de Datos"):
            if u_reg and c_reg:
                try:
                    res = requests.post(f"{URL_API}/auth/register", json={"usuario": u_reg, "contrasena": c_reg})
                    if res.status_code == 200:
                        st.success("¡Usuario guardado en la base de datos! Ya puedes iniciar sesión en la pestaña de al lado.")
                    else:
                        st.error(res.json().get("detail", "Error al registrar"))
                except requests.exceptions.ConnectionError:
                    st.error("🚨 El motor FastAPI está apagado. Enciéndelo con 'uvicorn main:app --reload'")

# ==========================================
# PANTALLA 2: CRUD DE INVENTARIO
# ==========================================
elif seleccion == "Gestión de Inventario":
    st.title("📦 Inventario Físico")
    
    col_in, col_tb = st.columns([1, 2])


    with col_in:
        t = st.selectbox("Tienda", range(1, 55))

        f = st.selectbox("Familia", ["AUTOMOTIVE", "BEAUTY", "BEVERAGES", "DAIRY", "PRODUCE"])
        cant = st.number_input("Cantidad", min_value=1, value=5)
        

        c1, c2 = st.columns(2)
        if c1.button("📥 Rellenar Stock", use_container_width=True):

            try:
                res = requests.post(f"{URL_API}/inventory/add", json={"store_nbr": t, "family": f, "cantidad": cant})
                if res.status_code == 200:
                    st.success("✅ ¡Guardado en la base de datos con éxito!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(f"El motor rechazó la orden: {res.text}")
            except Exception as e:
                st.error(f"Error interno en Streamlit: {e}")
            
        if c2.button("📤 Vender Stock", use_container_width=True):
            try:
                res = requests.post(f"{URL_API}/inventory/sell", json={"store_nbr": t, "family": f, "cantidad": cant})
                if res.status_code == 200:
                    st.success("✅ ¡Venta descontada del inventario!")

                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(f"El motor rechazó la orden: {res.text}")
            except Exception as e:
                st.error(f"Error interno en Streamlit: {e}")

                
    with col_tb:

        st.subheader("Base de Datos")
        try:
            res_inv = requests.get(f"{URL_API}/inventory")
            if res_inv.status_code == 200 and res_inv.json():
                st.dataframe(pd.DataFrame(res_inv.json()), use_container_width=True, hide_index=True)
            else:
                st.info("No hay productos en inventario aún. Agrega stock a la izquierda.")
        except:

            st.error("Esperando conexión con FastAPI...")


# ==========================================
# PANTALLA 3: DASHBOARD DE PREDICCIÓN DINÁMICO
# ==========================================
elif seleccion == "Dashboard de Predicción":

    st.title("📊 Análisis y Predicciones de Demanda")

    
    col1, col2, col3 = st.columns(3)

    with col1: 
        tienda = st.selectbox("1. Seleccionar Tienda", range(1, 55))
    with col2: 
        familia = st.selectbox("2. Seleccionar Familia", ["AUTOMOTIVE", "BEAUTY", "BEVERAGES", "DAIRY", "PRODUCE"])
    with col3: 

        fecha_default = (datetime.today(), datetime.today() + timedelta(days=14))
        entrada_fecha = st.date_input("3. Rango de Fechas", value=fecha_default)
    
    # --- CÁLCULO INTELIGENTE DE DÍAS ---
    if isinstance(entrada_fecha, tuple) and len(entrada_fecha) == 2:
        fecha_inicio = entrada_fecha[0]
        fecha_fin = entrada_fecha[1]
        dias_pred = (fecha_fin - fecha_inicio).days + 1
    elif isinstance(entrada_fecha, tuple) and len(entrada_fecha) == 1:
        fecha_inicio = entrada_fecha[0]
        dias_pred = 1
    else:
        fecha_inicio = entrada_fecha
        dias_pred = 1
        
    fecha_segura = str(fecha_inicio)
        

    if st.button(f"🔮 Ejecutar Predicción ({dias_pred} Días)", type="primary"):

        try:

            res = requests.post(
                f"{URL_API}/predict/demand", 
                json={"store_nbr": tienda, "family": familia, "fecha_inicio": fecha_segura, "dias_prediccion": dias_pred}
            )

            
            if res.status_code == 200:
                data = res.json()
                stock_actual = data['stock_actual_db']
                demanda = data['ventas_estimadas']
                balance_real = stock_actual - demanda
                
                st.divider()
                
                # --- DISEÑO ORGANIZADO EN PESTAÑAS ---
                tab_resumen, tab_historico = st.tabs(["📋 Resumen Logístico", "📈 Histórico de Ventas"])
                
                with tab_resumen:
                    if balance_real > (demanda * 0.2):
                        st.warning(f"⚠️ **SOBREINVENTARIO DETECTADO:** Tienes {round(balance_real, 2)} unidades extra que probablemente no se venderán en estos {dias_pred} días.")
                    elif balance_real < 0:
                        st.error(f"🚨 **DÉFICIT CRÍTICO:** Te faltan {abs(round(balance_real, 2))} unidades para cubrir la demanda de este periodo.")
                    else:
                        st.success(f"✅ **BALANCE PERFECTO:** Tu inventario es adecuado para los {dias_pred} días seleccionados.")


                    m1, m2, m3 = st.columns(3)
                    m1.metric("📦 Stock en Bodega", f"{stock_actual} unds")
                    m2.metric(f"📈 Demanda Estimada ({dias_pred} Días)", f"{demanda} unds")
                    m3.metric("🛒 Sugerencia de Pedido", f"{data['reposicion_sugerida']} unds")
                
                with tab_historico:
                    st.subheader(f"Últimas ventas registradas para Tienda {tienda} - {familia}")
                    
                    # Extracción segura de la clave 'historico' enviada por FastAPI

                    datos_hist = data.get('historico', [])
                    
                    if datos_hist:
                        df_hist = pd.DataFrame(datos_hist)
                        
                        # Conversión a tipo datetime y ordenamiento cronológico para graficar correctamente
                        df_hist['date'] = pd.to_datetime(df_hist['date'])
                        df_hist = df_hist.sort_values(by='date')

                        
                        col_grafica, col_tabla = st.columns([2, 1])

                        with col_grafica:
                            st.line_chart(data=df_hist, x='date', y='sales', use_container_width=True)
                        with col_tabla:
                            st.dataframe(df_hist, use_container_width=True, hide_index=True)

                    else:
                        # Si las tablas están vacías debido al borrado de datos

                        st.info("ℹ️ No se encontraron registros de ventas pasadas en la tabla 'ventas_historicas' para los parámetros seleccionados.")

            else:
                st.error(f"Error en los datos: {res.json().get('detail', res.text)}")
                
        except requests.exceptions.ConnectionError:
            st.error("🚨 El motor FastAPI no está respondiendo. Asegúrate de tener 'uvicorn main:app --reload' activo.")


# ==========================================
# CERRAR SESIÓN
# ==========================================
elif seleccion == "Cerrar Sesión":
    st.session_state['usuario_actual'] = None

    st.rerun()
