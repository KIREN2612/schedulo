from flask import Blueprint, jsonify, request, render_template
from core.scheduler import generate_schedule
from app.models import Task, db
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError

main = Blueprint('main', __name__)

# ────────────────────────────────
# 🔄 Basic Routes
# ────────────────────────────────

@main.route('/ping', methods=['GET'])
def ping():
    """Health check endpoint"""
    return jsonify({"message": "pong", "status": "healthy"})


@main.route('/', methods=['GET'])
def index():
    """Main page route"""
    return render_template('index.html')


# ────────────────────────────────
# 📋 Task CRUD Endpoints
# ────────────────────────────────

@main.route('/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks"""
    try:
        tasks = Task.query.order_by(Task.priority.asc(), Task.id.desc()).all()
        tasks_list = []
        
        for task in tasks:
            task_dict = {
                "id": task.id,
                "title": task.title,
                "estimated_time": task.estimated_time,
                "priority": task.priority,
                "deadline": task.deadline.isoformat() if task.deadline else None,
                "created_at": task.created_at.isoformat() if hasattr(task, 'created_at') and task.created_at else None
            }
            tasks_list.append(task_dict)
        
        return jsonify(tasks_list), 200
        
    except SQLAlchemyError as e:
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred"}), 500


@main.route('/tasks', methods=['POST'])
def add_task():
    """Add a new task"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        title = data.get('title', '').strip()
        if not title:
            return jsonify({"error": "Task title is required"}), 400
        
        estimated_time = data.get('estimated_time')
        if estimated_time is None:
            estimated_time = 30  # Default 30 minutes
        
        try:
            estimated_time = int(estimated_time)
            if estimated_time <= 0:
                return jsonify({"error": "Estimated time must be positive"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Estimated time must be a valid number"}), 400
        
        priority = data.get('priority', 2)  # Default medium priority
        try:
            priority = int(priority)
            if priority not in [1, 2, 3]:
                priority = 2  # Default to medium if invalid
        except (ValueError, TypeError):
            priority = 2
        
        # Handle deadline
        deadline = None
        deadline_str = data.get('deadline')
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"error": "Invalid deadline format. Use YYYY-MM-DD"}), 400
        
        # Check for duplicate titles (optional - remove if you want duplicates)
        existing_task = Task.query.filter_by(title=title).first()
        if existing_task:
            return jsonify({"error": "A task with this title already exists"}), 400
        
        # Create new task
        new_task = Task(
            title=title,
            estimated_time=estimated_time,
            priority=priority,
            deadline=deadline
        )
        
        db.session.add(new_task)
        db.session.commit()
        
        return jsonify({
            "message": "Task added successfully",
            "task": {
                "id": new_task.id,
                "title": new_task.title,
                "estimated_time": new_task.estimated_time,
                "priority": new_task.priority,
                "deadline": new_task.deadline.isoformat() if new_task.deadline else None
            }
        }), 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "An unexpected error occurred"}), 500


@main.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a specific task"""
    try:
        task = Task.query.get(task_id)
        
        if not task:
            return jsonify({"error": "Task not found"}), 404
        
        task_title = task.title  # Store for response
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({
            "message": f"Task '{task_title}' deleted successfully",
            "deleted_task_id": task_id
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "An unexpected error occurred"}), 500


@main.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update a specific task"""
    try:
        task = Task.query.get(task_id)
        
        if not task:
            return jsonify({"error": "Task not found"}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Update fields if provided
        if 'title' in data:
            title = data['title'].strip()
            if not title:
                return jsonify({"error": "Task title cannot be empty"}), 400
            task.title = title
        
        if 'estimated_time' in data:
            try:
                estimated_time = int(data['estimated_time'])
                if estimated_time <= 0:
                    return jsonify({"error": "Estimated time must be positive"}), 400
                task.estimated_time = estimated_time
            except (ValueError, TypeError):
                return jsonify({"error": "Estimated time must be a valid number"}), 400
        
        if 'priority' in data:
            try:
                priority = int(data['priority'])
                if priority not in [1, 2, 3]:
                    return jsonify({"error": "Priority must be 1 (High), 2 (Medium), or 3 (Low)"}), 400
                task.priority = priority
            except (ValueError, TypeError):
                return jsonify({"error": "Priority must be a valid number"}), 400
        
        if 'deadline' in data:
            deadline_str = data['deadline']
            if deadline_str:
                try:
                    task.deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({"error": "Invalid deadline format. Use YYYY-MM-DD"}), 400
            else:
                task.deadline = None
        
        db.session.commit()
        
        return jsonify({
            "message": "Task updated successfully",
            "task": {
                "id": task.id,
                "title": task.title,
                "estimated_time": task.estimated_time,
                "priority": task.priority,
                "deadline": task.deadline.isoformat() if task.deadline else None
            }
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "An unexpected error occurred"}), 500


# ────────────────────────────────
# 📆 Schedule Generator
# ────────────────────────────────

@main.route('/generate_schedule', methods=['POST'])
def generate():
    """Generate optimized schedule based on available time"""
    try:
        data = request.get_json() or {}
        tasks_data = data.get('tasks')
        available_time = data.get('available_time', 0)
        
        # Validate available_time
        try:
            available_time = int(available_time)
            if available_time <= 0:
                return jsonify({"error": "Available time must be positive"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Available time must be a valid number"}), 400
        
        # If no tasks passed, fetch from database
        if not tasks_data:
            all_tasks = Task.query.order_by(Task.priority.asc(), Task.deadline.asc()).all()
            tasks_data = []
            
            for task in all_tasks:
                task_dict = {
                    "id": task.id,
                    "title": task.title,
                    "estimated_time": task.estimated_time,
                    "priority": task.priority,
                    "deadline": task.deadline.isoformat() if task.deadline else None,
                }
                tasks_data.append(task_dict)
        
        if not tasks_data:
            return jsonify({
                "message": "No tasks available to schedule",
                "schedule": []
            }), 200
        
        # Generate schedule using the scheduler
        schedule = generate_schedule(tasks_data, available_time)
        
        return jsonify({
            "message": "Schedule generated successfully",
            "schedule": schedule,
            "total_tasks": len(schedule),
            "total_time": sum(task.get('allocated_time', task.get('estimated_time', 0)) for task in schedule)
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to generate schedule: {str(e)}"}), 500


@main.route('/current_schedule', methods=['GET'])
def current_schedule():
    """Get current day's schedule (simplified version)"""
    try:
        # Get tasks ordered by priority for current schedule
        tasks = Task.query.order_by(Task.priority.asc(), Task.deadline.asc()).all()
        
        schedule = []
        for task in tasks:
            schedule_item = {
                "id": task.id,
                "title": task.title,
                "allocated_time": task.estimated_time,
                "priority": task.priority,
                "deadline": task.deadline.isoformat() if task.deadline else None
            }
            schedule.append(schedule_item)
        
        return jsonify({
            "schedule": schedule,
            "total_tasks": len(schedule)
        }), 200
        
    except SQLAlchemyError as e:
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred"}), 500


# ────────────────────────────────
# 🔁 Schedule Adjustments
# ────────────────────────────────

@main.route('/reschedule_task/<task_title>', methods=['POST'])
def reschedule_task(task_title):
    """Reschedule a task to tomorrow"""
    try:
        task = Task.query.filter_by(title=task_title).first()
        
        if not task:
            return jsonify({"error": "Task not found"}), 404
        
        # Set deadline to tomorrow if not set, or push existing deadline by 1 day
        if task.deadline:
            task.deadline = task.deadline + timedelta(days=1)
        else:
            task.deadline = (datetime.now().date() + timedelta(days=1))
        
        db.session.commit()
        
        return jsonify({
            "message": f"Task '{task_title}' rescheduled successfully",
            "new_deadline": task.deadline.isoformat()
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "An unexpected error occurred"}), 500


@main.route('/remove_task_from_schedule/<task_title>', methods=['DELETE'])
def remove_task_from_schedule(task_title):
    """Remove task from schedule (delete the task)"""
    try:
        task = Task.query.filter_by(title=task_title).first()
        
        if not task:
            return jsonify({"error": "Task not found"}), 404
        
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({
            "message": f"Task '{task_title}' removed from schedule successfully"
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "An unexpected error occurred"}), 500


# ────────────────────────────────
# 📊 Statistics API
# ────────────────────────────────

@main.route('/stats', methods=['GET'])
def stats():
    """Get dashboard statistics"""
    try:
        tasks = Task.query.all()
        total_tasks = len(tasks)
        
        # Count tasks by priority
        priority_counts = {
            1: sum(1 for t in tasks if t.priority == 1),  # High
            2: sum(1 for t in tasks if t.priority == 2),  # Medium
            3: sum(1 for t in tasks if t.priority == 3),  # Low
        }
        
        # Calculate XP (10 points per task)
        xp = total_tasks * 10
        
        # Calculate streak (consecutive days with tasks due)
        streak = calculate_streak(tasks)
        
        # Additional stats
        total_estimated_time = sum(task.estimated_time for task in tasks)
        avg_task_time = total_estimated_time // total_tasks if total_tasks > 0 else 0
        
        # Tasks due today and this week
        today = datetime.now().date()
        week_from_now = today + timedelta(days=7)
        
        tasks_due_today = sum(1 for t in tasks if t.deadline == today)
        tasks_due_this_week = sum(1 for t in tasks if t.deadline and today <= t.deadline <= week_from_now)
        
        return jsonify({
            'total_tasks': total_tasks,
            'priority_counts': priority_counts,
            'xp': xp,
            'streak': streak,
            'total_estimated_time': total_estimated_time,
            'avg_task_time': avg_task_time,
            'tasks_due_today': tasks_due_today,
            'tasks_due_this_week': tasks_due_this_week,
            'high_priority_tasks': priority_counts[1],
            'medium_priority_tasks': priority_counts[2],
            'low_priority_tasks': priority_counts[3]
        }), 200
        
    except SQLAlchemyError as e:
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred"}), 500


def calculate_streak(tasks):
    """Calculate consecutive days streak based on task deadlines"""
    try:
        if not tasks:
            return 0
        
        # Get unique deadline dates
        deadline_dates = set()
        for task in tasks:
            if task.deadline:
                deadline_dates.add(task.deadline)
        
        if not deadline_dates:
            return 0
        
        # Sort dates
        sorted_dates = sorted(deadline_dates, reverse=True)
        
        # Calculate streak from today backwards
        today = datetime.now().date()
        streak = 0
        current_date = today
        
        for date in sorted_dates:
            if date == current_date:
                streak += 1
                current_date -= timedelta(days=1)
            elif date < current_date:
                # Check if there's a gap
                break
        
        return streak
        
    except Exception:
        return 0


# ────────────────────────────────
# 🎯 Task Completion and Focus
# ────────────────────────────────

@main.route('/complete_task/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    """Mark a task as completed and award XP"""
    try:
        task = Task.query.get(task_id)
        
        if not task:
            return jsonify({"error": "Task not found"}), 404
        
        data = request.get_json() or {}
        focus_time = data.get('focus_time', 0)  # Time actually spent focusing
        
        # For now, we'll delete completed tasks
        # In a more complex system, you might want to keep them with a 'completed' status
        task_title = task.title
        estimated_time = task.estimated_time
        
        db.session.delete(task)
        db.session.commit()
        
        # Calculate XP bonus based on task priority and focus time
        base_xp = 10
        priority_bonus = {1: 15, 2: 10, 3: 5}[task.priority]
        focus_bonus = min(focus_time // 60, 10)  # Bonus XP for each minute focused (max 10)
        
        total_xp = base_xp + priority_bonus + focus_bonus
        
        return jsonify({
            "message": f"Task '{task_title}' completed successfully!",
            "xp_earned": total_xp,
            "task_title": task_title,
            "estimated_time": estimated_time,
            "actual_focus_time": focus_time
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "An unexpected error occurred"}), 500


@main.route('/tasks/bulk_delete', methods=['DELETE'])
def bulk_delete_tasks():
    """Delete multiple tasks at once"""
    try:
        data = request.get_json()
        if not data or 'task_ids' not in data:
            return jsonify({"error": "Task IDs are required"}), 400
        
        task_ids = data['task_ids']
        if not isinstance(task_ids, list):
            return jsonify({"error": "Task IDs must be a list"}), 400
        
        deleted_count = 0
        for task_id in task_ids:
            task = Task.query.get(task_id)
            if task:
                db.session.delete(task)
                deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            "message": f"Successfully deleted {deleted_count} tasks",
            "deleted_count": deleted_count
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "An unexpected error occurred"}), 500


# ────────────────────────────────
# 🔍 Search and Filter
# ────────────────────────────────

@main.route('/tasks/search', methods=['GET'])
def search_tasks():
    """Search tasks by title or filter by priority/deadline"""
    try:
        query = request.args.get('q', '').strip()
        priority = request.args.get('priority')
        has_deadline = request.args.get('has_deadline')
        
        tasks_query = Task.query
        
        # Filter by search query
        if query:
            tasks_query = tasks_query.filter(Task.title.ilike(f'%{query}%'))
        
        # Filter by priority
        if priority:
            try:
                priority_int = int(priority)
                if priority_int in [1, 2, 3]:
                    tasks_query = tasks_query.filter(Task.priority == priority_int)
            except ValueError:
                pass
        
        # Filter by deadline existence
        if has_deadline is not None:
            if has_deadline.lower() == 'true':
                tasks_query = tasks_query.filter(Task.deadline.isnot(None))
            elif has_deadline.lower() == 'false':
                tasks_query = tasks_query.filter(Task.deadline.is_(None))
        
        tasks = tasks_query.order_by(Task.priority.asc(), Task.id.desc()).all()
        
        tasks_list = []
        for task in tasks:
            task_dict = {
                "id": task.id,
                "title": task.title,
                "estimated_time": task.estimated_time,
                "priority": task.priority,
                "deadline": task.deadline.isoformat() if task.deadline else None,
            }
            tasks_list.append(task_dict)
        
        return jsonify({
            "tasks": tasks_list,
            "total_found": len(tasks_list),
            "search_query": query,
            "filters": {
                "priority": priority,
                "has_deadline": has_deadline
            }
        }), 200
        
    except SQLAlchemyError as e:
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred"}), 500


# ────────────────────────────────
# 📈 Analytics
# ────────────────────────────────

@main.route('/analytics', methods=['GET'])
def analytics():
    """Get detailed analytics about tasks and productivity"""
    try:
        tasks = Task.query.all()
        
        if not tasks:
            return jsonify({
                "message": "No tasks available for analytics",
                "analytics": {}
            }), 200
        
        # Time-based analytics
        total_estimated_time = sum(task.estimated_time for task in tasks)
        avg_task_duration = total_estimated_time / len(tasks) if tasks else 0
        
        # Priority distribution
        priority_dist = {
            "high": sum(1 for t in tasks if t.priority == 1),
            "medium": sum(1 for t in tasks if t.priority == 2),
            "low": sum(1 for t in tasks if t.priority == 3)
        }
        
        # Deadline analytics
        today = datetime.now().date()
        overdue_tasks = sum(1 for t in tasks if t.deadline and t.deadline < today)
        due_today = sum(1 for t in tasks if t.deadline == today)
        due_this_week = sum(1 for t in tasks if t.deadline and today <= t.deadline <= today + timedelta(days=7))
        
        # Task duration distribution
        short_tasks = sum(1 for t in tasks if t.estimated_time <= 30)  # <= 30 min
        medium_tasks = sum(1 for t in tasks if 30 < t.estimated_time <= 90)  # 30-90 min
        long_tasks = sum(1 for t in tasks if t.estimated_time > 90)  # > 90 min
        
        analytics_data = {
            "total_tasks": len(tasks),
            "total_estimated_time": total_estimated_time,
            "avg_task_duration": round(avg_task_duration, 1),
            "priority_distribution": priority_dist,
            "deadline_analytics": {
                "overdue": overdue_tasks,
                "due_today": due_today,
                "due_this_week": due_this_week,
                "no_deadline": sum(1 for t in tasks if not t.deadline)
            },
            "duration_distribution": {
                "short_tasks": short_tasks,
                "medium_tasks": medium_tasks,
                "long_tasks": long_tasks
            },
            "productivity_score": calculate_productivity_score(tasks),
            "recommendations": generate_recommendations(tasks)
        }
        
        return jsonify({"analytics": analytics_data}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to generate analytics: {str(e)}"}), 500


def calculate_productivity_score(tasks):
    """Calculate a productivity score based on task management"""
    if not tasks:
        return 0
    
    score = 50  # Base score
    
    # Bonus for having deadlines
    tasks_with_deadlines = sum(1 for t in tasks if t.deadline)
    deadline_ratio = tasks_with_deadlines / len(tasks)
    score += deadline_ratio * 20
    
    # Bonus for balanced priority distribution
    priority_counts = [
        sum(1 for t in tasks if t.priority == 1),
        sum(1 for t in tasks if t.priority == 2),
        sum(1 for t in tasks if t.priority == 3)
    ]
    if all(count > 0 for count in priority_counts):
        score += 15
    
    # Penalty for overdue tasks
    today = datetime.now().date()
    overdue_tasks = sum(1 for t in tasks if t.deadline and t.deadline < today)
    if overdue_tasks > 0:
        score -= min(overdue_tasks * 5, 20)
    
    return max(0, min(100, round(score)))


def generate_recommendations(tasks):
    """Generate recommendations based on task analysis"""
    recommendations = []
    
    if not tasks:
        return ["Start by adding some tasks to get organized!"]
    
    # Check for tasks without deadlines
    no_deadline_count = sum(1 for t in tasks if not t.deadline)
    if no_deadline_count > len(tasks) * 0.5:
        recommendations.append("Consider setting deadlines for more of your tasks to improve time management.")
    
    # Check for priority balance
    high_priority = sum(1 for t in tasks if t.priority == 1)
    if high_priority > len(tasks) * 0.7:
        recommendations.append("You have many high-priority tasks. Consider reviewing and adjusting priorities.")
    
    # Check for task duration variety
    avg_duration = sum(t.estimated_time for t in tasks) / len(tasks)
    if avg_duration > 90:
        recommendations.append("Your tasks seem quite long. Consider breaking them into smaller, manageable chunks.")
    
    # Check for overdue tasks
    today = datetime.now().date()
    overdue_tasks = sum(1 for t in tasks if t.deadline and t.deadline < today)
    if overdue_tasks > 0:
        recommendations.append(f"You have {overdue_tasks} overdue task(s). Consider rescheduling or completing them soon.")
    
    if not recommendations:
        recommendations.append("Great job! Your task management looks well-organized.")
    
    return recommendations