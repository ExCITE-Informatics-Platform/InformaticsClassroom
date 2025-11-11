# Informatics Classroom Test Suite

Comprehensive unit tests for the Informatics Classroom application covering student, instructor, and admin workflows.

## Test Coverage

### Student Workflows (`test_student_workflows.py`)
- **Course Access**: Retrieving enrolled courses, handling empty enrollment
- **Dashboard**: Progress summaries, course statistics
- **Quiz Taking**: Retrieving quiz details, submitting answers (correct/incorrect), open-ended questions
- **Progress Tracking**: Module-level progress, completion metrics
- **Resource Access**: Class-specific resource viewing
- **Attempt Tracking**: Multiple quiz attempts, retry logic

### Instructor Workflows (`test_instructor_workflows.py`)
- **Class Management**: Creating classes, deleting classes, viewing managed classes
- **Quiz Creation**: Creating quizzes with questions, validating required fields
- **Quiz Editing**: Retrieving for edit, updating quizzes, change tracking
- **Quiz Deletion**: Removing quizzes with proper permissions
- **Quiz Listing**: Viewing all managed quizzes, filtering by class
- **Grade Viewing**: Grade matrix, assignment analysis
- **Member Management**: Adding/removing students, updating roles, permission validation
- **Token Generation**: Creating access tokens for classes/modules

### Admin Workflows (`test_admin_workflows.py`)
- **User Management**: Listing users with pagination, filtering by role, updating user details, changing roles
- **Permission Management**: Checking permissions, viewing user permission details
- **User Impersonation**: Starting impersonation, exiting impersonation, impersonation context
- **Audit Logging**: Viewing logs with pagination, filtering by action/user/date
- **System Operations**: Viewing all classes, deleting any class, managing any class members
- **Permission Checks**: Admin bypass, unauthorized blocking, class-level validation
- **Data Integrity**: Preserving answer data on deletion, maintaining class memberships on updates

### Permission System (`test_permissions.py`)
- **Role Hierarchy**: Admin, instructor, TA, student permission levels
- **Class Roles**: Class-specific role permissions (instructor, TA, student, viewer)
- **Permission Validation**: Role validation, class access checks
- **Permission Decorators**: Access control, role requirements
- **Quiz Permissions**: Owner permissions, TA permissions, student restrictions
- **Membership Permissions**: Role assignment, member management
- **Edge Cases**: No roles, multiple roles, invalid classes/users, admin bypass

## Test Structure

```
tests/
├── conftest.py                      # Fixtures and test configuration
├── test_student_workflows.py        # Student workflow tests
├── test_instructor_workflows.py     # Instructor workflow tests
├── test_admin_workflows.py          # Admin workflow tests
├── test_permissions.py              # Permission system tests
└── README.md                        # This file
```

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install pytest pytest-cov pytest-mock
```

### Run All Tests

```bash
# From project root
pytest tests/

# With coverage report
pytest tests/ --cov=informatics_classroom --cov-report=html

# Verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_student_workflows.py

# Run specific test class
pytest tests/test_student_workflows.py::TestQuizTaking

# Run specific test
pytest tests/test_student_workflows.py::TestQuizTaking::test_submit_answer_correct
```

### Test Markers

Tests can be run selectively using markers:

```bash
# Run only workflow tests (if marked)
pytest tests/ -m workflow

# Run only permission tests
pytest tests/ -m permission

# Skip slow tests
pytest tests/ -m "not slow"
```

## Fixtures

### User Fixtures
- `mock_jwt_user_student` - Student user with class membership
- `mock_jwt_user_instructor` - Instructor user with class management rights
- `mock_jwt_user_ta` - Teaching assistant user
- `mock_jwt_user_admin` - Admin user with system-wide access

### Data Fixtures
- `mock_db` - Mock database adapter with in-memory storage
- `sample_quiz` - Sample quiz with multiple question types
- `sample_user_data` - Sample user profile data
- `sample_answers` - Sample answer submissions
- `sample_class_data` - Sample class metadata
- `sample_resource` - Sample learning resource

### Application Fixtures
- `app` - Configured test Flask application
- `client` - Test client for making requests

## Test Patterns

### Making API Requests

```python
def test_example(client, mock_jwt_user_student):
    """Test example API endpoint."""
    with patch('module.request') as mock_request:
        mock_request.jwt_user = mock_jwt_user_student
        mock_request.get_json.return_value = {'key': 'value'}

        response = client.post('/api/endpoint', json={'key': 'value'})

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
```

### Using Mock Database

```python
def test_with_database(mock_db, sample_quiz):
    """Test with mock database."""
    # Add data to mock database
    mock_db._data['quiz'][sample_quiz['id']] = sample_quiz

    # Query will return the data
    quizzes = mock_db.query('quiz', filters={'class': 'INFORMATICS_101'})

    assert len(quizzes) == 1
```

### Testing Permissions

```python
@patch('module.user_has_class_permission')
def test_permission_check(mock_has_permission, client, mock_jwt_user_instructor):
    """Test permission validation."""
    mock_has_permission.return_value = True

    with patch('module.request') as mock_request:
        mock_request.jwt_user = mock_jwt_user_instructor

        response = client.get('/api/protected/endpoint')

    assert response.status_code == 200
    mock_has_permission.assert_called_once()
```

## Coverage Goals

- **Line Coverage**: > 80%
- **Branch Coverage**: > 75%
- **Critical Paths**: 100% (authentication, permissions, data persistence)

## Excluded from Testing

Per requirements, the following are **not** tested:
- SSO/OAuth authentication flows
- Microsoft Entra ID (Azure AD) integration
- MSAL authentication library interactions
- External OAuth callbacks

All authentication is mocked using JWT user fixtures to simulate authenticated users.

## Continuous Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-mock
    - name: Run tests
      run: pytest tests/ --cov=informatics_classroom --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Writing New Tests

When adding new tests:

1. **Follow naming conventions**: `test_<functionality>_<scenario>`
2. **Use descriptive docstrings**: Explain what is being tested and why
3. **Isolate tests**: Each test should be independent and not rely on others
4. **Mock external dependencies**: Use fixtures and patches for database, API calls
5. **Test edge cases**: Include error conditions, invalid inputs, boundary conditions
6. **Test permissions**: Ensure proper access control is validated
7. **Verify data integrity**: Check that operations preserve or correctly modify data

Example template:

```python
class TestNewFeature:
    """Test new feature workflow."""

    def test_feature_success_case(self, client, mock_jwt_user, mock_db):
        """Test feature works with valid inputs."""
        # Setup
        # Execute
        # Assert
        pass

    def test_feature_failure_case(self, client, mock_jwt_user):
        """Test feature handles invalid inputs."""
        # Setup
        # Execute
        # Assert error handling
        pass

    def test_feature_permissions(self, client, mock_jwt_user_student):
        """Test feature enforces proper permissions."""
        # Setup
        # Execute
        # Assert permission denied
        pass
```

## Troubleshooting

### Import Errors
If you encounter import errors, ensure the project root is in Python path:
```python
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
```

### Fixture Not Found
Make sure `conftest.py` is in the tests directory and pytest can discover it.

### Mock Not Working
Verify the patch path matches the actual import path in the module being tested.

### Database Tests Failing
Check that mock_db is properly reset between tests. The fixture should create a fresh instance for each test.

## Best Practices

1. **Keep tests fast**: Use mocks instead of real database/network calls
2. **Test behavior, not implementation**: Focus on what the code does, not how
3. **One assertion focus per test**: Each test should verify one specific behavior
4. **Use fixtures liberally**: Reduce duplication and improve readability
5. **Clear test names**: Name should describe what is being tested
6. **Clean up after tests**: Ensure no side effects between tests
7. **Test happy path and error paths**: Cover both success and failure scenarios
8. **Document complex tests**: Add comments for non-obvious test logic

## Test Metrics

Generate test metrics:

```bash
# Coverage report
pytest tests/ --cov=informatics_classroom --cov-report=term-missing

# HTML coverage report
pytest tests/ --cov=informatics_classroom --cov-report=html
open htmlcov/index.html

# JUnit XML for CI
pytest tests/ --junitxml=test-results.xml

# Test duration report
pytest tests/ --durations=10
```

## Contact

For questions about tests or to report issues, please consult the workflow documentation in `claudedocs/WORKFLOWS.md`.
