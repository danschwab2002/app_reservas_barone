from app import db, app

# Crear un contexto de aplicación
with app.app_context():
    # Crear o actualizar las tablas de la base de datos
    db.create_all()
    print("La base de datos se ha actualizado correctamente.")