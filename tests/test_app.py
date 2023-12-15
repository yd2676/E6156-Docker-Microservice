from app import main

def test_index():
    client = app.test_client()
    response = client.get('/posts')
    assert response.status_code == 200