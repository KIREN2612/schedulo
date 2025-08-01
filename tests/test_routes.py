from app import create_app

def test_ping():
    app = create_app()
    client = app.test_client()
    
    response = client.get('/ping')
    assert response.status_code == 200
    assert response.get_json() == {"message": "pong"}
