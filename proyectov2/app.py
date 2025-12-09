from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from routes.routes import rutas          # blueprint principal
from  proyectov2.models.db_mdl import db, valida_usuario,DATABASE_USER,DATABASE_PASSWD ,DATABASE_HOST,DATABASE_NAME,Usuario
import secrets

def create_app():
    app = Flask(__name__, template_folder='templates')

    # Clave de sesión
    app.secret_key = secrets.token_hex(24)

    # Configuración DB
    app.config["SQLALCHEMY_DATABASE_URI"] = (f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWD}@{DATABASE_HOST}/{DATABASE_NAME}")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializar DB
    db.init_app(app)

    # Registrar Blueprints
    app.register_blueprint(rutas, url_prefix="/api")

    # Crear tablas
    with app.app_context():
        db.create_all()

    return app


app = create_app()


# ----------------------------------------------------
# Páginas principales
# ----------------------------------------------------

@app.route('/')
def index():
    """Redirige al login si no hay sesión."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

# ----------------------------------------------------
# Validación API usuario
# ----------------------------------------------------



@app.route('/login', methods=["GET","POST"])
def login():
    """Maneja el login del usuario."""

    # GET → mostrar formulario
    if request.method == 'GET':
        return render_template('login.html')

    # POST → procesar login
    username = request.form.get('username')
    password = request.form.get('password')

    # Validación básica
    if not username or not password:
        return render_template('login.html', message='Por favor ingrese usuario y contraseña.')

    user = valida_usuario(username, password)

    # ---- ADMIN LOGIN ----
    if username == "admin" and password == "admin123":
        session['user_id'] = user.id
        session['role'] = 'admin'
        session['token'] = user.api_key
        return redirect(url_for('dashboard'))


    # ---- LOGIN USUARIO BD ----
    if user:
        session['user_id'] = user.id
        session['role'] = 'user'
        session['token'] = user.api_key
        return redirect(url_for('dashboard'))

    # ---- FALLA ----
    return render_template('login.html', message='Credenciales incorrectas.')


@app.route('/logout')
def logout():
    """Cierra sesión."""
    session.pop('user_id', None)
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    # POST
    nombre = request.form.get('nombre')
    apellido = request.form.get('apellido')
    username = request.form.get('username')   # <-- igual que en HTML
    clave = request.form.get('password')

    # Validación
    if not nombre or not apellido or not username or not clave:
        return render_template('register.html',
                               message="Por favor complete todos los campos.")

    # Verificar si existe
    existente = Usuario.query.filter_by(usuario=username).first()
    if existente:
        return render_template('register.html',
                               message="El usuario ya existe.")

    # Crear usuario nuevo
    nuevo = Usuario(
        nombre=nombre,
        apellido=apellido,
        usuario=username,
        clave=clave,
        api_key=None   # token vacío por ahora
    )

    db.session.add(nuevo)
    db.session.commit()

    return render_template('register.html',
                           message="Usuario creado con éxito. Ahora puede iniciar sesión.")

@app.route('/dashboard')
def dashboard():
    """Vista principal tras login."""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    token = session.get('token')  # ← recuperar token

    return render_template('dashboard.html', token=token)



# ----------------------------------------------------
# Run
# ----------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
