import json

import pytest


@pytest.fixture
def workspace_dir(tmp_path):
    """Create a workspace directory with empty prompts."""
    ws_dir = tmp_path / "ws-test"
    ws_dir.mkdir()
    with open(ws_dir / "category_definitions.json", "w") as f:
        json.dump({"version": 1, "categories": []}, f)
    (ws_dir / "category_definitions.history.jsonl").write_text(
        json.dumps(
            {
                "version": 1,
                "updated_at": "2026-01-01T00:00:00Z",
                "updated_by": "system",
                "source": "initialization",
                "change_request_id": None,
                "content": {"categories": []},
            }
        )
        + "\n"
    )
    with open(ws_dir / "few_shot_examples.json", "w") as f:
        json.dump({"version": 1, "examples": []}, f)
    (ws_dir / "few_shot_examples.history.jsonl").write_text(
        json.dumps(
            {
                "version": 1,
                "updated_at": "2026-01-01T00:00:00Z",
                "updated_by": "system",
                "source": "initialization",
                "change_request_id": None,
                "content": {"examples": []},
            }
        )
        + "\n"
    )
    with open(ws_dir / "system_prompt.json", "w") as f:
        json.dump({"version": 1, "content": ""}, f)
    (ws_dir / "system_prompt.history.jsonl").write_text(
        json.dumps(
            {
                "version": 1,
                "updated_at": "2026-01-01T00:00:00Z",
                "updated_by": "system",
                "source": "initialization",
                "change_request_id": None,
                "content": {"content": ""},
            }
        )
        + "\n"
    )
    return ws_dir


def test_get_categories_empty(workspace_dir):
    """PromptService returns empty categories initially."""
    from app.services.prompt_service import PromptService

    service = PromptService(workspace_dir)
    config = service.get_categories()

    assert config.version == 1
    assert config.categories == []


def test_save_categories(workspace_dir):
    """PromptService saves category definitions."""
    from app.models.prompts import CategoryDefinition, PromptConfig
    from app.services.prompt_service import PromptService

    service = PromptService(workspace_dir)
    config = PromptConfig(categories=[
        CategoryDefinition(name="Cat1", definition="Def1"),
    ])

    loaded = service.save_categories(
        config,
        updated_by="u-test",
        source="direct_save",
        change_request_id=None,
    )

    assert loaded.version == 2
    assert len(loaded.categories) == 1
    assert loaded.categories[0].name == "Cat1"


def test_get_few_shots_empty(workspace_dir):
    """PromptService returns empty few-shots initially."""
    from app.services.prompt_service import PromptService

    service = PromptService(workspace_dir)
    config = service.get_few_shots()

    assert config.version == 1
    assert config.examples == []


def test_save_few_shots(workspace_dir):
    """PromptService saves few-shot examples."""
    from app.models.prompts import FewShotConfig, FewShotExample
    from app.services.prompt_service import PromptService

    service = PromptService(workspace_dir)
    config = FewShotConfig(examples=[
        FewShotExample(
            id="ex-001",
            news_content="Test news",
            category="Cat1",
            reasoning="Test reasoning",
        ),
    ])

    loaded = service.save_few_shots(
        config,
        updated_by="u-test",
        source="direct_save",
        change_request_id=None,
    )

    assert loaded.version == 2
    assert len(loaded.examples) == 1
    assert loaded.examples[0].id == "ex-001"


def test_get_system_prompt_missing_file_raises(workspace_dir):
    """PromptService fails fast when system_prompt.json is missing."""
    from app.services.prompt_service import PromptService
    from app.services.prompt_service import PromptStorageFileMissingError

    (workspace_dir / "system_prompt.json").unlink()

    service = PromptService(workspace_dir)

    with pytest.raises(PromptStorageFileMissingError):
        service.get_system_prompt()


def test_save_system_prompt(workspace_dir):
    """PromptService saves system prompt content."""
    from app.models.prompts import SystemPromptConfig
    from app.services.prompt_service import PromptService

    service = PromptService(workspace_dir)
    config = SystemPromptConfig(content="Explain why other categories were rejected")

    loaded = service.save_system_prompt(
        config,
        updated_by="u-test",
        source="direct_save",
        change_request_id=None,
    )

    assert loaded.version == 2
    assert loaded.content == "Explain why other categories were rejected"


def test_save_categories_no_change_does_not_increment_version(workspace_dir):
    """Saving unchanged categories is idempotent and keeps version."""
    from app.models.prompts import PromptConfig
    from app.services.prompt_service import PromptService

    service = PromptService(workspace_dir)
    loaded = service.save_categories(
        PromptConfig(categories=[]),
        updated_by="u-test",
        source="direct_save",
        change_request_id=None,
    )
    assert loaded.version == 1


def test_get_categories_history_returns_latest_first(workspace_dir):
    """PromptService returns category history in descending version order."""
    from app.models.prompts import CategoryDefinition, PromptConfig
    from app.services.prompt_service import PromptService

    service = PromptService(workspace_dir)
    service.save_categories(
        PromptConfig(categories=[CategoryDefinition(name="Cat1", definition="Def1")]),
        updated_by="u-test",
        source="direct_save",
        change_request_id=None,
    )
    service.save_categories(
        PromptConfig(categories=[CategoryDefinition(name="Cat2", definition="Def2")]),
        updated_by="u-test",
        source="direct_save",
        change_request_id=None,
    )

    history = service.get_categories_history()

    assert [entry.version for entry in history] == [3, 2, 1]
    assert history[0].content == {"categories": [{"name": "Cat2", "definition": "Def2"}]}


def test_restore_categories_creates_new_version(workspace_dir):
    """Restoring categories from history creates a new version with old content."""
    from app.models.prompts import CategoryDefinition, PromptConfig
    from app.services.prompt_service import PromptService

    service = PromptService(workspace_dir)
    service.save_categories(
        PromptConfig(categories=[CategoryDefinition(name="Cat1", definition="Def1")]),
        updated_by="u-test",
        source="direct_save",
        change_request_id=None,
    )
    service.save_categories(
        PromptConfig(categories=[CategoryDefinition(name="Cat2", definition="Def2")]),
        updated_by="u-test",
        source="direct_save",
        change_request_id=None,
    )

    restored = service.restore_categories(
        version=2,
        updated_by="u-admin",
        source="direct_save",
        change_request_id=None,
    )

    assert restored.version == 4
    assert restored.categories[0].name == "Cat1"


def test_restore_categories_missing_version_raises(workspace_dir):
    """Restoring a missing category version fails fast."""
    from app.services.prompt_service import (
        PromptHistoryVersionNotFoundError,
        PromptService,
    )

    service = PromptService(workspace_dir)

    with pytest.raises(PromptHistoryVersionNotFoundError):
        service.restore_categories(
            version=99,
            updated_by="u-admin",
            source="direct_save",
            change_request_id=None,
        )
