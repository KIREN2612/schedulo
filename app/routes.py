from flask import Blueprint, jsonify, request, render_template
from core.scheduler import generate_schedule, get_task_recommendations, calculate_completion_stats
from app.models import Task, UserStats, db, get_or_create_user_stats
from app.utils.analytics import calculate_weekly_performance, calculate_monthly_stats, get_productivity_trends
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, func

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
    # Get or create user stats
    user_stats = UserStats.query.filter_by(user_id='default_user').first()
    if not user_stats:
        user_stats = UserStats(user_id='default_user')
        db.session.add(user_stats)
        db.session.commit()
    
    # Get task summary data for dashboard
    active_tasks = Task.query.filter_by(completed=False).all()
    completed_tasks = Task.query.filter_by(completed=True).all()
    overdue_tasks = [task for task in active_tasks if hasattr(task, 'is_overdue') and task.is_overdue]
    
    # Get priority counts
    high_priority = sum(1 for t in active_tasks if t.priority == 1)
    medium_priority = sum(1 for t in active_tasks if t.priority == 2)
    low_priority = sum(1 for t in active_tasks if t.priority == 3)
    
    return render_template('index.html', 
                         user_stats=user_stats,
                         active_tasks=active_tasks,
                         completed_tasks=completed_tasks,
                         overdue_tasks=overdue_tasks,
                         high_priority_count=high_priority,
                         medium_priority_count=medium_priority,
                         low_priority_count=low_priority,
                         total_tasks=len(active_tasks) + len(completed_tasks))


# ────────────────────────────────
# 📋 Task CRUD Endpoints
# ────────────────────────────────

@main.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks with optional filtering"""
    try:
        # Get query parameters for filtering
        show_completed = request.args.get('show_completed', 'false').lower() == 'true'
        priority_filter = request.args.get('priority')
        
        # Base query
        query = Task.query
        
        # Apply filters
        if not show_completed:
            query = query.filter(Task.completed == False)
        
        if priority_filter and priority_filter.isdigit():
            priority = int(priority_filter)
            if priority in [1, 2, 3]:
                query = query.filter(Task.priority == priority)
        
        # Order by priority and creation date
        tasks = query.order_by(Task.priority.asc(), Task.created_at.desc()).all()
        
        tasks_list = [task.to_dict() for task in tasks]
        
        return jsonify({
            'tasks': tasks_list,
            'total': len(tasks_list),
            'filters_applied': {
                'show_completed': show_completed,
                'priority_filter': priority_filter
            }
        }), 200
        
    except SQLAlchemyError as e:
        print(f"❌ Database error in get_tasks: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        print(f"❌ Unexpected error in get_tasks: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500


@main.route('/api/tasks', methods=['POST'])
def add_task():
    """Add a new task with comprehensive debugging and error handling"""
    print("🔍 POST /api/tasks called")
    print(f"Content-Type: {request.content_type}")
    print(f"Request data: {request.get_data()}")
    
    try:
        # Check if request contains JSON data
        if not request.is_json:
            print("❌ Request is not JSON")
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.get_json()
        print(f"📝 Parsed JSON data: {data}")
        
        if not data:
            print("❌ No JSON data provided")
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Validate required fields
        title = data.get('title', '').strip()
        print(f"🏷️ Title: '{title}'")
        
        if not title:
            print("❌ Title is empty")
            return jsonify({"error": "Task title is required"}), 400
        
        # Check title length
        if len(title) > 200:
            print("❌ Title too long")
            return jsonify({"error": "Task title too long (max 200 characters)"}), 400
        
        # Validate estimated time
        estimated_time = data.get('estimated_time', 30)
        print(f"⏱️ Estimated time: {estimated_time}")
        
        try:
            estimated_time = int(estimated_time)
            if estimated_time <= 0:
                print("❌ Estimated time is not positive")
                return jsonify({"error": "Estimated time must be positive"}), 400
            if estimated_time > 1440:  # More than 24 hours
                print("❌ Estimated time exceeds 24 hours")
                return jsonify({"error": "Estimated time cannot exceed 24 hours (1440 minutes)"}), 400
        except (ValueError, TypeError):
            print("❌ Estimated time is not a valid number")
            return jsonify({"error": "Estimated time must be a valid number"}), 400
        
        # Validate priority
        priority = data.get('priority', 2)
        print(f"🎯 Priority: {priority}")
        
        try:
            priority = int(priority)
            if priority not in [1, 2, 3]:
                priority = 2
        except (ValueError, TypeError):
            priority = 2
        
        # Handle deadline with better error handling
        deadline = None
        deadline_str = data.get('deadline')
        print(f"📅 Deadline string: {deadline_str}")
        
        if deadline_str and deadline_str.strip():
            try:
                # Handle both date and datetime strings
                if 'T' in deadline_str:  # ISO datetime format
                    deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00')).date()
                else:  # Date only format
                    deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
                
                print(f"📅 Parsed deadline: {deadline}")
                
                # Check if deadline is in the past
                if deadline < datetime.now().date():
                    print("❌ Deadline is in the past")
                    return jsonify({"error": "Deadline cannot be in the past"}), 400
                    
            except ValueError as e:
                print(f"❌ Deadline parsing error: {e}")
                return jsonify({"error": f"Invalid deadline format. Use YYYY-MM-DD or ISO format: {str(e)}"}), 400
        
        # Check for duplicate titles (case-insensitive)
        existing_task = Task.query.filter(
            and_(
                func.lower(Task.title) == func.lower(title), 
                Task.completed == False
            )
        ).first()
        
        if existing_task:
            print(f"❌ Duplicate task found: {existing_task.id}")
            return jsonify({
                "error": "An active task with this title already exists",
                "existing_task_id": existing_task.id
            }), 400
        
        # Create new task
        print("✨ Creating new task...")
        new_task = Task(
            title=title,
            estimated_time=estimated_time,
            priority=priority,
            deadline=deadline
        )
        
        # Add to database
        db.session.add(new_task)
        db.session.commit()
        
        print(f"✅ Task created successfully: ID={new_task.id}, Title='{new_task.title}'")
        
        return jsonify({
            "success": True,
            "message": "Task added successfully",
            "task": new_task.to_dict()
        }), 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"❌ Database error in add_task: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        db.session.rollback()
        print(f"❌ Unexpected error in add_task: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@main.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a specific task"""
    print(f"🗑️ DELETE /api/tasks/{task_id} called")
    
    try:
        task = Task.query.get(task_id)
        
        if not task:
            print(f"❌ Task {task_id} not found")
            return jsonify({"error": "Task not found"}), 404
        
        task_title = task.title
        db.session.delete(task)
        db.session.commit()
        
        print(f"✅ Task {task_id} deleted successfully")
        
        return jsonify({
            "message": f"Task '{task_title}' deleted successfully",
            "deleted_task_id": task_id
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"❌ Database error in delete_task: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        db.session.rollback()
        print(f"❌ Unexpected error in delete_task: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500


@main.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update a specific task"""
    print(f"✏️ PUT /api/tasks/{task_id} called")
    
    try:
        task = Task.query.get(task_id)
        
        if not task:
            print(f"❌ Task {task_id} not found")
            return jsonify({"error": "Task not found"}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        print(f"📝 Update data: {data}")
        
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
        
        print(f"✅ Task {task_id} updated successfully")
        
        return jsonify({
            "message": "Task updated successfully",
            "task": task.to_dict()
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"❌ Database error in update_task: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        db.session.rollback()
        print(f"❌ Unexpected error in update_task: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500


# ────────────────────────────────
# ✅ Task Completion Routes
# ────────────────────────────────

@main.route('/api/tasks/<int:task_id>/complete', methods=['POST'])
def complete_task_route(task_id):
    """Mark a task as completed and award XP"""
    print(f"🎯 POST /api/tasks/{task_id}/complete called")
    
    try:
        task = Task.query.get(task_id)
        
        if not task:
            print(f"❌ Task {task_id} not found")
            return jsonify({"error": "Task not found"}), 404
        
        if task.completed:
            print(f"❌ Task {task_id} already completed")
            return jsonify({"error": "Task is already completed"}), 400
        
        data = request.get_json() or {}
        actual_time = data.get('actual_time')
        focus_sessions = data.get('focus_sessions', 1)
        
        print(f"⏱️ Actual time: {actual_time}, Focus sessions: {focus_sessions}")
        
        # Mark task as completed
        task.completed = True
        task.completed_at = datetime.now()
        
        # Set actual time if provided
        if hasattr(task, 'actual_time') and actual_time:
            task.actual_time = actual_time
        if hasattr(task, 'focus_sessions'):
            task.focus_sessions = focus_sessions
        
        # Get or create user stats
        user_stats = UserStats.query.filter_by(user_id='default_user').first()
        if not user_stats:
            user_stats = UserStats(user_id='default_user')
            db.session.add(user_stats)
        
        # Update user stats
        user_stats.total_tasks_completed += 1
        user_stats.total_focus_time += actual_time or task.estimated_time
        
        # Update streak if method exists
        if hasattr(user_stats, 'update_streak'):
            user_stats.update_streak()
        
        # Calculate XP
        base_xp = 10
        priority_bonus = {1: 15, 2: 10, 3: 5}[task.priority]
        focus_bonus = min((actual_time or task.estimated_time) // 15, 10)
        deadline_bonus = 5 if task.deadline and task.deadline >= datetime.now().date() else 0
        
        total_xp = base_xp + priority_bonus + focus_bonus + deadline_bonus
        
        # Add XP to user stats
        if hasattr(user_stats, 'add_xp'):
            leveled_up = user_stats.add_xp(total_xp)
        else:
            old_level = user_stats.level
            user_stats.xp_points += total_xp
            # Simple leveling logic
            new_level = (user_stats.xp_points // 100) + 1
            user_stats.level = new_level
            leveled_up = new_level > old_level
        
        db.session.commit()
        
        print(f"✅ Task {task_id} completed successfully")
        
        return jsonify({
            "message": f"Task '{task.title}' completed successfully!",
            "xp_earned": total_xp,
            "total_xp": user_stats.xp_points,
            "level": user_stats.level,
            "leveled_up": leveled_up,
            "streak": getattr(user_stats, 'current_streak', 0),
            "task": task.to_dict()
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"❌ Database error in complete_task: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        db.session.rollback()
        print(f"❌ Unexpected error in complete_task: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


# ────────────────────────────────
# 📆 Schedule Generator
# ────────────────────────────────

@main.route('/api/generate_schedule', methods=['POST'])
def generate():
    """Generate optimized schedule based on available time"""
    print("📋 POST /api/generate_schedule called")
    
    try:
        data = request.get_json() or {}
        tasks_data = data.get('tasks')
        available_time = data.get('available_time', 0)
        
        print(f"⏰ Available time: {available_time}")
        
        # Validate available_time
        try:
            available_time = int(available_time)
            if available_time <= 0:
                return jsonify({"error": "Available time must be positive"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Available time must be a valid number"}), 400
        
        # If no tasks passed, fetch active tasks from database
        if not tasks_data:
            active_tasks = Task.query.filter(Task.completed == False).order_by(
                Task.priority.asc(), Task.deadline.asc().nullslast()
            ).all()
            tasks_data = [task.to_dict() for task in active_tasks]
        
        if not tasks_data:
            return jsonify({
                "message": "No active tasks available to schedule",
                "schedule": []
            }), 200
        
        print(f"📝 Scheduling {len(tasks_data)} tasks")
        
        # Generate schedule using the scheduler
        schedule = generate_schedule(tasks_data, available_time)
        
        print(f"✅ Schedule generated with {len(schedule)} tasks")
        
        return jsonify({
            "message": "Schedule generated successfully",
            "schedule": schedule,
            "total_tasks": len(schedule),
            "total_time": sum(task.get('allocated_time', task.get('estimated_time', 0)) for task in schedule)
        }), 200
        
    except Exception as e:
        print(f"❌ Error generating schedule: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to generate schedule: {str(e)}"}), 500


@main.route('/api/current_schedule', methods=['GET'])
def current_schedule():
    """Get current day's schedule (active tasks only)"""
    try:
        # Get active tasks ordered by priority for current schedule
        tasks = Task.query.filter(Task.completed == False).order_by(
            Task.priority.asc(), Task.deadline.asc().nullslast()
        ).all()
        
        schedule = []
        for task in tasks:
            is_overdue = False
            if hasattr(task, 'is_overdue'):
                is_overdue = task.is_overdue
            elif task.deadline:
                is_overdue = task.deadline < datetime.now().date()
            
            schedule_item = {
                "id": task.id,
                "title": task.title,
                "allocated_time": task.estimated_time,
                "priority": task.priority,
                "deadline": task.deadline.isoformat() if task.deadline else None,
                "is_overdue": is_overdue
            }
            schedule.append(schedule_item)
        
        return jsonify({
            "schedule": schedule,
            "total_tasks": len(schedule)
        }), 200
        
    except SQLAlchemyError as e:
        print(f"❌ Database error in current_schedule: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        print(f"❌ Unexpected error in current_schedule: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500


# ────────────────────────────────
# 🔁 Schedule Adjustments
# ────────────────────────────────

@main.route('/api/reschedule_task/<int:task_id>', methods=['POST'])
def reschedule_task(task_id):
    """Reschedule a task to tomorrow"""
    print(f"🔄 POST /api/reschedule_task/{task_id} called")
    
    try:
        task = Task.query.get(task_id)
        
        if not task:
            return jsonify({"error": "Task not found"}), 404
        
        # Set deadline to tomorrow if not set, or push existing deadline by 1 day
        if task.deadline:
            task.deadline = task.deadline + timedelta(days=1)
        else:
            task.deadline = (datetime.now().date() + timedelta(days=1))
        
        db.session.commit()
        
        print(f"✅ Task {task_id} rescheduled successfully")
        
        return jsonify({
            "message": f"Task '{task.title}' rescheduled successfully",
            "task": task.to_dict()
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"❌ Database error in reschedule_task: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        db.session.rollback()
        print(f"❌ Unexpected error in reschedule_task: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500


# ────────────────────────────────
# 📊 Statistics API
# ────────────────────────────────

@main.route('/api/stats', methods=['GET'])
def stats():
    """Get dashboard statistics"""
    try:
        # Get all tasks
        all_tasks = Task.query.all()
        active_tasks = [t for t in all_tasks if not t.completed]
        completed_tasks = [t for t in all_tasks if t.completed]
        
        total_tasks = len(all_tasks)
        active_count = len(active_tasks)
        completed_count = len(completed_tasks)
        
        # Count tasks by priority (active only)
        priority_counts = {
            1: sum(1 for t in active_tasks if t.priority == 1),  # High
            2: sum(1 for t in active_tasks if t.priority == 2),  # Medium
            3: sum(1 for t in active_tasks if t.priority == 3),  # Low
        }
        
        # Get user stats
        user_stats = UserStats.query.filter_by(user_id='default_user').first()
        if not user_stats:
            # Create default user stats
            user_stats = UserStats(user_id='default_user')
            db.session.add(user_stats)
            db.session.commit()
        
        # Calculate additional stats
        total_estimated_time = sum(task.estimated_time for task in active_tasks)
        avg_task_time = total_estimated_time // active_count if active_count > 0 else 0
        
        # Tasks due today and this week
        today = datetime.now().date()
        week_from_now = today + timedelta(days=7)
        
        tasks_due_today = sum(1 for t in active_tasks if t.deadline == today)
        tasks_due_this_week = sum(1 for t in active_tasks if t.deadline and today <= t.deadline <= week_from_now)
        
        # Count overdue tasks
        overdue_tasks = 0
        for t in active_tasks:
            if hasattr(t, 'is_overdue'):
                if t.is_overdue:
                    overdue_tasks += 1
            elif t.deadline and t.deadline < today:
                overdue_tasks += 1
        
        return jsonify({
            'total_tasks': total_tasks,
            'active_tasks': active_count,
            'completed_tasks': completed_count,
            'completion_rate': round((completed_count / total_tasks) * 100, 1) if total_tasks > 0 else 0,
            'priority_counts': priority_counts,
            'xp': user_stats.xp_points,
            'level': user_stats.level,
            'streak': getattr(user_stats, 'current_streak', 0),
            'total_estimated_time': total_estimated_time,
            'avg_task_time': avg_task_time,
            'tasks_due_today': tasks_due_today,
            'tasks_due_this_week': tasks_due_this_week,
            'overdue_tasks': overdue_tasks,
            'high_priority_tasks': priority_counts[1],
            'medium_priority_tasks': priority_counts[2],
            'low_priority_tasks': priority_counts[3]
        }), 200
        
    except SQLAlchemyError as e:
        print(f"❌ Database error in stats: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        print(f"❌ Unexpected error in stats: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500


# ────────────────────────────────
# 🔍 Search and Filter
# ────────────────────────────────

@main.route('/api/tasks/search', methods=['GET'])
def search_tasks():
    """Search tasks by title or filter by priority/deadline"""
    try:
        query_text = request.args.get('q', '').strip()
        priority = request.args.get('priority')
        has_deadline = request.args.get('has_deadline')
        show_completed = request.args.get('show_completed', 'false').lower() == 'true'
        
        print(f"🔍 Search: q='{query_text}', priority={priority}, has_deadline={has_deadline}")
        
        tasks_query = Task.query
        
        # Filter by completion status
        if not show_completed:
            tasks_query = tasks_query.filter(Task.completed == False)
        
        # Filter by search query
        if query_text:
            tasks_query = tasks_query.filter(Task.title.ilike(f'%{query_text}%'))
        
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
        
        tasks = tasks_query.order_by(Task.priority.asc(), Task.created_at.desc()).all()
        
        tasks_list = [task.to_dict() for task in tasks]
        
        print(f"✅ Found {len(tasks_list)} tasks")
        
        return jsonify({
            "tasks": tasks_list,
            "total_found": len(tasks_list),
            "search_query": query_text,
            "filters": {
                "priority": priority,
                "has_deadline": has_deadline,
                "show_completed": show_completed
            }
        }), 200
        
    except SQLAlchemyError as e:
        print(f"❌ Database error in search_tasks: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        print(f"❌ Unexpected error in search_tasks: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500


# ────────────────────────────────
# 🎮 Gamification Routes
# ────────────────────────────────

@main.route('/api/user_stats', methods=['GET'])
def get_user_stats():
    """Get detailed user statistics"""
    try:
        user_stats = UserStats.query.filter_by(user_id='default_user').first()
        
        if not user_stats:
            # Create default stats
            user_stats = UserStats(user_id='default_user')
            db.session.add(user_stats)
            db.session.commit()
        
        # Get additional stats
        all_tasks = Task.query.all()
        completed_tasks = [t for t in all_tasks if t.completed]
        
        # Calculate next level XP requirement
        next_level_xp = user_stats.level * 100
        current_level_xp = (user_stats.level - 1) * 100
        progress_to_next = ((user_stats.xp_points - current_level_xp) / (next_level_xp - current_level_xp)) * 100 if next_level_xp > current_level_xp else 0
        
        # Create stats dictionary
        stats_data = {
            'user_id': user_stats.user_id,
            'level': user_stats.level,
            'xp_points': user_stats.xp_points,
            'total_tasks_completed': user_stats.total_tasks_completed,
            'total_focus_time': getattr(user_stats, 'total_focus_time', 0),
            'current_streak': getattr(user_stats, 'current_streak', 0),
            'longest_streak': getattr(user_stats, 'longest_streak', 0),
            'next_level_xp': next_level_xp,
            'progress_to_next_level': round(progress_to_next, 1),
            'total_tasks_in_system': len(all_tasks),
            'completion_percentage': round((len(completed_tasks) / len(all_tasks)) * 100, 1) if all_tasks else 0
        }
        
        return jsonify(stats_data), 200
        
    except SQLAlchemyError as e:
        print(f"❌ Database error in get_user_stats: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        print(f"❌ Unexpected error in get_user_stats: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500


# ────────────────────────────────
# 🗂️ Bulk Operations
# ────────────────────────────────

@main.route('/api/tasks/bulk_delete', methods=['DELETE'])
def bulk_delete_tasks():
    """Delete multiple tasks at once"""
    print("🗑️ POST /api/tasks/bulk_delete called")
    
    try:
        data = request.get_json()
        if not data or 'task_ids' not in data:
            return jsonify({"error": "Task IDs are required"}), 400
        
        task_ids = data['task_ids']
        if not isinstance(task_ids, list):
            return jsonify({"error": "Task IDs must be a list"}), 400
        
        print(f"🗑️ Deleting tasks: {task_ids}")
        
        deleted_tasks = []
        for task_id in task_ids:
            task = Task.query.get(task_id)
            if task:
                deleted_tasks.append(task.title)
                db.session.delete(task)
        
        db.session.commit()
        
        print(f"✅ Deleted {len(deleted_tasks)} tasks")
        
        return jsonify({
            "message": f"Successfully deleted {len(deleted_tasks)} tasks",
            "deleted_count": len(deleted_tasks),
            "deleted_tasks": deleted_tasks
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"❌ Database error in bulk_delete_tasks: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        db.session.rollback()
        print(f"❌ Unexpected error in bulk_delete_tasks: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500


# ────────────────────────────────
# 📈 Analytics
# ────────────────────────────────

@main.route('/api/analytics', methods=['GET'])
def analytics():
    """Get detailed analytics about tasks and productivity"""
    try:
        all_tasks = Task.query.all()
        
        if not all_tasks:
            return jsonify({
                "message": "No tasks available for analytics",
                "analytics": {}
            }), 200
        
        # Basic task stats
        active_tasks = [task for task in all_tasks if not task.completed]
        completed_tasks = [task for task in all_tasks if task.completed]
        
        # Time-based analytics
        total_estimated_time = sum(task.estimated_time for task in active_tasks)
        avg_task_duration = sum(task.estimated_time for task in all_tasks) / len(all_tasks)
        
        # Priority distribution
        priority_dist = {
            "high": sum(1 for t in active_tasks if t.priority == 1),
            "medium": sum(1 for t in active_tasks if t.priority == 2),
            "low": sum(1 for t in active_tasks if t.priority == 3)
        }
        
        # Deadline analytics
        today = datetime.now().date()
        overdue_tasks = 0
        due_today = 0
        due_this_week = 0
        
        for t in active_tasks:
            if t.deadline:
                if t.deadline < today:
                    overdue_tasks += 1
                elif t.deadline == today:
                    due_today += 1
                elif today <= t.deadline <= today + timedelta(days=7):
                    due_this_week += 1
        
        # Task duration distribution
        short_tasks = sum(1 for t in active_tasks if t.estimated_time <= 30)  # <= 30 min
        medium_tasks = sum(1 for t in active_tasks if 30 < t.estimated_time <= 90)  # 30-90 min
        long_tasks = sum(1 for t in active_tasks if t.estimated_time > 90)  # > 90 min
        
        # Calculate completion stats
        completion_stats = {
            "total_completed": len(completed_tasks),
            "completion_rate": round((len(completed_tasks) / len(all_tasks)) * 100, 1),
            "avg_completion_time": round(avg_task_duration, 1)
        }
        
        analytics_data = {
            "total_tasks": len(all_tasks),
            "active_tasks": len(active_tasks),
            "completed_tasks": len(completed_tasks),
            "completion_stats": completion_stats,
            "total_estimated_time": total_estimated_time,
            "avg_task_duration": round(avg_task_duration, 1),
            "priority_distribution": priority_dist,
            "deadline_analytics": {
                "overdue": overdue_tasks,
                "due_today": due_today,
                "due_this_week": due_this_week,
                "no_deadline": sum(1 for t in active_tasks if not t.deadline)
            },
            "duration_distribution": {
                "short_tasks": short_tasks,
                "medium_tasks": medium_tasks,
                "long_tasks": long_tasks
            },
            "productivity_score": calculate_productivity_score(active_tasks)
        }
        
        return jsonify({"analytics": analytics_data}), 200
        
    except Exception as e:
        print(f"❌ Error in analytics: {str(e)}")
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


# ────────────────────────────────
# 🔄 Utility Routes
# ────────────────────────────────

@main.route('/api/reset_data', methods=['POST'])
def reset_data():
    """Reset all user data (for testing purposes)"""
    print("🔄 POST /api/reset_data called")
    
    try:
        data = request.get_json()
        confirm = data.get('confirm', False) if data else False
        
        if not confirm:
            return jsonify({"error": "Confirmation required"}), 400
        
        # Delete all tasks
        Task.query.delete()
        
        # Reset user stats
        user_stats = UserStats.query.filter_by(user_id='default_user').first()
        if user_stats:
            user_stats.total_tasks_completed = 0
            user_stats.total_focus_time = 0 if hasattr(user_stats, 'total_focus_time') else None
            user_stats.current_streak = 0 if hasattr(user_stats, 'current_streak') else None
            user_stats.longest_streak = 0 if hasattr(user_stats, 'longest_streak') else None
            user_stats.xp_points = 0
            user_stats.level = 1
            if hasattr(user_stats, 'last_activity'):
                user_stats.last_activity = None
        
        db.session.commit()
        
        print("✅ Data reset successfully")
        
        return jsonify({
            "message": "All data has been reset successfully"
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"❌ Database error in reset_data: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        db.session.rollback()
        print(f"❌ Unexpected error in reset_data: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500


@main.route('/api/export_data', methods=['GET'])
def export_data():
    """Export all user data as JSON"""
    try:
        # Get all tasks
        all_tasks = Task.query.all()
        tasks_data = [task.to_dict() for task in all_tasks]
        
        # Get user stats
        user_stats = UserStats.query.filter_by(user_id='default_user').first()
        stats_data = {}
        if user_stats:
            stats_data = {
                'user_id': user_stats.user_id,
                'level': user_stats.level,
                'xp_points': user_stats.xp_points,
                'total_tasks_completed': user_stats.total_tasks_completed,
                'total_focus_time': getattr(user_stats, 'total_focus_time', 0),
                'current_streak': getattr(user_stats, 'current_streak', 0),
                'longest_streak': getattr(user_stats, 'longest_streak', 0)
            }
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'tasks': tasks_data,
            'user_stats': stats_data,
            'summary': {
                'total_tasks': len(all_tasks),
                'completed_tasks': sum(1 for t in all_tasks if t.completed),
                'active_tasks': sum(1 for t in all_tasks if not t.completed)
            }
        }
        
        return jsonify(export_data), 200
        
    except Exception as e:
        print(f"❌ Error in export_data: {str(e)}")
        return jsonify({"error": f"Failed to export data: {str(e)}"}), 500


# ────────────────────────────────
# 🧪 Testing Routes
# ────────────────────────────────

@main.route('/api/test', methods=['GET'])
def test_models():
    """Test route to verify models are working"""
    try:
        print("🧪 Testing models...")
        
        # Test Task model
        task_count = Task.query.count()
        print(f"📊 Total tasks in database: {task_count}")
        
        # Test UserStats model  
        user_stats = UserStats.query.filter_by(user_id='default_user').first()
        if user_stats:
            print(f"👤 User stats found: Level {user_stats.level}, XP {user_stats.xp_points}")
        else:
            print("👤 No user stats found")
        
        # Test creating a simple task (without saving)
        try:
            test_task = Task(title="Test Task", estimated_time=30, priority=2)
            test_dict = test_task.to_dict()
            print(f"✅ Task model test passed: {test_dict}")
        except Exception as e:
            print(f"❌ Task model test failed: {e}")
        
        return jsonify({
            "message": "Models are working",
            "task_count": task_count,
            "user_stats_exists": user_stats is not None,
            "database_connected": True
        }), 200
        
    except Exception as e:
        print(f"❌ Model test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Model test failed: {str(e)}"}), 500


# Helper function to calculate streak (if not in model)
def calculate_streak(tasks):
    """Calculate consecutive days streak based on task completion"""
    try:
        completed_tasks = [task for task in tasks if task.completed and hasattr(task, 'completed_at') and task.completed_at]
        
        if not completed_tasks:
            return 0
        
        # Get unique completion dates
        completion_dates = set()
        for task in completed_tasks:
            completion_dates.add(task.completed_at.date())
        
        if not completion_dates:
            return 0
        
        # Sort dates in reverse order (newest first)
        sorted_dates = sorted(completion_dates, reverse=True)
        
        # Calculate streak from today backwards
        today = datetime.now().date()
        streak = 0
        current_date = today
        
        for date in sorted_dates:
            if date == current_date:
                streak += 1
                current_date -= timedelta(days=1)
            elif date == current_date:
                # Continue streak
                continue
            else:
                # Gap found, streak ends
                break
        
        return streak
        
    except Exception:
        return 0