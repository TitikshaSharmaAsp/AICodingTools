import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


def test_root_redirect():
    response = client.get("/")
    assert response.status_code == 200
    # Since it's a redirect to static, but TestClient follows redirects by default
    # Actually, RedirectResponse to /static/index.html, but since static is mounted, it might serve the file.
    # But for test, perhaps check if it redirects or serves.
    # The root returns RedirectResponse to /static/index.html
    # But TestClient might follow it.
    # To test redirect, use follow_redirects=False
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307  # Temporary redirect
    assert response.headers["location"] == "/static/index.html"


def test_get_activities():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Basketball" in data
    assert "description" in data["Basketball"]
    assert "schedule" in data["Basketball"]
    assert "max_participants" in data["Basketball"]
    assert "participants" in data["Basketball"]


def test_signup_for_activity():
    # Test successful signup
    response = client.post("/activities/Basketball/signup?email=test@example.com")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Signed up test@example.com for Basketball" in data["message"]

    # Check that the participant was added
    response = client.get("/activities")
    data = response.json()
    assert "test@example.com" in data["Basketball"]["participants"]

    # Test signup for non-existent activity
    response = client.post("/activities/NonExistent/signup?email=test@example.com")
    assert response.status_code == 404
    data = response.json()
    assert "Activity not found" in data["detail"]

    # Test duplicate signup
    response = client.post("/activities/Basketball/signup?email=test@example.com")
    assert response.status_code == 400
    data = response.json()
    assert "Student already signed up for this activity" in data["detail"]


def test_unregister_participant():
    # First, sign up a participant
    client.post("/activities/Soccer/signup?email=unregister@example.com")

    # Now unregister
    response = client.request("DELETE", "/activities/Soccer/participants?email=unregister@example.com")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Unregistered unregister@example.com from Soccer" in data["message"]

    # Check that the participant was removed
    response = client.get("/activities")
    data = response.json()
    assert "unregister@example.com" not in data["Soccer"]["participants"]

    # Test unregister from non-existent activity
    response = client.request("DELETE", "/activities/NonExistent/participants?email=test@example.com")
    assert response.status_code == 404
    data = response.json()
    assert "Activity not found" in data["detail"]

    # Test unregister not signed up
    response = client.request("DELETE", "/activities/Soccer/participants?email=notsigned@example.com")
    assert response.status_code == 400
    data = response.json()
    assert "Student not signed up for this activity" in data["detail"]