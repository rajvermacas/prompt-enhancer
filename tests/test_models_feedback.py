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
