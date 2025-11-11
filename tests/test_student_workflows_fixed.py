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
                                        auth_headers_student, sample_quiz,
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

        response = client.get('/api/student/dashboard', headers=auth_headers_student)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'course_summaries' in data

    @patch('informatics_classroom.classroom.api_routes.get_current_user')
    def test_get_dashboard_user_not_found(self, mock_get_user, client, auth_headers_student):
        """Test dashboard returns 404 when user not found."""
        mock_get_user.return_value = None

        response = client.get('/api/student/dashboard', headers=auth_headers_student)

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
