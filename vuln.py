from flask import Flask, request, render_template_string
import sqlite3
import os

app = Flask(__name__)
DB_NAME = "lab.db"

HTML_HOME = """
<!doctype html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <title>SQLi Lab</title>
</head>
<body>
    <h1>Laboratorio SQLi</h1>

    <h2>Login vulnerable</h2>
    <form method="POST" action="/login">
        <label>Usuario:</label><br>
        <input type="text" name="username"><br><br>

        <label>Contraseña:</label><br>
        <input type="text" name="password"><br><br>

        <button type="submit">Iniciar sesión</button>
    </form>

    <hr>

    <h2>Búsqueda vulnerable</h2>
    <form method="GET" action="/search">
        <label>Buscar usuario por nombre:</label><br>
        <input type="text" name="q"><br><br>
        <button type="submit">Buscar</button>
    </form>
</body>
</html>
"""

HTML_RESULT = """
<!doctype html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <title>Resultado</title>
</head>
<body>
    <h1>Resultado</h1>
    <pre>{{ content }}</pre>
    <a href="/">Volver</a>
</body>
</html>
"""

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    return conn

def init_db():
    if os.path.exists(DB_NAME):
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    users = [
        ("admin", "admin123", "administrator"),
        ("mauro", "clave123", "student"),
        ("test", "test123", "guest")
    ]

    cursor.executemany(
        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
        users
    )

    conn.commit()
    conn.close()

@app.route("/")
def home():
    return render_template_string(HTML_HOME)

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    conn = get_connection()
    cursor = conn.cursor()

    query = f"SELECT id, username, role FROM users WHERE username = '{username}' AND password = '{password}'"
    print(f"[DEBUG] Ejecutando query: {query}")

    try:
        cursor.execute(query)
        user = cursor.fetchone()
    except Exception as e:
        conn.close()
        return render_template_string(HTML_RESULT, content=f"Error SQL: {e}")

    conn.close()

    if user:
        return render_template_string(
            HTML_RESULT,
            content=f"Login exitoso\\nID: {user[0]}\\nUsuario: {user[1]}\\nRol: {user[2]}"
        )
    else:
        return render_template_string(HTML_RESULT, content="Credenciales inválidas")

@app.route("/search", methods=["GET"])
def search():
    q = request.args.get("q", "")

    conn = get_connection()
    cursor = conn.cursor()

    # VULNERABILIDAD
    query = f"SELECT id, username, role FROM users WHERE username LIKE '%{q}%'"
    print(f"[DEBUG] Ejecutando query: {query}")

    try:
        cursor.execute(query)
        rows = cursor.fetchall()
    except Exception as e:
        conn.close()
        return render_template_string(HTML_RESULT, content=f"Error SQL: {e}")

    conn.close()

    if not rows:
        return render_template_string(HTML_RESULT, content="Sin resultados")

    output = []
    for row in rows:
        output.append(f"ID: {row[0]} | Usuario: {row[1]} | Rol: {row[2]}")

    return render_template_string(HTML_RESULT, content="\\n".join(output))

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
