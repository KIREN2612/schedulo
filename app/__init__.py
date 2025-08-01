from flask import Flask

def create_app():
    app = Flask(__name__)

    # Simple in-memory task store
    app.config['TASKS_STORE'] = []

    from .routes import main
    app.register_blueprint(main)

    return app
