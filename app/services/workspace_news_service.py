from pathlib import Path


class WorkspaceNewsService:
    def __init__(self, workspaces_path: Path, default_news_path: Path):
        self.workspaces_path = Path(workspaces_path)
        self.default_news_path = Path(default_news_path)

    def _get_uploaded_news_path(self, workspace_id: str) -> Path:
        return self.workspaces_path / workspace_id / "uploaded_news.csv"
