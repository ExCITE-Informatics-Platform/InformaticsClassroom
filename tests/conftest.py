"""
Test configuration and fixtures for Informatics Classroom.

Provides common fixtures for testing workflows without SSO integration.
"""

import pytest
import uuid
import jwt
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from informatics_classroom import create_app
from informatics_classroom.database.interface import DatabaseAdapter
from informatics_classroom.config import Config


@pytest.fixture
def app():
    """Create and configure test Flask application."""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })

    yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class StatefulMockDatabase:
    """
    Stateful mock database that tracks changes across workflow steps.

    Simulates database operations with in-memory storage that persists
    throughout a test execution. Useful for workflow tests that need
    to verify state changes across multiple API calls.
    """

    def __init__(self):
        self._data = {
            'users': {},
            'quiz': {},
            'answer': {},
            'resources': {},
            'tokens': {},
            'classes': {}
        }

    def get(self, table, item_id):
        """Get single item by ID."""
        return self._data.get(table, {}).get(item_id)

    def query(self, table, filters=None):
        """Query items with optional filters."""
        items = list(self._data.get(table, {}).values())
        if not filters:
            return items

        # Apply filters
        filtered = []
        for item in items:
            match = True
            for key, value in filters.items():
                if item.get(key) != value:
                    match = False
                    break
            if match:
                filtered.append(item)
        return filtered

    def upsert(self, table, item):
        """Insert or update item."""
        if 'id' not in item:
            item['id'] = str(uuid.uuid4())
        self._data.setdefault(table, {})[item['id']] = item.copy()
        return item

    def delete(self, table, item_id):
        """Delete item by ID."""
        if item_id in self._data.get(table, {}):
            del self._data[table][item_id]
            return True
        return False

    def query_raw(self, table, query, params):
        """Raw query - simplified implementation."""
        return []

    def insert(self, table, item):
        """Alias for upsert."""
        return self.upsert(table, item)

    def update(self, table, item_id, updates):
        """Update existing item."""
        if item_id in self._data.get(table, {}):
            self._data[table][item_id].update(updates)
            return self._data[table][item_id]
        return None

    def clear(self):
        """Clear all data (for test cleanup)."""
        for table in self._data:
            self._data[table].clear()

    def seed(self, table, items):
        """Seed table with initial data."""
        for item in items:
            self.upsert(table, item)


@pytest.fixture
def mock_db():
    """Mock database adapter for testing."""
    db = Mock(spec=DatabaseAdapter)

    # Storage for test data
    db._data = {
        'users': {},
        'quiz': {},
        'answer': {},
        'resources': {},
        'tokens': {}
    }

    def mock_get(table, item_id):
        return db._data.get(table, {}).get(item_id)

    def mock_query(table, filters=None):
        items = list(db._data.get(table, {}).values())
        if not filters:
            return items

        # Apply filters
        filtered = []
        for item in items:
            match = True
            for key, value in filters.items():
                if item.get(key) != value:
                    match = False
                    break
            if match:
                filtered.append(item)
        return filtered

    def mock_upsert(table, item):
        if 'id' not in item:
            item['id'] = str(uuid.uuid4())
        db._data.setdefault(table, {})[item['id']] = item
        return item

    def mock_delete(table, item_id):
        if item_id in db._data.get(table, {}):
            del db._data[table][item_id]
            return True
        return False

    def mock_query_raw(table, query, params):
        # Simplified raw query mock - returns empty list
        return []

    db.get.side_effect = mock_get
    db.query.side_effect = mock_query
    db.upsert.side_effect = mock_upsert
    db.delete.side_effect = mock_delete
    db.query_raw.side_effect = mock_query_raw

    return db


@pytest.fixture
def stateful_db():
    """Stateful mock database for workflow testing."""
    return StatefulMockDatabase()


@pytest.fixture
def mock_jwt_user_student():
    """Mock JWT user data for student."""
    return {
        'user_id': 'student123',
        'email': 'student@university.edu',
        'display_name': 'Test Student',
        'roles': ['student'],
        'class_memberships': [
            {
                'class_id': 'INFORMATICS_101',
                'role': 'student',
                'assigned_at': datetime.now(timezone.utc).isoformat()
            }
        ]
    }


@pytest.fixture
def mock_jwt_user_instructor():
    """Mock JWT user data for instructor."""
    return {
        'user_id': 'instructor456',
        'email': 'instructor@university.edu',
        'display_name': 'Test Instructor',
        'roles': ['instructor'],
        'class_memberships': [
            {
                'class_id': 'INFORMATICS_101',
                'role': 'instructor',
                'assigned_at': datetime.now(timezone.utc).isoformat()
            }
        ]
    }


@pytest.fixture
def mock_jwt_user_ta():
    """Mock JWT user data for TA."""
    return {
        'user_id': 'ta789',
        'email': 'ta@university.edu',
        'display_name': 'Test TA',
        'roles': ['ta'],
        'class_memberships': [
            {
                'class_id': 'INFORMATICS_101',
                'role': 'ta',
                'assigned_at': datetime.now(timezone.utc).isoformat()
            }
        ]
    }


@pytest.fixture
def mock_jwt_user_admin():
    """Mock JWT user data for admin."""
    return {
        'user_id': 'admin001',
        'email': 'admin@university.edu',
        'display_name': 'Test Admin',
        'roles': ['admin']
    }


def generate_test_token(user_data):
    """
    Helper function to generate a valid JWT token for testing.

    Args:
        user_data (dict): User data to encode in token

    Returns:
        str: Valid JWT access token
    """
    payload = {
        'user_id': user_data.get('user_id'),
        'email': user_data.get('email'),
        'display_name': user_data.get('display_name'),
        'roles': user_data.get('roles', []),
        'class_memberships': user_data.get('class_memberships', []),
        'exp': datetime.now(timezone.utc) + timedelta(hours=1),
        'iat': datetime.now(timezone.utc),
        'type': 'access'
    }

    token = jwt.encode(
        payload,
        Config.JWT_SECRET_KEY,
        algorithm=Config.JWT_ALGORITHM
    )

    return token


@pytest.fixture
def auth_headers_student(mock_jwt_user_student):
    """Generate authentication headers for student."""
    token = generate_test_token(mock_jwt_user_student)
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def auth_headers_instructor(mock_jwt_user_instructor):
    """Generate authentication headers for instructor."""
    token = generate_test_token(mock_jwt_user_instructor)
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def auth_headers_ta(mock_jwt_user_ta):
    """Generate authentication headers for TA."""
    token = generate_test_token(mock_jwt_user_ta)
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def auth_headers_admin(mock_jwt_user_admin):
    """Generate authentication headers for admin."""
    token = generate_test_token(mock_jwt_user_admin)
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def sample_quiz():
    """Sample quiz data for testing."""
    return {
        'id': 'INFORMATICS_101_1',
        'class': 'INFORMATICS_101',
        'module': 1,
        'title': 'Introduction to Python',
        'module_name': 'Module 1: Python Basics',
        'description': 'Basic Python programming concepts',
        'owner': 'instructor456',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'updated_at': datetime.now(timezone.utc).isoformat(),
        'questions': [
            {
                'question_num': 1,
                'question_text': 'What is the output of print(2 + 2)?',
                'answers': ['3', '4', '22', 'Error'],
                'correct_answer': '4',
                'open': False
            },
            {
                'question_num': 2,
                'question_text': 'Which keyword is used to define a function?',
                'answers': ['func', 'def', 'function', 'define'],
                'correct_answer': 'def',
                'open': False
            },
            {
                'question_num': 3,
                'question_text': 'Explain list comprehension',
                'answers': [],
                'correct_answer': '',
                'open': True
            }
        ]
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        'id': 'student123',
        'email': 'student@university.edu',
        'display_name': 'Test Student',
        'team': 'student123',
        'role': 'student',
        'class_memberships': [
            {
                'class_id': 'INFORMATICS_101',
                'role': 'class_student',
                'assigned_at': datetime.now(timezone.utc).isoformat()
            }
        ]
    }


@pytest.fixture
def sample_answers():
    """Sample answer data for testing."""
    return [
        {
            'id': str(uuid.uuid4()),
            'PartitionKey': 'INFORMATICS_101_1',
            'course': 'INFORMATICS_101',
            'module': 1,
            'team': 'student123',
            'question': '1',
            'answer': '4',
            'correct': True,
            'open': False,
            'datetime': datetime.now(timezone.utc).isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'PartitionKey': 'INFORMATICS_101_1',
            'course': 'INFORMATICS_101',
            'module': 1,
            'team': 'student123',
            'question': '2',
            'answer': 'func',
            'correct': False,
            'open': False,
            'datetime': (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'PartitionKey': 'INFORMATICS_101_1',
            'course': 'INFORMATICS_101',
            'module': 1,
            'team': 'student123',
            'question': '2',
            'answer': 'def',
            'correct': True,
            'open': False,
            'datetime': datetime.now(timezone.utc).isoformat()
        }
    ]


@pytest.fixture
def sample_class_data():
    """Sample class data for testing."""
    return {
        'id': 'INFORMATICS_101',
        'name': 'INFORMATICS_101',
        'owner': 'instructor456',
        'created_at': datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def sample_resource():
    """Sample resource data for testing."""
    return {
        'id': str(uuid.uuid4()),
        'title': 'Python Documentation',
        'description': 'Official Python 3 documentation',
        'category': 'reference',
        'resource_type': 'document',
        'url': 'https://docs.python.org/3/',
        'class': 'INFORMATICS_101',
        'icon': 'book',
        'created_at': datetime.now(timezone.utc).isoformat()
    }


def create_mock_request_context(client, user_data):
    """Helper to create request context with mock JWT user."""
    ctx = client.application.test_request_context()
    ctx.push()

    # Mock request.jwt_user
    from flask import request
    request.jwt_user = user_data

    return ctx
