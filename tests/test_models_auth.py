import pytest
from datetime import datetime


def test_user_model():
    """User model holds id, email, created_at without password."""
    from app.models.auth import User

    user = User(id="u-abc123", email="test@example.com", created_at=datetime.now())
    assert user.id == "u-abc123"
    assert user.email == "test@example.com"
    assert isinstance(user.created_at, datetime)


def test_user_create_model():
    """UserCreate holds email and password for registration."""
    from app.models.auth import UserCreate

    data = UserCreate(email="test@example.com", password="secret123")
    assert data.email == "test@example.com"
    assert data.password == "secret123"


def test_user_login_model():
    """UserLogin holds email and password for login."""
    from app.models.auth import UserLogin

    data = UserLogin(email="test@example.com", password="secret123")
    assert data.email == "test@example.com"
    assert data.password == "secret123"


def test_session_model():
    """Session holds id, user_id, created_at, expires_at."""
    from app.models.auth import Session

    now = datetime.now()
    session = Session(id="s-abc", user_id="u-abc", created_at=now, expires_at=now)
    assert session.id == "s-abc"
    assert session.user_id == "u-abc"


def test_user_create_missing_email_raises():
    """UserCreate raises ValidationError when email is missing."""
    from pydantic import ValidationError
    from app.models.auth import UserCreate

    with pytest.raises(ValidationError):
        UserCreate(password="secret123")


def test_user_create_missing_password_raises():
    """UserCreate raises ValidationError when password is missing."""
    from pydantic import ValidationError
    from app.models.auth import UserCreate

    with pytest.raises(ValidationError):
        UserCreate(email="test@example.com")


def test_user_role_enum_values():
    """UserRole enum has USER and APPROVER values."""
    from app.models.auth import UserRole

    assert UserRole.USER.value == "USER"
    assert UserRole.APPROVER.value == "APPROVER"


def test_user_has_role_field():
    """User model has role field defaulting to USER."""
    from app.models.auth import User, UserRole

    user = User(
        id="u-12345678",
        email="test@example.com",
        created_at=datetime.now(),
    )

    assert user.role == UserRole.USER


def test_user_can_be_approver():
    """User model can have APPROVER role."""
    from app.models.auth import User, UserRole

    user = User(
        id="u-12345678",
        email="test@example.com",
        created_at=datetime.now(),
        role=UserRole.APPROVER,
    )

    assert user.role == UserRole.APPROVER
