from app import main

def test_index():
    client = main.TestClient(app)
    response = client.get('/')
    assert response.status_code == 200
