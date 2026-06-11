import os
import sys
import traceback
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

def get_db_connection():
    url = os.environ.get('DATABASE_URL')
    if url and "sslmode=" not in url:
        if "?" in url:
            url += "&sslmode=require"
        else:
            url += "?sslmode=require"
    connection = psycopg2.connect(url)
    return connection

def init_db():
    """Garantiza que la tabla 'estudiantes' exista con la estructura correcta"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS estudiantes (
                id SERIAL PRIMARY KEY,
                documento VARCHAR(50) UNIQUE NOT NULL,
                nombre VARCHAR(100) NOT NULL,
                correo VARCHAR(100) UNIQUE NOT NULL,
                programa VARCHAR(100) NOT NULL,
                ficha VARCHAR(50) NOT NULL,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        conn.commit()
        cur.close()
        conn.close()
        print("Base de datos sincronizada con la tabla 'estudiantes'.")
    except Exception as e:
        print(f"Error al inicializar la base de datos: {str(e)}", file=sys.stderr)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        documento = request.form.get('documento', '').strip()
        nombre = request.form.get('nombre', '').strip()
        correo = request.form.get('correo', '').strip()
        programa = request.form.get('programa', '').strip()
        ficha = request.form.get('ficha', '').strip()

        if not documento or not nombre or not correo or not programa or not ficha:
            raise ValueError("Faltan campos obligatorios en el formulario de registro.")

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Corrección de 'programme' a 'programa' para igualar la BD
            cur.execute('''
                INSERT INTO estudiantes (documento, nombre, correo, programa, ficha) 
                VALUES (%s, %s, %s, %s, %s)
            ''', (documento, nombre, correo, programa, ficha))
            
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('usuarios'))
            
        except psycopg2.errors.UniqueViolation as unique_error:
            print(f"Intento de duplicación controlado: {str(unique_error)}", file=sys.stderr)
            return f'''
            <div style="background:#141414; border:1px solid #ffaa00; padding:30px; font-family:sans-serif; color:#fff; text-align:center; margin:50px auto; max-width:500px;">
                <h2 style="color:#ffaa00;">Usuario ya registrado</h2>
                <p>El documento de identidad o correo ingresado ya se encuentra en nuestra base de datos.</p>
                <br>
                <a href="javascript:history.back()" style="color:#fff; text-decoration:none; border:1px solid #fff; padding:10px 20px;">Intentar con otros datos</a>
            </div>
            ''', 400
        
    return render_template('registro.html')

@app.route('/usuarios')
def usuarios():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT id, documento, nombre, correo, programa, ficha, fecha_registro FROM estudiantes ORDER BY id DESC;')
    lista_usuarios = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('usuarios.html', usuarios=lista_usuarios)

@app.errorhandler(Exception)
def handle_exception(e):
    exc_type, exc_value, exc_traceback = sys.exc_info()
    error_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    full_traceback = "".join(error_lines)
    
    print("====== DETECCION DE ERROR CRITICO ======", file=sys.stderr)
    print(full_traceback, file=sys.stderr)
    print("========================================", file=sys.stderr)
    
    html_error = f'''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Depurador Compuedu | Error Detectado</title>
        <style>
            body {{ background-color: #0d0d0d; color: #ff5555; font-family: 'Courier New', monospace; padding: 40px; }}
            .error-box {{ background-color: #141414; border: 1px solid #ff3333; padding: 30px; border-radius: 4px; }}
            h1 {{ font-size: 1.8rem; margin-bottom: 10px; color: #ffffff; border-bottom: 1px solid #333; padding-bottom: 10px; }}
            pre {{ background-color: #050505; padding: 20px; border: 1px solid #222; overflow-x: auto; color: #88ff88; font-size: 0.9rem; }}
        </style>
    </head>
    <body>
        <div class="error-box">
            <h1>Excepción Interna Detectada (Código 500)</h1>
            <h2>Mensaje del Error:</h2>
            <pre>{str(e)}</pre>
            <h2>Traza Completa:</h2>
            <pre>{full_traceback}</pre>
            <a href="javascript:history.back()" style="color:#fff; text-transform:uppercase; text-decoration:none; border:1px solid #fff; padding:5px 10px;">&larr; Volver</a>
        </div>
    </body>
    </html>
    '''
    return html_error, 500

init_db()

if __name__ == '__main__':
    app.run(debug=False)