from flask import Blueprint, jsonify, request, current_app,render_template
from core.scheduler import generate_schedule
from app.models import Task, db
from datetime import datetime,timedelta

main = Blueprint('main', __name__)

@main.route('/ping', methods=['GET'])
def ping():
    return jsonify({"message": "pong"})

@main.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    tasks_list = [ 
        {
            "id": task.id,
            "title": task.title,
            "estimated_time": task.estimated_time,
            "priority": task.priority,
            "deadline": task.deadline,
        } for task in tasks
    ]
    return jsonify({"tasks": tasks_list}), 200

@main.route('/tasks', methods=['POST'])
def add_task():
    data = request.get_json()
    required_fields = {'title', 'estimated_time', 'priority'}

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required task fields"}), 400

    new_task = Task(
        title=data['title'],
        estimated_time=data['estimated_time'],
        priority=data['priority'],
        deadline=data.get('deadline')
    )

    db.session.add(new_task)
    db.session.commit()

    return jsonify({"message": "Task added", "task": {
        "id": new_task.id,
        "title": new_task.title,
        "estimated_time": new_task.estimated_time,
        "priority": new_task.priority,
        "deadline": new_task.deadline
    }}), 201

@main.route('/tasks/<int:id>', methods=['DELETE'])
def delete_task(id):
    task = Task.query.get(id)
    if task:
        db.session.delete(task)
        db.session.commit()
        return jsonify({"message": f"Task with id {id} deleted"}), 200
    else:
        return jsonify({"error": "Task not found"}), 404

@main.route('/generate_schedule', methods=['POST'])
def generate():
    try:
        data = request.get_json() or {}
        tasks = data.get('tasks')
        available_time = data.get('available_time', 0)

        # If no tasks passed, fetch from DB
        if not tasks:
            all_tasks = Task.query.all()
            tasks = [
                {
                    "title": t.title,
                    "estimated_time": t.estimated_time,
                    "priority": t.priority,
                    "deadline": t.deadline,
                } for t in all_tasks
            ]

        if not isinstance(tasks, list) or not isinstance(available_time, int):
            return jsonify({"error": "Invalid input format"}), 400

        schedule = generate_schedule(tasks, available_time)
        return jsonify({"schedule": schedule}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/stats', methods=['GET'])
def stats():
    tasks = Task.query.all()

    total_tasks = len(tasks)
    priority_counts = {
        'High': sum(1 for t in tasks if t.priority == 1),
        'Medium': sum(1 for t in tasks if t.priority == 2),
        'Low': sum(1 for t in tasks if t.priority == 3),
    }

    # XP: 10 points per task
    xp = total_tasks * 10

    # Streak (based on days with tasks)
    today = datetime.today().date()
    dates = set()
    for task in tasks:
        if task.deadline:
            try:
                task_date = datetime.strptime(task.deadline, "%Y-%m-%d").date()
                dates.add(task_date)
            except:
                continue
    streak = 0
    current = today
    while current in dates:
        streak += 1
        current -= timedelta(days=1)

    return jsonify({
        'total_tasks': total_tasks,
        'priority_counts': priority_counts,
        'xp': xp,
        'streak': streak
    }), 200
