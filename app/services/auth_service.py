import bcrypt

from app.db import (
    create_session as db_create_session,
    create_user,
    delete_session,
    get_password_hash,
    get_session,
    get_user_by_email,
    get_user_by_id,
    UserNotFoundError,
)
from app.models.auth import Session, User


class InvalidCredentialsError(Exception):
    """Raised when login credentials are invalid."""

    def __init__(self):
        super().__init__("Invalid email or password")


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(
        password.encode("utf-8"), password_hash.encode("utf-8")
    )


class AuthService:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def register_user(self, email: str, password: str) -> User:
        """Register a new user. Raises DuplicateEmailError if email taken."""
        password_hash = _hash_password(password)
        return create_user(self.db_path, email, password_hash)

    def authenticate_user(self, email: str, password: str) -> User:
        """Authenticate a user. Raises InvalidCredentialsError on failure."""
        try:
            stored_hash = get_password_hash(self.db_path, email)
        except UserNotFoundError:
            raise InvalidCredentialsError()

        if not _verify_password(password, stored_hash):
            raise InvalidCredentialsError()

        return get_user_by_email(self.db_path, email)

    def create_session(self, user_id: str) -> Session:
        """Create a new session for the user."""
        return db_create_session(self.db_path, user_id)

    def validate_session(self, session_id: str) -> User:
        """Validate session and return the user. Raises on invalid/expired."""
        session = get_session(self.db_path, session_id)
        return get_user_by_id(self.db_path, session.user_id)

    def logout(self, session_id: str) -> None:
        """Delete the session."""
        delete_session(self.db_path, session_id)
