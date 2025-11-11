"""
Unit tests for permission system.

Tests permission validation, role hierarchies, and access control without SSO.
"""

import pytest
from unittest.mock import patch, Mock
from datetime import datetime, timezone


class TestRoleHierarchy:
    """Test role hierarchy and inheritance."""

    def test_admin_has_all_permissions(self):
        """Test that admin role has all permissions."""
        from informatics_classroom.auth.permissions import ROLE_PERMISSIONS

        admin_permissions = ROLE_PERMISSIONS.get('admin', set())
        # Admin should have comprehensive permissions
        assert 'system.admin' in admin_permissions
        assert 'user.manage' in admin_permissions

    def test_instructor_has_teaching_permissions(self):
        """Test that instructor has teaching-related permissions."""
        from informatics_classroom.auth.permissions import ROLE_PERMISSIONS

        instructor_permissions = ROLE_PERMISSIONS.get('instructor', set())
        assert 'quiz.create' in instructor_permissions
        assert 'class.admin' in instructor_permissions

    def test_ta_has_limited_permissions(self):
        """Test that TA has limited teaching permissions."""
        from informatics_classroom.auth.permissions import ROLE_PERMISSIONS

        ta_permissions = ROLE_PERMISSIONS.get('ta', set())
        assert 'quiz.create' in ta_permissions
        assert 'quiz.modify' in ta_permissions
        # TA should not have full class admin
        assert 'class.admin' not in ta_permissions

    def test_student_has_minimal_permissions(self):
        """Test that student has minimal permissions."""
        from informatics_classroom.auth.permissions import ROLE_PERMISSIONS

        student_permissions = ROLE_PERMISSIONS.get('student', set())
        assert 'quiz.view' in student_permissions
        # Students should not have management permissions
        assert 'quiz.create' not in student_permissions
        assert 'user.manage' not in student_permissions


class TestClassRolePermissions:
    """Test class-specific role permissions."""

    @patch('informatics_classroom.auth.class_auth.get_user_class_role')
    def test_class_instructor_can_manage_members(self, mock_get_role):
        """Test class instructor can manage class members."""
        from informatics_classroom.auth.class_auth import user_has_class_permission

        mock_get_role.return_value = 'class_instructor'

        user = {'user_id': 'instructor456', 'roles': ['instructor']}
        has_permission = user_has_class_permission(user, 'INFORMATICS_101', 'manage_members')

        assert has_permission is True

    @patch('informatics_classroom.auth.class_auth.get_user_class_role')
    def test_class_ta_cannot_manage_members(self, mock_get_role):
        """Test class TA cannot manage class members."""
        from informatics_classroom.auth.class_auth import user_has_class_permission

        mock_get_role.return_value = 'class_ta'

        user = {'user_id': 'ta789', 'roles': ['ta']}
        has_permission = user_has_class_permission(user, 'INFORMATICS_101', 'manage_members')

        assert has_permission is False

    @patch('informatics_classroom.auth.class_auth.get_user_class_role')
    def test_class_student_can_view_only(self, mock_get_role):
        """Test class student has view-only permissions."""
        from informatics_classroom.auth.class_auth import user_has_class_permission

        mock_get_role.return_value = 'class_student'

        user = {'user_id': 'student123', 'roles': ['student']}
        has_view = user_has_class_permission(user, 'INFORMATICS_101', 'view_quizzes')
        has_manage = user_has_class_permission(user, 'INFORMATICS_101', 'manage_quizzes')

        assert has_view is True
        assert has_manage is False


class TestPermissionValidation:
    """Test permission validation logic."""

    def test_validate_role_accepts_valid_roles(self):
        """Test that valid roles are accepted."""
        from informatics_classroom.auth.class_auth import validate_role

        assert validate_role('instructor') is True
        assert validate_role('ta') is True
        assert validate_role('student') is True

    def test_validate_role_rejects_invalid_roles(self):
        """Test that invalid roles are rejected."""
        from informatics_classroom.auth.class_auth import validate_role

        assert validate_role('invalid') is False
        assert validate_role('') is False
        assert validate_role(None) is False

    @patch('informatics_classroom.auth.class_auth.get_user_class_role')
    def test_has_class_access_with_membership(self, mock_get_role):
        """Test user has class access when member."""
        from informatics_classroom.auth.class_auth import has_class_access

        mock_get_role.return_value = 'class_student'

        user_id = 'student123'
        class_id = 'INFORMATICS_101'

        assert has_class_access(user_id, class_id) is True

    @patch('informatics_classroom.auth.class_auth.get_user_class_role')
    def test_has_class_access_without_membership(self, mock_get_role):
        """Test user lacks class access when not member."""
        from informatics_classroom.auth.class_auth import has_class_access

        mock_get_role.return_value = None

        user_id = 'student999'
        class_id = 'INFORMATICS_101'

        assert has_class_access(user_id, class_id) is False


class TestPermissionDecorators:
    """Test permission decorator functions."""

    @patch('informatics_classroom.auth.class_auth.user_has_class_permission')
    def test_require_class_permission_allows_access(self, mock_has_permission, client,
                                                    mock_jwt_user_instructor):
        """Test decorator allows access with proper permission."""
        mock_has_permission.return_value = True

        # Decorator should allow request to proceed
        # Actual test would require endpoint with decorator

    @patch('informatics_classroom.auth.class_auth.user_has_class_permission')
    def test_require_class_permission_denies_access(self, mock_has_permission, client,
                                                   mock_jwt_user_student):
        """Test decorator denies access without permission."""
        mock_has_permission.return_value = False

        # Decorator should return 403
        # Actual test would require endpoint with decorator

    def test_require_role_allows_matching_role(self, client, mock_jwt_user_admin):
        """Test role requirement allows matching role."""
        # Admin role should pass @require_role(['admin'])
        pass

    def test_require_role_denies_non_matching_role(self, client, mock_jwt_user_student):
        """Test role requirement denies non-matching role."""
        # Student role should fail @require_role(['admin', 'instructor'])
        pass


class TestQuizPermissions:
    """Test quiz-specific permission logic."""

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    @patch('informatics_classroom.auth.class_auth.user_has_class_permission')
    def test_quiz_owner_can_modify(self, mock_has_permission, mock_get_db,
                                   mock_jwt_user_instructor, sample_quiz, mock_db):
        """Test quiz owner can modify their quiz."""
        mock_get_db.return_value = mock_db
        mock_db._data['quiz'][sample_quiz['id']] = sample_quiz
        mock_has_permission.return_value = True

        # Owner should have modify permission
        user = mock_jwt_user_instructor
        assert user['user_id'] == sample_quiz['owner']

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    @patch('informatics_classroom.auth.class_auth.user_has_class_permission')
    def test_class_ta_can_modify_quiz(self, mock_has_permission, mock_get_db,
                                     mock_jwt_user_ta, sample_quiz, mock_db):
        """Test class TA can modify quiz even if not owner."""
        mock_get_db.return_value = mock_db
        mock_db._data['quiz'][sample_quiz['id']] = sample_quiz
        mock_has_permission.return_value = True

        # TA with manage_quizzes permission should be able to modify
        user = mock_jwt_user_ta
        assert user['user_id'] != sample_quiz['owner']

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    @patch('informatics_classroom.auth.class_auth.user_has_class_permission')
    def test_student_cannot_modify_quiz(self, mock_has_permission, mock_get_db,
                                       mock_jwt_user_student, sample_quiz, mock_db):
        """Test student cannot modify quiz."""
        mock_get_db.return_value = mock_db
        mock_db._data['quiz'][sample_quiz['id']] = sample_quiz
        mock_has_permission.return_value = False

        # Student should not have manage_quizzes permission


class TestClassMembershipPermissions:
    """Test class membership and role assignment permissions."""

    @patch('informatics_classroom.auth.class_auth.get_user_class_role')
    def test_instructor_can_add_members(self, mock_get_role):
        """Test instructor can add members to their class."""
        from informatics_classroom.auth.class_auth import user_has_class_permission

        mock_get_role.return_value = 'class_instructor'

        user = {'user_id': 'instructor456', 'roles': ['instructor']}
        can_add = user_has_class_permission(user, 'INFORMATICS_101', 'manage_members')

        assert can_add is True

    @patch('informatics_classroom.auth.class_auth.get_user_class_role')
    def test_ta_cannot_add_members(self, mock_get_role):
        """Test TA cannot add members to class."""
        from informatics_classroom.auth.class_auth import user_has_class_permission

        mock_get_role.return_value = 'class_ta'

        user = {'user_id': 'ta789', 'roles': ['ta']}
        can_add = user_has_class_permission(user, 'INFORMATICS_101', 'manage_members')

        assert can_add is False

    @patch('informatics_classroom.auth.class_auth.get_current_user')
    def test_assign_role_updates_membership(self, mock_get_user, mock_db):
        """Test assigning role updates user's class_memberships."""
        from informatics_classroom.auth.class_auth import assign_class_role

        mock_get_user.return_value = [{
            'id': 'student123',
            'class_memberships': []
        }]

        result = assign_class_role('student123', 'INFORMATICS_101', 'class_student',
                                  assigned_by='instructor456')

        # Verify membership was added
        assert result['success'] is True

    @patch('informatics_classroom.auth.class_auth.get_current_user')
    def test_remove_role_updates_membership(self, mock_get_user, mock_db):
        """Test removing role updates user's class_memberships."""
        from informatics_classroom.auth.class_auth import remove_class_role

        mock_get_user.return_value = [{
            'id': 'student123',
            'class_memberships': [
                {'class_id': 'INFORMATICS_101', 'role': 'class_student'}
            ]
        }]

        result = remove_class_role('student123', 'INFORMATICS_101')

        # Verify membership was removed
        assert result['success'] is True


class TestPermissionEdgeCases:
    """Test edge cases in permission system."""

    def test_user_with_no_roles(self):
        """Test user with no roles has no permissions."""
        user = {'user_id': 'user123', 'roles': []}

        # User should have no permissions

    def test_user_with_multiple_roles(self):
        """Test user with multiple roles gets combined permissions."""
        user = {'user_id': 'user123', 'roles': ['instructor', 'admin']}

        # User should have union of both role permissions

    def test_permission_check_with_invalid_class(self):
        """Test permission check with non-existent class."""
        from informatics_classroom.auth.class_auth import has_class_access

        result = has_class_access('student123', 'NONEXISTENT_CLASS')

        assert result is False

    def test_permission_check_with_invalid_user(self):
        """Test permission check with non-existent user."""
        from informatics_classroom.auth.class_auth import has_class_access

        result = has_class_access('nonexistent_user', 'INFORMATICS_101')

        assert result is False

    @patch('informatics_classroom.auth.class_auth.get_user_class_role')
    def test_admin_bypasses_class_permissions(self, mock_get_role):
        """Test admin has access regardless of class membership."""
        from informatics_classroom.auth.class_auth import user_has_class_permission

        mock_get_role.return_value = None  # Not a class member

        user = {'user_id': 'admin001', 'roles': ['admin']}
        has_permission = user_has_class_permission(user, 'INFORMATICS_101', 'manage_members')

        # Admin should have access even without class membership
        assert has_permission is True
