from flask import Blueprint, jsonify, request, current_app
from core.scheduler import generate_schedule

main = Blueprint('main', __name__)

@main.route('/ping', methods=['GET'])
def ping():
    return jsonify({"message": "pong"})

@main.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = current_app.config['TASKS_STORE']
    return jsonify({"tasks": tasks}), 200

@main.route('/tasks', methods=['POST'])
def add_task():
    task = request.get_json()
    required_fields = {'title', 'estimated_time', 'priority'}

    if not all(field in task for field in required_fields):
        return jsonify({"error": "Missing required task fields"}), 400

    current_app.config['TASKS_STORE'].append(task)
    return jsonify({"message": "Task added", "task": task}), 201

@main.route('/tasks/<string:title>', methods=['DELETE'])
def delete_task(title):
    tasks = current_app.config['TASKS_STORE']
    task_to_delete = next((t for t in tasks if t['title'] == title), None)

    if task_to_delete:
        tasks.remove(task_to_delete)
        return jsonify({"message": f"Task '{title}' deleted"}), 200
    else:
        return jsonify({"error": "Task not found"}), 404

@main.route('/generate_schedule', methods=['POST'])
def generate():
    try:
        data = request.get_json() or {}
        tasks = data.get('tasks')
        available_time = data.get('available_time', 0)

        # If no tasks passed, use stored tasks
        if not tasks:
            tasks = current_app.config['TASKS_STORE']

        if not isinstance(tasks, list) or not isinstance(available_time, int):
            return jsonify({"error": "Invalid input format"}), 400

        schedule = generate_schedule(tasks, available_time)
        return jsonify({"schedule": schedule}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
