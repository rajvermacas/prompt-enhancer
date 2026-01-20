import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.agents.analysis_agent import AnalysisAgent
from app.agents.evaluation_agent import EvaluationAgent
from app.agents.improvement_agent import ImprovementAgent
from app.agents.llm_provider import get_llm
from app.dependencies import get_news_service, get_settings, get_workspace_service
from app.models.feedback import AIInsight, EvaluationReport, Feedback, ImprovementSuggestion
from app.services.feedback_service import FeedbackService
from app.services.news_service import ArticleNotFoundError, NewsService
from app.services.prompt_service import PromptService
from app.services.workspace_service import WorkspaceNotFoundError, WorkspaceService

router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["workflows"])


class AnalyzeRequest(BaseModel):
    article_id: str


class FeedbackRequest(BaseModel):
    article_id: str
    thumbs_up: bool
    correct_category: str
    reasoning: str
    ai_insight: AIInsight


@router.post("/analyze", response_model=AIInsight)
def analyze_article(
    workspace_id: str,
    request: AnalyzeRequest,
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    news_service: NewsService = Depends(get_news_service),
):
    settings = get_settings()

    try:
        workspace_service.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise HTTPException(status_code=404, detail="Workspace not found")

    try:
        article = news_service.get_article(request.article_id)
    except ArticleNotFoundError:
        raise HTTPException(status_code=404, detail="Article not found")

    workspace_dir = Path(settings.workspaces_path) / workspace_id
    prompt_service = PromptService(workspace_dir)

    categories = prompt_service.get_categories().categories
    few_shots = prompt_service.get_few_shots().examples

    with open(settings.system_prompt_path) as f:
        system_prompt = f.read()

    llm = get_llm(settings)
    agent = AnalysisAgent(llm=llm, system_prompt=system_prompt)

    return agent.analyze(categories, few_shots, article.content)


@router.post("/feedback", response_model=EvaluationReport)
def submit_feedback(
    workspace_id: str,
    request: FeedbackRequest,
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    settings = get_settings()

    try:
        workspace_service.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise HTTPException(status_code=404, detail="Workspace not found")

    workspace_dir = Path(settings.workspaces_path) / workspace_id
    prompt_service = PromptService(workspace_dir)
    feedback_service = FeedbackService(workspace_dir)

    feedback = Feedback(
        id=f"fb-{uuid.uuid4().hex[:8]}",
        article_id=request.article_id,
        thumbs_up=request.thumbs_up,
        correct_category=request.correct_category,
        reasoning=request.reasoning,
        ai_insight=request.ai_insight,
        created_at=datetime.now(),
    )
    feedback_service.save_feedback(feedback)

    categories = prompt_service.get_categories().categories
    few_shots = prompt_service.get_few_shots().examples

    llm = get_llm(settings)
    agent = EvaluationAgent(llm=llm)
    report = agent.evaluate(feedback, categories, few_shots)

    feedback_service.save_evaluation_report(report)

    return report


@router.get("/feedback", response_model=list[Feedback])
def list_feedback(
    workspace_id: str,
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    settings = get_settings()

    try:
        workspace_service.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise HTTPException(status_code=404, detail="Workspace not found")

    workspace_dir = Path(settings.workspaces_path) / workspace_id
    feedback_service = FeedbackService(workspace_dir)

    return feedback_service.list_feedback()


@router.post("/suggest-improvements", response_model=ImprovementSuggestion)
def suggest_improvements(
    workspace_id: str,
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    settings = get_settings()

    try:
        workspace_service.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise HTTPException(status_code=404, detail="Workspace not found")

    workspace_dir = Path(settings.workspaces_path) / workspace_id
    prompt_service = PromptService(workspace_dir)
    feedback_service = FeedbackService(workspace_dir)

    categories = prompt_service.get_categories().categories
    few_shots = prompt_service.get_few_shots().examples
    reports = feedback_service.list_evaluation_reports()

    if not reports:
        raise HTTPException(status_code=400, detail="No evaluation reports available")

    llm = get_llm(settings)
    agent = ImprovementAgent(llm=llm)

    return agent.suggest_improvements(reports, categories, few_shots)
