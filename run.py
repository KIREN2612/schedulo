#!/usr/bin/env python3
"""
TaskFlow - Smart Task Management System
Run this file to start the Flask development server
"""

import os
import sys
from app import create_app

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main function to run the Flask app"""
    try:
        # Create Flask app
        app = create_app()
        
        # Get configuration from environment or use defaults
        host = os.environ.get('FLASK_HOST', '127.0.0.1')
        port = int(os.environ.get('FLASK_PORT', 5000))
        debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
        
        print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                            🚀 TaskFlow Starting                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Smart Task Management System                                                ║
║                                                                              ║
║  📍 Server: http://{host}:{port}                                    ║
║  🔧 Debug Mode: {'Enabled' if debug else 'Disabled'}                                             ║
║  💾 Database: SQLite (local file)                                           ║
║                                                                              ║
║  Press Ctrl+C to stop the server                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """)
        
        # Run the Flask development server
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n👋 TaskFlow server stopped by user")
        sys.exit(0)
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("\n💡 Make sure you have installed all required dependencies:")
        print("   pip install flask flask-sqlalchemy")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting TaskFlow: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()