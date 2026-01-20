import json
from pathlib import Path

from app.models.feedback import EvaluationReport, Feedback


class FeedbackService:
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = Path(workspace_dir)
        self.feedback_dir = self.workspace_dir / "feedback"
        self.reports_dir = self.workspace_dir / "evaluation_reports"

    def save_feedback(self, feedback: Feedback) -> None:
        file_path = self.feedback_dir / f"{feedback.id}.json"
        with open(file_path, "w") as f:
            json.dump(feedback.model_dump(mode="json"), f, indent=2)

    def list_feedback(self) -> list[Feedback]:
        feedbacks = []
        for file_path in self.feedback_dir.glob("*.json"):
            with open(file_path) as f:
                feedbacks.append(Feedback.model_validate(json.load(f)))
        return sorted(feedbacks, key=lambda fb: fb.created_at, reverse=True)

    def save_evaluation_report(self, report: EvaluationReport) -> None:
        file_path = self.reports_dir / f"{report.id}.json"
        with open(file_path, "w") as f:
            json.dump(report.model_dump(), f, indent=2)

    def list_evaluation_reports(self) -> list[EvaluationReport]:
        reports = []
        for file_path in self.reports_dir.glob("*.json"):
            with open(file_path) as f:
                reports.append(EvaluationReport.model_validate(json.load(f)))
        return reports
