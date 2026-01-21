from datetime import datetime


def test_reasoning_row_creation():
    """ReasoningRow holds the 3-column reasoning data."""
    from app.models.feedback import ReasoningRow

    row = ReasoningRow(
        category_excerpt="scheduled corporate events",
        news_excerpt="Q3 earnings call scheduled",
        reasoning="Direct match with definition",
    )

    assert row.category_excerpt == "scheduled corporate events"


def test_ai_insight_creation():
    """AIInsight holds the analysis result."""
    from app.models.feedback import AIInsight, ReasoningRow

    insight = AIInsight(
        category="Planned Price Sensitive",
        reasoning_table=[
            ReasoningRow(
                category_excerpt="excerpt1",
                news_excerpt="excerpt2",
                reasoning="reason",
            )
        ],
        confidence=0.85,
    )

    assert insight.category == "Planned Price Sensitive"
    assert insight.confidence == 0.85
    assert len(insight.reasoning_table) == 1


def test_feedback_creation():
    """Feedback captures user response to AI insight."""
    from app.models.feedback import AIInsight, Feedback, ReasoningRow

    feedback = Feedback(
        id="fb-001",
        article_id="news-001",
        thumbs_up=False,
        correct_category="Unplanned Price Sensitive",
        reasoning="This was an unexpected announcement",
        ai_insight=AIInsight(
            category="Planned Price Sensitive",
            reasoning_table=[],
            confidence=0.7,
        ),
        created_at=datetime.now(),
    )

    assert feedback.thumbs_up is False
    assert feedback.correct_category == "Unplanned Price Sensitive"


def test_evaluation_report_creation():
    """EvaluationReport holds the evaluation agent output."""
    from app.models.feedback import EvaluationReport, PromptGap

    report = EvaluationReport(
        id="rpt-001",
        feedback_id="fb-001",
        diagnosis="The category definition lacks clarity on timing",
        prompt_gaps=[
            PromptGap(
                location="Planned Price Sensitive definition",
                issue="Does not distinguish scheduled vs unscheduled",
                suggestion="Add clarification about pre-announced events",
            )
        ],
        few_shot_gaps=[],
        summary="Consider clarifying the timing aspect in definitions.",
    )

    assert report.diagnosis is not None
    assert len(report.prompt_gaps) == 1


def test_feedback_with_headline_includes_article_content():
    """FeedbackWithHeadline includes article_content field."""
    from app.models.feedback import AIInsight, FeedbackWithHeadline

    fb = FeedbackWithHeadline(
        id="fb-001",
        article_id="news-001",
        article_headline="Test Headline",
        article_content="Full article content here",
        thumbs_up=True,
        correct_category="Cat1",
        reasoning="Good classification",
        ai_insight=AIInsight(
            category="Cat1",
            reasoning_table=[],
            confidence=0.9,
        ),
        created_at=datetime.now(),
    )

    assert fb.article_content == "Full article content here"


def test_category_suggestion_item_creation():
    """CategorySuggestionItem holds suggestion with traceability."""
    from app.models.feedback import CategorySuggestionItem

    item = CategorySuggestionItem(
        category="Technology",
        current="Tech news",
        suggested="Technology and software news",
        rationale="More specific definition",
        based_on_feedback_ids=["fb-001", "fb-002"],
        user_reasoning_quotes=["User said: AI articles should be tech"],
    )

    assert item.category == "Technology"
    assert len(item.based_on_feedback_ids) == 2
    assert "User said" in item.user_reasoning_quotes[0]


def test_few_shot_suggestion_item_creation():
    """FewShotSuggestionItem holds suggestion with source type."""
    from app.models.feedback import FewShotSuggestionItem

    item = FewShotSuggestionItem(
        action="add",
        source="user_article",
        based_on_feedback_id="fb-001",
        details={"id": "ex-1", "news_content": "Test", "category": "Cat1", "reasoning": "Why"},
    )

    assert item.action == "add"
    assert item.source == "user_article"
    assert item.based_on_feedback_id == "fb-001"


def test_updated_category_with_traceability_fields():
    """UpdatedCategory includes traceability fields for feedback linkage."""
    from app.models.feedback import UpdatedCategory

    cat = UpdatedCategory(
        category="Technology",
        updated_definition="News about technology companies and their products",
        based_on_feedback_ids=["fb-001", "fb-002"],
        rationale="Definition was too vague, did not distinguish earnings from product news",
    )

    assert cat.category == "Technology"
    assert cat.updated_definition == "News about technology companies and their products"
    assert cat.based_on_feedback_ids == ["fb-001", "fb-002"]
    assert "too vague" in cat.rationale


def test_updated_category_traceability_fields_default_to_empty():
    """UpdatedCategory traceability fields default to empty when not provided."""
    from app.models.feedback import UpdatedCategory

    cat = UpdatedCategory(
        category="Finance",
        updated_definition="Financial news and earnings reports",
    )

    assert cat.based_on_feedback_ids == []
    assert cat.rationale == ""
