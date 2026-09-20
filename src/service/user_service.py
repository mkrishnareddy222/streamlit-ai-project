from repo.users_db import register_user, verify_user_login


def register_new_user(username: str, email: str, password: str) -> str | None:
    """Register a user through the users repository."""
    return register_user(
        username=username,
        email=email,
        plaintext_password=password,
    )


def authenticate_user(username_or_email: str, password: str) -> dict | None:
    """Authenticate a user through the users repository."""
    return verify_user_login(
        username_or_email=username_or_email,
        plaintext_password=password,
    )
