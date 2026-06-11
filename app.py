import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Conexión a PostgreSQL usando la variable de entorno de Render
def get_db_connection():
    connection = psycopg2.connect(os.environ.get('DATABASE_URL'))
    return connection

# Inicialización de la base de datos (Crea la tabla si no existe)
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

# Ejecutar la creación de tablas al iniciar
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registro', College_methods=['GET', 'POST'])
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO usuarios (nombre, email) VALUES (%s, %s)', (nombre, email))
            conn.commit()
        except psycopg2.IntegrityError:
            conn.rollback()
            return "El correo ya está registrado.", 400
        finally:
            cur.close()
            conn.close()
            
        return redirect(url_for('usuarios'))
        
    return render_template('registro.html')

@app.route('/usuarios')
def usuarios():
    conn = get_db_connection()
    # RealDictCursor permite retornar los registros como diccionarios
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT id, nombre, email FROM usuarios;')
    lista_usuarios = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('usuarios.html', usuarios=lista_usuarios)

if __name__ == '__main__':
    app.run(debug=False)