# 🛒 Modelo Predictivo de Ventas para Decisiones de Inventario en Supermercados

Bienvenido al repositorio oficial del proyecto desarrollado para **pequeñas y medianas empresas**. Esta aplicación es una solución basada en Machine Learning diseñada para optimizar la toma de decisiones en la gestión de inventario, reduciendo el desabastecimiento y las pérdidas económicas.

**Equipo de Desarrollo (Integrantes):**
* Maria Isabel Aristizabal Medina
* Cristian David Dorado Gomez
* Phillip Santiago Adarmes

---

## 🎯 Idea Central
El objetivo principal y la razón de ser de este proyecto es:
> **"Desarrollar un sistema de analítica predictiva capaz de estimar la demanda futura de productos utilizando datos históricos y variables contextuales."**

## 📊 Sobre los Datos (El Motor del Modelo)

Para entrenar este modelo, utilizamos la base de datos **"Store Sales - Time Series Forecasting"** (Kaggle), que contiene el histórico de ventas de la cadena de supermercados Corporación Favorita en Ecuador. 

El modelo no solo analiza el histórico de ventas, sino que integra variables contextuales críticas como:
* Ubicación y tipo de tienda.
* Comportamiento de los clientes (transacciones).
* Días festivos y fechas especiales.

* Factores económicos externos.

## ⚖️ Alineación con los Objetivos Estratégicos (Valor de Negocio)
Esta herramienta ataca directamente los dos grandes riesgos financieros y operativos de la mala planificación de la demanda en supermercados:

### 📉 Prevención cuando la "Demanda es Menor a la Esperada"
Al advertirnos que un producto tendrá baja rotación, el sistema previene:

* **Acumulación de inventario** innecesario en bodegas.
* **Mayores costos de almacenamiento** y logística operativa.
* **Desperdicio de productos perecederos** que superan su vida útil en los estantes.
* **Inmovilización de capital**, asegurando que los recursos financieros fluyan.

### 📈 Prevención cuando la "Demanda Supera lo Esperado"
Al anticipar los picos de ventas y tendencias, el sistema permite estar preparados, mitigando:
* **Desabastecimiento** en los puntos de venta.
* **Pérdida de ventas** e ingresos directos.
* **Insatisfacción del cliente**, manteniendo la fidelidad hacia el supermercado.


---


## ⚙️ Arquitectura de la Aplicación
La solución consta de un ecosistema en la nube accesible para cualquier usuario sin conocimientos de programación:
1. **El Cerebro (Backend con FastAPI):** Descarga automáticamente nuestro modelo de predicción (`.pkl`) y procesa las variables de entrada usando `scikit-learn` para calcular estimaciones en milisegundos.
2. **La Interfaz (Frontend con Streamlit):** Proporciona un panel de control intuitivo y visual para interactuar con los datos.
3. **Despliegue en la Nube (Render):** Todo el sistema está alojado en la nube para garantizar disponibilidad 24/7.

## 🌐 Acceso a la Aplicación

El sistema ya se encuentra completamente funcional. Puedes acceder a la plataforma interactiva haciendo clic en el siguiente enlace:


👉 **https://app-predictive.onrender.com**
