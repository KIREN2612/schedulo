from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()  # ✅ define db FIRST

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    estimated_time = db.Column(db.Integer, nullable=False)
    priority = db.Column(db.Integer, nullable=False)
    deadline = db.Column(db.String(20), nullable=True)  # Optional
