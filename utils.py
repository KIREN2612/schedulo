import sqlite3
import os
from flask import g
from datetime import datetime, timedelta

def get_db_connection():
    """Get database connection with row factory for dict-like access"""
    if not os.path.exists('instance'):
        os.makedirs('instance')
    
    conn = sqlite3.connect('instance/tasks.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with tables"""
    conn = get_db_connection()
    
    # Create users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            verification_token TEXT,
            is_verified BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create tasks table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT DEFAULT 'medium',
            due_date DATE,
            category TEXT DEFAULT 'general',
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    
    # Insert sample data for testing
    sample_user = conn.execute('SELECT id FROM users WHERE email = ?', ('demo@example.com',)).fetchone()
    if not sample_user:
        from werkzeug.security import generate_password_hash
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (name, email, password_hash, is_verified)
            VALUES (?, ?, ?, ?)
        ''', ('Demo User', 'demo@example.com', generate_password_hash('demo123'), True))
        
        user_id = cursor.lastrowid
        
        # Sample tasks with some completed ones for analytics
        sample_tasks = [
            ('Complete project proposal', 'Write and submit the Q4 project proposal', 'high', '2025-08-15', 'work', 'pending'),
            ('Buy groceries', 'Milk, bread, eggs, fruits', 'medium', '2025-08-12', 'personal', 'completed'),
            ('Exercise routine', '30 minutes cardio workout', 'low', '2025-08-13', 'health', 'completed'),
            ('Read book chapter', 'Chapter 5 of productivity book', 'medium', '2025-08-14', 'learning', 'pending'),
            ('Team meeting prep', 'Prepare slides for Monday meeting', 'high', '2025-08-16', 'work', 'completed'),
            ('Morning jog', 'Go for a 30-minute jog in the park', 'medium', '2025-08-11', 'health', 'completed'),
            ('Call dentist', 'Schedule annual checkup appointment', 'low', '2025-08-10', 'personal', 'completed'),
            ('Review code', 'Code review for team project', 'high', '2025-08-17', 'work', 'pending'),
            ('Meditation', '15 minutes mindfulness meditation', 'low', '2025-08-09', 'health', 'completed'),
            ('Email cleanup', 'Organize and clean up inbox', 'medium', '2025-08-08', 'personal', 'completed')
        ]
        
        # Add completed tasks with realistic completion dates
        base_date = datetime.now()
        for i, (title, desc, priority, due_date, category, status) in enumerate(sample_tasks):
            # Set completion date for completed tasks (spread over last 2 weeks)
            completed_at = None
            if status == 'completed':
                # Distribute completed tasks over the last 14 days
                completed_at = base_date - timedelta(days=(i % 14))
            
            cursor.execute('''
                INSERT INTO tasks (user_id, title, description, priority, due_date, category, status, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, title, desc, priority, due_date, category, status, completed_at))
    
    conn.commit()
    conn.close()

def send_verification_email(email, token):
    """Send verification email (placeholder for production implementation)"""
    # In production, integrate with email service like SendGrid, AWS SES, etc.
    verification_url = f"http://localhost:5000/verify/{token}"
    print(f"Verification email would be sent to {email}")
    print(f"Verification URL: {verification_url}")
    return True