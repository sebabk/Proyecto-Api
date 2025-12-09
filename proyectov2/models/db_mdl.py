import uuid
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from urllib.parse import quote


# ----------------------------------------------------
# Configuración DB (MySQL)
# ----------------------------------------------------

DATABASE_USER = "dbflaskinacap"
DATABASE_PASSWD = quote("1N@C@P_alumn05")
DATABASE_HOST = "mysql.flask.nogsus.org"
DATABASE_NAME = "api_alumnos"

ADMIN_USERNAME="admin"
ADMIN_PASSWORD= "admin123"

# Flask-SQLAlchemy
db = SQLAlchemy()

def get_db():
    return db

# ----------------------------------------------------
# MODELOS
# ----------------------------------------------------

class Usuario(db.Model):
    __tablename__ = 'saah_usuario'

    id = db.Column(Integer, primary_key=True)
    nombre = db.Column(Text)                 # Text NO lleva length
    apellido = db.Column(String(150))
    usuario = db.Column(String(50), unique=True)
    clave = db.Column(String(50))
    api_key = db.Column(String(250))

    def to_dict(self):
        return {
            "id": self.id, "nombre": self.nombre, "apellido": self.apellido,
            "usuario": self.usuario, "clave": self.clave, "api_key": self.api_key
        }


class Mercado(db.Model):
    __tablename__ = 'saah_mercados'

    id = db.Column(Integer, primary_key=True)
    nombre = db.Column(String(150), unique=True)

    productos = relationship("Producto", back_populates="origen_mercado", cascade="all, delete-orphan")

    def to_dict(self):
        return {"id": self.id, "nombre": self.nombre}


class Producto(db.Model):
    __tablename__ = 'saah_productos'

    id = db.Column(Integer, primary_key=True)
    idOrigen = db.Column(Integer, ForeignKey('saah_mercados.id'), nullable=False)
    nombre = db.Column(String(150))
    uMedida = db.Column(String(100))
    precio = db.Column(Integer)

    origen_mercado = relationship("Mercado", back_populates="productos")

    def to_dict(self):
        return {
            "id": self.id,
            "idOrigen": self.idOrigen,
            "nombre": self.nombre,
            "uMedida": self.uMedida,
            "precio": self.precio,
            "origen_mercado": self.origen_mercado.nombre if self.origen_mercado else None
        }


# ----------------------------------------------------
# INICIALIZACIÓN
# ----------------------------------------------------

def init_db(app):
    """
    Inicializa SQLAlchemy, crea tablas y carga datos iniciales.
    """
    app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWD}@{DATABASE_HOST}/{DATABASE_NAME}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

        # Usuario por defecto
        if Usuario.query.count() == 0:
            u = Usuario(
                nombre="Admin",
                apellido="User",
                usuario="admin",
                clave="admin123",
                api_key="TEST-API-KEY-12345"
            )
            db.session.add(u)

        # Mercados iniciales
        if Mercado.query.count() == 0:
            m1 = Mercado(nombre='Puerto Montt')
            m2 = Mercado(nombre='Osorno')
            m3 = Mercado(nombre='Temuco')
            db.session.add_all([m1, m2, m3])
            db.session.flush()

            p1 = Producto(idOrigen=m1.id, nombre='Tomate', uMedida='kg', precio=1200)
            p2 = Producto(idOrigen=m1.id, nombre='Lechuga', uMedida='unidad', precio=500)
            p3 = Producto(idOrigen=m2.id, nombre='Papa', uMedida='kg', precio=800)

            db.session.add_all([p1, p2, p3])

        db.session.commit()


# ----------------------------------------------------
# Función de validar usuario
# ----------------------------------------------------

def valida_usuario(usrname, passwd):
    try:
        user = Usuario.query.filter_by(usuario=usrname, clave=passwd).first()

        if user:
            user.api_key = uuid.uuid4().hex
            db.session.commit()
            return user  # devolver OBJETO Usuario

        return None  # no existe

    except Exception as e:
        print(f"Error en valida_usuario: {e}")
        return None