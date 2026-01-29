"""Tests for change request API routes."""

import pytest
from fastapi.testclient import TestClient


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

    from app.dependencies import get_settings

    get_settings.cache_clear()

    from app.db import init_db

    init_db(str(tmp_path / "auth.db"))

    from app.services.auth_service import AuthService

    auth = AuthService(str(tmp_path / "auth.db"))
    user = auth.register_user("user@example.com", "password123")
    session = auth.create_session(user.id)

    from app.main import app

    client = TestClient(app)
    client.cookies.set("session_id", session.id)
    # Store user_id for test access
    client.user_id = user.id
    return client


@pytest.fixture
def approver_client(tmp_path, monkeypatch):
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

    from app.dependencies import get_settings

    get_settings.cache_clear()

    from app.db import init_db

    init_db(str(tmp_path / "auth.db"))

    from app.services.auth_service import AuthService
    from app.services.user_service import UserService
    from app.models.auth import UserRole

    auth = AuthService(str(tmp_path / "auth.db"))
    user_service = UserService(str(tmp_path / "auth.db"))

    # Create approver user
    approver = auth.register_user("approver@example.com", "password123")
    user_service.update_user_role(approver.id, UserRole.APPROVER)

    # Create regular user
    regular_user = auth.register_user("user@example.com", "password123")

    # Create session for approver
    approver_session = auth.create_session(approver.id)

    # Create session for regular user
    regular_session = auth.create_session(regular_user.id)

    from app.main import app

    approver_client = TestClient(app)
    approver_client.cookies.set("session_id", approver_session.id)
    approver_client.user_id = approver.id

    regular_client = TestClient(app)
    regular_client.cookies.set("session_id", regular_session.id)
    regular_client.user_id = regular_user.id

    # Return both clients
    approver_client.regular_client = regular_client
    return approver_client


# POST /api/change-requests tests
class TestCreateChangeRequest:
    """Tests for POST /api/change-requests."""

    def test_create_change_request_success(self, client):
        """Creating a change request returns 201 and the created request."""
        payload = {
            "prompt_type": "CATEGORY_DEFINITIONS",
            "proposed_content": {"categories": [{"name": "Test", "definition": "A test"}]},
            "description": "Add a test category",
        }

        response = client.post("/api/change-requests", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["prompt_type"] == "CATEGORY_DEFINITIONS"
        assert data["status"] == "PENDING"
        assert data["proposed_content"] == payload["proposed_content"]
        assert data["description"] == "Add a test category"
        assert data["submitted_by"] == client.user_id
        assert data["id"].startswith("cr-")

    def test_create_change_request_without_description(self, client):
        """Creating a change request without description succeeds."""
        payload = {
            "prompt_type": "SYSTEM_PROMPT",
            "proposed_content": {"content": "New system prompt"},
        }

        response = client.post("/api/change-requests", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["description"] is None

    def test_create_duplicate_pending_request_returns_409(self, client):
        """Creating duplicate pending request for same prompt type returns 409."""
        payload = {
            "prompt_type": "CATEGORY_DEFINITIONS",
            "proposed_content": {"categories": []},
        }

        # First request succeeds
        response1 = client.post("/api/change-requests", json=payload)
        assert response1.status_code == 201

        # Second request for same type fails
        response2 = client.post("/api/change-requests", json=payload)
        assert response2.status_code == 409
        assert "pending" in response2.json()["detail"].lower()

    def test_create_change_request_unauthenticated(self, client):
        """Creating change request without authentication returns 401."""
        client.cookies.clear()
        payload = {
            "prompt_type": "CATEGORY_DEFINITIONS",
            "proposed_content": {"categories": []},
        }

        response = client.post("/api/change-requests", json=payload)

        assert response.status_code == 401


# GET /api/change-requests tests
class TestListChangeRequests:
    """Tests for GET /api/change-requests."""

    def test_list_change_requests_empty(self, client):
        """Listing change requests returns empty list initially."""
        response = client.get("/api/change-requests")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_change_requests_returns_all(self, client):
        """Listing change requests returns all requests."""
        # Create multiple requests
        client.post("/api/change-requests", json={
            "prompt_type": "CATEGORY_DEFINITIONS",
            "proposed_content": {"categories": []},
        })
        client.post("/api/change-requests", json={
            "prompt_type": "SYSTEM_PROMPT",
            "proposed_content": {"content": "Test"},
        })

        response = client.get("/api/change-requests")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_list_change_requests_filter_by_status(self, approver_client):
        """Filtering by status returns only matching requests."""
        # Create a request using regular user
        regular_client = approver_client.regular_client
        regular_client.post("/api/change-requests", json={
            "prompt_type": "CATEGORY_DEFINITIONS",
            "proposed_content": {"categories": []},
        })

        # Get the request ID
        all_requests = regular_client.get("/api/change-requests").json()
        request_id = all_requests[0]["id"]

        # Approve with the approver
        approver_client.post(f"/api/change-requests/{request_id}/approve", json={})

        # Filter by PENDING (should be 0)
        response = regular_client.get("/api/change-requests?status=PENDING")
        assert response.status_code == 200
        assert len(response.json()) == 0

        # Filter by APPROVED (should be 1)
        response = regular_client.get("/api/change-requests?status=APPROVED")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_list_change_requests_unauthenticated(self, client):
        """Listing change requests without authentication returns 401."""
        client.cookies.clear()

        response = client.get("/api/change-requests")

        assert response.status_code == 401


# GET /api/change-requests/{request_id} tests
class TestGetChangeRequest:
    """Tests for GET /api/change-requests/{request_id}."""

    def test_get_change_request_success(self, client):
        """Getting a change request by ID returns the request."""
        create_response = client.post("/api/change-requests", json={
            "prompt_type": "CATEGORY_DEFINITIONS",
            "proposed_content": {"categories": []},
        })
        request_id = create_response.json()["id"]

        response = client.get(f"/api/change-requests/{request_id}")

        assert response.status_code == 200
        assert response.json()["id"] == request_id

    def test_get_change_request_not_found(self, client):
        """Getting non-existent change request returns 404."""
        response = client.get("/api/change-requests/cr-nonexistent")

        assert response.status_code == 404

    def test_get_change_request_unauthenticated(self, client):
        """Getting change request without authentication returns 401."""
        client.cookies.clear()

        response = client.get("/api/change-requests/cr-12345678")

        assert response.status_code == 401


# POST /api/change-requests/{request_id}/approve tests
class TestApproveChangeRequest:
    """Tests for POST /api/change-requests/{request_id}/approve."""

    def test_approve_change_request_success(self, approver_client):
        """Approver can approve a change request."""
        regular_client = approver_client.regular_client

        # Create request as regular user
        create_response = regular_client.post("/api/change-requests", json={
            "prompt_type": "CATEGORY_DEFINITIONS",
            "proposed_content": {"categories": [{"name": "Approved", "definition": "Test"}]},
        })
        request_id = create_response.json()["id"]

        # Approve as approver
        response = approver_client.post(
            f"/api/change-requests/{request_id}/approve",
            json={"feedback": "Looks good!"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "APPROVED"
        assert data["review_feedback"] == "Looks good!"
        assert data["reviewed_by"] == approver_client.user_id

    def test_approve_change_request_without_feedback(self, approver_client):
        """Approver can approve without providing feedback."""
        regular_client = approver_client.regular_client

        create_response = regular_client.post("/api/change-requests", json={
            "prompt_type": "SYSTEM_PROMPT",
            "proposed_content": {"content": "New prompt"},
        })
        request_id = create_response.json()["id"]

        response = approver_client.post(
            f"/api/change-requests/{request_id}/approve",
            json={},
        )

        assert response.status_code == 200
        assert response.json()["review_feedback"] is None

    def test_approve_own_request_returns_403(self, approver_client):
        """Approver cannot approve their own request."""
        # Create request as approver themselves
        create_response = approver_client.post("/api/change-requests", json={
            "prompt_type": "CATEGORY_DEFINITIONS",
            "proposed_content": {"categories": []},
        })
        request_id = create_response.json()["id"]

        # Try to approve own request
        response = approver_client.post(
            f"/api/change-requests/{request_id}/approve",
            json={},
        )

        assert response.status_code == 403
        assert "own request" in response.json()["detail"].lower()

    def test_approve_non_approver_returns_403(self, approver_client):
        """Non-approver cannot approve requests."""
        regular_client = approver_client.regular_client

        # Create request
        create_response = approver_client.post("/api/change-requests", json={
            "prompt_type": "CATEGORY_DEFINITIONS",
            "proposed_content": {"categories": []},
        })
        request_id = create_response.json()["id"]

        # Try to approve as regular user
        response = regular_client.post(
            f"/api/change-requests/{request_id}/approve",
            json={},
        )

        assert response.status_code == 403

    def test_approve_not_found_returns_404(self, approver_client):
        """Approving non-existent request returns 404."""
        response = approver_client.post(
            "/api/change-requests/cr-nonexistent/approve",
            json={},
        )

        assert response.status_code == 404

    def test_approve_already_approved_returns_409(self, approver_client):
        """Approving already approved request returns 409."""
        regular_client = approver_client.regular_client

        create_response = regular_client.post("/api/change-requests", json={
            "prompt_type": "CATEGORY_DEFINITIONS",
            "proposed_content": {"categories": []},
        })
        request_id = create_response.json()["id"]

        # Approve once
        approver_client.post(f"/api/change-requests/{request_id}/approve", json={})

        # Try to approve again
        response = approver_client.post(
            f"/api/change-requests/{request_id}/approve",
            json={},
        )

        assert response.status_code == 409


# POST /api/change-requests/{request_id}/reject tests
class TestRejectChangeRequest:
    """Tests for POST /api/change-requests/{request_id}/reject."""

    def test_reject_change_request_success(self, approver_client):
        """Approver can reject a change request."""
        regular_client = approver_client.regular_client

        create_response = regular_client.post("/api/change-requests", json={
            "prompt_type": "CATEGORY_DEFINITIONS",
            "proposed_content": {"categories": []},
        })
        request_id = create_response.json()["id"]

        response = approver_client.post(
            f"/api/change-requests/{request_id}/reject",
            json={"feedback": "Needs more work"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "REJECTED"
        assert data["review_feedback"] == "Needs more work"
        assert data["reviewed_by"] == approver_client.user_id

    def test_reject_without_feedback(self, approver_client):
        """Approver can reject without feedback."""
        regular_client = approver_client.regular_client

        create_response = regular_client.post("/api/change-requests", json={
            "prompt_type": "SYSTEM_PROMPT",
            "proposed_content": {"content": "Bad prompt"},
        })
        request_id = create_response.json()["id"]

        response = approver_client.post(
            f"/api/change-requests/{request_id}/reject",
            json={},
        )

        assert response.status_code == 200
        assert response.json()["review_feedback"] is None

    def test_reject_non_approver_returns_403(self, approver_client):
        """Non-approver cannot reject requests."""
        regular_client = approver_client.regular_client

        create_response = approver_client.post("/api/change-requests", json={
            "prompt_type": "CATEGORY_DEFINITIONS",
            "proposed_content": {"categories": []},
        })
        request_id = create_response.json()["id"]

        response = regular_client.post(
            f"/api/change-requests/{request_id}/reject",
            json={},
        )

        assert response.status_code == 403

    def test_reject_not_found_returns_404(self, approver_client):
        """Rejecting non-existent request returns 404."""
        response = approver_client.post(
            "/api/change-requests/cr-nonexistent/reject",
            json={},
        )

        assert response.status_code == 404


# POST /api/change-requests/{request_id}/revise tests
class TestReviseChangeRequest:
    """Tests for POST /api/change-requests/{request_id}/revise."""

    def test_revise_rejected_request_success(self, approver_client):
        """Original submitter can revise their rejected request."""
        regular_client = approver_client.regular_client

        # Create and reject request
        create_response = regular_client.post("/api/change-requests", json={
            "prompt_type": "CATEGORY_DEFINITIONS",
            "proposed_content": {"categories": []},
        })
        request_id = create_response.json()["id"]

        approver_client.post(
            f"/api/change-requests/{request_id}/reject",
            json={"feedback": "Add more categories"},
        )

        # Revise as original submitter
        response = regular_client.post(
            f"/api/change-requests/{request_id}/revise",
            json={
                "proposed_content": {"categories": [{"name": "New", "definition": "Added"}]},
                "description": "Added a category as requested",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PENDING"
        assert len(data["proposed_content"]["categories"]) == 1
        assert data["description"] == "Added a category as requested"
        # Review info should be cleared
        assert data["reviewed_by"] is None
        assert data["review_feedback"] is None

    def test_revise_pending_request_returns_400(self, client):
        """Cannot revise a pending (not rejected) request."""
        create_response = client.post("/api/change-requests", json={
            "prompt_type": "CATEGORY_DEFINITIONS",
            "proposed_content": {"categories": []},
        })
        request_id = create_response.json()["id"]

        response = client.post(
            f"/api/change-requests/{request_id}/revise",
            json={"proposed_content": {"categories": []}},
        )

        assert response.status_code == 400

    def test_revise_by_non_submitter_returns_403(self, approver_client):
        """Cannot revise another user's request."""
        regular_client = approver_client.regular_client

        # Create request as regular user
        create_response = regular_client.post("/api/change-requests", json={
            "prompt_type": "CATEGORY_DEFINITIONS",
            "proposed_content": {"categories": []},
        })
        request_id = create_response.json()["id"]

        # Reject it
        approver_client.post(
            f"/api/change-requests/{request_id}/reject",
            json={},
        )

        # Try to revise as approver (not the original submitter)
        response = approver_client.post(
            f"/api/change-requests/{request_id}/revise",
            json={"proposed_content": {"categories": []}},
        )

        assert response.status_code == 403

    def test_revise_not_found_returns_404(self, client):
        """Revising non-existent request returns 404."""
        response = client.post(
            "/api/change-requests/cr-nonexistent/revise",
            json={"proposed_content": {"categories": []}},
        )

        assert response.status_code == 404


# DELETE /api/change-requests/{request_id} tests
class TestWithdrawChangeRequest:
    """Tests for DELETE /api/change-requests/{request_id}."""

    def test_withdraw_pending_request_success(self, client):
        """Original submitter can withdraw their pending request."""
        create_response = client.post("/api/change-requests", json={
            "prompt_type": "CATEGORY_DEFINITIONS",
            "proposed_content": {"categories": []},
        })
        request_id = create_response.json()["id"]

        response = client.delete(f"/api/change-requests/{request_id}")

        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/api/change-requests/{request_id}")
        assert get_response.status_code == 404

    def test_withdraw_non_pending_returns_400(self, approver_client):
        """Cannot withdraw an already approved request."""
        regular_client = approver_client.regular_client

        create_response = regular_client.post("/api/change-requests", json={
            "prompt_type": "CATEGORY_DEFINITIONS",
            "proposed_content": {"categories": []},
        })
        request_id = create_response.json()["id"]

        # Approve it first
        approver_client.post(f"/api/change-requests/{request_id}/approve", json={})

        # Try to withdraw
        response = regular_client.delete(f"/api/change-requests/{request_id}")

        assert response.status_code == 400

    def test_withdraw_by_non_submitter_returns_403(self, approver_client):
        """Cannot withdraw another user's request."""
        regular_client = approver_client.regular_client

        # Create request as regular user
        create_response = regular_client.post("/api/change-requests", json={
            "prompt_type": "CATEGORY_DEFINITIONS",
            "proposed_content": {"categories": []},
        })
        request_id = create_response.json()["id"]

        # Try to withdraw as approver (not the original submitter)
        response = approver_client.delete(f"/api/change-requests/{request_id}")

        assert response.status_code == 403

    def test_withdraw_not_found_returns_404(self, client):
        """Withdrawing non-existent request returns 404."""
        response = client.delete("/api/change-requests/cr-nonexistent")

        assert response.status_code == 404

    def test_withdraw_unauthenticated_returns_401(self, client):
        """Withdrawing without authentication returns 401."""
        client.cookies.clear()

        response = client.delete("/api/change-requests/cr-12345678")

        assert response.status_code == 401
