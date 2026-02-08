import json
import sqlite3
import uuid
from datetime import datetime

from app.models.analysis_history import AnalysisHistoryPage, AnalysisRunEntry
from app.models.feedback import AIInsightWithUserAnalysis


class AnalysisHistoryService:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def save_run(
        self,
        workspace_id: str,
        article_id: str,
        triggered_user_id: str,
        insight_payload: dict,
        created_at: datetime,
    ) -> AnalysisRunEntry:
        _require_value(workspace_id, "workspace_id")
        _require_value(article_id, "article_id")
        _require_value(triggered_user_id, "triggered_user_id")

        insight = AIInsightWithUserAnalysis.model_validate(insight_payload)
        run_id = f"ar-{uuid.uuid4().hex[:12]}"
        insight_json = json.dumps(insight.model_dump(mode="json"))

        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            INSERT INTO analysis_runs (
                id, workspace_id, article_id, triggered_user_id, insight_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                workspace_id,
                article_id,
                triggered_user_id,
                insight_json,
                created_at.isoformat(),
            ),
        )
        conn.commit()
        conn.close()

        return AnalysisRunEntry(
            id=run_id,
            workspace_id=workspace_id,
            article_id=article_id,
            triggered_user_id=triggered_user_id,
            insight=insight,
            created_at=created_at,
        )

    def list_runs(
        self,
        workspace_id: str,
        article_id: str,
        triggered_user_id: str,
        page: int,
        limit: int,
        exclude_latest: bool,
    ) -> AnalysisHistoryPage:
        _require_value(workspace_id, "workspace_id")
        _require_value(article_id, "article_id")
        _require_value(triggered_user_id, "triggered_user_id")
        if page < 1:
            raise ValueError("page must be >= 1")
        if limit < 1:
            raise ValueError("limit must be >= 1")
        if exclude_latest is None:
            raise ValueError("exclude_latest is required")
        if not isinstance(exclude_latest, bool):
            raise ValueError("exclude_latest must be a bool")

        offset = (page - 1) * limit
        raw_total = self._count_runs(workspace_id, article_id, triggered_user_id)
        total = raw_total - 1 if exclude_latest and raw_total > 0 else raw_total
        db_offset = offset + 1 if exclude_latest else offset
        entries = self._fetch_runs(
            workspace_id,
            article_id,
            triggered_user_id,
            limit,
            db_offset,
        )

        return AnalysisHistoryPage(
            items=entries,
            total=total,
            page=page,
            limit=limit,
            has_next=offset + len(entries) < total,
        )

    def _count_runs(
        self,
        workspace_id: str,
        article_id: str,
        triggered_user_id: str,
    ) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            """
            SELECT COUNT(*)
            FROM analysis_runs
            WHERE workspace_id = ? AND article_id = ? AND triggered_user_id = ?
            """,
            (workspace_id, article_id, triggered_user_id),
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def _fetch_runs(
        self,
        workspace_id: str,
        article_id: str,
        triggered_user_id: str,
        limit: int,
        offset: int,
    ) -> list[AnalysisRunEntry]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            """
            SELECT id, workspace_id, article_id, triggered_user_id, insight_json, created_at
            FROM analysis_runs
            WHERE workspace_id = ? AND article_id = ? AND triggered_user_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (workspace_id, article_id, triggered_user_id, limit, offset),
        )
        rows = cursor.fetchall()
        conn.close()

        entries = []
        for row in rows:
            payload = json.loads(row[4])
            insight = AIInsightWithUserAnalysis.model_validate(payload)
            entries.append(
                AnalysisRunEntry(
                    id=row[0],
                    workspace_id=row[1],
                    article_id=row[2],
                    triggered_user_id=row[3],
                    insight=insight,
                    created_at=datetime.fromisoformat(row[5]),
                )
            )
        return entries


def _require_value(value: str, name: str) -> None:
    if not value:
        raise ValueError(f"{name} is required")
