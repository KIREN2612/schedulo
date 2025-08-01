from core.scheduler import generate_schedule

def test_generate_schedule():
    tasks = [
        {"title": "Task A", "estimated_time": 30, "priority": 1, "deadline": "2025-08-05"},
        {"title": "Task B", "estimated_time": 45, "priority": 2, "deadline": "2025-08-10"},
        {"title": "Task C", "estimated_time": 60, "priority": 1, "deadline": "2025-08-01"},
    ]

    schedule = generate_schedule(tasks, available_time=90)

    assert len(schedule) == 2
    assert schedule[0]['title'] == "Task C"
    assert schedule[1]['title'] == "Task A"
    print("Test function reached!")
