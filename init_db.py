import sqlite3


def inicializar_db():
    conn = sqlite3.connect("sistema_retail.db")
    cursor = conn.cursor()

    # 1. Crear tablas si no existen
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            usuario TEXT PRIMARY KEY,
            contrasena TEXT
        )
    """)

    # 2. Insertar usuarios de prueba (con manejo de errores por si ya existen)
    usuarios_prueba = [("admin", "12345"), ("analista_retail", "retail2026")]

    for user, pwd in usuarios_prueba:
        try:
            cursor.execute(
                "INSERT INTO usuarios (usuario, contrasena) VALUES (?, ?)", (user, pwd)
            )
        except sqlite3.IntegrityError:
            print(f"El usuario '{user}' ya existe, saltando...")

    conn.commit()
    conn.close()
    print("? Base de datos inicializada correctamente con usuarios de prueba.")


if __name__ == "__main__":
    inicializar_db()
