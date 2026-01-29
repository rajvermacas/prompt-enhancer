from app.db import (
    count_approvers,
    get_all_users,
    get_user_by_id,
    update_user_role as db_update_user_role,
)
from app.models.auth import User, UserRole


class LastApproverError(Exception):
    """Raised when trying to demote the last approver."""

    def __init__(self):
        super().__init__("Cannot demote the last approver")


class UserService:
    """Service for managing user roles."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def list_users(self) -> list[User]:
        """Return all users."""
        return get_all_users(self.db_path)

    def update_user_role(self, user_id: str, role: UserRole) -> User:
        """Update a user's role.

        Raises LastApproverError if attempting to demote the last approver.
        Raises UserNotFoundError if the user does not exist.
        """
        current_user = get_user_by_id(self.db_path, user_id)

        if self._is_demoting_last_approver(current_user, role):
            raise LastApproverError()

        db_update_user_role(self.db_path, user_id, role)
        return get_user_by_id(self.db_path, user_id)

    def _is_demoting_last_approver(self, user: User, new_role: UserRole) -> bool:
        """Check if the role change would demote the last approver."""
        if user.role != UserRole.APPROVER:
            return False

        if new_role == UserRole.APPROVER:
            return False

        approver_count = count_approvers(self.db_path)
        return approver_count == 1
