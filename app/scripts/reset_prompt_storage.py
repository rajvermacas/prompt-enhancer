"""Reset prompt files for all workspaces and reinitialize versioned storage."""

import argparse
from pathlib import Path

from app.services.prompt_service import PromptService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Delete and recreate prompt files with versioned storage."
    )
    parser.add_argument(
        "--workspaces-path",
        required=True,
        help="Path to the workspaces root directory.",
    )
    parser.add_argument(
        "--updated-by",
        required=True,
        help="Actor label recorded in history entries.",
    )
    return parser.parse_args()


def list_workspace_dirs(workspaces_path: Path) -> list[Path]:
    if not workspaces_path.exists() or not workspaces_path.is_dir():
        raise NotADirectoryError(f"Invalid workspaces path: {workspaces_path}")
    workspace_dirs: list[Path] = []
    for entry in workspaces_path.iterdir():
        if not entry.is_dir():
            continue
        metadata_file = entry / "metadata.json"
        if metadata_file.exists() and metadata_file.is_file():
            workspace_dirs.append(entry)
    if not workspace_dirs:
        raise RuntimeError(f"No workspace directories found in {workspaces_path}")
    return workspace_dirs


def reset_workspace_prompts(workspace_dirs: list[Path], updated_by: str) -> None:
    if not updated_by:
        raise ValueError("updated_by is required")
    for workspace_dir in workspace_dirs:
        PromptService.reset_prompt_storage(workspace_dir, updated_by)


def main() -> None:
    args = parse_args()
    workspace_dirs = list_workspace_dirs(Path(args.workspaces_path))
    reset_workspace_prompts(workspace_dirs, args.updated_by)
    print(f"Reset prompt storage in {len(workspace_dirs)} workspaces.")


if __name__ == "__main__":
    main()
