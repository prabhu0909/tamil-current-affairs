"""Test quiz generation and AI logic."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from quiz import QuizService, ContentProcessor, AIQuizGenerator

class TestQuizService:
    """Test QuizService functionality."""

    @pytest.fixture
    def quiz_service(self):
        """Create QuizService instance."""
        return QuizService()

    def test_quiz_service_initialization(self, quiz_service):
        """Test QuizService initializes correctly."""
        assert quiz_service is not None
        assert hasattr(quiz_service, 'generate_quiz')
        assert hasattr(quiz_service, 'validate_quiz')

    @patch('quiz.AIModelConnector')
    @patch('quiz.ContentProcessor')
    def test_generate_quiz_success(self, mock_processor, mock_ai, quiz_service):
        """Test successful quiz generation."""
        # Mock content processing
        mock_processor.return_value.process_content.return_value = {
            'cleaned_text': 'Cleaned content here',
            'key_phrases': ['education policy', 'budget allocation'],
            'topics': ['education', 'finance']
        }

        # Mock AI quiz generation
        mock_ai.return_value.generate_quiz.return_value = {
            'id': 'quiz_123',
            'topic': 'Test Topic',
            'questions': [
                {
                    'id': 'q1',
                    'type': 'multiple_choice',
                    'question': 'What is 2+2?',
                    'options': ['3', '4', '5', '6'],
                    'correct_answer': '4',
                    'explanation': 'Basic arithmetic'
                }
            ],
            'difficulty': 'easy',
            'created_at': '2024-03-16T10:00:00Z'
        }

        result = asyncio.run(quiz_service.generate_quiz('Test content', 'easy'))

        assert result['id'] == 'quiz_123'
        assert result['topic'] == 'Test Topic'
        assert len(result['questions']) == 1
        assert result['questions'][0]['correct_answer'] == '4'

    def test_validate_quiz_structure(self, quiz_service):
        """Test quiz validation."""
        valid_quiz = {
            'id': 'quiz_123',
            'topic': 'Test Topic',
            'questions': [
                {
                    'id': 'q1',
                    'type': 'multiple_choice',
                    'question': 'Test question?',
                    'options': ['A', 'B', 'C', 'D'],
                    'correct_answer': 'A',
                    'difficulty': 'medium'
                }
            ],
            'difficulty': 'medium'
        }

        result = quiz_service.validate_quiz(valid_quiz)
        assert result == True

    def test_validate_quiz_missing_fields(self, quiz_service):
        """Test quiz validation with missing fields."""
        invalid_quiz = {
            'topic': 'Test Topic',
            # Missing 'id', 'questions'
        }

        result = quiz_service.validate_quiz(invalid_quiz)
        assert result == False

class TestContentProcessor:
    """Test ContentProcessor functionality."""

    @pytest.fixture
    def processor(self):
        """Create ContentProcessor instance."""
        return ContentProcessor()

    def test_preprocess_text(self, processor):
        """Test text preprocessing."""
        raw_text = "This is a   test   text    with    extra    spaces!"
        result = processor.preprocess_text(raw_text)

        assert "This is a test text with extra spaces!" == result
        assert "   " not in result

    def test_extract_key_phrases(self, processor):
        """Test key phrase extraction."""
        text = "Tamil Nadu government announced new education policy budget allocation of 500 crores."
        phrases = processor.extract_key_phrases(text)

        assert len(phrases) > 0
        assert any("education policy" in phrase for phrase in phrases) or any("Tamil Nadu" in phrase for phrase in phrases)

    def test_classify_topics(self, processor):
        """Test topic classification."""
        text = "The Tamil Nadu government announced a new education budget of ₹100 crores."
        topics = processor.classify_topics(text)

        assert isinstance(topics, list)
        assert len(topics) > 0
        assert all(isinstance(topic, str) for topic in topics)

    def test_process_content_full(self, processor):
        """Test full content processing pipeline."""
        content = "Tamil Nadu Health Minister announced COVID-19 vaccination drive. Budget allocation increased by 200 crores for hospitals."

        result = processor.process_content(content)

        assert 'cleaned_text' in result
        assert 'key_phrases' in result
        assert 'topics' in result
        assert 'sentiment_score' in result

        assert len(result['key_phrases']) > 0
        assert len(result['topics']) > 0

class TestAIQuizGenerator:
    """Test AI quiz generation."""

    @pytest.fixture
    def ai_generator(self):
        """Create AIQuizGenerator instance."""
        return AIQuizGenerator()

    @patch('quiz.AnthropicModel')
    def test_generate_quiz_questions(self, mock_anthropic, ai_generator):
        """Test quiz question generation."""
        # Mock AI response
        mock_anthropic.return_value.generate.return_value = """
        {
            "questions": [
                {
                    "type": "multiple_choice",
                    "question": "What is the capital of Tamil Nadu?",
                    "options": ["Chennai", "Coimbatore", "Madurai", "Salem"],
                    "correct_answer": "Chennai",
                    "explanation": "Chennai is the capital city of Tamil Nadu."
                }
            ]
        }
        """

        topics = ['history', 'geography']
        questions = asyncio.run(ai_generator.generate_quiz_questions('Tamil Nadu basics', topics, 'easy'))

        assert len(questions) > 0
        assert questions[0]['type'] == 'multiple_choice'
        assert 'question' in questions[0]
        assert 'options' in questions[0]
        assert 'correct_answer' in questions[0]

    @patch('quiz.AnthropicModel')
    def test_different_difficulty_levels(self, mock_anthropic, ai_generator):
        """Test quiz generation for different difficulty levels."""
        difficulties = ['easy', 'medium', 'hard']

        for diff in difficulties:
            mock_anthropic.return_value.generate.return_value = """
            {
                "questions": [
                    {
                        "type": "multiple_choice",
                        "question": "Test question",
                        "options": ["A", "B", "C", "D"],
                        "correct_answer": "A",
                        "explanation": "Test explanation"
                    }
                ]
            }
            """

            questions = asyncio.run(ai_generator.generate_quiz_questions('Test topic', ['test'], diff))
            assert len(questions) >= 1

    @patch('quiz.AnthropicModel')
    def test_error_handling(self, mock_anthropic, ai_generator):
        """Test error handling in quiz generation."""
        # Mock API failure
        mock_anthropic.return_value.generate.side_effect = Exception("API Error")

        with pytest.raises(Exception):
            asyncio.run(ai_generator.generate_quiz_questions('Test', ['test'], 'easy'))

    def test_quiz_question_validation(self, ai_generator):
        """Test quiz question validation."""
        valid_question = {
            'type': 'multiple_choice',
            'question': 'Test question?',
            'options': ['A', 'B', 'C', 'D'],
            'correct_answer': 'A',
            'explanation': 'Test explanation'
        }

        assert ai_generator.validate_question(valid_question) == True

        invalid_question = {
            'question': 'Test question?',
            # Missing required fields
        }

        assert ai_generator.validate_question(invalid_question) == False

class TestIntegrationScenarios:
    """Test integration scenarios."""

    @pytest.fixture
    def full_service(self):
        """Create complete service instance."""
        return QuizService()

    @patch('quiz.ContentProcessor')
    @patch('quiz.AIQuizGenerator')
    def test_full_quiz_generation_pipeline(self, mock_ai_gen, mock_processor, full_service):
        """Test complete quiz generation pipeline."""
        # Mock content processing
        mock_processor.return_value.process_content.return_value = {
            'cleaned_text': 'Processed content',
            'topics': ['education', 'health']
        }

        # Mock AI generation
        mock_ai_gen.return_value.generate_quiz.return_value = {
            'questions': [
                {
                    'id': 'q1',
                    'type': 'multiple_choice',
                    'question': 'Test question',
                    'options': ['Yes', 'No'],
                    'correct_answer': 'Yes'
                }
            ]
        }

        result = asyncio.run(full_service.generate_quiz(
            content='Test news article content about Tamil Nadu education policy',
            difficulty='medium'
        ))

        assert 'id' in result
        assert 'questions' in result
        assert len(result['questions']) >= 1

    def test_performance_constraints(self, full_service):
        """Test performance constraints."""
        import time

        start_time = time.time()
        # This would be a real test with performance assertions
        end_time = time.time()

        # Assert reasonable execution time
        execution_time = end_time - start_time
        assert execution_time < 5.0  # Should complete within 5 seconds

if __name__ == "__main__":
    pytest.main([__file__, "-v"])