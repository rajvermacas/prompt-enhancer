import sqlite3
import uuid
from datetime import datetime, timedelta

from app.models.auth import Session, User


class DuplicateEmailError(Exception):
    """Raised when attempting to create a user with an existing email."""

    def __init__(self, email: str):
        self.email = email
        super().__init__(f"Email already registered: {email}")


class UserNotFoundError(Exception):
    """Raised when a user is not found."""

    def __init__(self, identifier: str):
        self.identifier = identifier
        super().__init__(f"User not found: {identifier}")


class SessionNotFoundError(Exception):
    """Raised when a session is not found."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"Session not found: {session_id}")


class SessionExpiredError(Exception):
    """Raised when a session has expired."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"Session expired: {session_id}")


SESSION_DURATION_DAYS = 7


def init_db(db_path: str) -> None:
    """Create users and sessions tables if they don't exist."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id),
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def create_user(db_path: str, email: str, password_hash: str) -> User:
    """Insert a new user. Raises DuplicateEmailError if email exists."""
    user_id = f"u-{uuid.uuid4().hex[:8]}"
    created_at = datetime.now()

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO users (id, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (user_id, email, password_hash, created_at.isoformat()),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise DuplicateEmailError(email)
    finally:
        conn.close()

    return User(id=user_id, email=email, created_at=created_at)


def get_user_by_email(db_path: str, email: str) -> User:
    """Look up a user by email. Raises UserNotFoundError if not found."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT id, email, created_at FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise UserNotFoundError(email)

    return User(
        id=row["id"],
        email=row["email"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def get_user_by_id(db_path: str, user_id: str) -> User:
    """Look up a user by ID. Raises UserNotFoundError if not found."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT id, email, created_at FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise UserNotFoundError(user_id)

    return User(
        id=row["id"],
        email=row["email"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def get_password_hash(db_path: str, email: str) -> str:
    """Return the password hash for a user. Raises UserNotFoundError if not found."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT password_hash FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise UserNotFoundError(email)

    return row["password_hash"]


def create_session(db_path: str, user_id: str) -> Session:
    """Create a new session for the given user."""
    session_id = f"s-{uuid.uuid4().hex}"
    now = datetime.now()
    expires_at = now + timedelta(days=SESSION_DURATION_DAYS)

    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO sessions (id, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (session_id, user_id, now.isoformat(), expires_at.isoformat()),
    )
    conn.commit()
    conn.close()

    return Session(id=session_id, user_id=user_id, created_at=now, expires_at=expires_at)


def get_session(db_path: str, session_id: str) -> Session:
    """Retrieve a session. Raises SessionNotFoundError or SessionExpiredError."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(
        "SELECT id, user_id, created_at, expires_at FROM sessions WHERE id = ?",
        (session_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise SessionNotFoundError(session_id)

    expires_at = datetime.fromisoformat(row["expires_at"])
    if expires_at < datetime.now():
        raise SessionExpiredError(session_id)

    return Session(
        id=row["id"],
        user_id=row["user_id"],
        created_at=datetime.fromisoformat(row["created_at"]),
        expires_at=expires_at,
    )


def delete_session(db_path: str, session_id: str) -> None:
    """Delete a session by ID."""
    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()


def delete_expired_sessions(db_path: str) -> None:
    """Remove all expired sessions."""
    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM sessions WHERE expires_at < ?", (datetime.now().isoformat(),))
    conn.commit()
    conn.close()
