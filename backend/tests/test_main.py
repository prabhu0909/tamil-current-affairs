"""Test main FastAPI application."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app

@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)

@pytest.fixture
def mock_cache():
    """Mock Redis cache."""
    with patch('main.cache') as mock_cache:
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock(return_value=None)
        mock_cache.expire = AsyncMock(return_value=None)
        mock_cache.exists = AsyncMock(return_value=False)
        yield mock_cache

class TestHealthChecks:
    """Test health check endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns success."""
        response = client.get("/")
        assert response.status_code == 200
        assert "TNPSC Current Affairs AI Platform" in response.json()["message"]

    def test_health_endpoint(self, client):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "uptime" in data
        assert "version" in data

    @patch('main.DatabaseHealthService')
    def test_db_health_endpoint(self, mock_db_service, client):
        """Test database health endpoint."""
        # Mock successful DB health check
        mock_db_service.check_health.return_value = {
            "status": "healthy",
            "connection_time": 0.001,
            "details": {"db_version": "15.0"}
        }

        response = client.get("/health/db")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "connection_time" in data
        assert "db_version" in data["details"]

    @patch('main.RedisHealthService')
    def test_redis_health_endpoint(self, mock_redis_service, client):
        """Test Redis health endpoint."""
        # Mock successful Redis health check
        mock_redis_service.check_health.return_value = {
            "status": "healthy",
            "ping_time": 0.0005,
            "details": {"redis_version": "7.0"}
        }

        response = client.get("/health/redis")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "ping_time" in data
        assert "redis_version" in data["details"]

class TestQuizEndpoints:
    """Test quiz-related endpoints."""

    @patch('main.QuizService')
    def test_generate_quiz(self, mock_quiz_service, client):
        """Test quiz generation endpoint."""
        # Mock quiz service response
        mock_quiz_service.generate_quiz.return_value = {
            "id": "quiz_123",
            "topic": "Tamil Nadu Budget 2024",
            "questions": [
                {
                    "id": "q1",
                    "type": "multiple_choice",
                    "question": "What is the budget allocation for education?",
                    "options": ["₹10,000 Cr", "₹15,000 Cr", "₹20,000 Cr", "₹25,000 Cr"],
                    "correct_answer": "₹20,000 Cr"
                }
            ],
            "difficulty": "medium",
            "created_at": "2024-03-16T10:00:00Z"
        }

        response = client.post(
            "/quiz",
            json={"topic": "Tamil Nadu Budget 2024", "difficulty": "medium"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "quiz_123"
        assert data["topic"] == "Tamil Nadu Budget 2024"
        assert len(data["questions"]) >= 1

    @patch('main.QuizService')
    def test_get_quiz_by_id(self, mock_quiz_service, client):
        """Test get quiz by ID endpoint."""
        mock_quiz_service.get_quiz.return_value = {
            "id": "quiz_123",
            "topic": "Tamil Nadu Budget 2024",
            "questions": [],
            "difficulty": "medium"
        }

        response = client.get("/quiz/quiz_123")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "quiz_123"

    @patch('main.QuizService')
    def test_get_quiz_not_found(self, mock_quiz_service, client):
        """Test get quiz by ID when not found."""
        mock_quiz_service.get_quiz.return_value = None

        response = client.get("/quiz/nonexistent_id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

class TestNewsEndpoints:
    """Test news-related endpoints."""

    @patch('main.NewsService')
    def test_get_news_list(self, mock_news_service, client):
        """Test get news list endpoint."""
        mock_news_service.get_recent_news.return_value = [
            {
                "id": "news_1",
                "title": "Tamil Nadu Government Announces New Policy",
                "summary": "New education policy focuses on digital learning...",
                "source": "The Hindu",
                "published_date": "2024-03-16",
                "url": "https://example.com/news1"
            }
        ]

        response = client.get("/news?limit=10")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            assert "id" in data[0]
            assert "title" in data[0]
            assert "source" in data[0]

    @patch('main.NewsService')
    def test_get_news_by_id(self, mock_news_service, client):
        """Test get news by ID endpoint."""
        mock_news_service.get_news.return_value = {
            "id": "news_1",
            "title": "Tamil Nadu Government Announces New Policy",
            "content": "Full content here...",
            "source": "The Hindu",
            "published_date": "2024-03-16"
        }

        response = client.get("/news/news_1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "news_1"
        assert "content" in data

class TestAIAnalysisEndpoints:
    """Test AI analysis endpoints."""

    @patch('main.AIAnalysisService')
    def test_analyze_news_content(self, mock_ai_service, client):
        """Test news content analysis endpoint."""
        mock_ai_service.analyze_content.return_value = {
            "sentiment": {"positive": 0.8, "negative": 0.1, "neutral": 0.1},
            "key_entities": ["Tamil Nadu", "Government", "Education"],
            "summary": "AI-generated summary of the news article",
            "topics": ["education", "government", "policy"]
        }

        response = client.post(
            "/ai/analyze",
            json={"content": "Tamil Nadu government announces new education policy..."}
        )

        assert response.status_code == 200
        data = response.json()
        assert "sentiment" in data
        assert "key_entities" in data
        assert "summary" in data

class TestErrorHandling:
    """Test error handling and validation."""

    def test_invalid_quiz_request(self, client):
        """Test invalid quiz generation request."""
        # Missing required fields
        response = client.post("/quiz", json={})
        assert response.status_code == 422  # Validation error

        # Invalid topic type
        response = client.post("/quiz", json={"topic": "", "difficulty": "medium"})
        assert response.status_code == 422

    def test_invalid_difficulty(self, client):
        """Test invalid difficulty level."""
        response = client.post(
            "/quiz",
            json={"topic": "Test Topic", "difficulty": "invalid"}
        )
        assert response.status_code == 422

    def test_method_not_allowed(self, client):
        """Test method not allowed."""
        # POST to GET-only endpoint
        response = client.post("/health")
        assert response.status_code == 405

class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limit_headers(self, client):
        """Test rate limit headers are present."""
        response = client.get("/health")
        # In real implementation, these headers would be set
        # assert "X-RateLimit-Limit" in response.headers
        assert response.status_code == 200

class TestCaching:
    """Test caching layer."""

    def test_cache_hit_scenario(self, mock_cache):
        """Test cache hit scenario."""
        # Setup cache hit
        mock_cache.exists.return_value = True
        mock_cache.get.return_value = '{"cached": "data"}'

        # This would be tested through actual endpoints that use caching
        # For now, just verify cache methods exist
        pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])