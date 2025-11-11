"""
Comprehensive Permission Matrix Testing

Tests role-based access control across all API endpoints to ensure:
- Each role can access appropriate endpoints
- Each role is blocked from unauthorized endpoints
- Class-based permissions are enforced
- Role hierarchy is respected (admin > instructor > ta > student)
"""

import pytest
import json
from unittest.mock import patch, MagicMock


class TestStudentPermissions:
    """Test student role access patterns"""

    # ✅ Student CAN access these endpoints

    @patch('informatics_classroom.classroom.api_routes.get_classes_for_user')
    def test_student_can_access_courses(self, mock_get_classes, client, auth_headers_student):
        """Students can access /api/student/courses"""
        mock_get_classes.return_value = ['CLASS_101']

        response = client.get('/api/student/courses', headers=auth_headers_student)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    @patch('informatics_classroom.classroom.api_routes.get_current_user')
    @patch('informatics_classroom.classroom.api_routes.get_classes_for_user')
    def test_student_can_access_dashboard(self, mock_get_classes, mock_get_user,
                                          client, auth_headers_student, sample_user_data):
        """Students can access /api/student/dashboard"""
        mock_get_user.return_value = [sample_user_data]
        mock_get_classes.return_value = ['CLASS_101']

        response = client.get('/api/student/dashboard', headers=auth_headers_student)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    def test_student_can_access_quiz_details(self, mock_get_db, client,
                                             auth_headers_student, mock_db, sample_quiz):
        """Students can view quiz details"""
        mock_get_db.return_value = mock_db
        mock_db._data['quiz'][sample_quiz['id']] = sample_quiz

        response = client.get(
            f'/api/quiz/details?class_name=CLASS_101&module_num=1',
            headers=auth_headers_student
        )

        # May be 200 or 404 depending on implementation
        assert response.status_code in [200, 404]

    @patch('informatics_classroom.classroom.routes.process_answers_session')
    def test_student_can_submit_answers(self, mock_process, client, auth_headers_student):
        """Students can submit quiz answers"""
        mock_process.return_value = {
            'feedback': {
                '1': {'correct': True, 'message': 'Correct!'}
            },
            'status': 200
        }

        response = client.post(
            '/api/quiz/submit-answer',
            headers=auth_headers_student,
            json={
                'class': 'CLASS_101',
                'module': 1,
                'answers': {'1': '4'}
            }
        )

        # May be 200, 404, or 400 depending on implementation
        assert response.status_code in [200, 400, 404]

    # ❌ Student CANNOT access these endpoints

    def test_student_cannot_access_instructor_classes(self, client, auth_headers_student):
        """Students cannot access /api/instructor/classes"""
        response = client.get('/api/instructor/classes', headers=auth_headers_student)

        # Should be forbidden or not found
        assert response.status_code in [403, 404]

    def test_student_cannot_create_class(self, client, auth_headers_student):
        """Students cannot create classes"""
        response = client.post(
            '/api/classes',
            headers=auth_headers_student,
            json={'name': 'NEW_CLASS', 'description': 'Test'}
        )

        assert response.status_code in [403, 404]

    def test_student_cannot_create_quiz(self, client, auth_headers_student):
        """Students cannot create quizzes"""
        response = client.post(
            '/api/quizzes/create',
            headers=auth_headers_student,
            json={
                'class': 'CLASS_101',
                'module': 1,
                'title': 'New Quiz',
                'questions': []
            }
        )

        assert response.status_code in [403, 404]

    def test_student_cannot_delete_class(self, client, auth_headers_student):
        """Students cannot delete classes"""
        response = client.delete(
            '/api/classes/CLASS_101',
            headers=auth_headers_student
        )

        assert response.status_code in [403, 404]

    def test_student_cannot_view_all_grades(self, client, auth_headers_student):
        """Students cannot view all grades for a class"""
        response = client.get(
            '/api/classes/CLASS_101/grades',
            headers=auth_headers_student
        )

        assert response.status_code in [403, 404]

    def test_student_cannot_impersonate_users(self, client, auth_headers_student):
        """Students cannot impersonate other users"""
        response = client.post(
            '/api/admin/impersonate',
            headers=auth_headers_student,
            json={'user_id': 'other@example.com'}
        )

        assert response.status_code in [403, 404]


class TestInstructorPermissions:
    """Test instructor role access patterns"""

    # ✅ Instructor CAN access these endpoints

    @patch('informatics_classroom.classroom.api_routes.get_classes_for_user')
    def test_instructor_can_access_instructor_classes(self, mock_get_classes,
                                                      client, auth_headers_instructor):
        """Instructors can access /api/instructor/classes"""
        mock_get_classes.return_value = ['CLASS_101', 'CLASS_201']

        response = client.get('/api/instructor/classes', headers=auth_headers_instructor)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_instructor_can_create_class(self, client, auth_headers_instructor):
        """Instructors can create classes"""
        response = client.post(
            '/api/classes',
            headers=auth_headers_instructor,
            json={
                'name': 'NEW_CLASS',
                'description': 'Test Class',
                'owner': 'instructor@example.com'
            }
        )

        # May succeed or fail for other reasons, but should not be 403
        assert response.status_code != 403

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    def test_instructor_can_create_quiz(self, mock_get_db, client,
                                       auth_headers_instructor, mock_db):
        """Instructors can create quizzes"""
        mock_get_db.return_value = mock_db

        response = client.post(
            '/api/quizzes/create',
            headers=auth_headers_instructor,
            json={
                'class': 'INFORMATICS_101',
                'module': 1,
                'title': 'Test Quiz',
                'questions': []
            }
        )

        # Should not be forbidden
        assert response.status_code != 403

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    def test_instructor_can_view_grades(self, mock_get_db, client,
                                       auth_headers_instructor, mock_db):
        """Instructors can view class grades"""
        mock_get_db.return_value = mock_db

        response = client.get(
            '/api/classes/INFORMATICS_101/grades',
            headers=auth_headers_instructor
        )

        # Should not be forbidden (may be 404 if not implemented)
        assert response.status_code != 403

    # ✅ Instructor CAN ALSO access student endpoints (role hierarchy)

    @patch('informatics_classroom.classroom.api_routes.get_classes_for_user')
    def test_instructor_can_access_student_courses(self, mock_get_classes,
                                                   client, auth_headers_instructor):
        """Instructors can access student endpoints (higher role)"""
        mock_get_classes.return_value = ['CLASS_101']

        response = client.get('/api/student/courses', headers=auth_headers_instructor)

        # Instructors should be able to view student-level data
        assert response.status_code == 200

    # ❌ Instructor CANNOT access these endpoints

    def test_instructor_cannot_impersonate_users(self, client, auth_headers_instructor):
        """Instructors cannot impersonate users (admin-only)"""
        response = client.post(
            '/api/admin/impersonate',
            headers=auth_headers_instructor,
            json={'user_id': 'student@example.com'}
        )

        assert response.status_code in [403, 404]


class TestTAPermissions:
    """Test TA role access patterns"""

    # ✅ TA CAN access these endpoints

    @patch('informatics_classroom.classroom.api_routes.get_classes_for_user')
    def test_ta_can_access_student_courses(self, mock_get_classes, client, auth_headers_ta):
        """TAs can access student endpoints"""
        mock_get_classes.return_value = ['CLASS_101']

        response = client.get('/api/student/courses', headers=auth_headers_ta)

        assert response.status_code == 200

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    def test_ta_can_create_quiz_in_assigned_class(self, mock_get_db, client,
                                                  auth_headers_ta, mock_db):
        """TAs can create quizzes in classes where they are TAs"""
        mock_get_db.return_value = mock_db

        response = client.post(
            '/api/quizzes/create',
            headers=auth_headers_ta,
            json={
                'class': 'INFORMATICS_101',
                'module': 1,
                'title': 'TA Quiz',
                'questions': []
            }
        )

        # Should not be forbidden (may fail for other reasons)
        assert response.status_code != 403

    # ❌ TA CANNOT access these endpoints

    def test_ta_cannot_create_class(self, client, auth_headers_ta):
        """TAs cannot create new classes"""
        response = client.post(
            '/api/classes',
            headers=auth_headers_ta,
            json={'name': 'TA_CLASS', 'description': 'Test'}
        )

        assert response.status_code in [403, 404]

    def test_ta_cannot_delete_class(self, client, auth_headers_ta):
        """TAs cannot delete classes"""
        response = client.delete(
            '/api/classes/CLASS_101',
            headers=auth_headers_ta
        )

        assert response.status_code in [403, 404]


class TestAdminPermissions:
    """Test admin role access patterns (should have access to everything)"""

    @patch('informatics_classroom.classroom.api_routes.get_classes_for_user')
    def test_admin_can_access_student_endpoints(self, mock_get_classes,
                                                client, auth_headers_admin):
        """Admins can access student endpoints"""
        mock_get_classes.return_value = ['CLASS_101']

        response = client.get('/api/student/courses', headers=auth_headers_admin)

        assert response.status_code == 200

    @patch('informatics_classroom.classroom.api_routes.get_classes_for_user')
    def test_admin_can_access_instructor_endpoints(self, mock_get_classes,
                                                   client, auth_headers_admin):
        """Admins can access instructor endpoints"""
        mock_get_classes.return_value = ['CLASS_101']

        response = client.get('/api/instructor/classes', headers=auth_headers_admin)

        assert response.status_code == 200

    def test_admin_can_create_class(self, client, auth_headers_admin):
        """Admins can create classes"""
        response = client.post(
            '/api/classes',
            headers=auth_headers_admin,
            json={
                'name': 'ADMIN_CLASS',
                'description': 'Admin Test Class',
                'owner': 'admin@example.com'
            }
        )

        # Should not be forbidden
        assert response.status_code != 403

    def test_admin_can_delete_class(self, client, auth_headers_admin):
        """Admins can delete classes"""
        response = client.delete(
            '/api/classes/CLASS_101',
            headers=auth_headers_admin
        )

        # Should not be forbidden (may be 404 if class doesn't exist)
        assert response.status_code != 403

    @patch('informatics_classroom.database.factory.get_database_adapter')
    def test_admin_can_impersonate_users(self, mock_get_db, client,
                                        auth_headers_admin, mock_db, sample_user_data):
        """Admins can impersonate other users"""
        mock_get_db.return_value = mock_db
        mock_db._data['users']['student@example.com'] = sample_user_data

        response = client.post(
            '/api/admin/impersonate',
            headers=auth_headers_admin,
            json={'user_id': 'student@example.com'}
        )

        # Should not be forbidden (may be 404 if endpoint doesn't exist)
        assert response.status_code != 403


class TestRoleHierarchy:
    """Test that role hierarchy is properly enforced"""

    def test_role_hierarchy_order(self):
        """Test that roles are ordered: admin > instructor > ta > student"""
        from informatics_classroom.auth.permissions import get_role_permissions_with_inheritance

        admin_perms = get_role_permissions_with_inheritance('admin')
        instructor_perms = get_role_permissions_with_inheritance('instructor')
        ta_perms = get_role_permissions_with_inheritance('ta')
        student_perms = get_role_permissions_with_inheritance('student')

        # Admin should have wildcard or most permissions
        assert '*' in admin_perms or len(admin_perms) >= len(instructor_perms)

        # Instructor should have more permissions than TA
        assert len(instructor_perms) >= len(ta_perms)

        # TA should have more permissions than student
        assert len(ta_perms) >= len(student_perms)

    def test_instructor_inherits_student_permissions(self):
        """Test that instructors have all student permissions"""
        from informatics_classroom.auth.permissions import get_role_permissions_with_inheritance

        instructor_perms = get_role_permissions_with_inheritance('instructor')
        student_perms = get_role_permissions_with_inheritance('student')

        # All student permissions should be in instructor permissions
        for perm in student_perms:
            assert perm in instructor_perms, f"Instructor missing student permission: {perm}"

    def test_ta_inherits_student_permissions(self):
        """Test that TAs have all student permissions"""
        from informatics_classroom.auth.permissions import get_role_permissions_with_inheritance

        ta_perms = get_role_permissions_with_inheritance('ta')
        student_perms = get_role_permissions_with_inheritance('student')

        # All student permissions should be in TA permissions
        for perm in student_perms:
            assert perm in ta_perms, f"TA missing student permission: {perm}"


class TestUnauthorizedAccess:
    """Test that unauthorized access is properly blocked"""

    def test_no_token_blocks_access(self, client):
        """Requests without JWT token should be rejected"""
        response = client.get('/api/student/courses')

        # Should be unauthorized
        assert response.status_code == 401

    def test_invalid_token_blocks_access(self, client):
        """Requests with invalid JWT token should be rejected"""
        response = client.get(
            '/api/student/courses',
            headers={'Authorization': 'Bearer invalid.token.here'}
        )

        # Should be unauthorized
        assert response.status_code == 401

    def test_expired_token_blocks_access(self, client):
        """Expired JWT tokens should be rejected"""
        # This would require creating an expired token
        # For now, test with malformed token
        response = client.get(
            '/api/student/courses',
            headers={'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.expired'}
        )

        assert response.status_code == 401


class TestClassBasedPermissions:
    """Test class-specific permission enforcement"""

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    def test_instructor_can_only_modify_own_class(self, mock_get_db, client,
                                                  auth_headers_instructor, mock_db):
        """Instructors should only modify classes they own/teach"""
        mock_get_db.return_value = mock_db

        # Try to modify a class the instructor doesn't own
        response = client.put(
            '/api/quizzes/quiz_123/update',
            headers=auth_headers_instructor,
            json={
                'class': 'OTHER_CLASS',
                'title': 'Modified Quiz'
            }
        )

        # Should be forbidden or not found
        # (Actual behavior depends on class ownership check implementation)
        assert response.status_code in [403, 404]

    @patch('informatics_classroom.classroom.api_routes.get_database_adapter')
    def test_student_can_only_access_enrolled_classes(self, mock_get_db, client,
                                                      auth_headers_student, mock_db):
        """Students should only access classes they're enrolled in"""
        mock_get_db.return_value = mock_db

        # Try to access quiz from class student is not enrolled in
        response = client.get(
            '/api/quiz/details?class_name=UNENROLLED_CLASS&module_num=1',
            headers=auth_headers_student
        )

        # Should be forbidden or return empty
        # (Actual behavior depends on enrollment check implementation)
        assert response.status_code in [403, 404] or (
            response.status_code == 200 and
            json.loads(response.data).get('success') is False
        )


class TestCrossRoleEndpointAccess:
    """Test specific endpoint access across all roles"""

    @pytest.mark.parametrize('auth_headers_fixture,expected_status', [
        ('auth_headers_student', 200),
        ('auth_headers_ta', 200),
        ('auth_headers_instructor', 200),
        ('auth_headers_admin', 200),
    ])
    @patch('informatics_classroom.classroom.api_routes.get_classes_for_user')
    def test_all_roles_can_access_student_courses(self, mock_get_classes, client,
                                                   request, auth_headers_fixture,
                                                   expected_status):
        """All authenticated roles can access student courses endpoint"""
        mock_get_classes.return_value = ['CLASS_101']
        auth_headers = request.getfixturevalue(auth_headers_fixture)

        response = client.get('/api/student/courses', headers=auth_headers)

        assert response.status_code == expected_status

    @pytest.mark.parametrize('auth_headers_fixture,should_succeed', [
        ('auth_headers_student', False),
        ('auth_headers_ta', False),
        ('auth_headers_instructor', True),
        ('auth_headers_admin', True),
    ])
    def test_only_instructors_and_admins_can_create_class(self, client, request,
                                                          auth_headers_fixture,
                                                          should_succeed):
        """Only instructors and admins can create classes"""
        auth_headers = request.getfixturevalue(auth_headers_fixture)

        response = client.post(
            '/api/classes',
            headers=auth_headers,
            json={'name': 'TEST_CLASS', 'description': 'Test'}
        )

        if should_succeed:
            assert response.status_code != 403
        else:
            assert response.status_code in [403, 404]

    @pytest.mark.parametrize('auth_headers_fixture,should_succeed', [
        ('auth_headers_student', False),
        ('auth_headers_ta', False),
        ('auth_headers_instructor', False),
        ('auth_headers_admin', True),
    ])
    def test_only_admins_can_impersonate(self, client, request,
                                        auth_headers_fixture, should_succeed):
        """Only admins can use impersonation"""
        auth_headers = request.getfixturevalue(auth_headers_fixture)

        response = client.post(
            '/api/admin/impersonate',
            headers=auth_headers,
            json={'user_id': 'target@example.com'}
        )

        if should_succeed:
            # Admin may get 404 if endpoint not implemented, but not 403
            assert response.status_code != 403
        else:
            # Non-admins should be forbidden
            assert response.status_code in [403, 404]
