"""Simple health check test for debugging."""

from fastapi.testclient import TestClient

from app.main import create_app


def test_simple_health_basic():
    """Basic test without database dependency."""
    app = create_app()
    client = TestClient(app)

    # Test liveness probe (should always work)
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_api_info():
    """Test API info endpoint."""
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/v1")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data


def test_root_endpoint():
    """Test root endpoint."""
    app = create_app()
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


if __name__ == "__main__":
    test_simple_health_basic()
    test_api_info()
    test_root_endpoint()
    print("✅ All simple tests passed!")
