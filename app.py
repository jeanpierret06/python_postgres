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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        # Extracción estricta de variables enviadas desde el formulario HTML
        documento = request.form.get('documento', '').strip()
        nombre = request.form.get('nombre', '').strip()
        correo = request.form.get('correo', '').strip()
        programa = request.form.get('programa', '').strip()
        ficha = request.form.get('ficha', '').strip()

        # Si falta algún campo obligatorio, lanzamos una excepción clara
        if not documento or not nombre or not correo or not programa or not ficha:
            raise ValueError("Faltan campos obligatorios en el formulario de registro.")

        conn = get_db_connection()
        cur = conn.cursor()
        
        # Inserción parametrizada basada en la estructura real de tu base de datos
        cur.execute('''
            INSERT INTO usuarios (documento, nombre, correo, programa, ficha) 
            VALUES (%s, %s, %s, %s, %s)
        ''', (documento, nombre, correo, programa, ficha))
        
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('usuarios'))
        
    return render_template('registro.html')

@app.route('/usuarios')
def usuarios():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT id, documento, nombre, correo, programa, ficha, fecha_registro FROM usuarios ORDER BY id DESC;')
    lista_usuarios = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('usuarios.html', usuarios=lista_usuarios)


# =========================================================================
# CAPTURADOR GLOBAL DE ERRORES INTERNOS (DEPURADOR PARA PRODUCCIÓN)
# =========================================================================
@app.errorhandler(Exception)
def handle_exception(e):
    """Intercepta cualquier error en tiempo de ejecución y lo muestra detalladamente"""
    # Extrae la traza exacta del error (archivo, línea y módulo afectado)
    exc_type, exc_value, exc_traceback = sys.exc_info()
    error_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    full_traceback = "".join(error_lines)
    
    # Imprime también el error en la sección de logs de Render
    print("====== DETECCION DE ERROR CRITICO ======", file=sys.stderr)
    print(full_traceback, file=sys.stderr)
    print("========================================", file=sys.stderr)
    
    # Renderiza una plantilla de emergencia estructurada con el error técnico
    html_error = f'''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Depurador Compuedu | Error Detectado</title>
        <style>
            body {{ background-color: #0d0d0d; color: #ff5555; font-family: 'Courier New', monospace; padding: 40px; }}
            .error-box {{ background-color: #141414; border: 1px solid #ff3333; padding: 30px; border-radius: 4px; box-shadow: 0 0 20px rgba(255,0,0,0.2); }}
            h1 {{ font-size: 1.8rem; margin-bottom: 10px; color: #ffffff; border-bottom: 1px solid #333; padding-bottom: 10px; }}
            h2 {{ font-size: 1.1rem; color: #ff8888; margin-top: 20px; }}
            pre {{ background-color: #050505; padding: 20px; border: 1px solid #222; overflow-x: auto; color: #88ff88; font-size: 0.9rem; line-height: 1.4; }}
            .btn-back {{ display: inline-block; margin-top: 20px; color: #ffffff; text-decoration: none; border: 1px solid #fff; padding: 10px 20px; font-family: sans-serif; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; }}
            .btn-back:hover {{ background-color: #ffffff; color: #000000; }}
        </style>
    </head>
    <body>
        <div class="error-box">
            <h1>Excepción Interna Detectada (Código 500)</h1>
            <p>El servidor encontró un error al procesar la solicitud. A continuación se presentan los detalles técnicos:</p>
            
            <h2>Mensaje del Error:</h2>
            <pre>{str(e)}</pre>
            
            <h2>Traza Completa del Error (Stacktrace):</h2>
            <pre>{full_traceback}</pre>
            
            <a href="javascript:history.back()" class="btn-back">&larr; Volver e Intentar de Nuevo</a>
        </div>
    </body>
    </html>
    '''
    return html_error, 500