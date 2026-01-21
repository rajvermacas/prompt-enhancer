def test_news_article_creation():
    """NewsArticle can be created with required fields."""
    from app.models.news import NewsArticle

    article = NewsArticle(
        id="news-001",
        headline="Company X Reports Record Earnings",
        content="Full article content here...",
    )

    assert article.id == "news-001"
    assert article.headline == "Company X Reports Record Earnings"


def test_news_list_response():
    """NewsListResponse contains articles and pagination info."""
    from app.models.news import NewsArticle, NewsListResponse

    response = NewsListResponse(
        articles=[
            NewsArticle(id="1", headline="H1", content="C1"),
            NewsArticle(id="2", headline="H2", content="C2"),
        ],
        total=100,
        page=1,
        limit=20,
    )

    assert len(response.articles) == 2
    assert response.total == 100


def test_news_article_with_date():
    """NewsArticle accepts optional date field as string."""
    from app.models.news import NewsArticle

    article = NewsArticle(
        id="test-1",
        headline="Test Headline",
        content="Test content",
        date="2026-01-15"
    )

    assert article.date == "2026-01-15"


def test_news_article_without_date():
    """NewsArticle date defaults to None."""
    from app.models.news import NewsArticle

    article = NewsArticle(
        id="test-1",
        headline="Test Headline",
        content="Test content"
    )

    assert article.date is None
