import base64
import hmac

# Simple credentials for this school project only.
# In a real system these would never be hardcoded in the source.
VALID_USERNAME = "admin"
VALID_PASSWORD = "password123"


def is_authorized(auth_header):
    """Return True if the Authorization header has valid Basic Auth credentials."""
    if not auth_header:
        return False

    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "basic":
        return False

    try:
        decoded = base64.b64decode(parts[1].strip()).decode("utf-8")
    except Exception:
        return False

    if ":" not in decoded:
        return False

    username, password = decoded.split(":", 1)

    # compare_digest avoids timing differences when comparing secrets
    user_ok = hmac.compare_digest(username, VALID_USERNAME)
    pass_ok = hmac.compare_digest(password, VALID_PASSWORD)
    return user_ok and pass_ok
