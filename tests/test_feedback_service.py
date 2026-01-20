from datetime import datetime

import pytest


@pytest.fixture
def workspace_dir(tmp_path):
    """Create a workspace directory with feedback folders."""
    ws_dir = tmp_path / "ws-test"
    ws_dir.mkdir()
    (ws_dir / "feedback").mkdir()
    (ws_dir / "evaluation_reports").mkdir()
    return ws_dir


def test_save_feedback(workspace_dir):
    """FeedbackService saves feedback to disk."""
    from app.models.feedback import AIInsight, Feedback
    from app.services.feedback_service import FeedbackService

    service = FeedbackService(workspace_dir)
    feedback = Feedback(
        id="fb-001",
        article_id="news-001",
        thumbs_up=True,
        correct_category="Cat1",
        reasoning="Good",
        note="Accurate",
        ai_insight=AIInsight(category="Cat1", reasoning_table=[], confidence=0.9),
        created_at=datetime.now(),
    )

    service.save_feedback(feedback)

    assert (workspace_dir / "feedback" / "fb-001.json").exists()


def test_list_feedback(workspace_dir):
    """FeedbackService lists all feedback for workspace."""
    from app.models.feedback import AIInsight, Feedback
    from app.services.feedback_service import FeedbackService

    service = FeedbackService(workspace_dir)
    for i in range(3):
        feedback = Feedback(
            id=f"fb-{i:03d}",
            article_id=f"news-{i:03d}",
            thumbs_up=True,
            correct_category="Cat1",
            reasoning="Good",
            note="Note",
            ai_insight=AIInsight(category="Cat1", reasoning_table=[], confidence=0.9),
            created_at=datetime.now(),
        )
        service.save_feedback(feedback)

    feedbacks = service.list_feedback()

    assert len(feedbacks) == 3


def test_save_evaluation_report(workspace_dir):
    """FeedbackService saves evaluation report to disk."""
    from app.models.feedback import EvaluationReport
    from app.services.feedback_service import FeedbackService

    service = FeedbackService(workspace_dir)
    report = EvaluationReport(
        id="rpt-001",
        feedback_id="fb-001",
        diagnosis="Test diagnosis",
        prompt_gaps=[],
        few_shot_gaps=[],
        summary="Test summary",
    )

    service.save_evaluation_report(report)

    assert (workspace_dir / "evaluation_reports" / "rpt-001.json").exists()


def test_list_evaluation_reports(workspace_dir):
    """FeedbackService lists all evaluation reports."""
    from app.models.feedback import EvaluationReport
    from app.services.feedback_service import FeedbackService

    service = FeedbackService(workspace_dir)
    for i in range(2):
        report = EvaluationReport(
            id=f"rpt-{i:03d}",
            feedback_id=f"fb-{i:03d}",
            diagnosis="Diagnosis",
            prompt_gaps=[],
            few_shot_gaps=[],
            summary="Summary",
        )
        service.save_evaluation_report(report)

    reports = service.list_evaluation_reports()

    assert len(reports) == 2
