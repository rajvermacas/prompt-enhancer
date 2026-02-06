import json

import pytest


def test_list_workspace_dirs_returns_only_valid_workspaces(tmp_path):
    from app.scripts.reset_prompt_storage import list_workspace_dirs

    workspaces_path = tmp_path / "workspaces"
    workspaces_path.mkdir()

    ws1 = workspaces_path / "ws-1"
    ws1.mkdir()
    (ws1 / "metadata.json").write_text('{"id":"ws-1"}')

    invalid = workspaces_path / "invalid"
    invalid.mkdir()

    dirs = list_workspace_dirs(workspaces_path)

    assert dirs == [ws1]


def test_reset_workspace_prompts_recreates_versioned_files(tmp_path):
    from app.models.prompts import CategoryDefinition, PromptConfig
    from app.scripts.reset_prompt_storage import reset_workspace_prompts
    from app.services.prompt_service import PromptService

    workspaces_path = tmp_path / "workspaces"
    workspaces_path.mkdir()
    ws1 = workspaces_path / "ws-1"
    ws1.mkdir()
    (ws1 / "metadata.json").write_text('{"id":"ws-1"}')

    PromptService.initialize_prompt_storage(ws1, updated_by="system")
    service = PromptService(ws1)
    service.save_categories(
        PromptConfig(categories=[CategoryDefinition(name="Tech", definition="Tech news")]),
        updated_by="u-test",
        source="direct_save",
        change_request_id=None,
    )
    with open(ws1 / "category_definitions.history.jsonl") as f:
        before_lines = f.readlines()

    reset_workspace_prompts([ws1], updated_by="resetter")

    categories = json.loads((ws1 / "category_definitions.json").read_text())
    assert categories["version"] == 1
    with open(ws1 / "category_definitions.history.jsonl") as f:
        after_lines = f.readlines()
    assert len(after_lines) == 1
    assert len(before_lines) == 2


def test_list_workspace_dirs_raises_for_missing_root(tmp_path):
    from app.scripts.reset_prompt_storage import list_workspace_dirs

    with pytest.raises(NotADirectoryError):
        list_workspace_dirs(tmp_path / "missing")
