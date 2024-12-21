from app import db, app  # Importar db y app desde el archivo app.py

# Establecer el contexto de la aplicación
with app.app_context():
    db.create_all()  # Crear todas las tablas en la base de datos
    print("Base de datos creada correctamente.")
