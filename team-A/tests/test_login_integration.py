
import requests

# Flask server address
BASE_URL = "http://127.0.0.1:5000"
TEST_PASSWORD = "password123"


# Test successful login
def test_login_success():

    # Send a POST request to the login endpoint
    response = requests.post(
        f"{BASE_URL}/users/login",
        json={
            "username": "pixel_penguin",
            "password": "password123"
        }
    )

    # Check the API response
    assert response.status_code == 200
    assert response.json()["username"] == "pixel_penguin"


# Test incorrect password
def test_login_invalid_password():

    response = requests.post(
        f"{BASE_URL}/users/login",
        json={
            "username": "pixel_penguin",
            "password": "wrong_password"
        }
    )

    assert response.status_code == 401
    assert response.json()["error"] == "Invalid username or password"


# Test nonexistent username
def test_login_nonexistent_user():

    response = requests.post(
        f"{BASE_URL}/users/login",
        json={
            "username": "nonexistent_user",
            "password": "password123"
        }
    )

    assert response.status_code == 401
    assert response.json()["error"] == "Invalid username or password"
