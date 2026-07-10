from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_liveness():
    response = client.get("/healthz/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_create_and_get_item():
    payload = {"name": "Widget", "description": "Un widget di prova"}
    create_resp = client.post("/items", json=payload)
    assert create_resp.status_code == 201
    item_id = create_resp.json()["id"]

    get_resp = client.get(f"/items/{item_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Widget"


def test_get_item_not_found():
    response = client.get("/items/9999")
    assert response.status_code == 404


def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"api_requests_total" in response.content
