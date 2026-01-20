import csv

import pytest


@pytest.fixture
def news_csv(tmp_path):
    """Create a temporary news CSV file."""
    csv_path = tmp_path / "news.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "headline", "content"])
        writer.writeheader()
        for i in range(50):
            writer.writerow({
                "id": f"news-{i:03d}",
                "headline": f"Headline {i}",
                "content": f"Content for article {i}",
            })
    return csv_path


def test_get_news_paginated(news_csv):
    """NewsService returns paginated news articles."""
    from app.services.news_service import NewsService

    service = NewsService(news_csv)
    response = service.get_news(page=1, limit=10)

    assert len(response.articles) == 10
    assert response.total == 50
    assert response.page == 1
    assert response.limit == 10


def test_get_news_second_page(news_csv):
    """NewsService returns correct page of articles."""
    from app.services.news_service import NewsService

    service = NewsService(news_csv)
    response = service.get_news(page=2, limit=10)

    assert len(response.articles) == 10
    assert response.articles[0].id == "news-010"


def test_get_news_last_partial_page(news_csv):
    """NewsService handles partial last page correctly."""
    from app.services.news_service import NewsService

    service = NewsService(news_csv)
    response = service.get_news(page=3, limit=20)

    assert len(response.articles) == 10  # 50 total, page 3 of 20 = remaining 10


def test_get_article_by_id(news_csv):
    """NewsService retrieves a single article by ID."""
    from app.services.news_service import NewsService

    service = NewsService(news_csv)
    article = service.get_article("news-025")

    assert article.id == "news-025"
    assert article.headline == "Headline 25"


def test_get_article_not_found(news_csv):
    """NewsService raises exception for non-existent article."""
    from app.services.news_service import ArticleNotFoundError, NewsService

    service = NewsService(news_csv)

    with pytest.raises(ArticleNotFoundError):
        service.get_article("nonexistent")
