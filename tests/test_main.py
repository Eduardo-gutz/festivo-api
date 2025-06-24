from fastapi.testclient import TestClient

def test_root_endpoint(client):
    """Test que verifica que el endpoint principal responde correctamente"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "¡Bienvenido a Festivo API!"} 