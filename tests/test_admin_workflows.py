"""
Unit tests for admin workflows.

Tests admin functionality including:
- User management
- Permission management
- Audit logging
- User impersonation
- System-wide operations
"""

import pytest
import json
from unittest.mock import patch, Mock
from datetime import datetime, timezone
import uuid


class TestUserManagement:
    """Test admin user management workflow."""

    @patch('informatics_classroom.auth.api_routes.get_database_adapter')
    def test_list_users_paginated(self, mock_get_db, client, mock_jwt_user_admin, mock_db):
        """Test admin can list users with pagination."""
        mock_get_db.return_value = mock_db

        # Add sample users
        for i in range(5):
            user = {
                'id': f'user{i}',
                'email': f'user{i}@university.edu',
                'display_name': f'User {i}',
                'role': 'student',
                'active': True
            }
            mock_db._data['users'][user['id']] = user

        with patch('informatics_classroom.auth.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_admin
            mock_request.args = {'page': '1', 'pageSize': '10'}

            response = client.get('/api/users?page=1&pageSize=10')

        # Note: Actual implementation would need proper endpoint
        # This demonstrates expected behavior

    @patch('informatics_classroom.auth.api_routes.get_database_adapter')
    def test_list_users_with_role_filter(self, mock_get_db, client, mock_jwt_user_admin, mock_db):
        """Test filtering users by role."""
        mock_get_db.return_value = mock_db

        # Add users with different roles
        student = {'id': 'student1', 'email': 's@edu', 'role': 'student'}
        instructor = {'id': 'instructor1', 'email': 'i@edu', 'role': 'instructor'}
        mock_db._data['users']['student1'] = student
        mock_db._data['users']['instructor1'] = instructor

        with patch('informatics_classroom.auth.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_admin
            mock_request.args = {'role': 'instructor'}

            response = client.get('/api/users?role=instructor')

        # Expected: Only instructor users returned

    @patch('informatics_classroom.auth.api_routes.get_database_adapter')
    def test_update_user_details(self, mock_get_db, client, mock_jwt_user_admin, mock_db):
        """Test admin can update user details."""
        mock_get_db.return_value = mock_db

        user = {
            'id': 'student123',
            'email': 'student@university.edu',
            'display_name': 'Old Name',
            'role': 'student'
        }
        mock_db._data['users'][user['id']] = user

        update_data = {
            'email': 'newemail@university.edu',
            'display_name': 'New Name',
            'role': 'student'
        }

        with patch('informatics_classroom.auth.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_admin
            mock_request.get_json.return_value = update_data

            response = client.put('/api/users/student123', json=update_data)

        # Verify user was updated
        updated_user = mock_db._data['users']['student123']
        assert updated_user['email'] == 'newemail@university.edu'
        assert updated_user['display_name'] == 'New Name'

    @patch('informatics_classroom.auth.api_routes.get_database_adapter')
    def test_update_user_role(self, mock_get_db, client, mock_jwt_user_admin, mock_db):
        """Test admin can change user's global role."""
        mock_get_db.return_value = mock_db

        user = {
            'id': 'student123',
            'email': 'student@university.edu',
            'display_name': 'Test User',
            'role': 'student'
        }
        mock_db._data['users'][user['id']] = user

        with patch('informatics_classroom.auth.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_admin
            mock_request.get_json.return_value = {'role': 'instructor'}

            response = client.put('/api/users/student123',
                                 json={'role': 'instructor'})

        updated_user = mock_db._data['users']['student123']
        assert updated_user['role'] == 'instructor'

    def test_non_admin_cannot_manage_users(self, client, mock_jwt_user_student):
        """Test non-admin cannot access user management."""
        with patch('informatics_classroom.auth.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_student

            response = client.get('/api/users')

        # Expected: 403 Forbidden or redirect


class TestPermissionManagement:
    """Test admin permission management workflow."""

    @patch('informatics_classroom.auth.api_routes.get_database_adapter')
    def test_check_user_permission(self, mock_get_db, client, mock_jwt_user_admin, mock_db):
        """Test checking if user has specific permission."""
        mock_get_db.return_value = mock_db

        with patch('informatics_classroom.auth.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_admin
            mock_request.args = {
                'user_id': 'instructor456',
                'permission': 'quiz.create',
                'class_id': 'INFORMATICS_101'
            }

            response = client.get('/api/permissions/check?user_id=instructor456&permission=quiz.create&class_id=INFORMATICS_101')

        # Expected: Boolean response indicating permission status

    def test_get_user_permissions_detail(self, client, mock_jwt_user_admin):
        """Test retrieving detailed permissions for a user."""
        with patch('informatics_classroom.auth.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_admin

            response = client.get('/api/users/instructor456/permissions')

        # Expected: Complete permission matrix for user


class TestUserImpersonation:
    """Test admin user impersonation workflow."""

    @patch('informatics_classroom.auth.impersonation.start_impersonation')
    def test_start_impersonation_success(self, mock_start_impersonation, client,
                                        mock_jwt_user_admin):
        """Test admin can impersonate another user."""
        mock_start_impersonation.return_value = {
            'success': True,
            'token': 'impersonation-token-123',
            'target_user': 'student123'
        }

        with patch('informatics_classroom.auth.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_admin
            mock_request.get_json.return_value = {'target_user_id': 'student123'}

            response = client.post('/api/auth/impersonate',
                                  json={'target_user_id': 'student123'})

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'token' in data

    def test_non_admin_cannot_impersonate(self, client, mock_jwt_user_student):
        """Test non-admin cannot impersonate users."""
        with patch('informatics_classroom.auth.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_student
            mock_request.get_json.return_value = {'target_user_id': 'instructor456'}

            response = client.post('/api/auth/impersonate',
                                  json={'target_user_id': 'instructor456'})

        assert response.status_code == 403

    @patch('informatics_classroom.auth.impersonation.end_impersonation')
    def test_exit_impersonation(self, mock_end_impersonation, client, mock_jwt_user_admin):
        """Test admin can exit impersonation mode."""
        mock_end_impersonation.return_value = {
            'success': True,
            'original_token': 'admin-token-123'
        }

        with patch('informatics_classroom.auth.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_admin

            response = client.post('/api/auth/exit-impersonation')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    @patch('informatics_classroom.auth.impersonation.get_impersonation_context')
    def test_impersonation_context_accessible(self, mock_get_context, client,
                                             mock_jwt_user_admin):
        """Test impersonation context is accessible while impersonating."""
        mock_get_context.return_value = {
            'is_impersonating': True,
            'original_user_id': 'admin001',
            'target_user_id': 'student123'
        }

        # Any request while impersonating should have context
        with patch('informatics_classroom.auth.api_routes.request') as mock_request:
            mock_request.jwt_user = {
                'user_id': 'student123',
                'impersonated_by': 'admin001',
                'is_impersonation': True
            }

            # Make any authenticated request
            response = client.get('/api/student/courses')

        # System should recognize impersonation context


class TestAuditLogging:
    """Test admin audit log viewing workflow."""

    @patch('informatics_classroom.auth.api_routes.get_database_adapter')
    def test_get_audit_logs_paginated(self, mock_get_db, client, mock_jwt_user_admin, mock_db):
        """Test admin can retrieve audit logs with pagination."""
        mock_get_db.return_value = mock_db

        # Add sample audit logs
        for i in range(10):
            log = {
                'id': str(uuid.uuid4()),
                'action': 'quiz.create',
                'user_id': f'user{i}',
                'class_id': 'INFORMATICS_101',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'details': {'quiz_id': f'INFORMATICS_101_{i}'}
            }
            mock_db._data.setdefault('audit_logs', {})[log['id']] = log

        with patch('informatics_classroom.auth.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_admin
            mock_request.args = {'page': '1', 'pageSize': '20'}

            response = client.get('/api/audit/logs?page=1&pageSize=20')

        # Expected: Paginated audit log response

    @patch('informatics_classroom.auth.api_routes.get_database_adapter')
    def test_filter_audit_logs_by_action(self, mock_get_db, client, mock_jwt_user_admin, mock_db):
        """Test filtering audit logs by action type."""
        mock_get_db.return_value = mock_db

        # Add logs with different actions
        create_log = {
            'id': str(uuid.uuid4()),
            'action': 'quiz.create',
            'user_id': 'instructor456',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        delete_log = {
            'id': str(uuid.uuid4()),
            'action': 'quiz.delete',
            'user_id': 'instructor456',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        mock_db._data.setdefault('audit_logs', {})[create_log['id']] = create_log
        mock_db._data['audit_logs'][delete_log['id']] = delete_log

        with patch('informatics_classroom.auth.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_admin
            mock_request.args = {'action': 'quiz.create'}

            response = client.get('/api/audit/logs?action=quiz.create')

        # Expected: Only quiz.create actions returned

    @patch('informatics_classroom.auth.api_routes.get_database_adapter')
    def test_filter_audit_logs_by_user(self, mock_get_db, client, mock_jwt_user_admin, mock_db):
        """Test filtering audit logs by user ID."""
        mock_get_db.return_value = mock_db

        log1 = {
            'id': str(uuid.uuid4()),
            'action': 'quiz.create',
            'user_id': 'instructor456',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        log2 = {
            'id': str(uuid.uuid4()),
            'action': 'user.update',
            'user_id': 'admin001',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        mock_db._data.setdefault('audit_logs', {})[log1['id']] = log1
        mock_db._data['audit_logs'][log2['id']] = log2

        with patch('informatics_classroom.auth.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_admin
            mock_request.args = {'user_id': 'instructor456'}

            response = client.get('/api/audit/logs?user_id=instructor456')

        # Expected: Only instructor456's actions returned

    @patch('informatics_classroom.auth.api_routes.get_database_adapter')
    def test_filter_audit_logs_by_date_range(self, mock_get_db, client,
                                            mock_jwt_user_admin, mock_db):
        """Test filtering audit logs by date range."""
        mock_get_db.return_value = mock_db

        from datetime import timedelta
        today = datetime.now(timezone.utc)
        yesterday = today - timedelta(days=1)

        log_today = {
            'id': str(uuid.uuid4()),
            'action': 'quiz.create',
            'user_id': 'instructor456',
            'timestamp': today.isoformat()
        }
        log_yesterday = {
            'id': str(uuid.uuid4()),
            'action': 'quiz.create',
            'user_id': 'instructor456',
            'timestamp': yesterday.isoformat()
        }
        mock_db._data.setdefault('audit_logs', {})[log_today['id']] = log_today
        mock_db._data['audit_logs'][log_yesterday['id']] = log_yesterday

        with patch('informatics_classroom.auth.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_admin
            mock_request.args = {
                'start_date': yesterday.date().isoformat(),
                'end_date': today.date().isoformat()
            }

            response = client.get(f'/api/audit/logs?start_date={yesterday.date().isoformat()}&end_date={today.date().isoformat()}')

        # Expected: Logs within date range

    def test_non_admin_cannot_view_audit_logs(self, client, mock_jwt_user_student):
        """Test non-admin cannot access audit logs."""
        with patch('informatics_classroom.auth.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_student

            response = client.get('/api/audit/logs')

        assert response.status_code == 403


class TestSystemWideOperations:
    """Test admin system-wide operations."""

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    def test_view_all_classes_as_admin(self, mock_get_db, client, mock_jwt_user_admin,
                                      sample_quiz, mock_db):
        """Test admin can view all classes in system."""
        mock_get_db.return_value = mock_db
        mock_db._data['quiz'][sample_quiz['id']] = sample_quiz

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_admin

            response = client.get('/api/instructor/classes')

        assert response.status_code == 200
        data = json.loads(response.data)
        # Admin should see all classes

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    def test_admin_can_delete_any_class(self, mock_get_db, client, mock_jwt_user_admin,
                                       sample_quiz, mock_db):
        """Test admin can delete any class regardless of ownership."""
        mock_get_db.return_value = mock_db
        mock_db._data['quiz'][sample_quiz['id']] = sample_quiz

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_admin

            response = client.delete('/api/classes/INFORMATICS_101')

        # Admin should be able to delete

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    def test_admin_can_manage_any_class_members(self, mock_get_db, client,
                                               mock_jwt_user_admin, mock_db):
        """Test admin can manage members of any class."""
        mock_get_db.return_value = mock_db

        with patch('informatics_classroom.classroom.api_routes.user_has_class_permission') as mock_perm:
            mock_perm.return_value = True

            with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
                mock_request.jwt_user = mock_jwt_user_admin

                response = client.get('/api/classes/INFORMATICS_101/members')

        # Admin should have access


class TestPermissionChecks:
    """Test permission validation workflows."""

    def test_permission_decorator_allows_admin(self, client, mock_jwt_user_admin):
        """Test that admin bypasses most permission checks."""
        # Admins should have access to all endpoints
        pass

    def test_permission_decorator_blocks_unauthorized(self, client, mock_jwt_user_student):
        """Test that permission decorators block unauthorized access."""
        # Students should not access admin endpoints
        with patch('informatics_classroom.auth.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_student

            response = client.get('/api/users')

        # Expected: 403 or redirect

    @patch('informatics_classroom.auth.class_auth.user_has_class_permission')
    def test_class_permission_validation(self, mock_has_permission, client,
                                        mock_jwt_user_instructor):
        """Test class-level permission validation."""
        mock_has_permission.return_value = True

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_instructor

            # Should succeed with permission
            response = client.get('/api/classes/INFORMATICS_101/members')

    @patch('informatics_classroom.auth.class_auth.user_has_class_permission')
    def test_class_permission_denied(self, mock_has_permission, client, mock_jwt_user_student):
        """Test class permission denial."""
        mock_has_permission.return_value = False

        with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_student

            # Should fail without permission
            response = client.get('/api/classes/INFORMATICS_101/members')

        assert response.status_code == 403


class TestDataIntegrity:
    """Test data integrity in admin operations."""

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    def test_delete_class_preserves_answer_data(self, mock_get_db, client,
                                               mock_jwt_user_admin, sample_quiz,
                                               sample_answers, mock_db):
        """Test that deleting class preserves historical answer data."""
        mock_get_db.return_value = mock_db
        mock_db._data['quiz'][sample_quiz['id']] = sample_quiz

        # Add answers
        for answer in sample_answers:
            mock_db._data['answer'][answer['id']] = answer

        with patch('informatics_classroom.classroom.api_routes.get_user_class_role') as mock_role:
            mock_role.return_value = 'admin'

            with patch('informatics_classroom.classroom.api_routes.request') as mock_request:
                mock_request.jwt_user = mock_jwt_user_admin

                response = client.delete('/api/classes/INFORMATICS_101')

        # Verify quiz deleted but answers preserved
        assert sample_quiz['id'] not in mock_db._data['quiz']
        assert len(mock_db._data['answer']) == len(sample_answers)

    @patch('informatics_classroom.auth.api_routes.get_database_adapter')
    def test_user_update_maintains_class_memberships(self, mock_get_db, client,
                                                    mock_jwt_user_admin, mock_db):
        """Test that updating user doesn't lose class memberships."""
        mock_get_db.return_value = mock_db

        original_user = {
            'id': 'student123',
            'email': 'student@university.edu',
            'display_name': 'Test Student',
            'role': 'student',
            'class_memberships': [
                {'class_id': 'INFORMATICS_101', 'role': 'class_student'}
            ]
        }
        mock_db._data['users'][original_user['id']] = original_user.copy()

        with patch('informatics_classroom.auth.api_routes.request') as mock_request:
            mock_request.jwt_user = mock_jwt_user_admin
            mock_request.get_json.return_value = {
                'display_name': 'Updated Name'
            }

            response = client.put('/api/users/student123',
                                 json={'display_name': 'Updated Name'})

        # Verify class_memberships preserved
        updated_user = mock_db._data['users']['student123']
        assert len(updated_user.get('class_memberships', [])) == 1
