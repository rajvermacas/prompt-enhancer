import json

import pytest


@pytest.fixture
def workspace_dir(tmp_path):
    """Create a workspace directory with empty prompts."""
    ws_dir = tmp_path / "ws-test"
    ws_dir.mkdir()
    with open(ws_dir / "category_definitions.json", "w") as f:
        json.dump({"categories": []}, f)
    with open(ws_dir / "few_shot_examples.json", "w") as f:
        json.dump({"examples": []}, f)
    return ws_dir


def test_get_categories_empty(workspace_dir):
    """PromptService returns empty categories initially."""
    from app.services.prompt_service import PromptService

    service = PromptService(workspace_dir)
    config = service.get_categories()

    assert config.categories == []


def test_save_categories(workspace_dir):
    """PromptService saves category definitions."""
    from app.models.prompts import CategoryDefinition, PromptConfig
    from app.services.prompt_service import PromptService

    service = PromptService(workspace_dir)
    config = PromptConfig(categories=[
        CategoryDefinition(name="Cat1", definition="Def1"),
    ])

    service.save_categories(config)
    loaded = service.get_categories()

    assert len(loaded.categories) == 1
    assert loaded.categories[0].name == "Cat1"


def test_get_few_shots_empty(workspace_dir):
    """PromptService returns empty few-shots initially."""
    from app.services.prompt_service import PromptService

    service = PromptService(workspace_dir)
    config = service.get_few_shots()

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

    service.save_few_shots(config)
    loaded = service.get_few_shots()

    assert len(loaded.examples) == 1
    assert loaded.examples[0].id == "ex-001"


def test_get_system_prompt_returns_empty_when_file_missing(workspace_dir):
    """PromptService returns empty content when system_prompt.json doesn't exist."""
    from app.services.prompt_service import PromptService

    service = PromptService(workspace_dir)
    config = service.get_system_prompt()

    assert config.content == ""


def test_save_system_prompt(workspace_dir):
    """PromptService saves system prompt content."""
    from app.models.prompts import SystemPromptConfig
    from app.services.prompt_service import PromptService

    service = PromptService(workspace_dir)
    config = SystemPromptConfig(content="Explain why other categories were rejected")

    service.save_system_prompt(config)
    loaded = service.get_system_prompt()

    assert loaded.content == "Explain why other categories were rejected"
