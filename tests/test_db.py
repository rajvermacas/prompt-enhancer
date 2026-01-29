import pytest
from datetime import datetime, timedelta


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_auth.db")


def test_init_db_creates_tables(db_path):
    """init_db creates users and sessions tables."""
    from app.db import init_db
    import sqlite3

    init_db(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()

    assert "users" in tables
    assert "sessions" in tables


def test_create_user(db_path):
    """create_user inserts a user and returns User model."""
    from app.db import init_db, create_user

    init_db(db_path)
    user = create_user(db_path, "test@example.com", "hashed_pw")

    assert user.email == "test@example.com"
    assert user.id.startswith("u-")


def test_create_user_duplicate_email_raises(db_path):
    """create_user raises exception for duplicate email."""
    from app.db import init_db, create_user, DuplicateEmailError

    init_db(db_path)
    create_user(db_path, "test@example.com", "hashed_pw")

    with pytest.raises(DuplicateEmailError):
        create_user(db_path, "test@example.com", "hashed_pw2")


def test_get_user_by_email(db_path):
    """get_user_by_email returns the user for a valid email."""
    from app.db import init_db, create_user, get_user_by_email

    init_db(db_path)
    create_user(db_path, "test@example.com", "hashed_pw")

    user = get_user_by_email(db_path, "test@example.com")
    assert user.email == "test@example.com"


def test_get_user_by_email_not_found_raises(db_path):
    """get_user_by_email raises exception for unknown email."""
    from app.db import init_db, get_user_by_email, UserNotFoundError

    init_db(db_path)

    with pytest.raises(UserNotFoundError):
        get_user_by_email(db_path, "nonexistent@example.com")


def test_get_password_hash(db_path):
    """get_password_hash returns the stored hash for a user email."""
    from app.db import init_db, create_user, get_password_hash

    init_db(db_path)
    create_user(db_path, "test@example.com", "hashed_pw_123")

    password_hash = get_password_hash(db_path, "test@example.com")
    assert password_hash == "hashed_pw_123"


def test_get_user_by_id(db_path):
    """get_user_by_id returns the user for a valid ID."""
    from app.db import init_db, create_user, get_user_by_id

    init_db(db_path)
    created = create_user(db_path, "test@example.com", "hashed_pw")

    user = get_user_by_id(db_path, created.id)
    assert user.email == "test@example.com"
    assert user.id == created.id


def test_get_user_by_id_not_found_raises(db_path):
    """get_user_by_id raises exception for unknown ID."""
    from app.db import init_db, get_user_by_id, UserNotFoundError

    init_db(db_path)

    with pytest.raises(UserNotFoundError):
        get_user_by_id(db_path, "u-nonexistent")


def test_create_session(db_path):
    """create_session inserts a session and returns Session model."""
    from app.db import init_db, create_user, create_session

    init_db(db_path)
    user = create_user(db_path, "test@example.com", "hashed_pw")

    session = create_session(db_path, user.id)
    assert session.user_id == user.id
    assert session.id.startswith("s-")


def test_get_session(db_path):
    """get_session returns a valid, non-expired session."""
    from app.db import init_db, create_user, create_session, get_session

    init_db(db_path)
    user = create_user(db_path, "test@example.com", "hashed_pw")
    created = create_session(db_path, user.id)

    retrieved = get_session(db_path, created.id)
    assert retrieved.id == created.id
    assert retrieved.user_id == user.id


def test_get_session_not_found_raises(db_path):
    """get_session raises exception for unknown session ID."""
    from app.db import init_db, get_session, SessionNotFoundError

    init_db(db_path)

    with pytest.raises(SessionNotFoundError):
        get_session(db_path, "nonexistent-session")


def test_get_session_expired_raises(db_path):
    """get_session raises exception for expired session."""
    from app.db import init_db, create_user, get_session, SessionExpiredError
    import sqlite3

    init_db(db_path)
    user = create_user(db_path, "test@example.com", "hashed_pw")

    expired_at = (datetime.now() - timedelta(hours=1)).isoformat()
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO sessions (id, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        ("s-expired", user.id, datetime.now().isoformat(), expired_at),
    )
    conn.commit()
    conn.close()

    with pytest.raises(SessionExpiredError):
        get_session(db_path, "s-expired")


def test_delete_session(db_path):
    """delete_session removes the session."""
    from app.db import init_db, create_user, create_session, delete_session, get_session, SessionNotFoundError

    init_db(db_path)
    user = create_user(db_path, "test@example.com", "hashed_pw")
    session = create_session(db_path, user.id)

    delete_session(db_path, session.id)

    with pytest.raises(SessionNotFoundError):
        get_session(db_path, session.id)


def test_delete_expired_sessions(db_path):
    """delete_expired_sessions purges only expired sessions."""
    from app.db import init_db, create_user, create_session, delete_expired_sessions
    import sqlite3

    init_db(db_path)
    user = create_user(db_path, "test@example.com", "hashed_pw")

    valid_session = create_session(db_path, user.id)

    expired_at = (datetime.now() - timedelta(hours=1)).isoformat()
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO sessions (id, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        ("s-expired", user.id, datetime.now().isoformat(), expired_at),
    )
    conn.commit()
    conn.close()

    delete_expired_sessions(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT COUNT(*) FROM sessions")
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 1


# --- Role-related tests ---


def test_create_user_stores_role(db_path):
    """create_user stores the specified role in the database."""
    from app.db import init_db, create_user
    from app.models.auth import UserRole

    init_db(db_path)
    user = create_user(db_path, "approver@example.com", "hashed_pw", role=UserRole.APPROVER)

    assert user.role == UserRole.APPROVER


def test_create_user_defaults_to_user_role(db_path):
    """create_user defaults to USER role when no role is provided."""
    from app.db import init_db, create_user
    from app.models.auth import UserRole

    init_db(db_path)
    user = create_user(db_path, "test@example.com", "hashed_pw")

    assert user.role == UserRole.USER


def test_get_user_by_email_includes_role(db_path):
    """get_user_by_email returns User with role populated."""
    from app.db import init_db, create_user, get_user_by_email
    from app.models.auth import UserRole

    init_db(db_path)
    create_user(db_path, "approver@example.com", "hashed_pw", role=UserRole.APPROVER)

    user = get_user_by_email(db_path, "approver@example.com")
    assert user.role == UserRole.APPROVER


def test_get_user_by_id_includes_role(db_path):
    """get_user_by_id returns User with role populated."""
    from app.db import init_db, create_user, get_user_by_id
    from app.models.auth import UserRole

    init_db(db_path)
    created = create_user(db_path, "approver@example.com", "hashed_pw", role=UserRole.APPROVER)

    user = get_user_by_id(db_path, created.id)
    assert user.role == UserRole.APPROVER


def test_update_user_role(db_path):
    """update_user_role changes the role of an existing user."""
    from app.db import init_db, create_user, update_user_role, get_user_by_id
    from app.models.auth import UserRole

    init_db(db_path)
    user = create_user(db_path, "test@example.com", "hashed_pw")
    assert user.role == UserRole.USER

    update_user_role(db_path, user.id, UserRole.APPROVER)

    updated_user = get_user_by_id(db_path, user.id)
    assert updated_user.role == UserRole.APPROVER


def test_update_user_role_raises_for_nonexistent_user(db_path):
    """update_user_role raises UserNotFoundError for unknown user."""
    from app.db import init_db, update_user_role, UserNotFoundError
    from app.models.auth import UserRole

    init_db(db_path)

    with pytest.raises(UserNotFoundError):
        update_user_role(db_path, "u-nonexistent", UserRole.APPROVER)


def test_get_all_users(db_path):
    """get_all_users returns list of all users."""
    from app.db import init_db, create_user, get_all_users
    from app.models.auth import UserRole

    init_db(db_path)
    create_user(db_path, "user1@example.com", "hashed_pw", role=UserRole.USER)
    create_user(db_path, "user2@example.com", "hashed_pw", role=UserRole.APPROVER)

    users = get_all_users(db_path)
    assert len(users) == 2
    emails = {u.email for u in users}
    assert emails == {"user1@example.com", "user2@example.com"}


def test_get_all_users_empty(db_path):
    """get_all_users returns empty list when no users exist."""
    from app.db import init_db, get_all_users

    init_db(db_path)

    users = get_all_users(db_path)
    assert users == []


def test_count_approvers(db_path):
    """count_approvers returns count of users with APPROVER role."""
    from app.db import init_db, create_user, count_approvers
    from app.models.auth import UserRole

    init_db(db_path)
    create_user(db_path, "user1@example.com", "hashed_pw", role=UserRole.USER)
    create_user(db_path, "approver1@example.com", "hashed_pw", role=UserRole.APPROVER)
    create_user(db_path, "approver2@example.com", "hashed_pw", role=UserRole.APPROVER)

    count = count_approvers(db_path)
    assert count == 2


def test_count_approvers_zero(db_path):
    """count_approvers returns 0 when no approvers exist."""
    from app.db import init_db, create_user, count_approvers
    from app.models.auth import UserRole

    init_db(db_path)
    create_user(db_path, "user@example.com", "hashed_pw", role=UserRole.USER)

    count = count_approvers(db_path)
    assert count == 0


def test_is_first_user_true_when_no_users(db_path):
    """is_first_user returns True when no users exist."""
    from app.db import init_db, is_first_user

    init_db(db_path)

    assert is_first_user(db_path) is True


def test_is_first_user_false_when_users_exist(db_path):
    """is_first_user returns False when at least one user exists."""
    from app.db import init_db, create_user, is_first_user

    init_db(db_path)
    create_user(db_path, "test@example.com", "hashed_pw")

    assert is_first_user(db_path) is False
