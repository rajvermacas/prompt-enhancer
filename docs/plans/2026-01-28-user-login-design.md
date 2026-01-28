# User Login Feature Design

## Goal

Add multi-user isolation so each user sees only their own workspaces. Self-registration with email/password.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Motivation | Multi-user isolation | Users should only see their own workspaces |
| Account creation | Self-registration | Anyone can sign up with email/password |
| Existing workspaces | Wipe | Start fresh; existing data can be discarded |
| Credential storage | SQLite | Proper credential lookups, no external DB server |
| Session mechanism | Cookie-based sessions | Natural fit with Jinja2 server-rendered frontend |
| Session storage | SQLite (same DB as users) | Sessions survive server restarts, single storage location |
| Architecture | Minimal custom auth | Full control, no heavy dependencies, fits existing patterns |
| Workspace ownership | `user_id` in `metadata.json` | Consistent with existing file-based workspace storage |

## Data Model & Database Schema

SQLite database at `/data/auth.db` with two tables:

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,          -- UUID
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL       -- ISO 8601
);

CREATE TABLE sessions (
    id TEXT PRIMARY KEY,          -- UUID session token
    user_id TEXT NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL       -- 7 days from creation
);
```

Pydantic models in `app/models/auth.py`:

- `User` -- id, email, created_at (never includes password hash)
- `UserCreate` -- email, password (registration input)
- `UserLogin` -- email, password (login input)
- `Session` -- id, user_id, created_at, expires_at

Workspace ownership: Add a `user_id` field to the existing `WorkspaceMetadata` model. The workspace `metadata.json` files will include the owning user's ID.

Password hashing: `bcrypt` via the `passlib` library.

## Database Layer

New module `app/db.py` responsible for all SQLite operations:

- `init_db()` -- Creates the `auth.db` file and runs `CREATE TABLE IF NOT EXISTS` for both tables. Called on app startup.
- `create_user(email, password_hash) -> User` -- Inserts a new user. Raises exception if email already exists.
- `get_user_by_email(email) -> User` -- Looks up user by email. Raises exception if not found.
- `create_session(user_id) -> Session` -- Creates a session with UUID token and 7-day expiry.
- `get_session(session_id) -> Session` -- Retrieves session by ID. Raises exception if not found or expired.
- `delete_session(session_id)` -- Removes a session (logout).
- `delete_expired_sessions()` -- Cleanup utility to purge expired sessions.

Database path configured via `Settings` in `app/config.py` (`AUTH_DB_PATH=./data/auth.db`).

Uses Python's built-in `sqlite3` module -- no ORM.

## Auth Service & Dependencies

### Auth Service (`app/services/auth_service.py`)

- `register_user(email, password) -> User` -- Validates email format, hashes password with bcrypt, calls `create_user`. Raises exception if email already taken.
- `authenticate_user(email, password) -> User` -- Looks up user by email, verifies password against hash. Raises exception if credentials are invalid.
- `create_session(user_id) -> Session` -- Delegates to DB layer, returns session.
- `validate_session(session_id) -> User` -- Fetches session from DB, checks expiry, returns associated user. Raises exception if invalid or expired.
- `logout(session_id)` -- Deletes the session.

### Dependencies (`app/dependencies.py`)

Two new dependency functions:

- `get_current_user(request) -> User` -- For API routes. Reads `session_id` cookie, validates session, returns User. Raises `HTTPException(401)` on failure.
- `get_current_user_or_redirect(request) -> User` -- For page routes. Same logic but returns `RedirectResponse` to `/login` on failure.

## Routes & Pages

### New Auth Router (`app/routes/auth.py`)

- `GET /login` -- Renders login page. Redirects to home if already logged in.
- `POST /login` -- Authenticates user, creates session, sets cookie, redirects to home.
- `GET /register` -- Renders registration page. Redirects to home if already logged in.
- `POST /register` -- Creates user, creates session, sets cookie, redirects to home.
- `POST /logout` -- Deletes session, clears cookie, redirects to login.

### Cookie Configuration

- Name: `session_id`
- `httponly=True`
- `samesite="lax"`
- `secure=True` in production, `False` in dev
- `max_age=604800` (7 days)

### New Templates

- `app/templates/login.html` -- Email + password form, link to register, error display
- `app/templates/register.html` -- Email + password form, link to login, error display

### Existing Route Changes

All existing routes get auth dependency added:

- `app/routes/pages.py` -- `get_current_user_or_redirect`, pass `current_user` to templates
- `app/routes/workspaces.py` -- `get_current_user`, filter by `user.id`, set `user_id` on creation
- `app/routes/workflows.py` -- `get_current_user`
- `app/routes/news.py` -- `get_current_user`
- `app/routes/prompts.py` -- `get_current_user`
- `app/routes/workspace_news.py` -- `get_current_user`

## Error Handling

No global auth middleware. Uses FastAPI `Depends()` selectively:

- Page routes: Redirect to `/login` on auth failure
- API routes: Return `401 Unauthorized` JSON on auth failure

## UI Changes

- `app/templates/base.html` -- Add logout button in header when user is logged in

## File Change Summary

### New Files

| File | Purpose |
|------|---------|
| `app/models/auth.py` | User, UserCreate, UserLogin, Session models |
| `app/db.py` | SQLite init, user CRUD, session CRUD |
| `app/services/auth_service.py` | Register, authenticate, session management |
| `app/routes/auth.py` | Login, register, logout endpoints |
| `app/templates/login.html` | Login page |
| `app/templates/register.html` | Registration page |

### Modified Files

| File | Change |
|------|--------|
| `app/config.py` | Add `AUTH_DB_PATH` setting |
| `app/dependencies.py` | Add `get_current_user`, `get_current_user_or_redirect` |
| `app/models/workspace.py` | Add `user_id` field to `WorkspaceMetadata` |
| `app/services/workspace_service.py` | Filter workspaces by `user_id`, set `user_id` on creation |
| `app/routes/pages.py` | Add auth dependency, pass `current_user` to templates |
| `app/routes/workspaces.py` | Add auth dependency, pass `user.id` to service |
| `app/routes/workflows.py` | Add auth dependency |
| `app/routes/news.py` | Add auth dependency |
| `app/routes/prompts.py` | Add auth dependency |
| `app/routes/workspace_news.py` | Add auth dependency |
| `app/templates/base.html` | Add logout button in header |
| `app/main.py` | Mount auth router, call `init_db()` on startup |
| `pyproject.toml` | Add `passlib[bcrypt]` dependency |

### Unchanged

Agents, feedback service, news service, prompt service, and all AI logic remain untouched.
