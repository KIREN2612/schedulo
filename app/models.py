from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Task(db.Model):
    """Task model for storing task information"""
    
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    estimated_time = db.Column(db.Integer, nullable=False, default=30)  # in minutes
    priority = db.Column(db.Integer, nullable=False, default=2)  # 1=High, 2=Medium, 3=Low
    deadline = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Task {self.id}: {self.title}>'
    
    def to_dict(self):
        """Convert task to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'estimated_time': self.estimated_time,
            'priority': self.priority,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @staticmethod
    def get_priority_text(priority_num):
        """Get text representation of priority"""
        priority_map = {1: 'High', 2: 'Medium', 3: 'Low'}
        return priority_map.get(priority_num, 'Medium')
    
    @property
    def priority_text(self):
        """Get priority as text"""
        return self.get_priority_text(self.priority)
    
    @property
    def is_overdue(self):
        """Check if task is overdue"""
        if not self.deadline:
            return False
        return self.deadline < datetime.now().date()
    
    @property
    def days_until_deadline(self):
        """Get days until deadline"""
        if not self.deadline:
            return None
        delta = self.deadline - datetime.now().date()
        return delta.days


class CompletedTask(db.Model):
    """Model for storing completed tasks (optional - for analytics)"""
    
    __tablename__ = 'completed_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    original_task_id = db.Column(db.Integer, nullable=True)  # Reference to original task
    title = db.Column(db.String(200), nullable=False)
    estimated_time = db.Column(db.Integer, nullable=False)
    actual_time = db.Column(db.Integer, nullable=True)  # Time actually spent
    priority = db.Column(db.Integer, nullable=False)
    deadline = db.Column(db.Date, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    focus_sessions = db.Column(db.Integer, default=1)  # Number of focus sessions used
    was_completed_on_time = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<CompletedTask {self.id}: {self.title}>'
    
    def to_dict(self):
        """Convert completed task to dictionary"""
        return {
            'id': self.id,
            'original_task_id': self.original_task_id,
            'title': self.title,
            'estimated_time': self.estimated_time,
            'actual_time': self.actual_time,
            'priority': self.priority,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'completed_at': self.completed_at.isoformat(),
            'focus_sessions': self.focus_sessions,
            'was_completed_on_time': self.was_completed_on_time
        }


class UserStats(db.Model):
    """Model for storing user statistics and achievements"""
    
    __tablename__ = 'user_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False, default='default_user')  # For future multi-user support
    total_tasks_completed = db.Column(db.Integer, default=0)
    total_focus_time = db.Column(db.Integer, default=0)  # in minutes
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    xp_points = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    last_activity = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserStats {self.user_id}: Level {self.level}, {self.xp_points} XP>'
    
    def to_dict(self):
        """Convert user stats to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'total_tasks_completed': self.total_tasks_completed,
            'total_focus_time': self.total_focus_time,
            'current_streak': self.current_streak,
            'longest_streak': self.longest_streak,
            'xp_points': self.xp_points,
            'level': self.level,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def add_xp(self, points):
        """Add XP points and check for level up"""
        self.xp_points += points
        new_level = (self.xp_points // 100) + 1
        if new_level > self.level:
            self.level = new_level
            return True  # Leveled up
        return False
    
    def update_streak(self):
        """Update streak based on activity"""
        today = datetime.now().date()
        
        if self.last_activity is None:
            # First activity
            self.current_streak = 1
            self.last_activity = today
        elif self.last_activity == today:
            # Already active today, no change needed
            pass
        elif self.last_activity == today - datetime.timedelta(days=1):
            # Consecutive day, increment streak
            self.current_streak += 1
            self.last_activity = today
            
            # Update longest streak if needed
            if self.current_streak > self.longest_streak:
                self.longest_streak = self.current_streak
        else:
            # Streak broken, reset
            self.current_streak = 1
            self.last_activity = today


def init_db(app):
    """Initialize database with app context"""
    with app.app_context():
        db.create_all()
        
        # Create default user stats if not exists
        default_stats = UserStats.query.filter_by(user_id='default_user').first()
        if not default_stats:
            default_stats = UserStats(user_id='default_user')
            db.session.add(default_stats)
            db.session.commit()
            print("Created default user stats")
        
        print("Database initialized successfully!")