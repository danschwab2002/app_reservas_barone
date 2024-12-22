from flask import Flask, jsonify, request  # Importar Flask y utilidades
from flask_sqlalchemy import SQLAlchemy  # Importar SQLAlchemy para manejo de la base de datos
from datetime import date, time  # Para trabajar con fechas y horarios si es necesario
from sqlalchemy import inspect
from flask import Flask, render_template, request, jsonify
from flask import request
from flask import redirect, url_for, jsonify, render_template
import os



# Crear la aplicación Flask
app = Flask(__name__)

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///reservas.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if not app.config['SQLALCHEMY_DATABASE_URI']:
    raise ValueError("La variable DATABASE_URL no está configurada.")


# Inicializar la base de datos
db = SQLAlchemy(app)

# Modelos de la base de datos
class Zona(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    mesas = db.relationship('Mesa', backref='zona', lazy=True)

class Mesa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    capacidad = db.Column(db.Integer, nullable=False)
    zona_id = db.Column(db.Integer, db.ForeignKey('zona.id'), nullable=False)

class Reserva(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_cliente = db.Column(db.String(100), nullable=False)
    cantidad_personas = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    horario = db.Column(db.Time, nullable=False)
    mesa_id = db.Column(db.Integer, db.ForeignKey('mesa.id'), nullable=False)
    es_evento = db.Column(db.Boolean, default=False)  # Nuevo campo
    
    # Relación con Mesa
    mesa = db.relationship('Mesa', backref='reservas')

@app.before_request
def handle_http_methods():
    if request.form.get('_method') == 'DELETE':
        request.environ['REQUEST_METHOD'] = 'DELETE'

# Ruta Principal
@app.route('/')
def home():
    zonas = Zona.query.all()  # Obtener todas las zonas
    mesas = Mesa.query.all()  # Obtener todas las mesas
    reservas = Reserva.query.all()  # Obtener todas las reservas
    
    return render_template('index.html', zonas=zonas, mesas=mesas, reservas=reservas)



# RUTAS PARA AGREGAR/CREAR

# Ruta para agregar una zona
@app.route('/zonas', methods=['POST'])
def agregar_zona():
    data = request.get_json()  # Obtener datos del cuerpo de la solicitud
    nueva_zona = Zona(nombre=data['nombre'])
    db.session.add(nueva_zona)  # Agregar la nueva zona a la base de datos
    db.session.commit()  # Guardar los cambios
    return jsonify({"mensaje": "Zona creada correctamente", 
                    "zona": {"id": nueva_zona.id, "nombre": nueva_zona.nombre}}), 201

# Ruta para crear mesas
@app.route('/mesas', methods=['POST'])
def agregar_mesa():
    data = request.get_json()  # Ejemplo: {"capacidad": 4, "zona_id": 1}
    nueva_mesa = Mesa(capacidad=data['capacidad'], zona_id=data['zona_id'])
    db.session.add(nueva_mesa)
    db.session.commit()
    return jsonify({"mensaje": "Mesa creada correctamente", 
                    "mesa": {"id": nueva_mesa.id, "capacidad": nueva_mesa.capacidad, "zona_id": nueva_mesa.zona_id}}), 201

# Ruta para crear reservas

@app.route('/reservas', methods=['POST'])
def agregar_reserva():
    try:
        # Detectar si la solicitud proviene de un formulario o JSON
        if request.content_type == 'application/x-www-form-urlencoded':
            data = request.form  # Datos enviados desde un formulario
        elif request.content_type == 'application/json':
            data = request.get_json()  # Datos enviados como JSON
        else:
            return jsonify({"error": "Formato de contenido no soportado"}), 400

        # Depurar los datos recibidos (útil para encontrar problemas)
        print("Datos recibidos:", data)

        # Validar campos obligatorios
        campos_requeridos = ['nombre_cliente', 'cantidad_personas', 'fecha', 'horario', 'mesa_id']
        for campo in campos_requeridos:
            if campo not in data or not data[campo]:
                return jsonify({"error": f"Falta el campo requerido: {campo}"}), 400

        # Crear la nueva reserva
        nueva_reserva = Reserva(
            nombre_cliente=data['nombre_cliente'],
            cantidad_personas=int(data['cantidad_personas']),
            fecha=date.fromisoformat(data['fecha']),  # Manejar formato de fecha
            horario=time.fromisoformat(data['horario']),  # Manejar formato de hora
            mesa_id=int(data['mesa_id']),
            es_evento=(data.get('es_evento', 'off').lower() == 'on' or data.get('es_evento', 'false').lower() == 'true')  # Manejar checkboxes y JSON booleanos
        )
        db.session.add(nueva_reserva)
        db.session.commit()

        # Responder dependiendo del cliente
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            # Respuesta JSON para solicitudes AJAX o API
            return jsonify({
                "mensaje": "Reserva creada correctamente",
                "reserva": {
                    "id": nueva_reserva.id,
                    "nombre_cliente": nueva_reserva.nombre_cliente,
                    "cantidad_personas": nueva_reserva.cantidad_personas,
                    "fecha": nueva_reserva.fecha.isoformat(),
                    "horario": nueva_reserva.horario.isoformat(),
                    "mesa_id": nueva_reserva.mesa_id,
                    "es_evento": nueva_reserva.es_evento
                }
            }), 201
        else:
            # Redirigir al home para solicitudes normales desde formularios
            return redirect(url_for('home'))

    except ValueError as e:
        # Manejar errores en la conversión de datos (fecha, hora, etc.)
        return jsonify({"error": f"Error en los datos: {str(e)}"}), 400
    except Exception as e:
        # Manejar cualquier otro error
        return jsonify({"error": f"Error inesperado: {str(e)}"}), 500




# RUTAS PARA CONSULTAR/CHEQUEAR

# Ruta para chequear tablas
@app.route('/check-tables', methods=['GET'])
def check_tables():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    return jsonify(tables=tables)

# Ruta para listar todas las zonas
@app.route('/zonas', methods=['GET'])
def listar_zonas():
    zonas = Zona.query.all()  # Obtener todas las zonas de la base de datos
    zonas_lista = [{"id": zona.id, "nombre": zona.nombre} for zona in zonas]  # Convertir a JSON
    return jsonify(zonas=zonas_lista), 200

# Ruta para listar todas las mesas con el nombre de la zona asociada
@app.route('/mesas', methods=['GET'])
def listar_mesas_con_zonas():
    mesas = Mesa.query.all()  # Obtener todas las mesas
    resultado = []
    for mesa in mesas:
        zona = Zona.query.get(mesa.zona_id)  # Obtener la zona asociada a la mesa
        resultado.append({
            "id": mesa.id,
            "capacidad": mesa.capacidad,
            "zona_id": mesa.zona_id,
            "zona_nombre": zona.nombre if zona else "Zona no encontrada"
        })
    return jsonify({"mesas": resultado}), 200


# Ruta para listar todas las reservas con el nombre de la zona asociada
@app.route('/reservas', methods=['GET'])
def listar_reservas():
    reservas = Reserva.query.all()  # Obtener todas las reservas
    resultado = []
    for reserva in reservas:
        mesa = Mesa.query.get(reserva.mesa_id)  # Obtener la mesa asociada a la reserva
        zona = Zona.query.get(mesa.zona_id) if mesa else None  # Obtener la zona asociada a la mesa
        resultado.append({
            "id": reserva.id,
            "nombre_cliente": reserva.nombre_cliente,
            "cantidad_personas": reserva.cantidad_personas,
            "fecha": reserva.fecha.strftime('%Y-%m-%d'),
            "horario": reserva.horario.strftime('%H:%M'),
            "mesa_id": reserva.mesa_id,
            "zona_nombre": zona.nombre if zona else "Zona no encontrada",
            "es_evento": reserva.es_evento
        })
    return jsonify({"reservas": resultado}), 200



# Ruta para listar zonas, mesas y reservas asociadas
@app.route('/zonas/completo', methods=['GET'])
def listar_zonas_completo():
    zonas = Zona.query.all()
    resultado = []
    for zona in zonas:
        mesas = Mesa.query.filter_by(zona_id=zona.id).all()
        mesas_info = []
        for mesa in mesas:
            reservas = Reserva.query.filter_by(mesa_id=mesa.id).all()
            reservas_info = [
                {
                    "id": reserva.id,
                    "nombre_cliente": reserva.nombre_cliente,
                    "cantidad_personas": reserva.cantidad_personas,
                    "fecha": reserva.fecha.isoformat(),
                    "horario": reserva.horario.isoformat(),
                    "es_evento": reserva.es_evento
                }
                for reserva in reservas
            ]
            mesas_info.append({"id": mesa.id, "capacidad": mesa.capacidad, "reservas": reservas_info})
        resultado.append({"id": zona.id, "nombre": zona.nombre, "mesas": mesas_info})
    return jsonify(zonas=resultado)

# RUTAS PARA ELIMINARR

# Ruta para eliminar una mesa por su ID
@app.route('/zonas/<int:zona_id>/mesas/<int:mesa_id>', methods=['DELETE'])
def eliminar_mesa(zona_id, mesa_id):
    # Buscar la mesa en la base de datos
    mesa = Mesa.query.filter_by(id=mesa_id, zona_id=zona_id).first()
    
    if not mesa:
        return jsonify({"error": "La mesa no existe en la zona especificada"}), 404
    
    # Eliminar la mesa
    db.session.delete(mesa)
    db.session.commit()
    
    return jsonify({"mensaje": f"Mesa con ID {mesa_id} eliminada de la zona con ID {zona_id}"}), 200

# Ruta para eliminar una reserva por ID
@app.route('/reservas/<int:reserva_id>', methods=['DELETE'])
def eliminar_reserva(reserva_id):
    # Buscar la reserva por ID
    reserva = Reserva.query.get(reserva_id)
    
    # Si no existe, devolver un error con código 404
    if not reserva:
        return jsonify({
            "error": f"No se encontró ninguna reserva con ID {reserva_id}"
        }), 404
    
    try:
        # Eliminar la reserva de la base de datos
        db.session.delete(reserva)
        db.session.commit()  # Confirmar los cambios
    except Exception as e:
        # Manejar cualquier error durante la operación
        return jsonify({
            "error": "Ocurrió un error al intentar eliminar la reserva",
            "detalles": str(e)
        }), 500  # Devolver código de error 500 si algo sale mal
    
    # Confirmar la eliminación
    return jsonify({
        "mensaje": f"Reserva con ID {reserva_id} eliminada exitosamente"
    }), 200



if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Obtener el puerto de la variable de entorno o usar 5000
    app.run(debug=True, host='0.0.0.0', port=port)  # Host '0.0.0.0' para que sea accesible desde fuera del contenedor

