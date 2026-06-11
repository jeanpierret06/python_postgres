import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Modifica únicamente esta función en tu app.py
def get_db_connection():
    url = os.environ.get('DATABASE_URL')
    # Forzar el parámetro sslmode si no está presente en la URL de Render
    if url and "sslmode=" not in url:
        if "?" in url:
            url += "&sslmode=require"
        else:
            url += "?sslmode=require"
    
    connection = psycopg2.connect(url)
    return connection

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Definición basada exactamente en los nombres de columna de image_4921a1.png
    cur.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            documento VARCHAR(50) NOT NULL,
            nombre VARCHAR(100) NOT NULL,
            correo VARCHAR(100) UNIQUE NOT NULL,
            programa VARCHAR(150) NOT NULL,
            ficha VARCHAR(50) NOT NULL,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        # Extracción de los nuevos campos desde el formulario HTML
        documento = request.form['documento']
        nombre = request.form['nombre']
        correo = request.form['correo']
        programa = request.form['programa']
        ficha = request.form['ficha']
        
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Inserción parametrizada que respeta el orden de la tabla
            cur.execute('''
                INSERT INTO usuarios (documento, nombre, correo, programa, ficha) 
                VALUES (%s, %s, %s, %s, %s)
            ''', (documento, nombre, correo, programa, ficha))
            conn.commit()
        except psycopg2.IntegrityError:
            conn.rollback()
            return "El correo electrónico ya está registrado en el sistema.", 400
        finally:
            cur.close()
            conn.close()
            
        return redirect(url_for('usuarios'))
        
    return render_template('registro.html')

@app.route('/usuarios')
def usuarios():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    # Consulta explícita de todos los campos mapeados
    cur.execute('SELECT id, documento, nombre, correo, programa, ficha, fecha_registro FROM usuarios;')
    lista_usuarios = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('usuarios.html', usuarios=lista_usuarios)

if __name__ == '__main__':
    app.run(debug=False)