from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import sqlite3
import secrets
import re
from utils import send_verification_email, init_db, get_db_connection
from models import User, Task
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['DATABASE'] = 'instance/tasks.db'

# Initialize database on first run
init_db()

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        name = data.get('name', '').strip()
        
        # Validation
        if not email or not password or not name:
            return jsonify({'success': False, 'message': 'All fields are required'}) if request.is_json else (flash('All fields are required'), redirect(url_for('register')))[1]
        
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({'success': False, 'message': 'Invalid email format'}) if request.is_json else (flash('Invalid email format'), redirect(url_for('register')))[1]
        
        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}) if request.is_json else (flash('Password must be at least 6 characters'), redirect(url_for('register')))[1]
        
        conn = get_db_connection()
        
        # Check if user exists
        if conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Email already registered'}) if request.is_json else (flash('Email already registered'), redirect(url_for('register')))[1]
        
        # Create user
        verification_token = secrets.token_urlsafe(32)
        password_hash = generate_password_hash(password)
        
        conn.execute('''
            INSERT INTO users (name, email, password_hash, verification_token, is_verified)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, email, password_hash, verification_token, False))
        conn.commit()
        conn.close()
        
        # Send verification email (simulated)
        print(f"Verification link: http://localhost:5000/verify/{verification_token}")
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Registration successful! Check console for verification link.'})
        else:
            flash('Registration successful! Check console for verification link.')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/verify/<token>')
def verify_email(token):
    conn = get_db_connection()
    user = conn.execute('SELECT id FROM users WHERE verification_token = ?', (token,)).fetchone()
    
    if user:
        conn.execute('UPDATE users SET is_verified = ?, verification_token = NULL WHERE verification_token = ?', (True, token))
        conn.commit()
        conn.close()
        flash('Email verified successfully! You can now log in.')
        return redirect(url_for('login'))
    else:
        conn.close()
        flash('Invalid verification token.')
        return redirect(url_for('register'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password required'}) if request.is_json else (flash('Email and password required'), redirect(url_for('login')))[1]
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            if not user['is_verified']:
                return jsonify({'success': False, 'message': 'Please verify your email first'}) if request.is_json else (flash('Please verify your email first'), redirect(url_for('login')))[1]
            
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            
            if request.is_json:
                return jsonify({'success': True, 'redirect': url_for('dashboard')})
            return redirect(url_for('dashboard'))
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}) if request.is_json else (flash('Invalid credentials'), redirect(url_for('login')))[1]
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    tasks = conn.execute('''
        SELECT * FROM tasks WHERE user_id = ? ORDER BY 
        CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END,
        due_date ASC
    ''', (session['user_id'],)).fetchall()
    
    # Get user stats for gamification
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t['status'] == 'completed'])
    
    # Calculate streak
    streak = conn.execute('''
        SELECT COUNT(*) as streak FROM tasks 
        WHERE user_id = ? AND status = 'completed' 
        AND DATE(completed_at) >= DATE('now', '-7 days')
    ''', (session['user_id'],)).fetchone()['streak']
    
    conn.close()
    
    return render_template('dashboard.html', 
                         tasks=tasks, 
                         total_tasks=total_tasks,
                         completed_tasks=completed_tasks,
                         streak=streak)

@app.route('/analytics')
@app.route('/analytics/')
def analytics():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # This week's completed tasks (last 7 days)
    this_week = conn.execute('''
        SELECT COUNT(*) as count FROM tasks 
        WHERE user_id = ? AND status = 'completed' 
        AND DATE(completed_at) >= DATE('now', '-7 days')
    ''', (session['user_id'],)).fetchone()['count']
    
    # Last week's completed tasks (8-14 days ago)
    last_week = conn.execute('''
        SELECT COUNT(*) as count FROM tasks 
        WHERE user_id = ? AND status = 'completed' 
        AND DATE(completed_at) >= DATE('now', '-14 days')
        AND DATE(completed_at) < DATE('now', '-7 days')
    ''', (session['user_id'],)).fetchone()['count']
    
    # Daily completion data for chart (last 7 days)
    daily_data = conn.execute('''
        SELECT DATE(completed_at) as date, COUNT(*) as count 
        FROM tasks 
        WHERE user_id = ? AND status = 'completed' 
        AND completed_at IS NOT NULL
        AND DATE(completed_at) >= DATE('now', '-7 days')
        GROUP BY DATE(completed_at)
        ORDER BY date
    ''', (session['user_id'],)).fetchall()
    
    conn.close()
    
    # Convert to list of dictionaries for JSON serialization
    daily_data_list = [{'date': row['date'], 'count': row['count']} for row in daily_data]
    
    return render_template('analytics.html',
                        this_week=this_week,
                        last_week=last_week,
                        daily_data=daily_data_list)
# API Routes for AJAX
@app.route('/api/tasks', methods=['GET', 'POST'])
def api_tasks():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        data = request.get_json()
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        priority = data.get('priority', 'medium')
        due_date = data.get('due_date')
        category = data.get('category', 'general').strip()
        
        if not title:
            return jsonify({'success': False, 'message': 'Title is required'})
        
        try:
            conn.execute('''
                INSERT INTO tasks (user_id, title, description, priority, due_date, category, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (session['user_id'], title, description, priority, due_date, category, 'pending', datetime.now()))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': 'Task created successfully'})
        except Exception as e:
            conn.close()
            return jsonify({'success': False, 'message': 'Failed to create task'})
    
    # GET request - return all tasks
    tasks = conn.execute('''
        SELECT * FROM tasks WHERE user_id = ? ORDER BY 
        CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END,
        due_date ASC
    ''', (session['user_id'],)).fetchall()
    conn.close()
    
    return jsonify({'success': True, 'tasks': [dict(task) for task in tasks]})

@app.route('/api/tasks/<int:task_id>', methods=['PUT', 'DELETE'])
def api_task_detail(task_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    conn = get_db_connection()
    
    # Verify task belongs to user
    task = conn.execute('SELECT * FROM tasks WHERE id = ? AND user_id = ?', (task_id, session['user_id'])).fetchone()
    if not task:
        conn.close()
        return jsonify({'success': False, 'message': 'Task not found'}), 404
    
    if request.method == 'PUT':
        data = request.get_json()
        
        if 'status' in data and data['status'] == 'completed':
            # Mark as completed
            conn.execute('''
                UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?
            ''', ('completed', datetime.now(), task_id))
        else:
            # Update other fields
            title = data.get('title', task['title'])
            description = data.get('description', task['description'])
            priority = data.get('priority', task['priority'])
            due_date = data.get('due_date', task['due_date'])
            category = data.get('category', task['category'])
            status = data.get('status', task['status'])
            
            conn.execute('''
                UPDATE tasks SET title = ?, description = ?, priority = ?, due_date = ?, category = ?, status = ?
                WHERE id = ?
            ''', (title, description, priority, due_date, category, status, task_id))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Task updated successfully'})
    
    elif request.method == 'DELETE':
        conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Task deleted successfully'})

@app.route('/api/reschedule', methods=['POST'])
def api_reschedule():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    conn = get_db_connection()
    
    # Get all pending tasks, prioritize by priority and due date
    tasks = conn.execute('''
        SELECT * FROM tasks WHERE user_id = ? AND status = 'pending'
        ORDER BY 
        CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END,
        due_date ASC
    ''', (session['user_id'],)).fetchall()
    
    # Reschedule logic: spread tasks over next 7 days, prioritizing important ones
    today = datetime.now().date()
    for i, task in enumerate(tasks[:7]):  # Limit to 7 most important tasks
        new_due_date = today + timedelta(days=i)
        conn.execute('UPDATE tasks SET due_date = ? WHERE id = ?', (new_due_date, task['id']))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Tasks rescheduled successfully'})

if __name__ == '__main__':
    app.run(debug=True)