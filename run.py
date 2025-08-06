#!/usr/bin/env python3
"""
TaskFlow Application Launcher
Run this script to start the TaskFlow web application
"""

import os
import sys
from pathlib import Path

def main():
    """Main function to launch TaskFlow"""
    
    print("🔧 Creating Flask application...")
    
    try:
        # Add current directory to Python path
        current_dir = Path(__file__).parent.absolute()
        sys.path.insert(0, str(current_dir))
        
        # Import and create the Flask application
        from app import create_app
        
        # Create the Flask app
        app = create_app()
        
        # Print debug information
        print(f"Database will be created at: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        # Get template and static folders
        template_folder = os.path.join(current_dir, 'app', 'templates')
        static_folder = os.path.join(current_dir, 'app', 'static')
        
        # Create directories if they don't exist
        os.makedirs(template_folder, exist_ok=True)
        os.makedirs(static_folder, exist_ok=True)
        
        print(f"Template folder: {template_folder}")
        print(f"Static folder: {static_folder}")
        
        # Test database connection
        with app.app_context():
            from app.models import Task, UserStats
            
            # Test queries
            task_count = Task.query.count()
            user_stats_count = UserStats.query.count()
            
            print(f"✅ Database connected successfully!")
            print(f"   Tasks: {task_count}")
            print(f"   User Stats: {user_stats_count}")
        
        print("\n🚀 Starting TaskFlow application...")
        print("📱 Access your dashboard at: http://127.0.0.1:5000")
        print("🔗 API endpoints available at: http://127.0.0.1:5000/api/")
        print("💡 Press Ctrl+C to stop the server")
        print("=" * 60)
        
        # Start the development server
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=True,
            use_reloader=True
        )
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Make sure you have installed all required dependencies:")
        print("   pip install flask flask-sqlalchemy sqlalchemy")
        print("   You can also install from requirements.txt if available:")
        print("   pip install -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"❌ Error starting TaskFlow: {e}")
        
        # Print debug information
        print("🔍 Debug information:")
        print(f"   Python version: {sys.version}")
        print(f"   Working directory: {os.getcwd()}")
        print(f"   Script location: {__file__}")
        
        return False
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 TaskFlow server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)