"""
Unit tests for instructor workflows.

Tests instructor functionality including:
- Class management (create, delete)
- Quiz creation and editing
- Grade viewing and analytics
- Student management
"""

import pytest
import json
from unittest.mock import patch, Mock
from datetime import datetime, timezone
import uuid


class TestClassManagement:
    """Test instructor class management workflow."""

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    @patch('informatics_classroom.classroom.api_routes.get_user_managed_classes')
    @patch('informatics_classroom.classroom.api_routes.get_class_members')
    @patch('informatics_classroom.classroom.api_routes.get_user_class_role')
    def test_get_instructor_classes(self, mock_get_role, mock_get_members,
                                   mock_get_managed, mock_get_db, client,
                                   mock_jwt_user_instructor, sample_quiz, mock_db):
        """Test instructor can retrieve their managed classes."""
        mock_get_managed.return_value = ['INFORMATICS_101']
        mock_get_db.return_value = mock_db
        mock_db._data['quiz'][sample_quiz['id']] = sample_quiz
        mock_get_members.return_value = [
            {'user_id': 'student123', 'role': 'class_student'}
        ]
        mock_get_role.return_value = 'instructor'

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_instructor

            response = client.get('/api/instructor/classes')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['classes']) == 1

        class_data = data['classes'][0]
        assert class_data['name'] == 'INFORMATICS_101'
        assert class_data['quiz_count'] == 1
        assert class_data['student_count'] == 1
        assert class_data['can_delete'] is True

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    @patch('informatics_classroom.classroom.api_routes.assign_class_role')
    def test_create_class_success(self, mock_assign_role, mock_get_db, client,
                                  mock_jwt_user_instructor, mock_db):
        """Test instructor can create a new class."""
        mock_get_db.return_value = mock_db
        mock_assign_role.return_value = {'success': True}

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_instructor
            mock_request.get_json.return_value = {'name': 'INFORMATICS_201'}

            response = client.post('/api/classes',
                                  json={'name': 'INFORMATICS_201'})

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['class']['name'] == 'INFORMATICS_201'
        assert data['class']['owner'] == 'instructor456'
        assert data['class']['role'] == 'instructor'

        # Verify assign_class_role was called
        mock_assign_role.assert_called_once()

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    def test_create_class_duplicate_name(self, mock_get_db, client,
                                        mock_jwt_user_instructor, sample_quiz, mock_db):
        """Test creating class with duplicate name fails."""
        mock_get_db.return_value = mock_db
        mock_db._data['quiz'][sample_quiz['id']] = sample_quiz

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_instructor
            mock_request.get_json.return_value = {'name': 'INFORMATICS_101'}

            response = client.post('/api/classes',
                                  json={'name': 'INFORMATICS_101'})

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'already exists' in data['error']

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    @patch('informatics_classroom.classroom.api_routes.get_user_class_role')
    def test_delete_class_success(self, mock_get_role, mock_get_db, client,
                                  mock_jwt_user_instructor, sample_quiz, mock_db):
        """Test instructor can delete their class."""
        mock_get_db.return_value = mock_db
        mock_db._data['quiz'][sample_quiz['id']] = sample_quiz
        mock_get_role.return_value = 'instructor'

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_instructor

            response = client.delete('/api/classes/INFORMATICS_101')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

        # Verify quiz was deleted
        assert sample_quiz['id'] not in mock_db._data['quiz']

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    @patch('informatics_classroom.classroom.api_routes.get_user_class_role')
    def test_delete_class_no_permission(self, mock_get_role, mock_get_db, client,
                                       mock_jwt_user_student, sample_quiz, mock_db):
        """Test non-instructor cannot delete class."""
        mock_get_db.return_value = mock_db
        mock_db._data['quiz'][sample_quiz['id']] = sample_quiz
        mock_get_role.return_value = 'student'

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_student

            response = client.delete('/api/classes/INFORMATICS_101')

        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['success'] is False


class TestQuizCreationAndEditing:
    """Test quiz creation and editing workflow."""

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    def test_create_quiz_success(self, mock_get_db, client, mock_jwt_user_instructor, mock_db):
        """Test instructor can create a new quiz."""
        mock_get_db.return_value = mock_db

        quiz_data = {
            'class': 'INFORMATICS_101',
            'module': 2,
            'title': 'Python Functions',
            'description': 'Learn about functions',
            'questions': [
                {
                    'question_num': 1,
                    'question_text': 'What is a function?',
                    'answers': ['A loop', 'A reusable block of code', 'A variable', 'A class'],
                    'correct_answer': 'A reusable block of code',
                    'open': False
                }
            ]
        }

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_instructor
            mock_request.get_json.return_value = quiz_data

            response = client.post('/api/quizzes/create', json=quiz_data)

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'quiz_id' in data
        assert data['quiz_id'] == 'INFORMATICS_101_2'

        # Verify quiz was stored
        assert 'INFORMATICS_101_2' in mock_db._data['quiz']
        stored_quiz = mock_db._data['quiz']['INFORMATICS_101_2']
        assert stored_quiz['title'] == 'Python Functions'
        assert stored_quiz['owner'] == 'instructor456'

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    def test_create_quiz_missing_fields(self, mock_get_db, client, mock_jwt_user_instructor):
        """Test creating quiz with missing required fields fails."""
        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_instructor
            mock_request.get_json.return_value = {
                'class': 'INFORMATICS_101',
                'module': 2
            }

            response = client.post('/api/quizzes/create',
                                  json={'class': 'INFORMATICS_101', 'module': 2})

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Missing required fields' in data['error']

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    def test_get_quiz_for_edit(self, mock_get_db, client, mock_jwt_user_instructor,
                               sample_quiz, mock_db):
        """Test instructor can retrieve quiz for editing."""
        mock_get_db.return_value = mock_db
        mock_db._data['quiz'][sample_quiz['id']] = sample_quiz

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_instructor

            response = client.get(f'/api/quizzes/{sample_quiz["id"]}/edit')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['quiz']['id'] == sample_quiz['id']
        assert len(data['quiz']['questions']) == 3

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    def test_update_quiz_success(self, mock_get_db, client, mock_jwt_user_instructor,
                                sample_quiz, mock_db):
        """Test instructor can update existing quiz."""
        mock_get_db.return_value = mock_db
        mock_db._data['quiz'][sample_quiz['id']] = sample_quiz.copy()

        updated_data = {
            'title': 'Updated Python Introduction',
            'description': 'Updated description',
            'questions': sample_quiz['questions']
        }

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_instructor
            mock_request.get_json.return_value = updated_data

            response = client.put(f'/api/quizzes/{sample_quiz["id"]}/update',
                                 json=updated_data)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

        # Verify quiz was updated
        updated_quiz = mock_db._data['quiz'][sample_quiz['id']]
        assert updated_quiz['title'] == 'Updated Python Introduction'

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    def test_update_quiz_tracks_changes(self, mock_get_db, client, mock_jwt_user_instructor,
                                       sample_quiz, mock_db):
        """Test that quiz updates track changes in change_log."""
        mock_get_db.return_value = mock_db
        original_quiz = sample_quiz.copy()
        mock_db._data['quiz'][sample_quiz['id']] = original_quiz

        # Modify question 1's correct answer
        modified_questions = sample_quiz['questions'].copy()
        modified_questions[0] = modified_questions[0].copy()
        modified_questions[0]['correct_answer'] = '5'  # Changed from '4'

        updated_data = {
            'title': sample_quiz['title'],
            'description': sample_quiz['description'],
            'questions': modified_questions
        }

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_instructor
            mock_request.get_json.return_value = updated_data

            response = client.put(f'/api/quizzes/{sample_quiz["id"]}/update',
                                 json=updated_data)

        assert response.status_code == 200

        # Verify change_log was created
        updated_quiz = mock_db._data['quiz'][sample_quiz['id']]
        assert 'change_log' in updated_quiz['questions'][0]
        assert len(updated_quiz['questions'][0]['change_log']) > 0

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    def test_delete_quiz_success(self, mock_get_db, client, mock_jwt_user_instructor,
                                sample_quiz, mock_db):
        """Test instructor can delete quiz."""
        mock_get_db.return_value = mock_db
        mock_db._data['quiz'][sample_quiz['id']] = sample_quiz

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_instructor

            response = client.delete(f'/api/quizzes/{sample_quiz["id"]}')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

        # Verify quiz was deleted
        assert sample_quiz['id'] not in mock_db._data['quiz']


class TestInstructorQuizListing:
    """Test instructor quiz listing workflow."""

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    @patch('informatics_classroom.classroom.api_routes.get_user_managed_classes')
    def test_get_instructor_quizzes_all(self, mock_get_managed, mock_get_db, client,
                                       mock_jwt_user_instructor, sample_quiz, mock_db):
        """Test instructor can list all quizzes for managed classes."""
        mock_get_managed.return_value = ['INFORMATICS_101']
        mock_get_db.return_value = mock_db
        mock_db._data['quiz'][sample_quiz['id']] = sample_quiz

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_instructor
            mock_request.args = {}

            response = client.get('/api/instructor/quizzes')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['quizzes']) == 1
        assert data['quizzes'][0]['id'] == sample_quiz['id']

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    @patch('informatics_classroom.classroom.api_routes.get_user_managed_classes')
    def test_get_instructor_quizzes_filtered(self, mock_get_managed, mock_get_db, client,
                                            mock_jwt_user_instructor, sample_quiz, mock_db):
        """Test filtering quizzes by class."""
        mock_get_managed.return_value = ['INFORMATICS_101', 'INFORMATICS_201']
        mock_get_db.return_value = mock_db
        mock_db._data['quiz'][sample_quiz['id']] = sample_quiz

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_instructor
            mock_request.args = {'class': 'INFORMATICS_101'}

            response = client.get('/api/instructor/quizzes?class=INFORMATICS_101')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert all(q['class'] == 'INFORMATICS_101' for q in data['quizzes'])


class TestGradeViewing:
    """Test instructor grade viewing workflow."""

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    def test_get_class_grades(self, mock_get_db, client, mock_jwt_user_instructor,
                             sample_quiz, mock_db):
        """Test instructor can view class grade matrix."""
        mock_get_db.return_value = mock_db
        mock_db._data['quiz'][sample_quiz['id']] = sample_quiz

        # Mock query_raw for answers
        mock_db.query_raw.return_value = [
            {
                'team': 'student123',
                'question': '1',
                'correct': True,
                'module': 1,
                'course': 'INFORMATICS_101'
            },
            {
                'team': 'student123',
                'question': '2',
                'correct': True,
                'module': 1,
                'course': 'INFORMATICS_101'
            }
        ]

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_instructor

            response = client.get('/api/classes/INFORMATICS_101/grades')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'students' in data
        assert 'quizzes' in data
        assert 'grades' in data

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    @patch('informatics_classroom.classroom.api_routes.get_quiz')
    def test_analyze_assignment(self, mock_get_quiz, mock_get_db, client,
                               mock_jwt_user_instructor, sample_quiz, mock_db):
        """Test assignment analysis with statistics."""
        mock_get_db.return_value = mock_db
        mock_get_quiz.return_value = [sample_quiz]

        # Mock query_raw for answers
        mock_db.query_raw.return_value = [
            {
                'team': 'student123',
                'question': '1',
                'answer': '4',
                'correct': True,
                'module': 1,
                'datetime': datetime.now(timezone.utc).isoformat()
            },
            {
                'team': 'student456',
                'question': '1',
                'answer': '3',
                'correct': False,
                'module': 1,
                'datetime': datetime.now(timezone.utc).isoformat()
            }
        ]

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_instructor
            mock_request.get_json.return_value = {
                'class_name': 'INFORMATICS_101',
                'module_number': '1',
                'year_filter': ''
            }

            response = client.post('/api/assignments/analyze',
                                  json={
                                      'class_name': 'INFORMATICS_101',
                                      'module_number': '1',
                                      'year_filter': ''
                                  })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'module_summary' in data
        assert 'table_correctness' in data
        assert 'table_attempts' in data


class TestClassMemberManagement:
    """Test instructor class member management workflow."""

    @patch('informatics_classroom.classroom.api_routes.user_has_class_permission')
    @patch('informatics_classroom.classroom.api_routes.get_class_members')
    def test_list_class_members(self, mock_get_members, mock_has_permission, client,
                                mock_jwt_user_instructor):
        """Test instructor can list class members."""
        mock_has_permission.return_value = True
        mock_get_members.return_value = [
            {'user_id': 'student123', 'role': 'class_student', 'display_name': 'Student One'},
            {'user_id': 'ta789', 'role': 'class_ta', 'display_name': 'TA One'}
        ]

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_instructor

            response = client.get('/api/classes/INFORMATICS_101/members')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['members']) == 2

    @patch('informatics_classroom.classroom.api_routes.user_has_class_permission')
    @patch('informatics_classroom.classroom.api_routes.assign_class_role')
    @patch('informatics_classroom.classroom.api_routes.validate_role')
    def test_add_class_member(self, mock_validate, mock_assign, mock_has_permission,
                             client, mock_jwt_user_instructor):
        """Test instructor can add member to class."""
        mock_has_permission.return_value = True
        mock_validate.return_value = True
        mock_assign.return_value = {'success': True}

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_instructor
            mock_request.get_json.return_value = {
                'user_id': 'student999',
                'role': 'student'
            }

            response = client.post('/api/classes/INFORMATICS_101/members',
                                  json={'user_id': 'student999', 'role': 'student'})

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        mock_assign.assert_called_once()

    @patch('informatics_classroom.classroom.api_routes.user_has_class_permission')
    @patch('informatics_classroom.classroom.api_routes.update_class_role')
    @patch('informatics_classroom.classroom.api_routes.validate_role')
    def test_update_member_role(self, mock_validate, mock_update, mock_has_permission,
                               client, mock_jwt_user_instructor):
        """Test instructor can update member role."""
        mock_has_permission.return_value = True
        mock_validate.return_value = True
        mock_update.return_value = {'success': True}

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_instructor
            mock_request.get_json.return_value = {'role': 'ta'}

            response = client.put('/api/classes/INFORMATICS_101/members/student123',
                                 json={'role': 'ta'})

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        mock_update.assert_called_once()

    @patch('informatics_classroom.classroom.api_routes.user_has_class_permission')
    @patch('informatics_classroom.classroom.api_routes.remove_class_role')
    def test_remove_class_member(self, mock_remove, mock_has_permission, client,
                                mock_jwt_user_instructor):
        """Test instructor can remove member from class."""
        mock_has_permission.return_value = True
        mock_remove.return_value = {'success': True}

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_instructor

            response = client.delete('/api/classes/INFORMATICS_101/members/student123')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        mock_remove.assert_called_once()

    @patch('informatics_classroom.classroom.api_routes.user_has_class_permission')
    def test_member_management_no_permission(self, mock_has_permission, client,
                                            mock_jwt_user_student):
        """Test non-instructor cannot manage members."""
        mock_has_permission.return_value = False

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_student

            response = client.get('/api/classes/INFORMATICS_101/members')

        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['success'] is False


class TestTokenGeneration:
    """Test instructor token generation workflow."""

    @patch('informatics_classroom.classroom.api_routes.has_class_access')
    @patch('informatics_classroom.classroom.api_routes.set_object')
    def test_generate_token_success(self, mock_set_object, mock_has_access, client,
                                    mock_jwt_user_instructor):
        """Test instructor can generate access token."""
        mock_has_access.return_value = True

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_instructor
            mock_request.get_json.return_value = {
                'class_val': 'INFORMATICS_101',
                'module_val': '1'
            }

            response = client.post('/api/tokens/generate',
                                  json={'class_val': 'INFORMATICS_101', 'module_val': '1'})

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'token' in data
        assert 'expiry' in data
        mock_set_object.assert_called_once()

    @patch('informatics_classroom.classroom.api_routes.has_class_access')
    def test_generate_token_no_access(self, mock_has_access, client, mock_jwt_user_student):
        """Test cannot generate token without class access."""
        mock_has_access.return_value = False

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_student
            mock_request.get_json.return_value = {
                'class_val': 'INFORMATICS_101',
                'module_val': '1'
            }

            response = client.post('/api/tokens/generate',
                                  json={'class_val': 'INFORMATICS_101', 'module_val': '1'})

        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['success'] is False
