from app import create_app, init_runtime_database


app = create_app()

with app.app_context():
    init_runtime_database(app)
