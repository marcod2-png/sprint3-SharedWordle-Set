import pytest
from helpers import verify_user


class TestVerifyUser:

    TEST_PASSWORD = "password123"

    @pytest.mark.parametrize("username", [
        "pixel_penguin",
        "saffron_sloth",
        "greenstreak"
    ])

    def test_valid_credentials(self, username):
        result = verify_user(username, self.TEST_PASSWORD)

        assert result is not None
        assert result["username"] == username
        assert "user_id" in result

    @pytest.mark.parametrize("username", [
        "pixel_penguin",
        "saffron_sloth",
        "greenstreak"
    ])
    
    def test_invalid_password(self, username):
        result = verify_user(username, "wrong_password")

        assert result is None

    def test_nonexistent_username(self):
        result = verify_user("nonexistent_user", self.TEST_PASSWORD)

        assert result is None