import pytest


@pytest.fixture
def db_path(tmp_path):
    from app.db import init_db

    path = str(tmp_path / "test_auth.db")
    init_db(path)
    return path


def test_register_user(db_path):
    """register_user creates a new user with hashed password."""
    from app.services.auth_service import AuthService

    service = AuthService(db_path)
    user = service.register_user("test@example.com", "password123")

    assert user.email == "test@example.com"
    assert user.id.startswith("u-")


def test_register_user_duplicate_raises(db_path):
    """register_user raises DuplicateEmailError for duplicate email."""
    from app.services.auth_service import AuthService
    from app.db import DuplicateEmailError

    service = AuthService(db_path)
    service.register_user("test@example.com", "password123")

    with pytest.raises(DuplicateEmailError):
        service.register_user("test@example.com", "password456")


def test_authenticate_user(db_path):
    """authenticate_user returns user for valid credentials."""
    from app.services.auth_service import AuthService

    service = AuthService(db_path)
    service.register_user("test@example.com", "password123")

    user = service.authenticate_user("test@example.com", "password123")
    assert user.email == "test@example.com"


def test_authenticate_user_wrong_password_raises(db_path):
    """authenticate_user raises InvalidCredentialsError for wrong password."""
    from app.services.auth_service import AuthService, InvalidCredentialsError

    service = AuthService(db_path)
    service.register_user("test@example.com", "password123")

    with pytest.raises(InvalidCredentialsError):
        service.authenticate_user("test@example.com", "wrongpassword")


def test_authenticate_user_unknown_email_raises(db_path):
    """authenticate_user raises InvalidCredentialsError for unknown email."""
    from app.services.auth_service import AuthService, InvalidCredentialsError

    service = AuthService(db_path)

    with pytest.raises(InvalidCredentialsError):
        service.authenticate_user("unknown@example.com", "password123")


def test_create_session(db_path):
    """create_session returns a valid session."""
    from app.services.auth_service import AuthService

    service = AuthService(db_path)
    user = service.register_user("test@example.com", "password123")

    session = service.create_session(user.id)
    assert session.user_id == user.id


def test_validate_session(db_path):
    """validate_session returns the user for a valid session."""
    from app.services.auth_service import AuthService

    service = AuthService(db_path)
    user = service.register_user("test@example.com", "password123")
    session = service.create_session(user.id)

    validated_user = service.validate_session(session.id)
    assert validated_user.id == user.id
    assert validated_user.email == "test@example.com"


def test_validate_session_invalid_raises(db_path):
    """validate_session raises SessionNotFoundError for invalid session."""
    from app.services.auth_service import AuthService
    from app.db import SessionNotFoundError

    service = AuthService(db_path)

    with pytest.raises(SessionNotFoundError):
        service.validate_session("nonexistent-session")


def test_logout(db_path):
    """logout deletes the session."""
    from app.services.auth_service import AuthService
    from app.db import SessionNotFoundError

    service = AuthService(db_path)
    user = service.register_user("test@example.com", "password123")
    session = service.create_session(user.id)

    service.logout(session.id)

    with pytest.raises(SessionNotFoundError):
        service.validate_session(session.id)
