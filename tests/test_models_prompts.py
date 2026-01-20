def test_category_definition_creation():
    """CategoryDefinition can be created."""
    from app.models.prompts import CategoryDefinition

    category = CategoryDefinition(
        name="Planned Price Sensitive",
        definition="News about scheduled corporate events that may affect stock price.",
    )

    assert category.name == "Planned Price Sensitive"
    assert "scheduled corporate events" in category.definition


def test_few_shot_example_creation():
    """FewShotExample can be created with all required fields."""
    from app.models.prompts import FewShotExample

    example = FewShotExample(
        id="ex-001",
        news_content="Company X announces Q3 earnings call scheduled for Oct 15.",
        category="Planned Price Sensitive",
        reasoning="This is a scheduled earnings announcement.",
    )

    assert example.id == "ex-001"
    assert example.category == "Planned Price Sensitive"


def test_prompt_config_holds_all_definitions():
    """PromptConfig holds list of category definitions."""
    from app.models.prompts import CategoryDefinition, PromptConfig

    config = PromptConfig(
        categories=[
            CategoryDefinition(name="Cat1", definition="Def1"),
            CategoryDefinition(name="Cat2", definition="Def2"),
        ]
    )

    assert len(config.categories) == 2
