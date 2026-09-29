import base64
from auth import is_authorized


def make_header(username, password):
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return f"Basic {token}"


def test_correct_credentials():
    assert is_authorized(make_header("admin", "password123")) is True


def test_wrong_password():
    assert is_authorized(make_header("admin", "wrong")) is False


def test_wrong_username():
    assert is_authorized(make_header("bob", "password123")) is False


def test_missing_header():
    assert is_authorized(None) is False
    assert is_authorized("") is False


def test_not_basic_scheme():
    assert is_authorized("Bearer sometoken") is False


def test_garbage_base64():
    assert is_authorized("Basic !!!not-base64!!!") is False


def test_no_colon_in_decoded():
    token = base64.b64encode(b"adminpassword123").decode()
    assert is_authorized(f"Basic {token}") is False


if __name__ == "__main__":
    test_correct_credentials()
    test_wrong_password()
    test_wrong_username()
    test_missing_header()
    test_not_basic_scheme()
    test_garbage_base64()
    test_no_colon_in_decoded()
    print("All auth tests passed")
