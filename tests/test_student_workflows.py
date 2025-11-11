"""
Unit tests for student workflows.

Tests student functionality including:
- Quiz taking
- Progress tracking
- Course access
- Resource viewing
"""

import pytest
import json
from unittest.mock import patch, Mock
from datetime import datetime, timezone
import uuid


class TestStudentCourseAccess:
    """Test student course access and enrollment workflows."""

    @patch('informatics_classroom.classroom.api_routes.get_classes_for_user')
    def test_get_student_courses_success(self, mock_get_classes, client, auth_headers_student):
        """Test student can retrieve their enrolled courses."""
        mock_get_classes.return_value = ['INFORMATICS_101', 'INFORMATICS_201']

        response = client.get('/api/student/courses', headers=auth_headers_student)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['courses']) == 2
        assert 'INFORMATICS_101' in data['courses']

    @patch('informatics_classroom.classroom.api_routes.get_classes_for_user')
    def test_get_student_courses_empty(self, mock_get_classes, client, auth_headers_student):
        """Test student with no enrolled courses."""
        mock_get_classes.return_value = []

        response = client.get('/api/student/courses', headers=auth_headers_student)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['courses']) == 0


class TestStudentDashboard:
    """Test student dashboard workflow."""

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    @patch('informatics_classroom.classroom.api_routes.get_current_user')
    @patch('informatics_classroom.classroom.api_routes.get_classes_for_user')
    @patch('informatics_classroom.classroom.api_routes.get_user_answers_for_quiz')
    def test_get_dashboard_with_progress(self, mock_get_answers, mock_get_classes,
                                        mock_get_user, mock_get_db, client,
                                        mock_jwt_user_student, sample_quiz,
                                        sample_user_data, mock_db):
        """Test student dashboard returns progress summary."""
        # Setup mocks
        mock_get_user.return_value = [sample_user_data]
        mock_get_classes.return_value = ['INFORMATICS_101']
        mock_get_db.return_value = mock_db

        # Add quiz to mock database
        mock_db._data['quiz'][sample_quiz['id']] = sample_quiz

        # Mock answers
        mock_get_answers.return_value = [
            {'question': '1', 'correct': True},
            {'question': '2', 'correct': True}
        ]

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_student

            response = client.get('/api/student/dashboard')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'course_summaries' in data
        assert len(data['course_summaries']) == 1

        summary = data['course_summaries'][0]
        assert summary['course'] == 'INFORMATICS_101'
        assert summary['total_modules'] == 1
        assert summary['answered_questions'] == 2
        assert summary['correct_questions'] == 2

    @patch('informatics_classroom.classroom.api_routes.get_current_user')
    def test_get_dashboard_user_not_found(self, mock_get_user, client, mock_jwt_user_student):
        """Test dashboard returns 404 when user not found."""
        mock_get_user.return_value = None

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_student

            response = client.get('/api/student/dashboard')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False


class TestQuizTaking:
    """Test quiz taking workflow."""

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    @patch('informatics_classroom.classroom.api_routes.get_current_user')
    @patch('informatics_classroom.classroom.api_routes.get_user_answers_for_quiz')
    def test_get_quiz_details_success(self, mock_get_answers, mock_get_user,
                                     mock_get_db, client, mock_jwt_user_student,
                                     sample_quiz, sample_user_data, mock_db):
        """Test retrieving quiz details for taking."""
        mock_get_user.return_value = [sample_user_data]
        mock_get_db.return_value = mock_db
        mock_db._data['quiz'][sample_quiz['id']] = sample_quiz
        mock_get_answers.return_value = []

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_student
            mock_request.args = {'course': 'INFORMATICS_101', 'module': '1'}

            response = client.get('/api/quiz/details?course=INFORMATICS_101&module=1')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['quiz']['course'] == 'INFORMATICS_101'
        assert data['quiz']['module'] == '1'
        assert len(data['quiz']['questions']) == 3

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    def test_get_quiz_details_missing_params(self, mock_get_db, client, mock_jwt_user_student):
        """Test quiz details requires course and module parameters."""
        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_student
            mock_request.args = {'course': 'INFORMATICS_101'}

            response = client.get('/api/quiz/details?course=INFORMATICS_101')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'required' in data['error'].lower()

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    @patch('informatics_classroom.classroom.api_routes.get_current_user')
    def test_submit_answer_correct(self, mock_get_user, mock_get_db, client,
                                   mock_jwt_user_student, sample_user_data,
                                   mock_db, sample_quiz):
        """Test submitting a correct answer."""
        mock_get_user.return_value = [sample_user_data]
        mock_get_db.return_value = mock_db

        # Mock query_raw to return question data
        mock_db.query_raw.return_value = [
            {
                'question_num': 1,
                'correct_answer': '4',
                'open': False
            }
        ]

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_student
            mock_request.get_json.return_value = {
                'course': 'INFORMATICS_101',
                'module': 1,
                'question_num': 1,
                'answer': '4'
            }

            response = client.post('/api/quiz/submit-answer',
                                  json={
                                      'course': 'INFORMATICS_101',
                                      'module': 1,
                                      'question_num': 1,
                                      'answer': '4'
                                  })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['correct'] is True
        assert 'Correct' in data['feedback']

        # Verify answer was stored
        assert 'answer' in mock_db._data
        assert len(mock_db._data['answer']) > 0

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    @patch('informatics_classroom.classroom.api_routes.get_current_user')
    def test_submit_answer_incorrect(self, mock_get_user, mock_get_db, client,
                                    mock_jwt_user_student, sample_user_data, mock_db):
        """Test submitting an incorrect answer."""
        mock_get_user.return_value = [sample_user_data]
        mock_get_db.return_value = mock_db

        mock_db.query_raw.return_value = [
            {
                'question_num': 1,
                'correct_answer': '4',
                'open': False
            }
        ]

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_student
            mock_request.get_json.return_value = {
                'course': 'INFORMATICS_101',
                'module': 1,
                'question_num': 1,
                'answer': '3'
            }

            response = client.post('/api/quiz/submit-answer',
                                  json={
                                      'course': 'INFORMATICS_101',
                                      'module': 1,
                                      'question_num': 1,
                                      'answer': '3'
                                  })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['correct'] is False
        assert 'Incorrect' in data['feedback']

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    @patch('informatics_classroom.classroom.api_routes.get_current_user')
    def test_submit_answer_open_question(self, mock_get_user, mock_get_db, client,
                                        mock_jwt_user_student, sample_user_data, mock_db):
        """Test submitting answer to open-ended question (always correct)."""
        mock_get_user.return_value = [sample_user_data]
        mock_get_db.return_value = mock_db

        mock_db.query_raw.return_value = [
            {
                'question_num': 3,
                'correct_answer': '',
                'open': True
            }
        ]

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_student
            mock_request.get_json.return_value = {
                'course': 'INFORMATICS_101',
                'module': 1,
                'question_num': 3,
                'answer': 'List comprehension is a concise way to create lists'
            }

            response = client.post('/api/quiz/submit-answer',
                                  json={
                                      'course': 'INFORMATICS_101',
                                      'module': 1,
                                      'question_num': 3,
                                      'answer': 'List comprehension is a concise way to create lists'
                                  })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['correct'] is True
        assert data['is_open'] is True

    def test_submit_answer_missing_fields(self, client, mock_jwt_user_student):
        """Test submit answer with missing required fields."""
        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_student
            mock_request.get_json.return_value = {
                'course': 'INFORMATICS_101',
                'module': 1
            }

            response = client.post('/api/quiz/submit-answer',
                                  json={
                                      'course': 'INFORMATICS_101',
                                      'module': 1
                                  })

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False


class TestStudentProgress:
    """Test student progress tracking workflow."""

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    @patch('informatics_classroom.classroom.api_routes.get_current_user')
    @patch('informatics_classroom.classroom.api_routes.get_user_answers_for_quiz')
    def test_get_student_progress_success(self, mock_get_answers, mock_get_user,
                                         mock_get_db, client, mock_jwt_user_student,
                                         sample_quiz, sample_user_data, mock_db):
        """Test retrieving student progress for a course."""
        mock_get_user.return_value = [sample_user_data]
        mock_get_db.return_value = mock_db
        mock_db._data['quiz'][sample_quiz['id']] = sample_quiz

        mock_get_answers.return_value = [
            {'question': '1', 'correct': True},
            {'question': '2', 'correct': False}
        ]

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_student
            mock_request.args = {'course': 'INFORMATICS_101'}

            response = client.get('/api/student/progress?course=INFORMATICS_101')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['course'] == 'INFORMATICS_101'
        assert len(data['progress']) == 1

        module_progress = data['progress'][0]
        assert module_progress['module'] == 1
        assert module_progress['total_questions'] == 3
        assert module_progress['answered_questions'] == 2
        assert module_progress['correct_questions'] == 1

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    def test_get_student_progress_missing_course(self, mock_get_db, client, mock_jwt_user_student):
        """Test progress requires course parameter."""
        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_student
            mock_request.args = {}

            response = client.get('/api/student/progress')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False


class TestResourceAccess:
    """Test student resource access workflow."""

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    def test_access_class_resources(self, mock_get_db, client, mock_jwt_user_student,
                                    sample_resource, mock_db):
        """Test student can access resources for their class."""
        mock_get_db.return_value = mock_db
        mock_db._data['resources'][sample_resource['id']] = sample_resource

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_student

            response = client.get('/api/resources?class=INFORMATICS_101')

        assert response.status_code == 200
        # Note: Actual endpoint implementation would need to be tested with real routes


class TestQuizAttemptTracking:
    """Test quiz attempt tracking and retry logic."""

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    @patch('informatics_classroom.classroom.api_routes.get_current_user')
    def test_multiple_attempts_tracked(self, mock_get_user, mock_get_db, client,
                                      mock_jwt_user_student, sample_user_data, mock_db):
        """Test that multiple attempts are tracked for the same question."""
        mock_get_user.return_value = [sample_user_data]
        mock_get_db.return_value = mock_db

        mock_db.query_raw.return_value = [
            {
                'question_num': 1,
                'correct_answer': '4',
                'open': False
            }
        ]

        # First attempt (incorrect)
        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_student
            mock_request.get_json.return_value = {
                'course': 'INFORMATICS_101',
                'module': 1,
                'question_num': 1,
                'answer': '3'
            }

            response1 = client.post('/api/quiz/submit-answer',
                                   json={'course': 'INFORMATICS_101', 'module': 1,
                                        'question_num': 1, 'answer': '3'})

        # Second attempt (correct)
        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_student
            mock_request.get_json.return_value = {
                'course': 'INFORMATICS_101',
                'module': 1,
                'question_num': 1,
                'answer': '4'
            }

            response2 = client.post('/api/quiz/submit-answer',
                                   json={'course': 'INFORMATICS_101', 'module': 1,
                                        'question_num': 1, 'answer': '4'})

        # Both attempts should be successful submissions
        assert response1.status_code == 200
        assert response2.status_code == 200

        # Verify both attempts were stored
        assert len(mock_db._data['answer']) == 2
