import mysql.connector

def test_conexion():
    config = {
        'host': '172.17.0.1', # IP por defecto de la red de Docker en Debian
        'user': 'root',
        'password': 'oncogyn_ML5',
        'database': 'docma'
    }

    print(f"--- Intentando conectar a {config['host']} ---")
    try:
        conn = mysql.connector.connect(**config)
        if conn.is_connected():
            print("✅ ¡CONEXIÓN EXITOSA, CHOCHERA!")
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION();")
            version = cursor.fetchone()
            print(f"Versión del servidor MySQL: {version[0]}")
            conn.close()
    except Exception as e:
        print("❌ ERROR DE CONEXIÓN:")
        print(f"Detalle: {e}")

if __name__ == "__main__":
    test_conexion()
