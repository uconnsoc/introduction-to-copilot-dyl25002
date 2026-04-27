import copy
import sys
from pathlib import Path
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from app import app, activities  # noqa: E402

client = TestClient(app)
initial_activities = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    activities.clear()
    activities.update(copy.deepcopy(initial_activities))


def test_root_redirects_to_static_index():
    response = client.get("/")

    assert response.status_code == 200
    assert "/static/index.html" in response.url.path


def test_get_activities_returns_all_activities():
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == initial_activities


def test_signup_for_activity_adds_participant():
    new_email = "newstudent@mergington.edu"
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": new_email},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {new_email} for Chess Club"}
    assert new_email in activities["Chess Club"]["participants"]


def test_signup_for_activity_already_signed_up_returns_400():
    email = initial_activities["Chess Club"]["participants"][0]
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_for_missing_activity_returns_404():
    response = client.post(
        "/activities/Nonexistent Activity/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_removes_existing_participant():
    email = initial_activities["Chess Club"]["participants"][0]
    encoded_email = quote(email, safe="")
    response = client.delete(f"/activities/Chess Club/participants/{encoded_email}")

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    assert email not in activities["Chess Club"]["participants"]


def test_remove_missing_participant_returns_404():
    encoded_email = quote("notregistered@mergington.edu", safe="")
    response = client.delete(f"/activities/Chess Club/participants/{encoded_email}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"


def test_remove_participant_from_missing_activity_returns_404():
    encoded_email = quote("student@mergington.edu", safe="")
    response = client.delete(f"/activities/Nonexistent Activity/participants/{encoded_email}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
