"""
TaskFlow Application Package
"""
from flask import Flask
import os

def create_app(config=None):
    """Create and configure the Flask application"""
    
    app = Flask(__name__)
    
    # Configure database
    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_path = os.path.join(basedir, '..', 'instance')
    
    # Ensure instance directory exists
    os.makedirs(instance_path, exist_ok=True)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instance_path, "taskflow.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
    
    # Apply custom config if provided
    if config:
        app.config.update(config)
    
    # Import and initialize the db from models
    from app.models import db
    db.init_app(app)
    
    # Import models after db initialization (this ensures they're registered)
    from app.models import Task, UserStats
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create default user stats if not exists
        from app.models import get_or_create_user_stats
        get_or_create_user_stats()
    
    # Register blueprints/routes
    from app.routes import main
    app.register_blueprint(main)
    
    return app