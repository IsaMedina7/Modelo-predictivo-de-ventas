import sqlite3
import random
from datetime import datetime, timedelta
import os


def inicializar_db():
    db_name = "sistema_retail.db"

    # 1. ELIMINAR LA BASE DE DATOS ANTERIOR (Limpieza total)
    if os.path.exists(db_name):
        os.remove(db_name)
        print(f"🗑️ Base de datos anterior '{db_name}' eliminada.")

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # 2. CREAR TABLAS DESDE CERO
    cursor.executescript("""
        CREATE TABLE usuarios (usuario TEXT PRIMARY KEY, contrasena TEXT);
        CREATE TABLE inventario (
            store_nbr INTEGER, 
            family TEXT, 
            stock INTEGER, 
            PRIMARY KEY (store_nbr, family)
        );
        CREATE TABLE ventas_historicas (
            date TEXT, 
            store_nbr INTEGER, 
            family TEXT, 
            sales REAL
        );
    """)

    # 3. SEMBRAR USUARIOS
    cursor.execute("INSERT INTO usuarios VALUES (?, ?)", ("admin", "12345"))
    cursor.execute("INSERT INTO usuarios VALUES (?, ?)", ("analista", "retail2026"))

    # 4. LAS 33 FAMILIAS REALES DEL DATASET DE KAGGLE
    familias_reales = [
        "AUTOMOTIVE",
        "BABY CARE",
        "BEAUTY",
        "BEVERAGES",
        "BOOKS",
        "BREAD/BAKERY",
        "CELEBRATION",
        "CLEANING",
        "DAIRY",
        "DELI",
        "EGGS",
        "FROZEN FOODS",
        "GROCERY I",
        "GROCERY II",
        "HARDWARE",
        "HOME AND KITCHEN I",
        "HOME AND KITCHEN II",
        "HOME APPLIANCES",
        "HOME CARE",
        "LADIESWEAR",
        "LAWN AND GARDEN",
        "LINGERIE",
        "LIQUOR,WINE,BEER",
        "MAGAZINES",
        "MEATS",
        "PERSONAL CARE",
        "PET SUPPLIES",
        "PLAYERS AND ELECTRONICS",
        "POULTRY",
        "PREPARED FOODS",
        "PRODUCE",
        "SCHOOL AND OFFICE SUPPLIES",
        "SEAFOOD",
    ]

    # Tiendas (Usaremos las primeras 5 tiendas para la demo)
    tiendas = [1, 2, 3, 4, 5]

    print(
        "⏳ Generando inventario y ventas históricas reales (tomará unos segundos)..."
    )

    # 5. SEMBRAR INVENTARIO
    for s in tiendas:
        for f in familias_reales:
            # Stock aleatorio realista
            stock = random.randint(20, 1500)
            cursor.execute("INSERT INTO inventario VALUES (?, ?, ?)", (s, f, stock))

    # 6. SEMBRAR HISTÓRICO (30 Días hacia atrás)
    hoy = datetime.now()
    for s in tiendas:
        for f in familias_reales:
            for i in range(30):
                fecha = (hoy - timedelta(days=i)).strftime("%Y-%m-%d")

                # Lógica realista: Productos de primera necesidad venden más
                if f in ["GROCERY I", "BEVERAGES", "PRODUCE", "CLEANING", "DAIRY"]:
                    ventas = random.uniform(150.0, 1200.0)
                else:
                    ventas = random.uniform(5.0, 100.0)

                cursor.execute(
                    "INSERT INTO ventas_historicas VALUES (?, ?, ?, ?)",
                    (fecha, s, f, ventas),
                )

    conn.commit()
    conn.close()
    print("✅ Base de datos recreada con éxito con las 33 FAMILIAS REALES de Kaggle.")


if __name__ == "__main__":
    inicializar_db()
