from app import create_app
import json

def test_get_tasks_empty():
    app = create_app()
    client = app.test_client()

    response = client.get('/tasks')
    assert response.status_code == 200
    assert response.get_json() == {"tasks": []}

def test_add_task():
    app = create_app()
    client = app.test_client()

    task = {
        "title": "New Task",
        "estimated_time": 30,
        "priority": 1
    }

    response = client.post('/tasks', json=task)
    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "Task added"
    assert data["task"] == task

def test_get_tasks_after_adding():
    app = create_app()
    client = app.test_client()

    task = {
        "title": "New Task",
        "estimated_time": 30,
        "priority": 1
    }

    client.post('/tasks', json=task)
    response = client.get('/tasks')
    assert response.status_code == 200
    tasks = response.get_json().get("tasks")
    assert any(t["title"] == "New Task" for t in tasks)

def test_delete_task():
    app = create_app()
    client = app.test_client()

    task = {
        "title": "Delete Me",
        "estimated_time": 15,
        "priority": 2
    }

    client.post('/tasks', json=task)
    response = client.delete(f"/tasks/{task['title']}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == f"Task '{task['title']}' deleted"

def test_delete_nonexistent_task():
    app = create_app()
    client = app.test_client()

    response = client.delete("/tasks/NotExist")
    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "Task not found"
