from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

def create_app():
    """Create and configure the Flask application"""
    # Get the directory where this __init__.py file is located
    basedir = os.path.abspath(os.path.dirname(__file__))
    
    # Create Flask app with proper static and template folder paths
    app = Flask(__name__,
                static_folder=os.path.join(basedir, 'static'),
                template_folder=os.path.join(basedir, 'templates'))
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
    
    # Database configuration
    database_path = os.path.join(basedir, '..', 'instance', 'taskflow.db')
    
    # Ensure instance directory exists
    instance_dir = os.path.dirname(database_path)
    os.makedirs(instance_dir, exist_ok=True)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    from .models import db
    db.init_app(app)
    
    # Register blueprints
    from .routes import main
    app.register_blueprint(main)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        print(f"Database created at: {database_path}")
        print(f"Static folder: {app.static_folder}")
        print(f"Template folder: {app.template_folder}")
        
        # Initialize default data if needed
        from .models import UserStats
        default_stats = UserStats.query.filter_by(user_id='default_user').first()
        if not default_stats:
            default_stats = UserStats(user_id='default_user')
            db.session.add(default_stats)
            db.session.commit()
            print("Created default user stats")
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        # Check if it's an API request or static file request
        if '/api/' in str(error) or '/static/' in str(error):
            return {'error': 'Resource not found'}, 404
        return {'error': 'Page not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error'}, 500
    
    return app