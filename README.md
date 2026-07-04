# SQLi Lab (Flask + SQLite)

Pequeña aplicación web vulnerable a **SQL Injection**, pensada para
practicar y entender este tipo de vulnerabilidad en un entorno controlado y aislado.

> **Este proyecto es intencionalmente inseguro.** Nunca lo despliegues en
> internet, en una red compartida, ni con datos reales. Está pensado
> exclusivamente para correr en `localhost` con fines educativos.

## ¿Qué incluye?

- **`/login`** (POST): formulario de login que arma la consulta SQL
  concatenando directamente el usuario y la contraseña ingresados.
- **`/search`** (GET): buscador de usuarios por nombre (`LIKE '%...%'`) que
  también concatena el parámetro `q` sin sanitizar.
- Una base SQLite (`lab.db`) con 3 usuarios de ejemplo, creada
  automáticamente la primera vez que se corre la app.

Ambos endpoints construyen la query SQL usando f-strings en vez de
consultas parametrizadas, lo que permite inyectar SQL arbitrario a través
de los campos de usuario/contraseña o del parámetro de búsqueda.

## Requisitos

- Python 3.9+
- pip

No se necesita instalar SQLite aparte: viene incluido en la librería
estándar de Python (`sqlite3`).

## Instalación

```bash
git clone <url-de-tu-repo>
cd <carpeta-del-repo>
python -m venv venv
source venv/bin/activate    # En Windows: venv\Scripts\activate
pip install flask
```

## Cómo correrlo (entorno aislado)

Este laboratorio está pensado para correr **solo en tu máquina local**,
nunca expuesto a una red. Recomendaciones:

- Ejecutalo en una VM, container, o máquina que no esté conectada a redes
  con otros dispositivos sensibles.
- No cambies `host="127.0.0.1"` en `app.run(...)`. Si lo cambiás a
  `0.0.0.0`, la app queda accesible desde otras máquinas de tu red — evitalo.
- Si querés aislarlo más, podés correrlo dentro de Docker (ver sección
  opcional más abajo) o en una VM sin salida a internet.

Para levantarlo:

```bash
python app.py
```

La primera vez se crea automáticamente `lab.db` con estos usuarios de
prueba:

| usuario | contraseña | rol            |
|---------|-----------|----------------|
| admin   | admin123  | administrator  |
| mauro   | clave123  | student        |
| test    | test123   | guest          |

La app queda disponible en: `http://127.0.0.1:5000`

Para reiniciar el laboratorio desde cero, simplemente borrá `lab.db` y
volvé a correr `python app.py`.

## Cómo probar la inyección

### 1. Login (`/login`)

Con credenciales válidas, el login funciona normal. La vulnerabilidad
aparece cuando se manipula el campo **usuario** (o contraseña) para alterar
la lógica de la consulta SQL.

**Bypass sin conocer la contraseña**, en el campo *Usuario*:

```
admin' --
```

(dejando cualquier valor en Contraseña). La consulta queda comentada
después del `--`, ignorando la verificación de contraseña.

**Bypass con condición siempre verdadera**, en *Usuario* y *Contraseña*:

```
' OR '1'='1
```

Esto hace que la condición `WHERE username = '...' OR '1'='1'` sea
verdadera para cualquier fila, devolviendo el primer usuario de la tabla.

### 2. Búsqueda (`/search?q=...`)

Este endpoint es más flexible para explorar técnicas de inyección porque
sus resultados se muestran directamente en pantalla.

**Ver todos los usuarios** (rompiendo el `LIKE`):

```
http://127.0.0.1:5000/search?q=%' OR '1'='1
```

**UNION-based, para extraer datos de otra tabla** (ejemplo genérico, ajustar
número de columnas según la consulta):

```
http://127.0.0.1:5000/search?q=%' UNION SELECT 1,name,sql FROM sqlite_master--
```

Esto permite listar la estructura de la base (nombres de tablas, columnas,
etc.), un patrón típico de reconocimiento en SQLi.

> Estos payloads sirven para practicar sobre **esta app propia**. La idea
> es entender el mecanismo (por qué funciona, qué parte de la query se
> altera) y después mirar el código fuente para ver exactamente dónde está
> el fallo y cómo se arregla.

## Cómo se arregla (para comparar)

La forma correcta es usar **consultas parametrizadas**, dejando que el
driver de la base de datos se encargue de escapar los valores:

```python
# Vulnerable
query = f"SELECT id, username, role FROM users WHERE username = '{username}' AND password = '{password}'"
cursor.execute(query)

# Correcto
query = "SELECT id, username, role FROM users WHERE username = ? AND password = ?"
cursor.execute(query, (username, password))
```

Podés crear una rama o un segundo archivo (`app_seguro.py`) con esta
versión corregida para comparar el comportamiento antes/después.

## Estructura del proyecto

```
.
├── app.py        # Aplicación Flask (login + búsqueda vulnerables)
├── lab.db        # Se genera automáticamente al primer arranque (no subir a git)
└── README.md
```

## (Opcional) Correr en Docker para mayor aislamiento

Si preferís aislar aún más el laboratorio del resto de tu sistema, un
`Dockerfile` simple sería:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY app.py .
RUN pip install flask
EXPOSE 5000
CMD ["python", "app.py"]
```

Y para correrlo mapeando el puerto solo a localhost:

```bash
docker build -t sqli-lab .
docker run --rm -p 127.0.0.1:5000:5000 sqli-lab
```

## .gitignore sugerido

Para no subir la base de datos generada ni el entorno virtual:

```
lab.db
venv/
__pycache__/
*.pyc
```

## Advertencia final

Usar estas técnicas contra sistemas que no son de tu propiedad, o sin
autorización explícita del dueño, es ilegal en la mayoría de las
jurisdicciones. Este laboratorio existe únicamente para practicar en un
entorno propio y controlado.
