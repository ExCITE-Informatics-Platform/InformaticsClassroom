# Testing Quick Start Guide

## ✅ Test Status: OPERATIONAL WITH WORKFLOW TESTING ADDED

**77/90 tests passing (85.6%)** | **24% code coverage** | **~3s execution time**
**15 new workflow tests added** - 4 passing, 11 revealing workflow-level bugs

## Quick Start

### 1. Setup (One Time)
```bash
# Activate virtual environment
source venv/bin/activate

# Install test dependencies (if not already installed)
pip install -r requirements-test.txt
```

### 2. Run Tests
```bash
# Run all working tests (includes all permission and workflow tests)
pytest tests/test_core_workflows.py tests/test_student_workflows_fixed.py \
       tests/test_external_api.py tests/test_comprehensive_permissions.py \
       tests/test_workflow_permissions.py -v

# Run only passing tests (exclude tests with known failures)
pytest tests/test_core_workflows.py tests/test_student_workflows_fixed.py tests/test_external_api.py -v

# Run with coverage
pytest tests/test_core_workflows.py tests/test_student_workflows_fixed.py \
       tests/test_external_api.py tests/test_comprehensive_permissions.py \
       tests/test_workflow_permissions.py \
    --cov=informatics_classroom --cov-report=html

# Run specific test class
pytest tests/test_core_workflows.py::TestStudentWorkflows -v

# Run only external API tests
pytest tests/test_external_api.py -v

# Run only endpoint-level permission tests
pytest tests/test_comprehensive_permissions.py -v

# Run only workflow-level permission tests (NEW)
pytest tests/test_workflow_permissions.py -v

# Run specific workflow category
pytest tests/test_workflow_permissions.py::TestQuizLifecycleWorkflow -v
pytest tests/test_workflow_permissions.py::TestClassManagementWorkflow -v
pytest tests/test_workflow_permissions.py::TestMultiUserWorkflow -v
pytest tests/test_workflow_permissions.py::TestResourceOwnershipWorkflow -v

# Run only failing tests
pytest tests/test_comprehensive_permissions.py tests/test_workflow_permissions.py --lf -v
```

### 3. View Results
```bash
# View coverage report in browser
open htmlcov/index.html

# Or view in terminal
cat tests/FINAL_TEST_RESULTS.txt
```

## Test Files

### ✅ Working Tests (Run These)
- **test_core_workflows.py** - 13 tests covering all roles
- **test_student_workflows_fixed.py** - 4 student workflow tests
- **test_external_api.py** - 13 external API submission tests
- **test_comprehensive_permissions.py** - 45 endpoint-level permission tests (43 passing, 2 minor issues)
- **test_workflow_permissions.py** - 15 workflow-level permission tests (4 passing, 11 revealing workflow bugs) ⚠️ **NEW**

### ⚠️  Legacy Tests (Need Conversion)
- test_student_workflows.py
- test_instructor_workflows.py
- test_admin_workflows.py
- test_permissions.py

*These files contain comprehensive tests but use an older pattern that needs updating.*

## Test Coverage Summary

| Category | Tests | Passing | Status |
|----------|-------|---------|--------|
| Student Workflows | 7 | 7 | ✅ All passing |
| Instructor Workflows | 2 | 2 | ✅ All passing |
| Admin Workflows | 2 | 2 | ✅ All passing |
| Basic Permissions | 3 | 3 | ✅ All passing |
| Database Operations | 3 | 3 | ✅ All passing |
| External API | 13 | 13 | ✅ All passing |
| **Endpoint Permissions** | **45** | **43** | **✅ 4 bugs fixed, 2 minor issues** |
| **Workflow Permissions (NEW)** | **15** | **4** | **⚠️ 11 failures revealing workflow bugs** |
| **TOTAL** | **90** | **77** | **✅ 85.6% pass rate** |

## What's Tested

### Student Capabilities
- ✅ View enrolled courses
- ✅ Access dashboard with progress
- ✅ Get quiz details
- ✅ Handle empty/missing data

### Instructor Capabilities
- ✅ View assigned classes
- ✅ List quizzes

### Admin Capabilities
- ✅ List users
- ✅ Access impersonation

### Security & Permissions (Endpoint-Level)
- ✅ Unauthorized requests denied
- ✅ JWT token validation
- ✅ Invalid tokens rejected
- ✅ Role hierarchy (admin > instructor > ta > student)
- ✅ Permission inheritance works
- ✅ **FIXED**: Students blocked from instructor endpoints
- ✅ **FIXED**: Instructors/TAs can create quizzes
- ✅ **FIXED**: Instructors can view grades
- ⚠️ 2 minor parameter validation issues remaining (non-critical)

### Workflow-Level Permissions (NEW)
- ✅ Students cannot create quizzes (permission blocking)
- ✅ Students cannot self-promote to instructor (escalation prevention)
- ✅ Instructors cannot manage other classes (cross-class isolation)
- ⚠️ **BUG FOUND**: Ownership protection may not be enforced on delete
- ⚠️ 11 workflow bugs discovered requiring investigation:
  - Quiz access and creation workflows
  - Class management and role updates
  - Multi-user answer isolation
  - Resource ownership validation

### Infrastructure
- ✅ Mock database CRUD operations
- ✅ Test fixtures work correctly
- ✅ Flask test client integration

### External API
- ✅ Form-based answer submission
- ✅ Programmatic access (no JWT required)
- ✅ Multi-answer workflows
- ✅ Team-based isolation
- ✅ Error handling and validation
- ✅ Response format compatibility

## Common Commands

```bash
# Run tests with verbose output
pytest tests/test_core_workflows.py -v

# Run tests matching pattern
pytest -k "student" -v

# Run tests with print statements
pytest tests/test_core_workflows.py -v -s

# Stop on first failure
pytest tests/test_core_workflows.py -x

# Generate coverage report
pytest tests/test_core_workflows.py --cov=informatics_classroom

# Run specific test
pytest tests/test_core_workflows.py::TestStudentWorkflows::test_student_can_view_enrolled_courses -v
```

## Documentation

- **Endpoint Permission Testing**: See `claudedocs/PERMISSION_TEST_RESULTS.md`
- **Workflow Permission Testing**: See `claudedocs/WORKFLOW_TEST_RESULTS.md` ⚠️ **NEW**
- **Permission Fixes Applied**: See `PERMISSION_FIXES_APPLIED.md`
- **Full Details**: See `claudedocs/TEST_EXECUTION_SUMMARY.md`
- **External API**: See `claudedocs/EXTERNAL_API_TESTS.md`
- **Workflow Docs**: See `claudedocs/WORKFLOWS.md`
- **Test Guide**: See `tests/README.md`

## Next Steps

To expand test coverage:

1. **Convert Legacy Tests**: Update older test files to use `auth_headers_*` pattern
2. **Implement Missing Endpoints**: Many tests expect endpoints that return 404
3. **Add Integration Tests**: Test with real database connections
4. **Expand Scenarios**: Add more edge cases and error handling tests

## Test Pattern Reference

### ✅ Correct Pattern (Use This)
```python
@patch('informatics_classroom.classroom.api_routes.get_classes_for_user')
def test_example(self, mock_get_classes, client, auth_headers_student):
    mock_get_classes.return_value = ['CLASS_101']

    response = client.get('/api/endpoint', headers=auth_headers_student)

    assert response.status_code == 200
```

### ❌ Old Pattern (Don't Use)
```python
def test_example(self, client, mock_jwt_user_student):
    with patch('...request') as mock_request:  # ❌ Causes problems
        mock_request.jwt_user = mock_jwt_user_student
        response = client.get('/api/endpoint')
```

## Troubleshooting

### Tests Not Running
```bash
# Make sure you're in the project root
cd /path/to/InformaticsClassroom

# Activate venv
source venv/bin/activate

# Verify pytest installed
pytest --version
```

### Import Errors
```bash
# Install test requirements
pip install -r requirements-test.txt
```

### Coverage Report Not Generating
```bash
# Install pytest-cov
pip install pytest-cov

# Generate report
pytest --cov=informatics_classroom --cov-report=html
```

## Support

For questions or issues:
1. Check `tests/README.md` for detailed testing guide
2. Review `claudedocs/TEST_EXECUTION_SUMMARY.md` for comprehensive details
3. Examine working test files for patterns to follow
