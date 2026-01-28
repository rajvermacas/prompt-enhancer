# User Login Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add self-registration and login with multi-user workspace isolation.

**Architecture:** SQLite for users/sessions, bcrypt password hashing, cookie-based sessions with FastAPI dependency injection, `user_id` in workspace `metadata.json` for ownership.

**Tech Stack:** Python sqlite3, passlib[bcrypt], FastAPI Depends, Jinja2 templates, Pydantic models.

---

### Task 1: Add passlib[bcrypt] dependency

**Files:**
- Modify: `pyproject.toml:6-16`

**Step 1: Add the dependency**

In `pyproject.toml`, add `"passlib[bcrypt]>=1.7.0"` to the `dependencies` list:

```toml
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "jinja2>=3.1.0",
    "python-multipart>=0.0.9",
    "langchain>=0.3.0",
    "langchain-openai>=0.2.0",
    "langchain-google-genai>=2.0.0",
    "pydantic>=2.9.0",
    "pydantic-settings>=2.5.0",
    "passlib[bcrypt]>=1.7.0",
]
```

**Step 2: Install**

Run: `cd /workspaces/prompt-enhancer && uv sync`
Expected: Successful install with passlib and bcrypt.

**Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: add passlib[bcrypt] dependency for password hashing"
```

---

### Task 2: Create auth Pydantic models

**Files:**
- Create: `app/models/auth.py`
- Test: `tests/test_models_auth.py`

**Step 1: Write the failing test**

Create `tests/test_models_auth.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `cd /workspaces/prompt-enhancer && python -m pytest tests/test_models_auth.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.models.auth'`

**Step 3: Write minimal implementation**

Create `app/models/auth.py`:

```python
from datetime import datetime

from pydantic import BaseModel


class User(BaseModel):
    id: str
    email: str
    created_at: datetime


class UserCreate(BaseModel):
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class Session(BaseModel):
    id: str
    user_id: str
    created_at: datetime
    expires_at: datetime
```

**Step 4: Run test to verify it passes**

Run: `cd /workspaces/prompt-enhancer && python -m pytest tests/test_models_auth.py -v`
Expected: All 6 tests PASS.

**Step 5: Commit**

```bash
git add app/models/auth.py tests/test_models_auth.py
git commit -m "feat: add auth Pydantic models (User, UserCreate, UserLogin, Session)"
```

---

### Task 3: Add AUTH_DB_PATH to config

**Files:**
- Modify: `app/config.py:27-29`
- Modify: `tests/test_config.py` (if it tests required fields)

**Step 1: Write the failing test**

Add to `tests/test_config.py` (or create a new test):

```python
def test_auth_db_path_required(monkeypatch):
    """Settings requires auth_db_path."""
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setenv("NEWS_CSV_PATH", "./data/news.csv")
    monkeypatch.setenv("WORKSPACES_PATH", "./data/workspaces")
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", "./prompts/system.txt")
    monkeypatch.setenv("AUTH_DB_PATH", "./data/auth.db")

    from app.dependencies import get_settings
    get_settings.cache_clear()

    from app.config import Settings
    settings = Settings()

    assert settings.auth_db_path == "./data/auth.db"
```

**Step 2: Run test to verify it fails**

Run: `cd /workspaces/prompt-enhancer && python -m pytest tests/test_config.py::test_auth_db_path_required -v`
Expected: FAIL — field `auth_db_path` not found.

**Step 3: Write minimal implementation**

In `app/config.py`, add `auth_db_path` to the data paths section:

```python
    # Data paths
    news_csv_path: str
    workspaces_path: str
    system_prompt_path: str
    auth_db_path: str
```

**Step 4: Run test to verify it passes**

Run: `cd /workspaces/prompt-enhancer && python -m pytest tests/test_config.py::test_auth_db_path_required -v`
Expected: PASS.

**Step 5: Update .env file**

Add to `.env`:
```
AUTH_DB_PATH=./data/auth.db
```

**Step 6: Update any test fixtures that create Settings**

Any test fixture that sets environment variables for `Settings` must now also set `AUTH_DB_PATH`. Search for `monkeypatch.setenv("WORKSPACES_PATH"` across tests and add `monkeypatch.setenv("AUTH_DB_PATH", str(tmp_path / "auth.db"))` alongside.

Run: `cd /workspaces/prompt-enhancer && python -m pytest tests/ -v`
Expected: All existing tests PASS.

**Step 7: Commit**

```bash
git add app/config.py tests/ .env
git commit -m "feat: add AUTH_DB_PATH to Settings configuration"
```

---

### Task 4: Create database layer (app/db.py)

**Files:**
- Create: `app/db.py`
- Create: `tests/test_db.py`

**Step 1: Write the failing tests**

Create `tests/test_db.py`:

```python
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
    from datetime import datetime, timedelta

    init_db(db_path)
    user = create_user(db_path, "test@example.com", "hashed_pw")

    # Insert an expired session directly
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
    from datetime import datetime, timedelta

    init_db(db_path)
    user = create_user(db_path, "test@example.com", "hashed_pw")

    # Create a valid session
    valid_session = create_session(db_path, user.id)

    # Insert an expired session directly
    expired_at = (datetime.now() - timedelta(hours=1)).isoformat()
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO sessions (id, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        ("s-expired", user.id, datetime.now().isoformat(), expired_at),
    )
    conn.commit()
    conn.close()

    delete_expired_sessions(db_path)

    # Valid session still exists
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT COUNT(*) FROM sessions")
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 1
```

**Step 2: Run tests to verify they fail**

Run: `cd /workspaces/prompt-enhancer && python -m pytest tests/test_db.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.db'`

**Step 3: Write the implementation**

Create `app/db.py`:

```python
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

    def __init__(self, email: str):
        self.email = email
        super().__init__(f"User not found: {email}")


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
```

**Step 4: Run tests to verify they pass**

Run: `cd /workspaces/prompt-enhancer && python -m pytest tests/test_db.py -v`
Expected: All 13 tests PASS.

**Step 5: Commit**

```bash
git add app/db.py tests/test_db.py
git commit -m "feat: add SQLite database layer for users and sessions"
```

---

### Task 5: Create auth service

**Files:**
- Create: `app/services/auth_service.py`
- Create: `tests/test_auth_service.py`

**Step 1: Write the failing tests**

Create `tests/test_auth_service.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `cd /workspaces/prompt-enhancer && python -m pytest tests/test_auth_service.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.auth_service'`

**Step 3: Write the implementation**

Create `app/services/auth_service.py`:

```python
from passlib.hash import bcrypt

from app.db import (
    create_session as db_create_session,
    create_user,
    get_password_hash,
    get_session,
    get_user_by_email,
    delete_session,
    UserNotFoundError,
)
from app.models.auth import Session, User


class InvalidCredentialsError(Exception):
    """Raised when login credentials are invalid."""

    def __init__(self):
        super().__init__("Invalid email or password")


class AuthService:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def register_user(self, email: str, password: str) -> User:
        """Register a new user. Raises DuplicateEmailError if email taken."""
        password_hash = bcrypt.hash(password)
        return create_user(self.db_path, email, password_hash)

    def authenticate_user(self, email: str, password: str) -> User:
        """Authenticate a user. Raises InvalidCredentialsError on failure."""
        try:
            stored_hash = get_password_hash(self.db_path, email)
        except UserNotFoundError:
            raise InvalidCredentialsError()

        if not bcrypt.verify(password, stored_hash):
            raise InvalidCredentialsError()

        return get_user_by_email(self.db_path, email)

    def create_session(self, user_id: str) -> Session:
        """Create a new session for the user."""
        return db_create_session(self.db_path, user_id)

    def validate_session(self, session_id: str) -> User:
        """Validate session and return the user. Raises on invalid/expired."""
        session = get_session(self.db_path, session_id)
        return get_user_by_email(self.db_path, session.user_id)

    def logout(self, session_id: str) -> None:
        """Delete the session."""
        delete_session(self.db_path, session_id)
```

Note: `validate_session` calls `get_user_by_email` using the user_id from the session. However, `get_user_by_email` looks up by email. We need a `get_user_by_id` function. Add it to `app/db.py`:

```python
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
```

Then update `auth_service.py` `validate_session` to use `get_user_by_id`:

```python
from app.db import (
    create_session as db_create_session,
    create_user,
    get_password_hash,
    get_session,
    get_user_by_email,
    get_user_by_id,
    delete_session,
    UserNotFoundError,
)

# ... in validate_session:
    def validate_session(self, session_id: str) -> User:
        session = get_session(self.db_path, session_id)
        return get_user_by_id(self.db_path, session.user_id)
```

**Step 4: Run tests to verify they pass**

Run: `cd /workspaces/prompt-enhancer && python -m pytest tests/test_auth_service.py -v`
Expected: All 9 tests PASS.

**Step 5: Commit**

```bash
git add app/db.py app/services/auth_service.py tests/test_auth_service.py
git commit -m "feat: add auth service with register, login, session management"
```

---

### Task 6: Add user_id to WorkspaceMetadata model

**Files:**
- Modify: `app/models/workspace.py:8-13`
- Modify: `tests/test_models_workspace.py`

**Step 1: Write the failing test**

Add to `tests/test_models_workspace.py`:

```python
def test_workspace_metadata_requires_user_id():
    """WorkspaceMetadata requires user_id field."""
    from pydantic import ValidationError
    from app.models.workspace import WorkspaceMetadata
    from datetime import datetime

    # Should succeed with user_id
    ws = WorkspaceMetadata(
        id="ws-123", name="Test", created_at=datetime.now(), user_id="u-abc"
    )
    assert ws.user_id == "u-abc"

    # Should fail without user_id
    with pytest.raises(ValidationError):
        WorkspaceMetadata(id="ws-123", name="Test", created_at=datetime.now())
```

**Step 2: Run test to verify it fails**

Run: `cd /workspaces/prompt-enhancer && python -m pytest tests/test_models_workspace.py::test_workspace_metadata_requires_user_id -v`
Expected: FAIL — `user_id` field doesn't exist.

**Step 3: Write minimal implementation**

In `app/models/workspace.py`, add `user_id: str`:

```python
from datetime import datetime

from pydantic import BaseModel

from app.models.news import NewsSource


class WorkspaceMetadata(BaseModel):
    id: str
    name: str
    created_at: datetime
    description: str | None = None
    news_source: NewsSource = NewsSource.MERGE
    user_id: str
```

**Step 4: Fix existing tests**

Existing tests that create `WorkspaceMetadata` or call `create_workspace` will now need a `user_id`. Update:

- `tests/test_models_workspace.py` — Add `user_id` to all existing `WorkspaceMetadata` constructions.
- `app/services/workspace_service.py` — `create_workspace` must accept and store `user_id`.
- `tests/test_workspace_service.py` — Pass `user_id` to `create_workspace`.
- `tests/test_routes_workspaces.py` — Tests will be updated in Task 9 (route changes).

Update `app/services/workspace_service.py` `create_workspace`:

```python
    def create_workspace(self, name: str, user_id: str) -> WorkspaceMetadata:
        workspace_id = f"ws-{uuid.uuid4().hex[:8]}"
        workspace_dir = self.workspaces_path / workspace_id

        workspace_dir.mkdir()
        (workspace_dir / "feedback").mkdir()
        (workspace_dir / "evaluation_reports").mkdir()

        metadata = WorkspaceMetadata(
            id=workspace_id,
            name=name,
            created_at=datetime.now(),
            user_id=user_id,
        )

        self._save_metadata(workspace_dir, metadata)
        self._init_empty_prompts(workspace_dir)

        return metadata
```

Add `list_workspaces_for_user` method:

```python
    def list_workspaces_for_user(self, user_id: str) -> list[WorkspaceMetadata]:
        workspaces = []
        for ws_dir in self.workspaces_path.iterdir():
            if ws_dir.is_dir() and (ws_dir / "metadata.json").exists():
                metadata = self._load_metadata(ws_dir)
                if metadata.user_id == user_id:
                    workspaces.append(metadata)
        return sorted(workspaces, key=lambda w: w.created_at, reverse=True)
```

**Step 5: Run all tests to verify they pass**

Run: `cd /workspaces/prompt-enhancer && python -m pytest tests/test_models_workspace.py tests/test_workspace_service.py -v`
Expected: All PASS (after updating test fixtures to include `user_id`).

**Step 6: Commit**

```bash
git add app/models/workspace.py app/services/workspace_service.py tests/test_models_workspace.py tests/test_workspace_service.py
git commit -m "feat: add user_id to WorkspaceMetadata and workspace service"
```

---

### Task 7: Add auth dependencies

**Files:**
- Modify: `app/dependencies.py`
- Create: `tests/test_dependencies_auth.py`

**Step 1: Write the failing tests**

Create `tests/test_dependencies_auth.py`:

```python
import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException


def test_get_current_user_valid_session(tmp_path, monkeypatch):
    """get_current_user returns user when valid session cookie exists."""
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setenv("NEWS_CSV_PATH", str(tmp_path / "news.csv"))
    monkeypatch.setenv("WORKSPACES_PATH", str(tmp_path / "workspaces"))
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", str(tmp_path / "system.txt"))
    monkeypatch.setenv("AUTH_DB_PATH", str(tmp_path / "auth.db"))

    (tmp_path / "news.csv").write_text("id,headline,content\n")
    (tmp_path / "workspaces").mkdir()
    (tmp_path / "system.txt").write_text("Test prompt")

    from app.dependencies import get_settings
    get_settings.cache_clear()

    from app.db import init_db
    db_path = str(tmp_path / "auth.db")
    init_db(db_path)

    from app.services.auth_service import AuthService
    auth = AuthService(db_path)
    user = auth.register_user("test@example.com", "password123")
    session = auth.create_session(user.id)

    from app.dependencies import get_current_user
    request = MagicMock()
    request.cookies = {"session_id": session.id}

    result = get_current_user(request)
    assert result.email == "test@example.com"


def test_get_current_user_no_cookie_raises(tmp_path, monkeypatch):
    """get_current_user raises HTTPException when no session cookie."""
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setenv("NEWS_CSV_PATH", str(tmp_path / "news.csv"))
    monkeypatch.setenv("WORKSPACES_PATH", str(tmp_path / "workspaces"))
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", str(tmp_path / "system.txt"))
    monkeypatch.setenv("AUTH_DB_PATH", str(tmp_path / "auth.db"))

    (tmp_path / "news.csv").write_text("id,headline,content\n")
    (tmp_path / "workspaces").mkdir()
    (tmp_path / "system.txt").write_text("Test prompt")

    from app.dependencies import get_settings
    get_settings.cache_clear()

    from app.db import init_db
    init_db(str(tmp_path / "auth.db"))

    from app.dependencies import get_current_user
    request = MagicMock()
    request.cookies = {}

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(request)
    assert exc_info.value.status_code == 401
```

**Step 2: Run tests to verify they fail**

Run: `cd /workspaces/prompt-enhancer && python -m pytest tests/test_dependencies_auth.py -v`
Expected: FAIL — `get_current_user` not defined.

**Step 3: Write the implementation**

Update `app/dependencies.py` to add:

```python
from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse

from app.services.auth_service import AuthService
from app.db import SessionNotFoundError, SessionExpiredError


def get_auth_service() -> AuthService:
    settings = get_settings()
    return AuthService(settings.auth_db_path)


def get_current_user(request: Request) -> "User":
    """For API routes. Returns User or raises HTTPException(401)."""
    from app.models.auth import User

    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    auth_service = get_auth_service()
    try:
        return auth_service.validate_session(session_id)
    except (SessionNotFoundError, SessionExpiredError):
        raise HTTPException(status_code=401, detail="Session invalid or expired")


def get_current_user_or_redirect(request: Request):
    """For page routes. Returns User or RedirectResponse to /login."""
    from app.models.auth import User

    session_id = request.cookies.get("session_id")
    if not session_id:
        raise _redirect_to_login()

    auth_service = get_auth_service()
    try:
        return auth_service.validate_session(session_id)
    except (SessionNotFoundError, SessionExpiredError):
        raise _redirect_to_login()


def _redirect_to_login():
    """Return an HTTPException that triggers redirect to login."""
    raise HTTPException(
        status_code=303,
        headers={"Location": "/login"},
    )
```

Note: `get_current_user_or_redirect` needs to raise a redirect. FastAPI's dependency injection doesn't natively support returning a `RedirectResponse` from a `Depends`. Instead, we'll use an exception handler approach. The simplest: raise a custom exception and register an exception handler in `main.py`, OR raise `HTTPException(303)` with a Location header. The cleanest approach: use an exception handler.

Create a custom exception and handler. Add to `app/dependencies.py`:

```python
class AuthRedirectException(Exception):
    """Raised to trigger redirect to login page."""
    pass
```

Then `get_current_user_or_redirect` raises `AuthRedirectException`, and we register a handler in `main.py`:

```python
@app.exception_handler(AuthRedirectException)
async def auth_redirect_handler(request, exc):
    return RedirectResponse(url="/login", status_code=303)
```

**Step 4: Run tests to verify they pass**

Run: `cd /workspaces/prompt-enhancer && python -m pytest tests/test_dependencies_auth.py -v`
Expected: All PASS.

**Step 5: Commit**

```bash
git add app/dependencies.py tests/test_dependencies_auth.py
git commit -m "feat: add get_current_user and get_current_user_or_redirect dependencies"
```

---

### Task 8: Create auth routes and templates

**Files:**
- Create: `app/routes/auth.py`
- Create: `app/templates/login.html`
- Create: `app/templates/register.html`
- Create: `tests/test_routes_auth.py`

**Step 1: Write the failing tests**

Create `tests/test_routes_auth.py`:

```python
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setenv("NEWS_CSV_PATH", str(tmp_path / "news.csv"))
    monkeypatch.setenv("WORKSPACES_PATH", str(tmp_path / "workspaces"))
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", str(tmp_path / "system.txt"))
    monkeypatch.setenv("AUTH_DB_PATH", str(tmp_path / "auth.db"))

    (tmp_path / "news.csv").write_text("id,headline,content\n")
    (tmp_path / "workspaces").mkdir()
    (tmp_path / "system.txt").write_text("Test prompt")

    from app.dependencies import get_settings
    get_settings.cache_clear()

    from app.db import init_db
    init_db(str(tmp_path / "auth.db"))

    from app.main import app
    return TestClient(app, follow_redirects=False)


def test_get_login_page(client):
    """GET /login returns the login page."""
    response = client.get("/login")
    assert response.status_code == 200
    assert "Login" in response.text


def test_get_register_page(client):
    """GET /register returns the registration page."""
    response = client.get("/register")
    assert response.status_code == 200
    assert "Register" in response.text


def test_register_and_redirect(client):
    """POST /register creates user and redirects to home."""
    response = client.post(
        "/register",
        data={"email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert "session_id" in response.cookies


def test_login_valid_credentials(client):
    """POST /login with valid credentials redirects to home."""
    # Register first
    client.post("/register", data={"email": "test@example.com", "password": "password123"})

    # Login
    response = client.post(
        "/login",
        data={"email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert "session_id" in response.cookies


def test_login_invalid_credentials(client):
    """POST /login with bad credentials returns login page with error."""
    response = client.post(
        "/login",
        data={"email": "bad@example.com", "password": "wrong"},
    )
    assert response.status_code == 200
    assert "Invalid" in response.text


def test_logout(client):
    """POST /logout clears session and redirects to login."""
    # Register and get session
    register_response = client.post(
        "/register",
        data={"email": "test@example.com", "password": "password123"},
    )
    session_cookie = register_response.cookies.get("session_id")

    # Logout
    response = client.post("/logout", cookies={"session_id": session_cookie})
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_register_duplicate_email(client):
    """POST /register with existing email shows error."""
    client.post("/register", data={"email": "test@example.com", "password": "pass1"})
    response = client.post(
        "/register",
        data={"email": "test@example.com", "password": "pass2"},
    )
    assert response.status_code == 200
    assert "already registered" in response.text.lower()
```

**Step 2: Run tests to verify they fail**

Run: `cd /workspaces/prompt-enhancer && python -m pytest tests/test_routes_auth.py -v`
Expected: FAIL — routes don't exist.

**Step 3: Create login template**

Create `app/templates/login.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Prompt Enhancer</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center">
    <div class="bg-white rounded-lg shadow-lg p-8 w-full max-w-md">
        <h1 class="text-2xl font-bold text-center mb-6">Login</h1>

        {% if error %}
        <div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {{ error }}
        </div>
        {% endif %}

        <form method="POST" action="/login" class="space-y-4">
            <div>
                <label for="email" class="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input type="email" id="email" name="email" required
                       class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-600 focus:border-transparent outline-none">
            </div>
            <div>
                <label for="password" class="block text-sm font-medium text-gray-700 mb-1">Password</label>
                <input type="password" id="password" name="password" required
                       class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-600 focus:border-transparent outline-none">
            </div>
            <button type="submit"
                    class="w-full bg-red-600 text-white py-2 rounded-lg font-medium hover:bg-red-700 transition-colors">
                Login
            </button>
        </form>

        <p class="text-center text-sm text-gray-500 mt-4">
            Don't have an account? <a href="/register" class="text-red-600 hover:underline">Register</a>
        </p>
    </div>
</body>
</html>
```

**Step 4: Create register template**

Create `app/templates/register.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Register - Prompt Enhancer</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center">
    <div class="bg-white rounded-lg shadow-lg p-8 w-full max-w-md">
        <h1 class="text-2xl font-bold text-center mb-6">Register</h1>

        {% if error %}
        <div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {{ error }}
        </div>
        {% endif %}

        <form method="POST" action="/register" class="space-y-4">
            <div>
                <label for="email" class="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input type="email" id="email" name="email" required
                       class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-600 focus:border-transparent outline-none">
            </div>
            <div>
                <label for="password" class="block text-sm font-medium text-gray-700 mb-1">Password</label>
                <input type="password" id="password" name="password" required
                       class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-600 focus:border-transparent outline-none">
            </div>
            <button type="submit"
                    class="w-full bg-red-600 text-white py-2 rounded-lg font-medium hover:bg-red-700 transition-colors">
                Register
            </button>
        </form>

        <p class="text-center text-sm text-gray-500 mt-4">
            Already have an account? <a href="/login" class="text-red-600 hover:underline">Login</a>
        </p>
    </div>
</body>
</html>
```

**Step 5: Create auth routes**

Create `app/routes/auth.py`:

```python
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db import DuplicateEmailError
from app.dependencies import get_auth_service
from app.services.auth_service import InvalidCredentialsError

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="app/templates")

COOKIE_MAX_AGE = 604800  # 7 days


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id:
        auth_service = get_auth_service()
        try:
            auth_service.validate_session(session_id)
            return RedirectResponse(url="/", status_code=303)
        except Exception:
            pass
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    auth_service = get_auth_service()

    try:
        user = auth_service.authenticate_user(email, password)
    except InvalidCredentialsError:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid email or password"},
        )

    session = auth_service.create_session(user.id)
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="session_id",
        value=session.id,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
    )
    return response


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id:
        auth_service = get_auth_service()
        try:
            auth_service.validate_session(session_id)
            return RedirectResponse(url="/", status_code=303)
        except Exception:
            pass
    return templates.TemplateResponse("register.html", {"request": request, "error": None})


@router.post("/register")
def register(request: Request, email: str = Form(...), password: str = Form(...)):
    auth_service = get_auth_service()

    try:
        user = auth_service.register_user(email, password)
    except DuplicateEmailError:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Email already registered"},
        )

    session = auth_service.create_session(user.id)
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="session_id",
        value=session.id,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
    )
    return response


@router.post("/logout")
def logout(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id:
        auth_service = get_auth_service()
        auth_service.logout(session_id)

    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="session_id")
    return response
```

**Step 6: Run tests to verify they pass**

Run: `cd /workspaces/prompt-enhancer && python -m pytest tests/test_routes_auth.py -v`
Expected: All 7 tests PASS.

**Step 7: Commit**

```bash
git add app/routes/auth.py app/templates/login.html app/templates/register.html tests/test_routes_auth.py
git commit -m "feat: add auth routes with login, register, logout pages"
```

---

### Task 9: Wire auth into main.py and init_db on startup

**Files:**
- Modify: `app/main.py`

**Step 1: Update main.py**

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.db import init_db
from app.dependencies import get_settings, AuthRedirectException
from app.routes import pages, workspaces, news, prompts, workflows
from app.routes.auth import router as auth_router
from app.routes.workspace_news import router as workspace_news_router
from app.routes.workspace_news import news_source_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_db(settings.auth_db_path)
    yield


app = FastAPI(title="Prompt Enhancer", version="0.1.0", lifespan=lifespan)


@app.exception_handler(AuthRedirectException)
async def auth_redirect_handler(request, exc):
    return RedirectResponse(url="/login", status_code=303)


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth_router)
app.include_router(pages.router)
app.include_router(workspaces.router, prefix="/api")
app.include_router(news.router, prefix="/api")
app.include_router(prompts.router, prefix="/api")
app.include_router(workflows.router, prefix="/api")
app.include_router(workspace_news_router, prefix="/api")
app.include_router(news_source_router, prefix="/api")


@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

**Step 2: Run existing tests to make sure nothing is broken**

Run: `cd /workspaces/prompt-enhancer && python -m pytest tests/ -v`
Expected: All pass (some existing route tests may fail due to missing `AUTH_DB_PATH` env var — fix those fixtures).

**Step 3: Commit**

```bash
git add app/main.py
git commit -m "feat: wire auth router and init_db into app startup"
```

---

### Task 10: Protect existing routes with auth

**Files:**
- Modify: `app/routes/pages.py`
- Modify: `app/routes/workspaces.py`
- Modify: `app/routes/workflows.py`
- Modify: `app/routes/news.py`
- Modify: `app/routes/prompts.py`
- Modify: `app/routes/workspace_news.py`

**Step 1: Update pages.py**

Add auth dependency to page routes. These use `get_current_user_or_redirect` so unauthenticated users are redirected to `/login`:

```python
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import get_current_user_or_redirect, get_workspace_service
from app.models.auth import User
from app.services.workspace_service import WorkspaceService

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def news_list_page(
    request: Request,
    current_user: User = Depends(get_current_user_or_redirect),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    workspaces = workspace_service.list_workspaces_for_user(current_user.id)
    return templates.TemplateResponse(
        "news_list.html",
        {"request": request, "workspaces": workspaces, "current_user": current_user},
    )


@router.get("/prompts", response_class=HTMLResponse)
def prompts_page(
    request: Request,
    current_user: User = Depends(get_current_user_or_redirect),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    workspaces = workspace_service.list_workspaces_for_user(current_user.id)
    return templates.TemplateResponse(
        "prompts.html",
        {"request": request, "workspaces": workspaces, "current_user": current_user},
    )
```

**Step 2: Update workspaces.py**

Add `get_current_user` dependency. Pass `user.id` to `create_workspace` and use `list_workspaces_for_user`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.dependencies import get_current_user, get_workspace_service
from app.models.auth import User
from app.models.workspace import WorkspaceMetadata
from app.services.workspace_service import WorkspaceNotFoundError, WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


class CreateWorkspaceRequest(BaseModel):
    name: str


@router.post("", status_code=status.HTTP_201_CREATED, response_model=WorkspaceMetadata)
def create_workspace(
    request: CreateWorkspaceRequest,
    current_user: User = Depends(get_current_user),
    service: WorkspaceService = Depends(get_workspace_service),
):
    return service.create_workspace(request.name, current_user.id)


@router.get("", response_model=list[WorkspaceMetadata])
def list_workspaces(
    current_user: User = Depends(get_current_user),
    service: WorkspaceService = Depends(get_workspace_service),
):
    return service.list_workspaces_for_user(current_user.id)


@router.get("/{workspace_id}", response_model=WorkspaceMetadata)
def get_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        return service.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise HTTPException(status_code=404, detail="Workspace not found")


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        service.delete_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise HTTPException(status_code=404, detail="Workspace not found")
```

**Step 3: Update workflows.py, news.py, prompts.py, workspace_news.py**

For each of these, add `current_user: User = Depends(get_current_user)` as a parameter to every route function. Import `get_current_user` from `app.dependencies` and `User` from `app.models.auth`.

For `workflows.py`, add to every route function signature:
```python
current_user: User = Depends(get_current_user),
```

For `news.py`, add to `get_news` and `get_article`:
```python
current_user: User = Depends(get_current_user),
```

For `prompts.py`, add to the `get_prompt_service` dependency (it's called by all routes):
```python
# No change to get_prompt_service itself, but add get_current_user to each route
```

Actually, the simplest approach for `prompts.py` is to add `current_user: User = Depends(get_current_user)` to each route handler.

For `workspace_news.py`, add to each route handler.

**Step 4: Run all tests**

Run: `cd /workspaces/prompt-enhancer && python -m pytest tests/ -v`
Expected: Many existing route tests will fail because they don't send a session cookie. Fix each test fixture to register a user, create a session, and include the session cookie in requests.

**Step 5: Fix existing test fixtures**

Every test fixture that creates a `TestClient` needs to:
1. Set `AUTH_DB_PATH` env var
2. Call `init_db`
3. Register a test user and create a session
4. Pass `cookies={"session_id": session.id}` in test requests

Example update pattern for `tests/test_routes_workspaces.py`:

```python
@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setenv("NEWS_CSV_PATH", str(tmp_path / "news.csv"))
    monkeypatch.setenv("WORKSPACES_PATH", str(tmp_path / "workspaces"))
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", str(tmp_path / "system.txt"))
    monkeypatch.setenv("AUTH_DB_PATH", str(tmp_path / "auth.db"))

    (tmp_path / "news.csv").write_text("id,headline,content\n")
    (tmp_path / "workspaces").mkdir()
    (tmp_path / "system.txt").write_text("Test prompt")

    from app.dependencies import get_settings
    get_settings.cache_clear()

    from app.db import init_db
    init_db(str(tmp_path / "auth.db"))

    from app.services.auth_service import AuthService
    auth = AuthService(str(tmp_path / "auth.db"))
    user = auth.register_user("test@example.com", "password123")
    session = auth.create_session(user.id)

    from app.main import app
    client = TestClient(app)
    client.cookies.set("session_id", session.id)
    return client
```

Apply this pattern to all route test files:
- `tests/test_routes_workspaces.py`
- `tests/test_routes_news.py`
- `tests/test_routes_prompts.py`
- `tests/test_routes_workflows.py`
- `tests/test_routes_workspace_news.py`

**Step 6: Run all tests**

Run: `cd /workspaces/prompt-enhancer && python -m pytest tests/ -v`
Expected: All PASS.

**Step 7: Commit**

```bash
git add app/routes/ tests/
git commit -m "feat: protect all routes with auth dependencies"
```

---

### Task 11: Add logout button to base.html

**Files:**
- Modify: `app/templates/base.html:101-122`

**Step 1: Update the header nav**

In `app/templates/base.html`, add a logout form after the workspace selector section. Replace the `<nav>` block (lines 104-119) with:

```html
        <nav class="flex items-center gap-6">
            <a href="/" class="nav-link text-gray-400 hover:text-white transition-all duration-200 hover:-translate-y-0.5 {{ 'text-white border-b-2 border-red-600 pb-1' if request.path == '/' else '' }}">News</a>
            <a href="/prompts" class="nav-link text-gray-400 hover:text-white transition-all duration-200 hover:-translate-y-0.5 {{ 'text-white border-b-2 border-red-600 pb-1' if request.path == '/prompts' else '' }}">Prompts</a>
            <div class="flex items-center gap-3">
                <select id="workspace-selector"
                        class="bg-white/10 text-white rounded-lg px-4 py-2 text-sm border-0 cursor-pointer hover:bg-white/20 transition-colors duration-200 focus:ring-2 focus:ring-red-600/50 focus:outline-none">
                    <option value="" class="bg-gray-900">Select Workspace</option>
                    {% for ws in workspaces %}
                    <option value="{{ ws.id }}" class="bg-gray-900">{{ ws.name }}</option>
                    {% endfor %}
                </select>
                <button onclick="createWorkspace()"
                        class="border border-red-600 text-red-600 px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-600 hover:text-white transition-all duration-200">
                    + New
                </button>
            </div>
            {% if current_user %}
            <div class="flex items-center gap-3 ml-4 border-l border-white/20 pl-4">
                <span class="text-gray-400 text-sm">{{ current_user.email }}</span>
                <form method="POST" action="/logout" class="inline">
                    <button type="submit"
                            class="text-gray-400 hover:text-white text-sm transition-colors duration-200">
                        Logout
                    </button>
                </form>
            </div>
            {% endif %}
        </nav>
```

**Step 2: Verify visually**

Start the dev server and check that the logout button appears in the header when logged in.

Run: `cd /workspaces/prompt-enhancer && uvicorn app.main:app --reload`

**Step 3: Commit**

```bash
git add app/templates/base.html
git commit -m "feat: add user email and logout button to header"
```

---

### Task 12: Update .env and run full test suite

**Files:**
- Modify: `.env`

**Step 1: Ensure .env has AUTH_DB_PATH**

Add to `.env` if not already present:
```
AUTH_DB_PATH=./data/auth.db
```

**Step 2: Run full test suite**

Run: `cd /workspaces/prompt-enhancer && python -m pytest tests/ -v`
Expected: All tests PASS.

**Step 3: Manual smoke test**

1. Start server: `uvicorn app.main:app --reload`
2. Visit `/` — should redirect to `/login`
3. Click "Register" — register with email/password
4. Should redirect to home, see workspace page
5. Create a workspace — should be visible
6. Logout — should redirect to login
7. Login again — workspace should still be there
8. Register another user — should see empty workspace list

**Step 4: Commit**

```bash
git add .env
git commit -m "chore: add AUTH_DB_PATH to .env configuration"
```
