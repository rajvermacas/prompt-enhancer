import json
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agents.analysis_agent import AnalysisAgent
from app.agents.chat_reasoning_agent import ChatReasoningAgent
from app.agents.evaluation_agent import EvaluationAgent
from app.agents.improvement_agent import ImprovementAgent
from app.agents.llm_provider import get_llm
from app.dependencies import get_settings, get_workspace_news_service, get_workspace_service
from app.models.chat import ChatReasoningRequest
from app.models.feedback import (
    AIInsight,
    EvaluationReport,
    Feedback,
    FeedbackWithHeadline,
    ImprovementSuggestion,
    ImprovementSuggestionResponse,
)
from app.services.feedback_service import FeedbackNotFoundError, FeedbackService
from app.services.prompt_service import PromptService
from app.services.workspace_news_service import (
    ArticleNotFoundError,
    WorkspaceNewsService,
)
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
    workspace_news_service: WorkspaceNewsService = Depends(get_workspace_news_service),
):
    settings = get_settings()

    try:
        workspace_service.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise HTTPException(status_code=404, detail="Workspace not found")

    try:
        article = workspace_news_service.get_article(workspace_id, request.article_id)
    except ArticleNotFoundError:
        raise HTTPException(status_code=404, detail="Article not found")

    workspace_dir = Path(settings.workspaces_path) / workspace_id
    prompt_service = PromptService(workspace_dir)

    categories = prompt_service.get_categories().categories
    few_shots = prompt_service.get_few_shots().examples

    if not categories:
        raise HTTPException(
            status_code=400,
            detail="No categories defined in workspace. Please add at least one category before analyzing articles.",
        )

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


@router.get("/feedback-with-headlines", response_model=list[FeedbackWithHeadline])
def list_feedback_with_headlines(
    workspace_id: str,
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    workspace_news_service: WorkspaceNewsService = Depends(get_workspace_news_service),
):
    settings = get_settings()

    try:
        workspace_service.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise HTTPException(status_code=404, detail="Workspace not found")

    workspace_dir = Path(settings.workspaces_path) / workspace_id
    feedback_service = FeedbackService(workspace_dir)
    feedbacks = feedback_service.list_feedback()

    return _enrich_feedbacks_with_headlines(feedbacks, workspace_id, workspace_news_service)


@router.delete("/feedback/{feedback_id}")
def delete_feedback(
    workspace_id: str,
    feedback_id: str,
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    settings = get_settings()

    try:
        workspace_service.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise HTTPException(status_code=404, detail="Workspace not found")

    workspace_dir = Path(settings.workspaces_path) / workspace_id
    feedback_service = FeedbackService(workspace_dir)

    try:
        feedback_service.delete_feedback(feedback_id)
    except FeedbackNotFoundError:
        raise HTTPException(status_code=404, detail="Feedback not found")

    return {"status": "deleted"}


@router.post("/suggest-improvements", response_model=ImprovementSuggestionResponse)
def suggest_improvements(
    workspace_id: str,
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    workspace_news_service: WorkspaceNewsService = Depends(get_workspace_news_service),
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
    feedbacks = feedback_service.list_feedback()

    if not feedbacks:
        raise HTTPException(status_code=400, detail="No feedback available")

    feedbacks_with_headlines = _enrich_feedbacks_with_headlines(
        feedbacks, workspace_id, workspace_news_service
    )

    llm = get_llm(settings)
    agent = ImprovementAgent(llm=llm)
    suggestions = agent.suggest_improvements(feedbacks_with_headlines, categories, few_shots)

    return ImprovementSuggestionResponse(
        suggestions=suggestions,
        feedbacks=feedbacks_with_headlines,
    )


def _enrich_feedbacks_with_headlines(
    feedbacks: list[Feedback],
    workspace_id: str,
    workspace_news_service: WorkspaceNewsService,
) -> list[FeedbackWithHeadline]:
    enriched = []
    for feedback in feedbacks:
        try:
            article = workspace_news_service.get_article(workspace_id, feedback.article_id)
            headline = article.headline
            content = article.content
        except ArticleNotFoundError:
            headline = f"Article {feedback.article_id} (not found)"
            content = ""

        enriched.append(
            FeedbackWithHeadline(
                id=feedback.id,
                article_id=feedback.article_id,
                article_headline=headline,
                article_content=content,
                thumbs_up=feedback.thumbs_up,
                correct_category=feedback.correct_category,
                reasoning=feedback.reasoning,
                ai_insight=feedback.ai_insight,
                created_at=feedback.created_at,
            )
        )
    return enriched


@router.post("/chat-reasoning")
def chat_reasoning(
    workspace_id: str,
    request: ChatReasoningRequest,
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    workspace_news_service: WorkspaceNewsService = Depends(get_workspace_news_service),
):
    settings = get_settings()

    try:
        workspace_service.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise HTTPException(status_code=404, detail="Workspace not found")

    try:
        article = workspace_news_service.get_article(workspace_id, request.article_id)
    except ArticleNotFoundError:
        raise HTTPException(status_code=404, detail="Article not found")

    workspace_dir = Path(settings.workspaces_path) / workspace_id
    prompt_service = PromptService(workspace_dir)

    categories = prompt_service.get_categories().categories
    few_shots = prompt_service.get_few_shots().examples

    llm = get_llm(settings)
    agent = ChatReasoningAgent(llm=llm)

    def generate():
        for token in agent.stream(
            article_content=article.content,
            categories=categories,
            few_shots=few_shots,
            ai_insight=request.ai_insight,
            chat_history=request.chat_history,
            message=request.message,
        ):
            yield f"data: {json.dumps({'token': token})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
