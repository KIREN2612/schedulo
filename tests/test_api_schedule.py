from app import create_app

def test_generate_schedule_api():
    app = create_app()
    client = app.test_client()

    data = {
        "available_time": 90,
        "tasks": [
            {"title": "Task A", "estimated_time": 30, "priority": 1, "deadline": "2025-08-05"},
            {"title": "Task B", "estimated_time": 45, "priority": 2, "deadline": "2025-08-10"},
            {"title": "Task C", "estimated_time": 60, "priority": 1, "deadline": "2025-08-01"}
        ]
    }

    response = client.post('/generate_schedule', json=data)
    assert response.status_code == 200

    json_data = response.get_json()
    schedule = json_data.get('schedule', [])
    
    assert len(schedule) == 2
    assert schedule[0]['title'] == "Task C"
    assert schedule[1]['title'] == "Task A"
