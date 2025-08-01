from flask import Blueprint, jsonify, request
from core.scheduler import generate_schedule

main = Blueprint('main', __name__)

@main.route('/ping', methods=['GET'])
def ping():
    return jsonify({"message": "pong"})

@main.route('/generate_schedule', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        tasks = data.get('tasks', [])
        available_time = data.get('available_time', 0)

        if not isinstance(tasks, list) or not isinstance(available_time, int):
            return jsonify({"error": "Invalid input format"}), 400

        schedule = generate_schedule(tasks, available_time)
        return jsonify({"schedule": schedule}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
