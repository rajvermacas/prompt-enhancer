import pytest


@pytest.fixture
def db_path(tmp_path):
    from app.db import init_db

    path = str(tmp_path / "test_user_service.db")
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
