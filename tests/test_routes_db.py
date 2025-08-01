import pytest
from app import create_app, db
from app.models import Task

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",  # In-memory DB for tests
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_crud_tasks(client):
    # Test adding a task
    response = client.post('/tasks', json={
        "title": "Test Task",
        "estimated_time": 60,
        "priority": 1,
        "deadline": "2025-08-01"
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "Task added"
    task_id = data["task"]["id"]

    # Test getting tasks
    response = client.get('/tasks')
    assert response.status_code == 200
    tasks = response.get_json()["tasks"]
    assert any(t["id"] == task_id for t in tasks)

    # Test deleting the task
    response = client.delete(f'/tasks/{task_id}')
    assert response.status_code == 200
    assert f"Task with id {task_id} deleted" in response.get_json()["message"]

    # Confirm deletion
    response = client.get('/tasks')
    tasks = response.get_json()["tasks"]
    assert not any(t["id"] == task_id for t in tasks)

def test_generate_schedule_endpoint(client):
    # Add multiple tasks
    client.post('/tasks', json={
        "title": "Task 1",
        "estimated_time": 30,
        "priority": 1
    })
    client.post('/tasks', json={
        "title": "Task 2",
        "estimated_time": 60,
        "priority": 2
    })

    # Call schedule generation without tasks (should use DB tasks)
    response = client.post('/generate_schedule', json={"available_time": 45})
    assert response.status_code == 200
    schedule = response.get_json()["schedule"]
    # Should only include Task 1 because it fits within 45 minutes
    assert any(t["title"] == "Task 1" for t in schedule)
    assert not any(t["title"] == "Task 2" for t in schedule)
