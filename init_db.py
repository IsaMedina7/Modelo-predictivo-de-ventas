import sqlite3
import random
from datetime import datetime, timedelta


def inicializar_db():
    conn = sqlite3.connect("sistema_retail.db")
    cursor = conn.cursor()

    # 1. Crear Tablas
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, contrasena TEXT);
        CREATE TABLE IF NOT EXISTS inventario (
            store_nbr INTEGER, 
            family TEXT, 
            stock INTEGER, 
            PRIMARY KEY (store_nbr, family)
        );
        CREATE TABLE IF NOT EXISTS ventas_historicas (
            date TEXT, 
            store_nbr INTEGER, 
            family TEXT, 
            sales REAL
        );
    """)

    # 2. Sembrar Usuarios
    cursor.execute("INSERT OR IGNORE INTO usuarios VALUES (?, ?)", ("admin", "12345"))

    # 3. Sembrar Inventario (Stock inicial para 5 tiendas y 3 familias de productos)
    tiendas = [1, 2, 3, 4, 5]
    familias = ["GROCERY I", "BEVERAGES", "CLEANING"]
    for s in tiendas:
        for f in familias:
            stock = random.randint(50, 500)
            cursor.execute(
                "INSERT OR REPLACE INTO inventario VALUES (?, ?, ?)", (s, f, stock)
            )

    # 4. Sembrar Historico (ultimos 30 dias para que los Lags no fallen)
    for s in tiendas:
        for f in familias:
            for i in range(30):
                fecha = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                ventas = random.uniform(10.0, 100.0)
                cursor.execute(
                    "INSERT INTO ventas_historicas VALUES (?, ?, ?, ?)",
                    (fecha, s, f, ventas),
                )

    conn.commit()
    conn.close()
    print("? Base de datos poblada con exito: Usuarios, Inventario y Ventas.")


if __name__ == "__main__":
    inicializar_db()
