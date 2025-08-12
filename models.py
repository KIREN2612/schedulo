import sqlite3
from datetime import datetime

class User:
    def __init__(self, id=None, name=None, email=None, password_hash=None, 
                verification_token=None, is_verified=False, created_at=None):
        self.id = id
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.verification_token = verification_token
        self.is_verified = is_verified
        self.created_at = created_at or datetime.now()

class Task:
    def __init__(self, id=None, user_id=None, title=None, description=None, 
                priority='medium', due_date=None, category='general', 
                status='pending', created_at=None, completed_at=None):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.description = description
        self.priority = priority  # high, medium, low
        self.due_date = due_date
        self.category = category
        self.status = status  # pending, completed, cancelled
        self.created_at = created_at or datetime.now()
        self.completed_at = completed_at
