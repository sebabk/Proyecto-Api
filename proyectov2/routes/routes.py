from flask import Blueprint, request, jsonify
from proyectov2.models.db_mdl import db, Producto, Mercado,Usuario

rutas = Blueprint("rutas", __name__)

# ------------------------------------------------------
# GET: Listar productos
# ------------------------------------------------------
@rutas.route("/productos", methods=["GET"])
def listar_productos():
    """Listar productos, con opción de filtrar por id"""
    try:
        idprd = request.args.get("id", type=int)

        # --- Si viene id → devolver solo ese producto ---
        if idprd:
            producto = Producto.query.get(idprd)
            if not producto:
                return jsonify({"error": "Producto no encontrado"}), 404

            return jsonify(producto.to_dict()), 200

        # --- Si NO viene id → devolver todos ---
        productos = Producto.query.all()
        return jsonify([p.to_dict() for p in productos]), 200

    except Exception as e:
        print(f"Error en listar_productos: {e}")
        return jsonify({"error": "Error al listar productos"}), 500
# ------------------------------------------------------
# POST: Crear producto
# ------------------------------------------------------
@rutas.route("/productos", methods=["POST"])
@rutas.route("/productos", methods=["POST"])
def crear_producto():
    data = request.get_json() or {}

    # Obtener token
    token = request.args.get("tkn")
    usuario = Usuario.query.filter_by(api_key=token).first()

    if not usuario:
        return jsonify({"error": "Token inválido"}), 403

    if usuario.usuario != "admin":
        return jsonify({"error": "Acceso denegado: solo el administrador puede crear productos"}), 403

    # Si mandan un solo producto, lo convertimos a lista
    if isinstance(data, dict):
        data = [data]

    if not isinstance(data, list):
        return jsonify({"error": "El formato debe ser un objeto o lista de objetos JSON"}), 400

    creados = []
    errores = []

    required_fields = ["nombre", "idOrigen", "uMedida", "precio"]

    for idx, producto in enumerate(data):
        faltantes = [f for f in required_fields if f not in producto]
        if faltantes:
            errores.append({"item": idx, "faltan": faltantes})
            continue

        # Validar mercado
        mercado = Mercado.query.get(producto["idOrigen"])
        if not mercado:
            errores.append({"item": idx, "error": "El mercado no existe"})
            continue

        try:
            nuevo = Producto(
                nombre=producto["nombre"],
                idOrigen=producto["idOrigen"],
                uMedida=producto["uMedida"],
                precio=producto["precio"]
            )
            db.session.add(nuevo)
            creados.append(nuevo)

        except Exception as e:
            errores.append({"item": idx, "error": str(e)})
            continue

    # Commit final
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error interno al guardar", "detalle": str(e)}), 500

    return jsonify({
        "creados": [p.to_dict() for p in creados],
        "errores": errores
    }), 201

# ------------------------------------------------------
# PUT: Actualizar producto
# ------------------------------------------------------
@rutas.route("/productos/<int:idprd>", methods=["PUT"])
def actualizar_producto(idprd):
    data = request.get_json() or {}
    check_usr(Usuario)
    try:
        prod = Producto.query.filter_by(id=idprd).first()

        if not prod:
            return jsonify({"error": "Producto no encontrado"}), 404

        # Actualizar atributos si existen en JSON
        if "nombre" in data:
            prod.nombre = data["nombre"]
        if "uMedida" in data:
            prod.uMedida = data["uMedida"]
        if "precio" in data:
            prod.precio = data["precio"]

        if "idOrigen" in data:
            mercado = Mercado.query.filter_by(id=data["idOrigen"]).first()
            if not mercado:
                return jsonify({"error": "El mercado asignado no existe"}), 404
            prod.idOrigen = data["idOrigen"]

        db.session.commit()
        db.session.refresh(prod)

        return jsonify({
            "mensaje": "Producto actualizado correctamente",
            "producto": prod.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error en actualizar_producto: {e}")
        return jsonify({"error": "Error al actualizar producto"}), 500


# ------------------------------------------------------
# DELETE: Eliminar producto
# ------------------------------------------------------
@rutas.route("/productos/<int:idprd>", methods=["DELETE"])
def eliminar_producto(idprd):
    admin = Usuario.query.filter_by(usuario= "admin").first()
    if not admin:
        return jsonify({"error": "sin permisos de administracion"}), 403
    try:
        prod = Producto.query.filter_by(id=idprd).first()

        if not prod:
            return jsonify({"error": "Producto no encontrado"}), 404

        db.session.delete(prod)
        db.session.commit()

        return jsonify({"mensaje": "Producto eliminado correctamente"}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error en eliminar_producto: {e}")
        return jsonify({"error": "Error al eliminar producto"}), 500
