from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .models import db  # ✅ import db after defining it in models

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:/schedulo/instance/schedulo.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    from .routes import main
    app.register_blueprint(main)

    return app
