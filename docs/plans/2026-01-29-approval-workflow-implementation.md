# Approval Workflow Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add role-based approval workflow for organization workspace prompt changes.

**Architecture:** Two roles (USER/APPROVER) stored in SQLite. Organization workspace auto-created on startup. Users submit change requests for org prompts; Approvers can approve/reject or edit directly. Personal workspaces unaffected.

**Tech Stack:** FastAPI, Pydantic, SQLite, pytest, Jinja2 templates

---

## Task 1: Add UserRole Enum and Update User Model

**Files:**
- Modify: `app/models/auth.py`
- Test: `tests/test_models_auth.py`

**Step 1: Write the failing test**

Create test file:

```python
# tests/test_models_auth.py
from datetime import datetime

import pytest


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
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models_auth.py -v`
Expected: FAIL with "cannot import name 'UserRole'"

**Step 3: Write minimal implementation**

Update `app/models/auth.py`:

```python
from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class UserRole(str, Enum):
    USER = "USER"
    APPROVER = "APPROVER"


class User(BaseModel):
    id: str
    email: str
    created_at: datetime
    role: UserRole = UserRole.USER


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

Run: `uv run pytest tests/test_models_auth.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/models/auth.py tests/test_models_auth.py
git commit -m "feat(models): add UserRole enum and role field to User model"
```

---

## Task 2: Update Database Schema for User Role

**Files:**
- Modify: `app/db.py`
- Test: `tests/test_db.py`

**Step 1: Write the failing test**

Create test file:

```python
# tests/test_db.py
import pytest


@pytest.fixture
def db_path(tmp_path):
    from app.db import init_db

    path = str(tmp_path / "test.db")
    init_db(path)
    return path


def test_create_user_stores_role(db_path):
    """create_user stores user role in database."""
    from app.db import create_user, get_user_by_id
    from app.models.auth import UserRole

    user = create_user(db_path, "test@example.com", "hash123", UserRole.APPROVER)

    retrieved = get_user_by_id(db_path, user.id)
    assert retrieved.role == UserRole.APPROVER


def test_create_user_defaults_to_user_role(db_path):
    """create_user defaults to USER role when not specified."""
    from app.db import create_user, get_user_by_id
    from app.models.auth import UserRole

    user = create_user(db_path, "test@example.com", "hash123")

    retrieved = get_user_by_id(db_path, user.id)
    assert retrieved.role == UserRole.USER


def test_update_user_role(db_path):
    """update_user_role changes user role."""
    from app.db import create_user, get_user_by_id, update_user_role
    from app.models.auth import UserRole

    user = create_user(db_path, "test@example.com", "hash123")
    assert user.role == UserRole.USER

    update_user_role(db_path, user.id, UserRole.APPROVER)

    updated = get_user_by_id(db_path, user.id)
    assert updated.role == UserRole.APPROVER


def test_get_all_users(db_path):
    """get_all_users returns all users with roles."""
    from app.db import create_user, get_all_users
    from app.models.auth import UserRole

    create_user(db_path, "user1@example.com", "hash1")
    create_user(db_path, "user2@example.com", "hash2", UserRole.APPROVER)

    users = get_all_users(db_path)

    assert len(users) == 2
    emails = {u.email for u in users}
    assert emails == {"user1@example.com", "user2@example.com"}


def test_count_approvers(db_path):
    """count_approvers returns number of users with APPROVER role."""
    from app.db import count_approvers, create_user
    from app.models.auth import UserRole

    assert count_approvers(db_path) == 0

    create_user(db_path, "user1@example.com", "hash1")
    assert count_approvers(db_path) == 0

    create_user(db_path, "user2@example.com", "hash2", UserRole.APPROVER)
    assert count_approvers(db_path) == 1

    create_user(db_path, "user3@example.com", "hash3", UserRole.APPROVER)
    assert count_approvers(db_path) == 2


def test_is_first_user_true_when_no_users(db_path):
    """is_first_user returns True when no users exist."""
    from app.db import is_first_user

    assert is_first_user(db_path) is True


def test_is_first_user_false_when_users_exist(db_path):
    """is_first_user returns False when users exist."""
    from app.db import create_user, is_first_user

    create_user(db_path, "test@example.com", "hash123")

    assert is_first_user(db_path) is False
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_db.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Update `app/db.py` - modify `init_db`, `create_user`, `get_user_by_email`, `get_user_by_id` and add new functions:

```python
# Add to imports
from app.models.auth import UserRole

# Update init_db - add role column
def init_db(db_path: str) -> None:
    """Initialize the database with required tables."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'USER',
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()
    conn.close()


# Update create_user to accept optional role
def create_user(
    db_path: str,
    email: str,
    password_hash: str,
    role: UserRole = UserRole.USER,
) -> User:
    """Create a new user. Raises DuplicateEmailError if email exists."""
    user_id = f"u-{uuid.uuid4().hex[:8]}"
    created_at = datetime.now(timezone.utc)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (id, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, email, password_hash, role.value, created_at.isoformat()),
        )
        conn.commit()
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed: users.email" in str(e):
            raise DuplicateEmailError(f"Email {email} already exists")
        raise
    finally:
        conn.close()

    return User(id=user_id, email=email, created_at=created_at, role=role)


# Update get_user_by_email to include role
def get_user_by_email(db_path: str, email: str) -> User:
    """Get user by email. Raises UserNotFoundError if not found."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, email, role, created_at FROM users WHERE email = ?", (email,)
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise UserNotFoundError(f"User with email {email} not found")

    return User(
        id=row[0],
        email=row[1],
        role=UserRole(row[2]),
        created_at=datetime.fromisoformat(row[3]),
    )


# Update get_user_by_id to include role
def get_user_by_id(db_path: str, user_id: str) -> User:
    """Get user by ID. Raises UserNotFoundError if not found."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, email, role, created_at FROM users WHERE id = ?", (user_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise UserNotFoundError(f"User with id {user_id} not found")

    return User(
        id=row[0],
        email=row[1],
        role=UserRole(row[2]),
        created_at=datetime.fromisoformat(row[3]),
    )


# Add new functions
def update_user_role(db_path: str, user_id: str, role: UserRole) -> None:
    """Update a user's role. Raises UserNotFoundError if user doesn't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("UPDATE users SET role = ? WHERE id = ?", (role.value, user_id))

    if cursor.rowcount == 0:
        conn.close()
        raise UserNotFoundError(f"User with id {user_id} not found")

    conn.commit()
    conn.close()


def get_all_users(db_path: str) -> list[User]:
    """Get all users."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id, email, role, created_at FROM users ORDER BY created_at")
    rows = cursor.fetchall()
    conn.close()

    return [
        User(
            id=row[0],
            email=row[1],
            role=UserRole(row[2]),
            created_at=datetime.fromisoformat(row[3]),
        )
        for row in rows
    ]


def count_approvers(db_path: str) -> int:
    """Count users with APPROVER role."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users WHERE role = ?", (UserRole.APPROVER.value,))
    count = cursor.fetchone()[0]
    conn.close()

    return count


def is_first_user(db_path: str) -> bool:
    """Check if this would be the first user in the system."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()

    return count == 0
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_db.py -v`
Expected: PASS

**Step 5: Run all tests to check for regressions**

Run: `uv run pytest -v`
Expected: All tests pass

**Step 6: Commit**

```bash
git add app/db.py tests/test_db.py
git commit -m "feat(db): add role column and user management functions"
```

---

## Task 3: Update AuthService for Role-Aware Registration

**Files:**
- Modify: `app/services/auth_service.py`
- Test: `tests/test_auth_service.py`

**Step 1: Write the failing test**

Add to `tests/test_auth_service.py`:

```python
def test_first_user_becomes_approver(db_path):
    """First registered user automatically becomes APPROVER."""
    from app.models.auth import UserRole
    from app.services.auth_service import AuthService

    service = AuthService(db_path)
    user = service.register_user("first@example.com", "password123")

    assert user.role == UserRole.APPROVER


def test_second_user_is_regular_user(db_path):
    """Second registered user is a regular USER."""
    from app.models.auth import UserRole
    from app.services.auth_service import AuthService

    service = AuthService(db_path)
    service.register_user("first@example.com", "password123")
    second_user = service.register_user("second@example.com", "password456")

    assert second_user.role == UserRole.USER
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_auth_service.py::test_first_user_becomes_approver tests/test_auth_service.py::test_second_user_is_regular_user -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Update `app/services/auth_service.py`:

```python
from app.db import (
    create_user,
    get_password_hash,
    get_user_by_email,
    get_user_by_id,
    is_first_user,
    create_session as db_create_session,
    get_session,
    delete_session,
)
from app.models.auth import Session, User, UserRole


class AuthService:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def register_user(self, email: str, password: str) -> User:
        """Register a new user. First user becomes APPROVER."""
        password_hash = _hash_password(password)

        # First user becomes approver
        role = UserRole.APPROVER if is_first_user(self.db_path) else UserRole.USER

        return create_user(self.db_path, email, password_hash, role)

    # ... rest of the methods stay the same
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_auth_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/auth_service.py tests/test_auth_service.py
git commit -m "feat(auth): first registered user becomes approver"
```

---

## Task 4: Create PromptType Enum and ChangeRequest Model

**Files:**
- Create: `app/models/change_request.py`
- Test: `tests/test_models_change_request.py`

**Step 1: Write the failing test**

```python
# tests/test_models_change_request.py
from datetime import datetime

import pytest


def test_prompt_type_enum_values():
    """PromptType enum has three values."""
    from app.models.change_request import PromptType

    assert PromptType.CATEGORY_DEFINITIONS.value == "CATEGORY_DEFINITIONS"
    assert PromptType.FEW_SHOTS.value == "FEW_SHOTS"
    assert PromptType.SYSTEM_PROMPT.value == "SYSTEM_PROMPT"


def test_change_request_status_enum_values():
    """ChangeRequestStatus enum has three values."""
    from app.models.change_request import ChangeRequestStatus

    assert ChangeRequestStatus.PENDING.value == "PENDING"
    assert ChangeRequestStatus.APPROVED.value == "APPROVED"
    assert ChangeRequestStatus.REJECTED.value == "REJECTED"


def test_change_request_creation():
    """ChangeRequest can be created with required fields."""
    from app.models.change_request import (
        ChangeRequest,
        ChangeRequestStatus,
        PromptType,
    )

    request = ChangeRequest(
        id="cr-12345678",
        workspace_id="organization",
        prompt_type=PromptType.CATEGORY_DEFINITIONS,
        submitted_by="u-12345678",
        submitted_at=datetime.now(),
        status=ChangeRequestStatus.PENDING,
        current_content={"categories": []},
        proposed_content={"categories": [{"name": "Tech", "definition": "Tech news"}]},
    )

    assert request.id == "cr-12345678"
    assert request.status == ChangeRequestStatus.PENDING
    assert request.description is None
    assert request.reviewed_by is None
    assert request.reviewed_at is None
    assert request.review_feedback is None


def test_change_request_with_optional_fields():
    """ChangeRequest can include optional fields."""
    from app.models.change_request import (
        ChangeRequest,
        ChangeRequestStatus,
        PromptType,
    )

    now = datetime.now()
    request = ChangeRequest(
        id="cr-12345678",
        workspace_id="organization",
        prompt_type=PromptType.FEW_SHOTS,
        submitted_by="u-12345678",
        submitted_at=now,
        status=ChangeRequestStatus.APPROVED,
        current_content={},
        proposed_content={},
        description="Adding examples for better classification",
        reviewed_by="u-approver1",
        reviewed_at=now,
        review_feedback="Looks good!",
    )

    assert request.description == "Adding examples for better classification"
    assert request.reviewed_by == "u-approver1"
    assert request.review_feedback == "Looks good!"


def test_create_change_request_input():
    """CreateChangeRequestInput validates input for submission."""
    from app.models.change_request import CreateChangeRequestInput, PromptType

    input_data = CreateChangeRequestInput(
        prompt_type=PromptType.SYSTEM_PROMPT,
        proposed_content={"prompt": "You are an expert classifier."},
        description="Improved system instructions",
    )

    assert input_data.prompt_type == PromptType.SYSTEM_PROMPT
    assert input_data.description == "Improved system instructions"


def test_review_change_request_input():
    """ReviewChangeRequestInput validates approval/rejection input."""
    from app.models.change_request import ReviewChangeRequestInput

    input_data = ReviewChangeRequestInput(feedback="Great improvement!")

    assert input_data.feedback == "Great improvement!"


def test_revise_change_request_input():
    """ReviseChangeRequestInput validates revision input."""
    from app.models.change_request import ReviseChangeRequestInput

    input_data = ReviseChangeRequestInput(
        proposed_content={"updated": True},
        description="Updated based on feedback",
    )

    assert input_data.proposed_content == {"updated": True}
    assert input_data.description == "Updated based on feedback"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models_change_request.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# app/models/change_request.py
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel


class PromptType(str, Enum):
    CATEGORY_DEFINITIONS = "CATEGORY_DEFINITIONS"
    FEW_SHOTS = "FEW_SHOTS"
    SYSTEM_PROMPT = "SYSTEM_PROMPT"


class ChangeRequestStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ChangeRequest(BaseModel):
    id: str
    workspace_id: str
    prompt_type: PromptType
    submitted_by: str
    submitted_at: datetime
    status: ChangeRequestStatus
    current_content: dict[str, Any]
    proposed_content: dict[str, Any]
    description: str | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    review_feedback: str | None = None


class CreateChangeRequestInput(BaseModel):
    prompt_type: PromptType
    proposed_content: dict[str, Any]
    description: str | None = None


class ReviewChangeRequestInput(BaseModel):
    feedback: str | None = None


class ReviseChangeRequestInput(BaseModel):
    proposed_content: dict[str, Any]
    description: str | None = None
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_models_change_request.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/models/change_request.py tests/test_models_change_request.py
git commit -m "feat(models): add ChangeRequest model and related types"
```

---

## Task 5: Create ChangeRequestService

**Files:**
- Create: `app/services/change_request_service.py`
- Test: `tests/test_change_request_service.py`

**Step 1: Write the failing test**

```python
# tests/test_change_request_service.py
from datetime import datetime
from pathlib import Path

import pytest


@pytest.fixture
def workspace_path(tmp_path):
    """Create organization workspace directory."""
    org_path = tmp_path / "workspaces" / "organization"
    org_path.mkdir(parents=True)

    # Create change_requests directory
    (org_path / "change_requests").mkdir()

    # Create initial prompt files
    import json

    (org_path / "category_definitions.json").write_text(
        json.dumps({"categories": [{"name": "Tech", "definition": "Technology news"}]})
    )
    (org_path / "few_shot_examples.json").write_text(json.dumps({"examples": []}))
    (org_path / "system_prompt.json").write_text(json.dumps({"prompt": "Default"}))

    return str(tmp_path / "workspaces")


def test_create_change_request(workspace_path):
    """create_change_request creates a pending change request."""
    from app.models.change_request import ChangeRequestStatus, PromptType
    from app.services.change_request_service import ChangeRequestService

    service = ChangeRequestService(workspace_path)

    request = service.create_change_request(
        user_id="u-user1234",
        prompt_type=PromptType.CATEGORY_DEFINITIONS,
        proposed_content={"categories": [{"name": "Sports", "definition": "Sports news"}]},
        description="Adding sports category",
    )

    assert request.id.startswith("cr-")
    assert request.workspace_id == "organization"
    assert request.prompt_type == PromptType.CATEGORY_DEFINITIONS
    assert request.submitted_by == "u-user1234"
    assert request.status == ChangeRequestStatus.PENDING
    assert request.description == "Adding sports category"
    assert request.current_content == {
        "categories": [{"name": "Tech", "definition": "Technology news"}]
    }


def test_get_change_request(workspace_path):
    """get_change_request returns a change request by ID."""
    from app.models.change_request import PromptType
    from app.services.change_request_service import ChangeRequestService

    service = ChangeRequestService(workspace_path)

    created = service.create_change_request(
        user_id="u-user1234",
        prompt_type=PromptType.FEW_SHOTS,
        proposed_content={"examples": [{"id": "1", "content": "test"}]},
    )

    retrieved = service.get_change_request(created.id)

    assert retrieved.id == created.id
    assert retrieved.prompt_type == PromptType.FEW_SHOTS


def test_get_change_request_not_found(workspace_path):
    """get_change_request raises ChangeRequestNotFoundError for unknown ID."""
    from app.services.change_request_service import (
        ChangeRequestNotFoundError,
        ChangeRequestService,
    )

    service = ChangeRequestService(workspace_path)

    with pytest.raises(ChangeRequestNotFoundError):
        service.get_change_request("cr-nonexistent")


def test_list_change_requests(workspace_path):
    """list_change_requests returns all change requests."""
    from app.models.change_request import PromptType
    from app.services.change_request_service import ChangeRequestService

    service = ChangeRequestService(workspace_path)

    service.create_change_request(
        user_id="u-user1",
        prompt_type=PromptType.CATEGORY_DEFINITIONS,
        proposed_content={},
    )
    service.create_change_request(
        user_id="u-user2",
        prompt_type=PromptType.FEW_SHOTS,
        proposed_content={},
    )

    requests = service.list_change_requests()

    assert len(requests) == 2


def test_list_change_requests_filter_by_status(workspace_path):
    """list_change_requests can filter by status."""
    from app.models.change_request import ChangeRequestStatus, PromptType
    from app.services.change_request_service import ChangeRequestService

    service = ChangeRequestService(workspace_path)

    service.create_change_request(
        user_id="u-user1",
        prompt_type=PromptType.CATEGORY_DEFINITIONS,
        proposed_content={},
    )

    pending = service.list_change_requests(status=ChangeRequestStatus.PENDING)
    approved = service.list_change_requests(status=ChangeRequestStatus.APPROVED)

    assert len(pending) == 1
    assert len(approved) == 0


def test_approve_change_request(workspace_path):
    """approve_change_request updates status and applies changes."""
    import json

    from app.models.change_request import ChangeRequestStatus, PromptType
    from app.services.change_request_service import ChangeRequestService

    service = ChangeRequestService(workspace_path)

    request = service.create_change_request(
        user_id="u-user1234",
        prompt_type=PromptType.CATEGORY_DEFINITIONS,
        proposed_content={"categories": [{"name": "Sports", "definition": "Sports"}]},
    )

    approved = service.approve_change_request(
        request_id=request.id,
        reviewer_id="u-approver1",
        feedback="Looks good!",
    )

    assert approved.status == ChangeRequestStatus.APPROVED
    assert approved.reviewed_by == "u-approver1"
    assert approved.review_feedback == "Looks good!"
    assert approved.reviewed_at is not None

    # Verify prompt file was updated
    prompt_path = Path(workspace_path) / "organization" / "category_definitions.json"
    saved_content = json.loads(prompt_path.read_text())
    assert saved_content == {"categories": [{"name": "Sports", "definition": "Sports"}]}


def test_approve_change_request_conflict(workspace_path):
    """approve_change_request raises ConflictError if prompts changed."""
    import json

    from app.models.change_request import PromptType
    from app.services.change_request_service import (
        ChangeRequestService,
        ChangeRequestConflictError,
    )

    service = ChangeRequestService(workspace_path)

    request = service.create_change_request(
        user_id="u-user1234",
        prompt_type=PromptType.CATEGORY_DEFINITIONS,
        proposed_content={"categories": []},
    )

    # Simulate another change being applied
    prompt_path = Path(workspace_path) / "organization" / "category_definitions.json"
    prompt_path.write_text(json.dumps({"categories": [{"name": "Modified", "definition": "X"}]}))

    with pytest.raises(ChangeRequestConflictError):
        service.approve_change_request(request.id, "u-approver1")


def test_reject_change_request(workspace_path):
    """reject_change_request updates status without applying changes."""
    from app.models.change_request import ChangeRequestStatus, PromptType
    from app.services.change_request_service import ChangeRequestService

    service = ChangeRequestService(workspace_path)

    request = service.create_change_request(
        user_id="u-user1234",
        prompt_type=PromptType.CATEGORY_DEFINITIONS,
        proposed_content={"categories": []},
    )

    rejected = service.reject_change_request(
        request_id=request.id,
        reviewer_id="u-approver1",
        feedback="Needs more categories",
    )

    assert rejected.status == ChangeRequestStatus.REJECTED
    assert rejected.reviewed_by == "u-approver1"
    assert rejected.review_feedback == "Needs more categories"


def test_revise_change_request(workspace_path):
    """revise_change_request updates a rejected request."""
    from app.models.change_request import ChangeRequestStatus, PromptType
    from app.services.change_request_service import ChangeRequestService

    service = ChangeRequestService(workspace_path)

    request = service.create_change_request(
        user_id="u-user1234",
        prompt_type=PromptType.CATEGORY_DEFINITIONS,
        proposed_content={"categories": []},
    )
    service.reject_change_request(request.id, "u-approver1", "Add more")

    revised = service.revise_change_request(
        request_id=request.id,
        proposed_content={"categories": [{"name": "New", "definition": "New cat"}]},
        description="Added category",
    )

    assert revised.status == ChangeRequestStatus.PENDING
    assert revised.proposed_content == {"categories": [{"name": "New", "definition": "New cat"}]}
    assert revised.description == "Added category"
    assert revised.reviewed_by is None
    assert revised.reviewed_at is None
    assert revised.review_feedback is None


def test_revise_non_rejected_request_fails(workspace_path):
    """revise_change_request raises error for non-rejected request."""
    from app.models.change_request import PromptType
    from app.services.change_request_service import (
        ChangeRequestService,
        InvalidChangeRequestStateError,
    )

    service = ChangeRequestService(workspace_path)

    request = service.create_change_request(
        user_id="u-user1234",
        prompt_type=PromptType.CATEGORY_DEFINITIONS,
        proposed_content={},
    )

    with pytest.raises(InvalidChangeRequestStateError):
        service.revise_change_request(request.id, {"new": "content"})


def test_withdraw_change_request(workspace_path):
    """withdraw_change_request deletes a pending request."""
    from app.models.change_request import PromptType
    from app.services.change_request_service import (
        ChangeRequestNotFoundError,
        ChangeRequestService,
    )

    service = ChangeRequestService(workspace_path)

    request = service.create_change_request(
        user_id="u-user1234",
        prompt_type=PromptType.CATEGORY_DEFINITIONS,
        proposed_content={},
    )

    service.withdraw_change_request(request.id)

    with pytest.raises(ChangeRequestNotFoundError):
        service.get_change_request(request.id)


def test_withdraw_non_pending_request_fails(workspace_path):
    """withdraw_change_request raises error for non-pending request."""
    from app.models.change_request import PromptType
    from app.services.change_request_service import (
        ChangeRequestService,
        InvalidChangeRequestStateError,
    )

    service = ChangeRequestService(workspace_path)

    request = service.create_change_request(
        user_id="u-user1234",
        prompt_type=PromptType.CATEGORY_DEFINITIONS,
        proposed_content={},
    )
    service.reject_change_request(request.id, "u-approver1")

    with pytest.raises(InvalidChangeRequestStateError):
        service.withdraw_change_request(request.id)


def test_has_pending_request_for_prompt_type(workspace_path):
    """has_pending_request returns True if user has pending request for type."""
    from app.models.change_request import PromptType
    from app.services.change_request_service import ChangeRequestService

    service = ChangeRequestService(workspace_path)

    assert service.has_pending_request("u-user1", PromptType.CATEGORY_DEFINITIONS) is False

    service.create_change_request(
        user_id="u-user1",
        prompt_type=PromptType.CATEGORY_DEFINITIONS,
        proposed_content={},
    )

    assert service.has_pending_request("u-user1", PromptType.CATEGORY_DEFINITIONS) is True
    assert service.has_pending_request("u-user1", PromptType.FEW_SHOTS) is False
    assert service.has_pending_request("u-user2", PromptType.CATEGORY_DEFINITIONS) is False


def test_count_pending_requests(workspace_path):
    """count_pending_requests returns number of pending requests."""
    from app.models.change_request import PromptType
    from app.services.change_request_service import ChangeRequestService

    service = ChangeRequestService(workspace_path)

    assert service.count_pending_requests() == 0

    service.create_change_request(
        user_id="u-user1",
        prompt_type=PromptType.CATEGORY_DEFINITIONS,
        proposed_content={},
    )
    service.create_change_request(
        user_id="u-user2",
        prompt_type=PromptType.FEW_SHOTS,
        proposed_content={},
    )

    assert service.count_pending_requests() == 2
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_change_request_service.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# app/services/change_request_service.py
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.models.change_request import (
    ChangeRequest,
    ChangeRequestStatus,
    PromptType,
)


class ChangeRequestNotFoundError(Exception):
    """Raised when a change request is not found."""

    pass


class ChangeRequestConflictError(Exception):
    """Raised when prompts have changed since the request was created."""

    pass


class InvalidChangeRequestStateError(Exception):
    """Raised when an operation is invalid for the current request state."""

    pass


class DuplicatePendingRequestError(Exception):
    """Raised when user already has a pending request for the same prompt type."""

    pass


PROMPT_TYPE_TO_FILE = {
    PromptType.CATEGORY_DEFINITIONS: "category_definitions.json",
    PromptType.FEW_SHOTS: "few_shot_examples.json",
    PromptType.SYSTEM_PROMPT: "system_prompt.json",
}


class ChangeRequestService:
    def __init__(self, workspaces_path: str):
        self.workspaces_path = Path(workspaces_path)
        self.org_path = self.workspaces_path / "organization"
        self.requests_path = self.org_path / "change_requests"

    def _get_current_content(self, prompt_type: PromptType) -> dict:
        """Read current content from the prompt file."""
        file_name = PROMPT_TYPE_TO_FILE[prompt_type]
        file_path = self.org_path / file_name
        return json.loads(file_path.read_text())

    def _save_prompt_content(self, prompt_type: PromptType, content: dict) -> None:
        """Write content to the prompt file."""
        file_name = PROMPT_TYPE_TO_FILE[prompt_type]
        file_path = self.org_path / file_name
        file_path.write_text(json.dumps(content, indent=2))

    def _load_request(self, request_id: str) -> ChangeRequest:
        """Load a change request from file."""
        file_path = self.requests_path / f"{request_id}.json"
        if not file_path.exists():
            raise ChangeRequestNotFoundError(f"Change request {request_id} not found")
        data = json.loads(file_path.read_text())
        return ChangeRequest(**data)

    def _save_request(self, request: ChangeRequest) -> None:
        """Save a change request to file."""
        file_path = self.requests_path / f"{request.id}.json"
        file_path.write_text(request.model_dump_json(indent=2))

    def _delete_request(self, request_id: str) -> None:
        """Delete a change request file."""
        file_path = self.requests_path / f"{request_id}.json"
        if file_path.exists():
            file_path.unlink()

    def create_change_request(
        self,
        user_id: str,
        prompt_type: PromptType,
        proposed_content: dict,
        description: str | None = None,
    ) -> ChangeRequest:
        """Create a new change request."""
        if self.has_pending_request(user_id, prompt_type):
            raise DuplicatePendingRequestError(
                f"User {user_id} already has a pending request for {prompt_type.value}"
            )

        request = ChangeRequest(
            id=f"cr-{uuid.uuid4().hex[:8]}",
            workspace_id="organization",
            prompt_type=prompt_type,
            submitted_by=user_id,
            submitted_at=datetime.now(timezone.utc),
            status=ChangeRequestStatus.PENDING,
            current_content=self._get_current_content(prompt_type),
            proposed_content=proposed_content,
            description=description,
        )

        self._save_request(request)
        return request

    def get_change_request(self, request_id: str) -> ChangeRequest:
        """Get a change request by ID."""
        return self._load_request(request_id)

    def list_change_requests(
        self, status: ChangeRequestStatus | None = None
    ) -> list[ChangeRequest]:
        """List all change requests, optionally filtered by status."""
        requests = []
        for file_path in self.requests_path.glob("cr-*.json"):
            data = json.loads(file_path.read_text())
            request = ChangeRequest(**data)
            if status is None or request.status == status:
                requests.append(request)
        return sorted(requests, key=lambda r: r.submitted_at, reverse=True)

    def approve_change_request(
        self,
        request_id: str,
        reviewer_id: str,
        feedback: str | None = None,
    ) -> ChangeRequest:
        """Approve a change request and apply the changes."""
        request = self._load_request(request_id)

        # Check for conflicts
        current = self._get_current_content(request.prompt_type)
        if current != request.current_content:
            raise ChangeRequestConflictError(
                "Prompts have changed since submission. Request must be revised."
            )

        # Apply the changes
        self._save_prompt_content(request.prompt_type, request.proposed_content)

        # Update request status
        request.status = ChangeRequestStatus.APPROVED
        request.reviewed_by = reviewer_id
        request.reviewed_at = datetime.now(timezone.utc)
        request.review_feedback = feedback

        self._save_request(request)
        return request

    def reject_change_request(
        self,
        request_id: str,
        reviewer_id: str,
        feedback: str | None = None,
    ) -> ChangeRequest:
        """Reject a change request."""
        request = self._load_request(request_id)

        request.status = ChangeRequestStatus.REJECTED
        request.reviewed_by = reviewer_id
        request.reviewed_at = datetime.now(timezone.utc)
        request.review_feedback = feedback

        self._save_request(request)
        return request

    def revise_change_request(
        self,
        request_id: str,
        proposed_content: dict,
        description: str | None = None,
    ) -> ChangeRequest:
        """Revise a rejected change request."""
        request = self._load_request(request_id)

        if request.status != ChangeRequestStatus.REJECTED:
            raise InvalidChangeRequestStateError(
                f"Cannot revise request with status {request.status.value}"
            )

        # Reset to pending with fresh snapshot
        request.status = ChangeRequestStatus.PENDING
        request.current_content = self._get_current_content(request.prompt_type)
        request.proposed_content = proposed_content
        request.description = description
        request.reviewed_by = None
        request.reviewed_at = None
        request.review_feedback = None

        self._save_request(request)
        return request

    def withdraw_change_request(self, request_id: str) -> None:
        """Withdraw (delete) a pending change request."""
        request = self._load_request(request_id)

        if request.status != ChangeRequestStatus.PENDING:
            raise InvalidChangeRequestStateError(
                f"Cannot withdraw request with status {request.status.value}"
            )

        self._delete_request(request_id)

    def has_pending_request(self, user_id: str, prompt_type: PromptType) -> bool:
        """Check if user has a pending request for the given prompt type."""
        for request in self.list_change_requests(status=ChangeRequestStatus.PENDING):
            if request.submitted_by == user_id and request.prompt_type == prompt_type:
                return True
        return False

    def count_pending_requests(self) -> int:
        """Count all pending change requests."""
        return len(self.list_change_requests(status=ChangeRequestStatus.PENDING))
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_change_request_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/change_request_service.py tests/test_change_request_service.py
git commit -m "feat(services): add ChangeRequestService for approval workflow"
```

---

## Task 6: Create UserService for Role Management

**Files:**
- Create: `app/services/user_service.py`
- Test: `tests/test_user_service.py`

**Step 1: Write the failing test**

```python
# tests/test_user_service.py
import pytest


@pytest.fixture
def db_path(tmp_path):
    from app.db import init_db

    path = str(tmp_path / "test.db")
    init_db(path)
    return path


def test_list_users(db_path):
    """list_users returns all users."""
    from app.db import create_user
    from app.services.user_service import UserService

    create_user(db_path, "user1@example.com", "hash1")
    create_user(db_path, "user2@example.com", "hash2")

    service = UserService(db_path)
    users = service.list_users()

    assert len(users) == 2


def test_update_user_role(db_path):
    """update_user_role changes a user's role."""
    from app.db import create_user
    from app.models.auth import UserRole
    from app.services.user_service import UserService

    user = create_user(db_path, "user@example.com", "hash")

    service = UserService(db_path)
    updated = service.update_user_role(user.id, UserRole.APPROVER)

    assert updated.role == UserRole.APPROVER


def test_cannot_demote_last_approver(db_path):
    """update_user_role raises error when demoting last approver."""
    from app.db import create_user
    from app.models.auth import UserRole
    from app.services.user_service import LastApproverError, UserService

    user = create_user(db_path, "approver@example.com", "hash", UserRole.APPROVER)

    service = UserService(db_path)

    with pytest.raises(LastApproverError):
        service.update_user_role(user.id, UserRole.USER)


def test_can_demote_approver_when_others_exist(db_path):
    """update_user_role allows demotion when other approvers exist."""
    from app.db import create_user
    from app.models.auth import UserRole
    from app.services.user_service import UserService

    user1 = create_user(db_path, "approver1@example.com", "hash1", UserRole.APPROVER)
    create_user(db_path, "approver2@example.com", "hash2", UserRole.APPROVER)

    service = UserService(db_path)
    updated = service.update_user_role(user1.id, UserRole.USER)

    assert updated.role == UserRole.USER
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_user_service.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# app/services/user_service.py
from app.db import count_approvers, get_all_users, get_user_by_id, update_user_role
from app.models.auth import User, UserRole


class LastApproverError(Exception):
    """Raised when trying to demote the last approver."""

    pass


class UserService:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def list_users(self) -> list[User]:
        """List all users."""
        return get_all_users(self.db_path)

    def update_user_role(self, user_id: str, role: UserRole) -> User:
        """Update a user's role. Raises LastApproverError if demoting last approver."""
        current_user = get_user_by_id(self.db_path, user_id)

        # Check if this would remove the last approver
        if current_user.role == UserRole.APPROVER and role == UserRole.USER:
            if count_approvers(self.db_path) <= 1:
                raise LastApproverError("Cannot demote the last approver")

        update_user_role(self.db_path, user_id, role)
        return get_user_by_id(self.db_path, user_id)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_user_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/user_service.py tests/test_user_service.py
git commit -m "feat(services): add UserService for role management"
```

---

## Task 7: Create Organization Workspace Initialization

**Files:**
- Modify: `app/services/workspace_service.py`
- Test: `tests/test_workspace_service.py`

**Step 1: Write the failing test**

Add to `tests/test_workspace_service.py`:

```python
def test_init_organization_workspace_creates_workspace(tmp_path, monkeypatch):
    """init_organization_workspace creates org workspace if missing."""
    import json

    workspaces_path = tmp_path / "workspaces"
    workspaces_path.mkdir()

    monkeypatch.setenv("WORKSPACES_PATH", str(workspaces_path))

    from app.services.workspace_service import WorkspaceService

    service = WorkspaceService(str(workspaces_path))
    service.init_organization_workspace()

    org_path = workspaces_path / "organization"
    assert org_path.exists()
    assert (org_path / "metadata.json").exists()
    assert (org_path / "category_definitions.json").exists()
    assert (org_path / "few_shot_examples.json").exists()
    assert (org_path / "system_prompt.json").exists()
    assert (org_path / "change_requests").exists()

    metadata = json.loads((org_path / "metadata.json").read_text())
    assert metadata["id"] == "organization"
    assert metadata["name"] == "Organization"
    assert metadata["user_id"] is None


def test_init_organization_workspace_skips_if_exists(tmp_path, monkeypatch):
    """init_organization_workspace does nothing if workspace exists."""
    import json

    workspaces_path = tmp_path / "workspaces"
    org_path = workspaces_path / "organization"
    org_path.mkdir(parents=True)

    # Create existing metadata
    (org_path / "metadata.json").write_text(
        json.dumps({"id": "organization", "name": "Custom Name", "user_id": None})
    )

    from app.services.workspace_service import WorkspaceService

    service = WorkspaceService(str(workspaces_path))
    service.init_organization_workspace()

    # Verify name wasn't overwritten
    metadata = json.loads((org_path / "metadata.json").read_text())
    assert metadata["name"] == "Custom Name"


def test_list_workspaces_includes_organization(tmp_path, monkeypatch):
    """list_workspaces_for_user includes organization workspace first."""
    workspaces_path = tmp_path / "workspaces"
    workspaces_path.mkdir()

    from app.services.workspace_service import WorkspaceService

    service = WorkspaceService(str(workspaces_path))
    service.init_organization_workspace()

    # Create a user workspace
    service.create_workspace("My Workspace", "u-user1234")

    workspaces = service.list_workspaces_for_user("u-user1234")

    assert len(workspaces) == 2
    assert workspaces[0].id == "organization"
    assert workspaces[0].is_organization is True
    assert workspaces[1].name == "My Workspace"
    assert workspaces[1].is_organization is False


def test_cannot_delete_organization_workspace(tmp_path, monkeypatch):
    """delete_workspace raises error for organization workspace."""
    workspaces_path = tmp_path / "workspaces"
    workspaces_path.mkdir()

    from app.services.workspace_service import (
        OrganizationWorkspaceProtectedError,
        WorkspaceService,
    )

    service = WorkspaceService(str(workspaces_path))
    service.init_organization_workspace()

    with pytest.raises(OrganizationWorkspaceProtectedError):
        service.delete_workspace("organization")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_workspace_service.py::test_init_organization_workspace_creates_workspace -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Update `app/models/workspace.py` to add `is_organization` field:

```python
class WorkspaceMetadata(BaseModel):
    id: str
    name: str
    created_at: datetime
    user_id: str | None = None  # None for organization workspace
    description: str | None = None
    news_source: NewsSource = NewsSource.MERGE
    is_organization: bool = False
```

Update `app/services/workspace_service.py`:

```python
# Add new exception
class OrganizationWorkspaceProtectedError(Exception):
    """Raised when trying to delete organization workspace."""
    pass


# Add to WorkspaceService class
def init_organization_workspace(self) -> None:
    """Initialize the organization workspace if it doesn't exist."""
    org_path = self.workspaces_path / "organization"

    if org_path.exists():
        return

    org_path.mkdir(parents=True)
    (org_path / "change_requests").mkdir()

    # Create metadata
    metadata = {
        "id": "organization",
        "name": "Organization",
        "user_id": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "description": "Shared organization workspace",
        "news_source": "MERGE",
    }
    (org_path / "metadata.json").write_text(json.dumps(metadata, indent=2))

    # Copy default prompts
    default_categories = {"categories": []}
    default_few_shots = {"examples": []}
    default_system_prompt = {"prompt": ""}

    (org_path / "category_definitions.json").write_text(
        json.dumps(default_categories, indent=2)
    )
    (org_path / "few_shot_examples.json").write_text(
        json.dumps(default_few_shots, indent=2)
    )
    (org_path / "system_prompt.json").write_text(
        json.dumps(default_system_prompt, indent=2)
    )


def list_workspaces_for_user(self, user_id: str) -> list[WorkspaceMetadata]:
    """List workspaces for a user, including organization workspace first."""
    workspaces = []

    # Add organization workspace first if it exists
    org_path = self.workspaces_path / "organization"
    if org_path.exists():
        org_metadata = self._load_metadata("organization")
        org_metadata.is_organization = True
        workspaces.append(org_metadata)

    # Add user's personal workspaces
    for path in self.workspaces_path.iterdir():
        if path.is_dir() and path.name != "organization":
            try:
                metadata = self._load_metadata(path.name)
                if metadata.user_id == user_id:
                    metadata.is_organization = False
                    workspaces.append(metadata)
            except WorkspaceNotFoundError:
                continue

    return workspaces


def delete_workspace(self, workspace_id: str) -> None:
    """Delete a workspace. Raises error for organization workspace."""
    if workspace_id == "organization":
        raise OrganizationWorkspaceProtectedError(
            "Organization workspace cannot be deleted"
        )

    workspace_path = self.workspaces_path / workspace_id
    if not workspace_path.exists():
        raise WorkspaceNotFoundError(f"Workspace {workspace_id} not found")

    shutil.rmtree(workspace_path)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_workspace_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/models/workspace.py app/services/workspace_service.py tests/test_workspace_service.py
git commit -m "feat(workspace): add organization workspace initialization"
```

---

## Task 8: Update App Startup to Initialize Organization Workspace

**Files:**
- Modify: `app/main.py`
- Test: Manual verification

**Step 1: Update main.py lifespan**

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_db(settings.auth_db_path)

    # Initialize organization workspace
    from app.services.workspace_service import WorkspaceService
    workspace_service = WorkspaceService(settings.workspaces_path)
    workspace_service.init_organization_workspace()

    yield
```

**Step 2: Verify app starts without errors**

Run: `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000`
Expected: App starts, organization workspace created

**Step 3: Commit**

```bash
git add app/main.py
git commit -m "feat(startup): initialize organization workspace on app start"
```

---

## Task 9: Add Dependencies for New Services

**Files:**
- Modify: `app/dependencies.py`

**Step 1: Add new dependency functions**

```python
from app.services.change_request_service import ChangeRequestService
from app.services.user_service import UserService


def get_change_request_service() -> ChangeRequestService:
    settings = get_settings()
    return ChangeRequestService(settings.workspaces_path)


def get_user_service() -> UserService:
    settings = get_settings()
    return UserService(settings.auth_db_path)


def get_current_approver(request: Request) -> User:
    """Get current user and verify they are an approver."""
    user = get_current_user(request)
    if user.role != UserRole.APPROVER:
        raise HTTPException(status_code=403, detail="Approver role required")
    return user
```

**Step 2: Commit**

```bash
git add app/dependencies.py
git commit -m "feat(deps): add dependencies for change request and user services"
```

---

## Task 10: Create Change Request API Routes

**Files:**
- Create: `app/routes/change_requests.py`
- Test: `tests/test_routes_change_requests.py`

**Step 1: Write the failing test**

```python
# tests/test_routes_change_requests.py
import json
from pathlib import Path

import pytest
from starlette.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create test client with authenticated user."""
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setenv("NEWS_CSV_PATH", str(tmp_path / "news.csv"))
    monkeypatch.setenv("WORKSPACES_PATH", str(tmp_path / "workspaces"))
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", str(tmp_path / "system.txt"))
    monkeypatch.setenv("AUTH_DB_PATH", str(tmp_path / "auth.db"))

    (tmp_path / "news.csv").write_text("id,headline,content\n")
    (tmp_path / "workspaces").mkdir()
    (tmp_path / "system.txt").write_text("Test prompt")

    from app.db import init_db
    from app.dependencies import get_settings
    from app.main import app
    from app.services.auth_service import AuthService
    from app.services.workspace_service import WorkspaceService

    get_settings.cache_clear()
    init_db(str(tmp_path / "auth.db"))

    # Initialize organization workspace
    workspace_service = WorkspaceService(str(tmp_path / "workspaces"))
    workspace_service.init_organization_workspace()

    # Create initial categories for org workspace
    org_path = tmp_path / "workspaces" / "organization"
    (org_path / "category_definitions.json").write_text(
        json.dumps({"categories": [{"name": "Tech", "definition": "Tech news"}]})
    )

    # Create user (first user = approver)
    auth = AuthService(str(tmp_path / "auth.db"))
    user = auth.register_user("approver@example.com", "password123")
    session = auth.create_session(user.id)

    client = TestClient(app)
    client.cookies.set("session_id", session.id)

    # Store user info for tests
    client.user = user
    client.tmp_path = tmp_path

    return client


@pytest.fixture
def regular_user_client(client):
    """Create a second client with regular user role."""
    from app.services.auth_service import AuthService

    auth = AuthService(str(client.tmp_path / "auth.db"))
    user = auth.register_user("user@example.com", "password123")
    session = auth.create_session(user.id)

    regular_client = TestClient(client.app)
    regular_client.cookies.set("session_id", session.id)
    regular_client.user = user

    return regular_client


def test_create_change_request(regular_user_client):
    """POST /api/change-requests creates a change request."""
    response = regular_user_client.post(
        "/api/change-requests",
        json={
            "prompt_type": "CATEGORY_DEFINITIONS",
            "proposed_content": {"categories": [{"name": "Sports", "definition": "Sports news"}]},
            "description": "Adding sports",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"].startswith("cr-")
    assert data["status"] == "PENDING"
    assert data["submitted_by"] == regular_user_client.user.id


def test_list_change_requests(client, regular_user_client):
    """GET /api/change-requests lists all requests."""
    # Create a request as regular user
    regular_user_client.post(
        "/api/change-requests",
        json={
            "prompt_type": "CATEGORY_DEFINITIONS",
            "proposed_content": {},
        },
    )

    # List as approver
    response = client.get("/api/change-requests")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_list_change_requests_filter_status(client, regular_user_client):
    """GET /api/change-requests?status=PENDING filters by status."""
    regular_user_client.post(
        "/api/change-requests",
        json={"prompt_type": "CATEGORY_DEFINITIONS", "proposed_content": {}},
    )

    response = client.get("/api/change-requests?status=PENDING")
    assert len(response.json()) == 1

    response = client.get("/api/change-requests?status=APPROVED")
    assert len(response.json()) == 0


def test_get_change_request(client, regular_user_client):
    """GET /api/change-requests/{id} returns request details."""
    create_response = regular_user_client.post(
        "/api/change-requests",
        json={"prompt_type": "CATEGORY_DEFINITIONS", "proposed_content": {}},
    )
    request_id = create_response.json()["id"]

    response = client.get(f"/api/change-requests/{request_id}")

    assert response.status_code == 200
    assert response.json()["id"] == request_id


def test_approve_change_request(client, regular_user_client):
    """POST /api/change-requests/{id}/approve approves and applies changes."""
    create_response = regular_user_client.post(
        "/api/change-requests",
        json={
            "prompt_type": "CATEGORY_DEFINITIONS",
            "proposed_content": {"categories": [{"name": "New", "definition": "New cat"}]},
        },
    )
    request_id = create_response.json()["id"]

    response = client.post(
        f"/api/change-requests/{request_id}/approve",
        json={"feedback": "Looks good!"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"

    # Verify prompts were updated
    org_path = client.tmp_path / "workspaces" / "organization"
    saved = json.loads((org_path / "category_definitions.json").read_text())
    assert saved == {"categories": [{"name": "New", "definition": "New cat"}]}


def test_cannot_approve_own_request(client):
    """Approver cannot approve their own request."""
    create_response = client.post(
        "/api/change-requests",
        json={"prompt_type": "CATEGORY_DEFINITIONS", "proposed_content": {}},
    )
    request_id = create_response.json()["id"]

    response = client.post(f"/api/change-requests/{request_id}/approve", json={})

    assert response.status_code == 403
    assert "own" in response.json()["detail"].lower()


def test_reject_change_request(client, regular_user_client):
    """POST /api/change-requests/{id}/reject rejects request."""
    create_response = regular_user_client.post(
        "/api/change-requests",
        json={"prompt_type": "CATEGORY_DEFINITIONS", "proposed_content": {}},
    )
    request_id = create_response.json()["id"]

    response = client.post(
        f"/api/change-requests/{request_id}/reject",
        json={"feedback": "Needs work"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "REJECTED"


def test_revise_change_request(client, regular_user_client):
    """POST /api/change-requests/{id}/revise updates rejected request."""
    create_response = regular_user_client.post(
        "/api/change-requests",
        json={"prompt_type": "CATEGORY_DEFINITIONS", "proposed_content": {}},
    )
    request_id = create_response.json()["id"]

    # Reject first
    client.post(f"/api/change-requests/{request_id}/reject", json={})

    # Revise
    response = regular_user_client.post(
        f"/api/change-requests/{request_id}/revise",
        json={"proposed_content": {"updated": True}, "description": "Fixed"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "PENDING"
    assert response.json()["proposed_content"] == {"updated": True}


def test_withdraw_change_request(regular_user_client):
    """DELETE /api/change-requests/{id} withdraws pending request."""
    create_response = regular_user_client.post(
        "/api/change-requests",
        json={"prompt_type": "CATEGORY_DEFINITIONS", "proposed_content": {}},
    )
    request_id = create_response.json()["id"]

    response = regular_user_client.delete(f"/api/change-requests/{request_id}")

    assert response.status_code == 204

    # Verify deleted
    get_response = regular_user_client.get(f"/api/change-requests/{request_id}")
    assert get_response.status_code == 404


def test_regular_user_cannot_approve(regular_user_client, client):
    """Regular user cannot approve requests."""
    create_response = client.post(
        "/api/change-requests",
        json={"prompt_type": "CATEGORY_DEFINITIONS", "proposed_content": {}},
    )
    request_id = create_response.json()["id"]

    response = regular_user_client.post(
        f"/api/change-requests/{request_id}/approve", json={}
    )

    assert response.status_code == 403
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_routes_change_requests.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# app/routes/change_requests.py
from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_change_request_service, get_current_approver, get_current_user
from app.models.auth import User, UserRole
from app.models.change_request import (
    ChangeRequest,
    ChangeRequestStatus,
    CreateChangeRequestInput,
    PromptType,
    ReviewChangeRequestInput,
    ReviseChangeRequestInput,
)
from app.services.change_request_service import (
    ChangeRequestConflictError,
    ChangeRequestNotFoundError,
    ChangeRequestService,
    DuplicatePendingRequestError,
    InvalidChangeRequestStateError,
)

router = APIRouter(prefix="/change-requests", tags=["change-requests"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ChangeRequest)
def create_change_request(
    request: CreateChangeRequestInput,
    current_user: User = Depends(get_current_user),
    service: ChangeRequestService = Depends(get_change_request_service),
):
    """Submit a new change request for organization prompts."""
    try:
        return service.create_change_request(
            user_id=current_user.id,
            prompt_type=request.prompt_type,
            proposed_content=request.proposed_content,
            description=request.description,
        )
    except DuplicatePendingRequestError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("", response_model=list[ChangeRequest])
def list_change_requests(
    status: ChangeRequestStatus | None = None,
    current_user: User = Depends(get_current_user),
    service: ChangeRequestService = Depends(get_change_request_service),
):
    """List all change requests, optionally filtered by status."""
    return service.list_change_requests(status=status)


@router.get("/{request_id}", response_model=ChangeRequest)
def get_change_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    service: ChangeRequestService = Depends(get_change_request_service),
):
    """Get a specific change request."""
    try:
        return service.get_change_request(request_id)
    except ChangeRequestNotFoundError:
        raise HTTPException(status_code=404, detail="Change request not found")


@router.post("/{request_id}/approve", response_model=ChangeRequest)
def approve_change_request(
    request_id: str,
    input_data: ReviewChangeRequestInput,
    current_user: User = Depends(get_current_approver),
    service: ChangeRequestService = Depends(get_change_request_service),
):
    """Approve a change request and apply the changes."""
    try:
        request = service.get_change_request(request_id)
    except ChangeRequestNotFoundError:
        raise HTTPException(status_code=404, detail="Change request not found")

    if request.submitted_by == current_user.id:
        raise HTTPException(status_code=403, detail="Cannot approve your own change request")

    try:
        return service.approve_change_request(
            request_id=request_id,
            reviewer_id=current_user.id,
            feedback=input_data.feedback,
        )
    except ChangeRequestConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/{request_id}/reject", response_model=ChangeRequest)
def reject_change_request(
    request_id: str,
    input_data: ReviewChangeRequestInput,
    current_user: User = Depends(get_current_approver),
    service: ChangeRequestService = Depends(get_change_request_service),
):
    """Reject a change request."""
    try:
        return service.reject_change_request(
            request_id=request_id,
            reviewer_id=current_user.id,
            feedback=input_data.feedback,
        )
    except ChangeRequestNotFoundError:
        raise HTTPException(status_code=404, detail="Change request not found")


@router.post("/{request_id}/revise", response_model=ChangeRequest)
def revise_change_request(
    request_id: str,
    input_data: ReviseChangeRequestInput,
    current_user: User = Depends(get_current_user),
    service: ChangeRequestService = Depends(get_change_request_service),
):
    """Revise a rejected change request."""
    try:
        request = service.get_change_request(request_id)
    except ChangeRequestNotFoundError:
        raise HTTPException(status_code=404, detail="Change request not found")

    if request.submitted_by != current_user.id:
        raise HTTPException(status_code=403, detail="Can only revise your own requests")

    try:
        return service.revise_change_request(
            request_id=request_id,
            proposed_content=input_data.proposed_content,
            description=input_data.description,
        )
    except InvalidChangeRequestStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def withdraw_change_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    service: ChangeRequestService = Depends(get_change_request_service),
):
    """Withdraw a pending change request."""
    try:
        request = service.get_change_request(request_id)
    except ChangeRequestNotFoundError:
        raise HTTPException(status_code=404, detail="Change request not found")

    if request.submitted_by != current_user.id:
        raise HTTPException(status_code=403, detail="Can only withdraw your own requests")

    try:
        service.withdraw_change_request(request_id)
    except InvalidChangeRequestStateError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**Step 4: Register router in main.py**

Add to `app/main.py`:

```python
from app.routes.change_requests import router as change_requests_router

app.include_router(change_requests_router, prefix="/api")
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_routes_change_requests.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add app/routes/change_requests.py app/main.py tests/test_routes_change_requests.py
git commit -m "feat(api): add change request API endpoints"
```

---

## Task 11: Create User Management API Routes

**Files:**
- Create: `app/routes/users.py`
- Test: `tests/test_routes_users.py`

**Step 1: Write the failing test**

```python
# tests/test_routes_users.py
import pytest
from starlette.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create test client with approver user."""
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setenv("NEWS_CSV_PATH", str(tmp_path / "news.csv"))
    monkeypatch.setenv("WORKSPACES_PATH", str(tmp_path / "workspaces"))
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", str(tmp_path / "system.txt"))
    monkeypatch.setenv("AUTH_DB_PATH", str(tmp_path / "auth.db"))

    (tmp_path / "news.csv").write_text("id,headline,content\n")
    (tmp_path / "workspaces").mkdir()
    (tmp_path / "system.txt").write_text("Test prompt")

    from app.db import init_db
    from app.dependencies import get_settings
    from app.main import app
    from app.services.auth_service import AuthService

    get_settings.cache_clear()
    init_db(str(tmp_path / "auth.db"))

    auth = AuthService(str(tmp_path / "auth.db"))
    user = auth.register_user("approver@example.com", "password123")
    session = auth.create_session(user.id)

    client = TestClient(app)
    client.cookies.set("session_id", session.id)
    client.user = user
    client.tmp_path = tmp_path
    client.auth = auth

    return client


def test_get_current_user(client):
    """GET /api/users/me returns current user with role."""
    response = client.get("/api/users/me")

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "approver@example.com"
    assert data["role"] == "APPROVER"


def test_list_users_as_approver(client):
    """GET /api/users lists all users for approvers."""
    # Create another user
    client.auth.register_user("user@example.com", "password")

    response = client.get("/api/users")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_list_users_forbidden_for_regular_user(client):
    """GET /api/users is forbidden for regular users."""
    user = client.auth.register_user("user@example.com", "password")
    session = client.auth.create_session(user.id)

    regular_client = TestClient(client.app)
    regular_client.cookies.set("session_id", session.id)

    response = regular_client.get("/api/users")

    assert response.status_code == 403


def test_update_user_role(client):
    """PATCH /api/users/{id}/role updates user role."""
    user = client.auth.register_user("user@example.com", "password")

    response = client.patch(
        f"/api/users/{user.id}/role",
        json={"role": "APPROVER"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "APPROVER"


def test_cannot_update_own_role(client):
    """PATCH /api/users/{id}/role fails for own role."""
    response = client.patch(
        f"/api/users/{client.user.id}/role",
        json={"role": "USER"},
    )

    assert response.status_code == 403
    assert "own role" in response.json()["detail"].lower()


def test_cannot_demote_last_approver(client):
    """PATCH /api/users/{id}/role fails when demoting last approver."""
    # Create second approver, then try to demote first via second
    second = client.auth.register_user("approver2@example.com", "password")
    client.patch(f"/api/users/{second.id}/role", json={"role": "APPROVER"})

    # Login as second approver
    session = client.auth.create_session(second.id)
    second_client = TestClient(client.app)
    second_client.cookies.set("session_id", session.id)

    # Demote first approver
    second_client.patch(f"/api/users/{client.user.id}/role", json={"role": "USER"})

    # Now try to demote second (last) approver - should fail
    response = client.patch(f"/api/users/{second.id}/role", json={"role": "USER"})

    assert response.status_code == 400
    assert "last approver" in response.json()["detail"].lower()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_routes_users.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# app/routes/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.dependencies import get_current_approver, get_current_user, get_user_service
from app.models.auth import User, UserRole
from app.services.user_service import LastApproverError, UserService

router = APIRouter(prefix="/users", tags=["users"])


class UpdateRoleRequest(BaseModel):
    role: UserRole


@router.get("/me", response_model=User)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get the current authenticated user."""
    return current_user


@router.get("", response_model=list[User])
def list_users(
    current_user: User = Depends(get_current_approver),
    service: UserService = Depends(get_user_service),
):
    """List all users. Approver only."""
    return service.list_users()


@router.patch("/{user_id}/role", response_model=User)
def update_user_role(
    user_id: str,
    request: UpdateRoleRequest,
    current_user: User = Depends(get_current_approver),
    service: UserService = Depends(get_user_service),
):
    """Update a user's role. Approver only, cannot change own role."""
    if user_id == current_user.id:
        raise HTTPException(status_code=403, detail="Cannot change your own role")

    try:
        return service.update_user_role(user_id, request.role)
    except LastApproverError:
        raise HTTPException(status_code=400, detail="Cannot demote the last approver")
```

**Step 4: Register router in main.py**

Add to `app/main.py`:

```python
from app.routes.users import router as users_router

app.include_router(users_router, prefix="/api")
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_routes_users.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add app/routes/users.py app/main.py tests/test_routes_users.py
git commit -m "feat(api): add user management API endpoints"
```

---

## Task 12: Modify Prompts Routes for Approval Workflow

**Files:**
- Modify: `app/routes/prompts.py`
- Test: `tests/test_routes_prompts.py`

**Step 1: Write the failing test**

Add to `tests/test_routes_prompts.py`:

```python
def test_save_org_categories_as_user_creates_change_request(client, regular_user_client):
    """PUT /api/workspaces/organization/prompts/categories creates change request for users."""
    response = regular_user_client.put(
        "/api/workspaces/organization/prompts/categories",
        json={"categories": [{"name": "New", "definition": "New cat"}]},
    )

    assert response.status_code == 202
    data = response.json()
    assert data["id"].startswith("cr-")
    assert data["status"] == "PENDING"


def test_save_org_categories_as_approver_saves_directly(client):
    """PUT /api/workspaces/organization/prompts/categories saves directly for approvers."""
    response = client.put(
        "/api/workspaces/organization/prompts/categories",
        json={"categories": [{"name": "Direct", "definition": "Direct save"}]},
    )

    assert response.status_code == 200

    # Verify saved
    get_response = client.get("/api/workspaces/organization/prompts/categories")
    assert get_response.json()["categories"][0]["name"] == "Direct"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_routes_prompts.py::test_save_org_categories_as_user_creates_change_request -v`
Expected: FAIL

**Step 3: Update prompts.py**

Modify the PUT endpoints to check for organization workspace and user role:

```python
from app.dependencies import get_change_request_service
from app.models.auth import UserRole
from app.models.change_request import PromptType
from app.services.change_request_service import ChangeRequestService, DuplicatePendingRequestError


@router.put("/{workspace_id}/prompts/categories")
def save_categories(
    workspace_id: str,
    request: PromptConfig,
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
    change_request_service: ChangeRequestService = Depends(get_change_request_service),
):
    """Save category definitions. Creates change request for org workspace if user is not approver."""
    if workspace_id == "organization" and current_user.role != UserRole.APPROVER:
        try:
            change_request = change_request_service.create_change_request(
                user_id=current_user.id,
                prompt_type=PromptType.CATEGORY_DEFINITIONS,
                proposed_content=request.model_dump(),
            )
            return JSONResponse(status_code=202, content=change_request.model_dump(mode="json"))
        except DuplicatePendingRequestError as e:
            raise HTTPException(status_code=409, detail=str(e))

    prompt_service.save_categories(workspace_id, request)
    return request


@router.put("/{workspace_id}/prompts/few-shots")
def save_few_shots(
    workspace_id: str,
    request: FewShotConfig,
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
    change_request_service: ChangeRequestService = Depends(get_change_request_service),
):
    """Save few-shot examples. Creates change request for org workspace if user is not approver."""
    if workspace_id == "organization" and current_user.role != UserRole.APPROVER:
        try:
            change_request = change_request_service.create_change_request(
                user_id=current_user.id,
                prompt_type=PromptType.FEW_SHOTS,
                proposed_content=request.model_dump(),
            )
            return JSONResponse(status_code=202, content=change_request.model_dump(mode="json"))
        except DuplicatePendingRequestError as e:
            raise HTTPException(status_code=409, detail=str(e))

    prompt_service.save_few_shots(workspace_id, request)
    return request


@router.put("/{workspace_id}/prompts/system-prompt")
def save_system_prompt(
    workspace_id: str,
    request: SystemPromptConfig,
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
    change_request_service: ChangeRequestService = Depends(get_change_request_service),
):
    """Save system prompt. Creates change request for org workspace if user is not approver."""
    if workspace_id == "organization" and current_user.role != UserRole.APPROVER:
        try:
            change_request = change_request_service.create_change_request(
                user_id=current_user.id,
                prompt_type=PromptType.SYSTEM_PROMPT,
                proposed_content=request.model_dump(),
            )
            return JSONResponse(status_code=202, content=change_request.model_dump(mode="json"))
        except DuplicatePendingRequestError as e:
            raise HTTPException(status_code=409, detail=str(e))

    prompt_service.save_system_prompt(workspace_id, request)
    return request
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_routes_prompts.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/routes/prompts.py tests/test_routes_prompts.py
git commit -m "feat(prompts): integrate approval workflow for org workspace"
```

---

## Task 13: Add Copy From Organization Endpoint

**Files:**
- Modify: `app/routes/workspaces.py`
- Test: `tests/test_routes_workspaces.py`

**Step 1: Write the failing test**

Add to `tests/test_routes_workspaces.py`:

```python
def test_copy_from_organization(client):
    """POST /api/workspaces/{id}/copy-from-organization copies org prompts."""
    import json

    # Setup org prompts
    org_path = client.tmp_path / "workspaces" / "organization"
    org_path.mkdir(parents=True, exist_ok=True)
    (org_path / "category_definitions.json").write_text(
        json.dumps({"categories": [{"name": "Org Cat", "definition": "From org"}]})
    )
    (org_path / "few_shot_examples.json").write_text(json.dumps({"examples": []}))
    (org_path / "system_prompt.json").write_text(json.dumps({"prompt": "Org prompt"}))
    (org_path / "metadata.json").write_text(json.dumps({"id": "organization", "name": "Org", "user_id": None}))

    # Create user workspace
    create_response = client.post("/api/workspaces", json={"name": "My Workspace"})
    workspace_id = create_response.json()["id"]

    # Copy from org
    response = client.post(f"/api/workspaces/{workspace_id}/copy-from-organization")

    assert response.status_code == 200
    assert response.json()["success"] is True

    # Verify copied
    categories = client.get(f"/api/workspaces/{workspace_id}/prompts/categories").json()
    assert categories["categories"][0]["name"] == "Org Cat"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_routes_workspaces.py::test_copy_from_organization -v`
Expected: FAIL

**Step 3: Add endpoint to workspaces.py**

```python
@router.post("/{workspace_id}/copy-from-organization")
def copy_from_organization(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    prompt_service: PromptService = Depends(get_prompt_service),
):
    """Copy prompts from organization workspace to user workspace."""
    # Verify user owns the target workspace
    workspace = workspace_service.get_workspace(workspace_id)
    if workspace.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot copy to workspace you don't own")

    if workspace_id == "organization":
        raise HTTPException(status_code=400, detail="Cannot copy to organization workspace")

    # Get org prompts
    org_categories = prompt_service.get_categories("organization")
    org_few_shots = prompt_service.get_few_shots("organization")
    org_system_prompt = prompt_service.get_system_prompt("organization")

    # Save to user workspace
    prompt_service.save_categories(workspace_id, org_categories)
    prompt_service.save_few_shots(workspace_id, org_few_shots)
    prompt_service.save_system_prompt(workspace_id, org_system_prompt)

    return {"success": True}
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_routes_workspaces.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/routes/workspaces.py tests/test_routes_workspaces.py
git commit -m "feat(workspaces): add copy-from-organization endpoint"
```

---

## Task 14: Run Full Test Suite

**Step 1: Run all tests**

Run: `uv run pytest -v`
Expected: All tests pass

**Step 2: Fix any regressions**

If tests fail, fix them before proceeding.

**Step 3: Commit any fixes**

```bash
git add -A
git commit -m "fix: resolve test regressions"
```

---

## Task 15: Create UI for Approval Queue (Templates)

**Files:**
- Create: `templates/approvals.html`
- Modify: `templates/base.html` (add nav link and badge)

This task involves creating Jinja2 templates for the approval workflow UI. The implementation details depend on the existing template structure.

**Key UI Elements:**
1. Navigation badge showing pending request count (for approvers)
2. Approvals list page at `/approvals`
3. Change request detail view with diff display
4. Approve/Reject buttons with optional feedback

**Step 1: Examine existing templates**

Review `templates/base.html` and existing page templates for patterns.

**Step 2: Add nav link with badge for approvers**

Update base template navigation to show approvals link with pending count badge.

**Step 3: Create approvals list template**

Create `templates/approvals.html` with list of change requests.

**Step 4: Create approval detail template**

Create template showing diff and action buttons.

**Step 5: Commit**

```bash
git add templates/
git commit -m "feat(ui): add approval workflow templates"
```

---

## Task 16: Create UI Routes for Approval Pages

**Files:**
- Create or modify: `app/routes/pages.py`

**Step 1: Add page routes**

```python
@router.get("/approvals")
def approvals_page(
    request: Request,
    current_user: User = Depends(get_current_user_or_redirect),
    change_request_service: ChangeRequestService = Depends(get_change_request_service),
):
    """Approvals queue page."""
    requests = change_request_service.list_change_requests()
    pending_count = change_request_service.count_pending_requests()

    return templates.TemplateResponse(
        request,
        "approvals.html",
        {
            "user": current_user,
            "change_requests": requests,
            "pending_count": pending_count,
        },
    )


@router.get("/approvals/{request_id}")
def approval_detail_page(
    request: Request,
    request_id: str,
    current_user: User = Depends(get_current_user_or_redirect),
    change_request_service: ChangeRequestService = Depends(get_change_request_service),
):
    """Approval detail page with diff view."""
    try:
        change_request = change_request_service.get_change_request(request_id)
    except ChangeRequestNotFoundError:
        raise HTTPException(status_code=404, detail="Change request not found")

    return templates.TemplateResponse(
        request,
        "approval_detail.html",
        {
            "user": current_user,
            "change_request": change_request,
        },
    )
```

**Step 2: Commit**

```bash
git add app/routes/pages.py
git commit -m "feat(ui): add approval page routes"
```

---

## Task 17: Create User Management UI

**Files:**
- Create: `templates/users.html`
- Modify: `app/routes/pages.py`

**Step 1: Add users page route**

```python
@router.get("/users")
def users_page(
    request: Request,
    current_user: User = Depends(get_current_user_or_redirect),
    user_service: UserService = Depends(get_user_service),
):
    """User management page. Approver only."""
    if current_user.role != UserRole.APPROVER:
        raise HTTPException(status_code=403, detail="Approver access required")

    users = user_service.list_users()

    return templates.TemplateResponse(
        request,
        "users.html",
        {"user": current_user, "users": users},
    )
```

**Step 2: Create users template**

Create `templates/users.html` with user list and role toggle buttons.

**Step 3: Commit**

```bash
git add templates/users.html app/routes/pages.py
git commit -m "feat(ui): add user management page"
```

---

## Task 18: Final Integration Test

**Step 1: Run full test suite**

Run: `uv run pytest -v`
Expected: All tests pass

**Step 2: Manual testing**

1. Start the app: `uv run uvicorn app.main:app --reload`
2. Register first user (becomes approver)
3. Register second user (regular user)
4. As regular user, try to edit org prompts - should create change request
5. As approver, view and approve the request
6. Verify prompts were updated

**Step 3: Final commit**

```bash
git add -A
git commit -m "feat: complete approval workflow implementation"
```

---

## Summary

This plan implements the approval workflow in 18 tasks:

1. **Tasks 1-3**: Update User model with roles
2. **Tasks 4-6**: Create ChangeRequest model and services
3. **Tasks 7-8**: Initialize organization workspace
4. **Tasks 9-13**: Create API endpoints
5. **Tasks 14-17**: Create UI templates and pages
6. **Task 18**: Final integration testing

Each task follows TDD with explicit test-first steps and frequent commits.
