"""
Database models for TaskFlow application
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
from sqlalchemy import func
import math
import json

# Initialize SQLAlchemy instance
db = SQLAlchemy()


class Task(db.Model):
    """Task model for storing user tasks"""
    
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    estimated_time = db.Column(db.Integer, default=30)  # in minutes
    actual_time = db.Column(db.Integer, nullable=True)  # actual time spent
    priority = db.Column(db.Integer, default=2)  # 1=High, 2=Medium, 3=Low
    completed = db.Column(db.Boolean, default=False)
    deadline = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    focus_sessions = db.Column(db.Integer, default=0)  # number of focus sessions completed
    
    # Additional metadata
    description = db.Column(db.Text, nullable=True)
    tags = db.Column(db.String(500), nullable=True)  # comma-separated tags
    difficulty = db.Column(db.Integer, default=2)  # 1=Easy, 2=Medium, 3=Hard
    
    def __repr__(self):
        return f'<Task {self.id}: {self.title}>'
    
    @property
    def is_overdue(self):
        """Check if task is overdue"""
        if not self.deadline or self.completed:
            return False
        return self.deadline < date.today()
    
    @property
    def days_until_deadline(self):
        """Calculate days until deadline"""
        if not self.deadline:
            return None
        return (self.deadline - date.today()).days
    
    @property
    def priority_label(self):
        """Get human-readable priority label"""
        return {1: 'High', 2: 'Medium', 3: 'Low'}.get(self.priority, 'Medium')
    
    @property
    def difficulty_label(self):
        """Get human-readable difficulty label"""
        return {1: 'Easy', 2: 'Medium', 3: 'Hard'}.get(self.difficulty, 'Medium')
    
    @property
    def completion_time_accuracy(self):
        """Calculate how accurate the time estimation was"""
        if not self.actual_time or not self.estimated_time:
            return None
        return min(100, (self.estimated_time / self.actual_time) * 100)
    
    def mark_completed(self, actual_time=None, focus_sessions=1):
        """Mark task as completed with optional actual time"""
        self.completed = True
        self.completed_at = datetime.utcnow()
        if actual_time:
            self.actual_time = actual_time
        if focus_sessions:
            self.focus_sessions = focus_sessions
        db.session.commit()
    
    def update_progress(self, time_spent, sessions_completed=0):
        """Update task progress without marking as complete"""
        if not self.actual_time:
            self.actual_time = 0
        self.actual_time += time_spent
        self.focus_sessions += sessions_completed
        db.session.commit()
    
    def to_dict(self):
        """Convert task to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'estimated_time': self.estimated_time,
            'actual_time': self.actual_time,
            'priority': self.priority,
            'priority_label': self.priority_label,
            'difficulty': self.difficulty,
            'difficulty_label': self.difficulty_label,
            'completed': self.completed,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'is_overdue': self.is_overdue,
            'days_until_deadline': self.days_until_deadline,
            'focus_sessions': self.focus_sessions,
            'description': self.description,
            'tags': self.tags.split(',') if self.tags else [],
            'completion_time_accuracy': self.completion_time_accuracy
        }
    
    @classmethod
    def get_active_tasks(cls):
        """Get all active (not completed) tasks"""
        return cls.query.filter_by(completed=False).all()
    
    @classmethod
    def get_completed_tasks(cls):
        """Get all completed tasks"""
        return cls.query.filter_by(completed=True).all()
    
    @classmethod
    def get_overdue_tasks(cls):
        """Get all overdue tasks"""
        return cls.query.filter(
            cls.completed == False,
            cls.deadline < date.today()
        ).all()
    
    @classmethod
    def get_tasks_by_priority(cls, priority, completed=None):
        """Get tasks by priority level"""
        query = cls.query.filter_by(priority=priority)
        if completed is not None:
            query = query.filter_by(completed=completed)
        return query.all()
    
    @classmethod
    def get_weekly_completed_tasks(cls):
        """Get tasks completed in the last 7 days"""
        week_ago = datetime.utcnow() - timedelta(days=7)
        return cls.query.filter(
            cls.completed == True,
            cls.completed_at >= week_ago
        ).all()


class UserStats(db.Model):
    """User statistics and gamification data"""
    
    __tablename__ = 'user_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), unique=True, nullable=False)
    
    # XP and Level System
    xp_points = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    
    # Task Statistics
    total_tasks_completed = db.Column(db.Integer, default=0)
    total_focus_time = db.Column(db.Integer, default=0)  # in minutes
    
    # Streak System
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_activity = db.Column(db.Date, nullable=True)
    
    # Achievement Tracking
    achievements_unlocked = db.Column(db.Text, default='[]')  # JSON string of achievements
    badges_earned = db.Column(db.Text, default='[]')  # JSON string of badges
    
    # Performance Metrics
    avg_completion_time_accuracy = db.Column(db.Float, default=100.0)
    favorite_work_time = db.Column(db.String(20), default='morning')  # morning, afternoon, evening
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserStats {self.user_id}: Level {self.level}, XP {self.xp_points}>'
    
    @property
    def xp_for_next_level(self):
        """Calculate XP required for next level"""
        return self.level * 100
    
    @property
    def xp_progress_percentage(self):
        """Calculate progress to next level as percentage"""
        current_level_xp = (self.level - 1) * 100
        next_level_xp = self.level * 100
        progress_xp = self.xp_points - current_level_xp
        total_xp_needed = next_level_xp - current_level_xp
        
        return min(100, (progress_xp / total_xp_needed) * 100) if total_xp_needed > 0 else 0
    
    @property
    def rank_title(self):
        """Get rank title based on level"""
        if self.level < 5:
            return "Beginner"
        elif self.level < 10:
            return "Apprentice"
        elif self.level < 20:
            return "Journeyman"
        elif self.level < 35:
            return "Expert"
        elif self.level < 50:
            return "Master"
        else:
            return "Grandmaster"
    
    def add_xp(self, points):
        """Add XP points and check for level up"""
        self.xp_points += points
        old_level = self.level
        
        # Calculate new level
        new_level = math.floor(self.xp_points / 100) + 1
        
        leveled_up = new_level > old_level
        if leveled_up:
            self.level = new_level
        
        self.updated_at = datetime.utcnow()
        return leveled_up
    
    def update_streak(self):
        """Update streak based on current activity"""
        today = date.today()
        
        if self.last_activity is None:
            # First activity
            self.current_streak = 1
            self.longest_streak = max(self.longest_streak, 1)
        elif self.last_activity == today:
            # Already active today, no change
            pass
        elif self.last_activity == today - timedelta(days=1):
            # Consecutive day
            self.current_streak += 1
            self.longest_streak = max(self.longest_streak, self.current_streak)
        else:
            # Streak broken
            self.current_streak = 1
        
        self.last_activity = today
        self.updated_at = datetime.utcnow()
    
    def calculate_productivity_score(self):
        """Calculate overall productivity score (0-100)"""
        score = 0
        
        # Level contribution (0-30 points)
        score += min(30, self.level * 2)
        
        # Streak contribution (0-25 points)
        score += min(25, self.current_streak * 2)
        
        # Task completion rate (0-25 points)
        if self.total_tasks_completed > 0:
            # This would need to be calculated with actual task data
            # For now, we'll use a placeholder based on completed tasks
            score += min(25, self.total_tasks_completed)
        
        # Time accuracy (0-20 points)
        accuracy_score = (self.avg_completion_time_accuracy / 100) * 20
        score += accuracy_score
        
        return min(100, score)
    
    def get_achievement_list(self):
        """Get list of achievements"""
        try:
            return json.loads(self.achievements_unlocked) if self.achievements_unlocked else []
        except json.JSONDecodeError:
            return []
    
    def add_achievement(self, achievement_id, achievement_name):
        """Add new achievement"""
        achievements = self.get_achievement_list()
        
        achievement = {
            'id': achievement_id,
            'name': achievement_name,
            'unlocked_at': datetime.utcnow().isoformat()
        }
        
        # Check if already unlocked
        if not any(a['id'] == achievement_id for a in achievements):
            achievements.append(achievement)
            self.achievements_unlocked = json.dumps(achievements)
            return True
        return False
    
    def get_badges_list(self):
        """Get list of badges"""
        try:
            return json.loads(self.badges_earned) if self.badges_earned else []
        except json.JSONDecodeError:
            return []
    
    def check_and_award_achievements(self):
        """Check for new achievements and award them"""
        new_achievements = []
        
        # First task completion
        if self.total_tasks_completed == 1:
            if self.add_achievement('first_task', 'First Task Completed'):
                new_achievements.append('First Task Completed')
        
        # Task completion milestones
        milestones = [5, 10, 25, 50, 100, 250, 500, 1000]
        for milestone in milestones:
            if self.total_tasks_completed == milestone:
                achievement_id = f'tasks_{milestone}'
                achievement_name = f'{milestone} Tasks Completed'
                if self.add_achievement(achievement_id, achievement_name):
                    new_achievements.append(achievement_name)
        
        # Streak achievements
        if self.current_streak == 7:
            if self.add_achievement('week_streak', 'Week Streak'):
                new_achievements.append('Week Streak')
        elif self.current_streak == 30:
            if self.add_achievement('month_streak', 'Month Streak'):
                new_achievements.append('Month Streak')
        elif self.current_streak == 100:
            if self.add_achievement('hundred_streak', '100 Day Streak'):
                new_achievements.append('100 Day Streak')
        
        # Level achievements
        level_milestones = [5, 10, 20, 35, 50]
        for milestone in level_milestones:
            if self.level == milestone:
                achievement_id = f'level_{milestone}'
                achievement_name = f'Reached Level {milestone}'
                if self.add_achievement(achievement_id, achievement_name):
                    new_achievements.append(achievement_name)
        
        return new_achievements
    
    def to_dict(self):
        """Convert user stats to dictionary for JSON serialization"""
        return {
            'user_id': self.user_id,
            'xp_points': self.xp_points,
            'level': self.level,
            'rank_title': self.rank_title,
            'xp_for_next_level': self.xp_for_next_level,
            'xp_progress_percentage': round(self.xp_progress_percentage, 2),
            'total_tasks_completed': self.total_tasks_completed,
            'total_focus_time': self.total_focus_time,
            'current_streak': self.current_streak,
            'longest_streak': self.longest_streak,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'avg_completion_time_accuracy': round(self.avg_completion_time_accuracy, 2),
            'favorite_work_time': self.favorite_work_time,
            'productivity_score': round(self.calculate_productivity_score(), 2),
            'achievements': self.get_achievement_list(),
            'badges': self.get_badges_list(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


# Additional utility functions for database operations
def get_or_create_user_stats(user_id='default_user'):
    """Get existing user stats or create new ones"""
    user_stats = UserStats.query.filter_by(user_id=user_id).first()
    
    if not user_stats:
        user_stats = UserStats(user_id=user_id)
        db.session.add(user_stats)
        db.session.commit()
    
    return user_stats


def calculate_global_stats():
    """Calculate global statistics across all tasks and users"""
    try:
        total_tasks = Task.query.count()
        completed_tasks = Task.query.filter_by(completed=True).count()
        active_tasks = total_tasks - completed_tasks
        
        # Time statistics
        total_estimated_time = db.session.query(func.sum(Task.estimated_time)).scalar() or 0
        total_actual_time = db.session.query(func.sum(Task.actual_time)).filter(Task.actual_time.isnot(None)).scalar() or 0
        
        # Priority distribution
        high_priority = Task.query.filter_by(priority=1, completed=False).count()
        medium_priority = Task.query.filter_by(priority=2, completed=False).count()
        low_priority = Task.query.filter_by(priority=3, completed=False).count()
        
        # Recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_completions = Task.query.filter(
            Task.completed == True,
            Task.completed_at >= week_ago
        ).count()
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'active_tasks': active_tasks,
            'completion_rate': round((completed_tasks / total_tasks) * 100, 2) if total_tasks > 0 else 0,
            'total_estimated_time': total_estimated_time,
            'total_actual_time': total_actual_time,
            'priority_distribution': {
                'high': high_priority,
                'medium': medium_priority,
                'low': low_priority
            },
            'recent_completions': recent_completions,
            'avg_task_duration': round(total_estimated_time / total_tasks, 2) if total_tasks > 0 else 0
        }
        
    except Exception as e:
        return {
            'error': f"Failed to calculate global stats: {str(e)}",
            'total_tasks': 0,
            'completed_tasks': 0,
            'active_tasks': 0
        }