import json
import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from pydantic import ValidationError

from app.models.workspace import WorkspaceMetadata

logger = logging.getLogger(__name__)


class WorkspaceNotFoundError(Exception):
    """Raised when a workspace is not found."""

    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        super().__init__(f"Workspace not found: {workspace_id}")


class OrganizationWorkspaceProtectedError(Exception):
    """Raised when attempting to delete the organization workspace."""

    def __init__(self):
        super().__init__("Cannot delete the organization workspace")


class WorkspaceService:
    def __init__(self, workspaces_path: Path):
        self.workspaces_path = Path(workspaces_path)
        self.workspaces_path.mkdir(parents=True, exist_ok=True)

    def create_workspace(self, name: str, user_id: str) -> WorkspaceMetadata:
        workspace_id = f"ws-{uuid.uuid4().hex[:8]}"
        workspace_dir = self.workspaces_path / workspace_id

        workspace_dir.mkdir()
        (workspace_dir / "feedback").mkdir()
        (workspace_dir / "evaluation_reports").mkdir()

        metadata = WorkspaceMetadata(
            id=workspace_id,
            name=name,
            user_id=user_id,
            created_at=datetime.now(),
        )

        self._save_metadata(workspace_dir, metadata)
        self._init_empty_prompts(workspace_dir)

        return metadata

    def init_organization_workspace(self) -> None:
        """Initialize the organization workspace if it doesn't exist."""
        org_dir = self.workspaces_path / "organization"

        # Skip if already exists
        if org_dir.exists():
            return

        # Create directory structure
        org_dir.mkdir()
        (org_dir / "change_requests").mkdir()

        # Create metadata
        metadata = WorkspaceMetadata(
            id="organization",
            name="Organization",
            user_id=None,
            created_at=datetime.now(),
            is_organization=True,
        )
        self._save_metadata(org_dir, metadata)

        # Initialize prompt files
        with open(org_dir / "category_definitions.json", "w") as f:
            json.dump({"categories": []}, f)
        with open(org_dir / "few_shot_examples.json", "w") as f:
            json.dump({"examples": []}, f)
        with open(org_dir / "system_prompt.json", "w") as f:
            json.dump({"prompt": ""}, f)

    def list_workspaces(self) -> list[WorkspaceMetadata]:
        workspaces = []
        for ws_dir in self.workspaces_path.iterdir():
            if ws_dir.is_dir() and (ws_dir / "metadata.json").exists():
                try:
                    workspaces.append(self._load_metadata(ws_dir))
                except ValidationError:
                    logger.warning(
                        "Skipping workspace with invalid metadata: %s",
                        ws_dir.name,
                    )
        return sorted(workspaces, key=lambda w: w.created_at, reverse=True)

    def list_workspaces_for_user(self, user_id: str) -> list[WorkspaceMetadata]:
        result = []
        user_workspaces = []

        # Check for organization workspace first
        org_dir = self.workspaces_path / "organization"
        if org_dir.is_dir() and (org_dir / "metadata.json").exists():
            try:
                org_metadata = self._load_metadata(org_dir)
                org_metadata = org_metadata.model_copy(update={"is_organization": True})
                result.append(org_metadata)
            except ValidationError:
                logger.warning(
                    "Skipping workspace with invalid metadata: organization"
                )

        # Collect user workspaces
        for ws_dir in self.workspaces_path.iterdir():
            if ws_dir.name == "organization":
                continue
            if ws_dir.is_dir() and (ws_dir / "metadata.json").exists():
                try:
                    metadata = self._load_metadata(ws_dir)
                except ValidationError:
                    logger.warning(
                        "Skipping workspace with invalid metadata: %s",
                        ws_dir.name,
                    )
                    continue
                if metadata.user_id == user_id:
                    user_workspaces.append(metadata)

        # Add user workspaces sorted by creation date (newest first)
        result.extend(sorted(user_workspaces, key=lambda w: w.created_at, reverse=True))
        return result

    def get_workspace(self, workspace_id: str) -> WorkspaceMetadata:
        workspace_dir = self.workspaces_path / workspace_id
        if not workspace_dir.exists():
            raise WorkspaceNotFoundError(workspace_id)
        return self._load_metadata(workspace_dir)

    def delete_workspace(self, workspace_id: str) -> None:
        if workspace_id == "organization":
            raise OrganizationWorkspaceProtectedError()
        workspace_dir = self.workspaces_path / workspace_id
        if not workspace_dir.exists():
            raise WorkspaceNotFoundError(workspace_id)
        shutil.rmtree(workspace_dir)

    def _save_metadata(
        self, workspace_dir: Path, metadata: WorkspaceMetadata
    ) -> None:
        with open(workspace_dir / "metadata.json", "w") as f:
            json.dump(metadata.model_dump(mode="json"), f, indent=2)

    def _load_metadata(self, workspace_dir: Path) -> WorkspaceMetadata:
        with open(workspace_dir / "metadata.json") as f:
            return WorkspaceMetadata.model_validate(json.load(f))

    def _init_empty_prompts(self, workspace_dir: Path) -> None:
        with open(workspace_dir / "category_definitions.json", "w") as f:
            json.dump({"categories": []}, f)
        with open(workspace_dir / "few_shot_examples.json", "w") as f:
            json.dump({"examples": []}, f)
