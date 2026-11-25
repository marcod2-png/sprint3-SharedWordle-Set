# CMSC 447 - Shared-State Wordle

# Shared test fixtures. Test will run against local Supabase stack. Making
# players, test client, and game is written here once and available for every
# Players, games do not persist across tests
# Please ensure that you have ran:
#   $ supabase start
# and are using the rights keys in .env

import os
import uuid
import pytest
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

from flask_server import app as flask_app   # noqa: E402
from db import admin, rows                  # noqa: E402

PASSWORD = "password123"

# This tests creates a new player with a random username and
# returns their id, username, token, and request headers
def _register_player() -> dict:
    client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_PUBLISHABLE_KEY"])
    username = f"test_{uuid.uuid4().hex[:10]}"
    res = client.auth.sign_up({
        "email": f"{username}@test.local",
        "password": PASSWORD,
        "options": {"data": {"username": username}},
    })

    assert res.user is not None
    assert res.session is not None # Only works with enable_confirmations = false [config.toml]

    token = res.session.access_token
    return {
        "player_id": res.user.id,
        "username": username,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }

# Test fails if supabase isn't up
@pytest.fixture(scope="session", autouse=True)
def check_supabase():
    try:
        admin().table("language").select("language_code").limit(1).execute()
    except Exception:
        pytest.exit("Unable to reach local Supabase")

""" PYTEST TEST CLIENT FIXTURE . NO SERVER NEEDED """

@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c

""" PYTEST PLAYER FIXTURES """

@pytest.fixture
def sofia():
    return _register_player()

@pytest.fixture
def grace():
    return _register_player()

@pytest.fixture
def julia():
    return _register_player()

""" PYTESTS FIXTURES FOR DIRECT DATABASE ACCESS """

@pytest.fixture
def db():
    return admin()

@pytest.fixture
def db_rows():
    return rows