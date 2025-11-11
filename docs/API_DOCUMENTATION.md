# API Documentation

Complete REST API reference for the Informatics Classroom platform.

## Base URL

- **Development**: `http://localhost:5001/api`
- **Production**: `https://<your-domain>/api`

## Authentication

All API endpoints (except `/auth/login`) require authentication. The API uses session-based authentication with optional JWT token support.

### Authentication Flow

1. **Login**: POST to `/api/auth/login` to obtain session
2. **Session**: Session cookie is automatically managed
3. **Token** (optional): JWT tokens can be obtained for API-only access

## Common Response Format

```json
{
  "status": "success" | "error",
  "data": { /* response payload */ },
  "message": "Human-readable message",
  "error": "Error details (when status is error)"
}
```

## HTTP Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Authentication Endpoints

### Login

Initiate Azure AD authentication flow.

```http
POST /api/auth/login
```

**Request Body:**
```json
{
  "redirect_uri": "http://localhost:5173/callback"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "auth_url": "https://login.microsoftonline.com/..."
  }
}
```

---

### Callback

Handle OAuth callback and create session.

```http
POST /api/auth/callback
```

**Request Body:**
```json
{
  "code": "authorization_code_from_azure"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "access_token": "jwt_token",
    "expires_in": 3600,
    "user": {
      "id": "user_id",
      "email": "user@example.com",
      "displayName": "User Name",
      "roles": ["student", "instructor"]
    }
  }
}
```

---

### Refresh Token

Refresh authentication token.

```http
POST /api/auth/refresh
```

**Request Body:**
```json
{
  "refresh_token": "refresh_token_string"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "access_token": "new_jwt_token",
    "token_type": "Bearer",
    "expires_in": 3600
  }
}
```

---

### Get Session

Get current session information.

```http
GET /api/auth/session
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "isAuthenticated": true,
    "user": {
      "id": "user_id",
      "email": "user@example.com",
      "displayName": "User Name",
      "roles": ["student"]
    }
  }
}
```

---

### Logout

End current session.

```http
POST /api/auth/logout
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "logout_url": "https://login.microsoftonline.com/..."
  }
}
```

---

### Validate Token

Validate JWT token.

```http
POST /api/auth/validate
```

**Request Body:**
```json
{
  "token": "jwt_token_string"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "valid": true,
    "payload": {
      "user_id": "user_id",
      "email": "user@example.com"
    }
  }
}
```

---

## Student Endpoints

### Get Student Courses

Get all courses for the current student.

```http
GET /api/student/courses
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "courses": [
      {
        "id": "course_id",
        "name": "Course Name",
        "modules": [
          {
            "module": "1",
            "module_name": "Module Name",
            "title": "Module Title"
          }
        ]
      }
    ]
  }
}
```

---

### Get Student Progress

Get progress for a specific class.

```http
GET /api/student/progress/:class
```

**Parameters:**
- `class` (path) - Class identifier

**Response:**
```json
{
  "status": "success",
  "data": {
    "class": "class_name",
    "overall_progress": 75.5,
    "overall_correctness": 85.2,
    "quizzes": [
      {
        "quiz_id": "quiz_id",
        "module": "1",
        "title": "Quiz Title",
        "questions_attempted": 8,
        "questions_correct": 7,
        "total_questions": 10,
        "percentage": 70.0,
        "attempts": 2
      }
    ]
  }
}
```

---

### Get Student Dashboard

Get comprehensive dashboard data for student.

```http
GET /api/student/dashboard/:class
```

**Parameters:**
- `class` (path) - Class identifier

**Response:**
```json
{
  "status": "success",
  "data": {
    "class": "class_name",
    "progress": {
      "overall_progress": 75.0,
      "completed_modules": 3,
      "total_modules": 4
    },
    "course_summaries": [
      {
        "course": "Course 1",
        "modules": [
          {
            "module": "1",
            "answered": 8,
            "total": 10
          }
        ]
      }
    ],
    "grades": {
      "table_correctness": [
        {
          "module": "1",
          "correct": 7,
          "total": 10,
          "percent_correct": 70.0
        }
      ],
      "table_attempts": [
        {
          "module": "1",
          "avg_attempts": 1.5
        }
      ]
    }
  }
}
```

---

### Get Quiz Details

Get details for a specific quiz.

```http
GET /api/student/quiz/:class/:module
```

**Parameters:**
- `class` (path) - Class identifier
- `module` (path) - Module number

**Response:**
```json
{
  "status": "success",
  "data": {
    "quiz_id": "quiz_id",
    "class": "class_name",
    "module": "1",
    "title": "Quiz Title",
    "description": "Quiz description",
    "questions": [
      {
        "question_num": 1,
        "question_text": "Question text",
        "answer": "Correct answer",
        "user_answer": "User's answer",
        "is_correct": true,
        "attempt_count": 2,
        "feedback": "Feedback text"
      }
    ]
  }
}
```

---

### Submit Answer

Submit answer to a quiz question.

```http
POST /api/student/submit-answer
```

**Request Body:**
```json
{
  "class": "class_name",
  "module": "1",
  "question_num": 1,
  "answer": "Student's answer"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "correct": true,
    "correct_answer": "The correct answer",
    "feedback": "Great job!",
    "attempt_count": 1
  }
}
```

---

## Instructor Endpoints

### Get Instructor Classes

Get all classes for the current instructor.

```http
GET /api/instructor/classes
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "classes": [
      {
        "id": "class_id",
        "name": "Class Name",
        "description": "Class description",
        "owner": "instructor_email",
        "created_at": "2025-11-01T12:00:00Z",
        "student_count": 25,
        "quiz_count": 10,
        "can_delete": true
      }
    ]
  }
}
```

---

### Create Class

Create a new class.

```http
POST /api/instructor/class
```

**Request Body:**
```json
{
  "name": "New Class Name",
  "description": "Class description"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "class": {
      "id": "new_class_id",
      "name": "New Class Name",
      "description": "Class description",
      "owner": "instructor_email",
      "created_at": "2025-11-08T12:00:00Z"
    }
  },
  "message": "Class created successfully"
}
```

---

### Delete Class

Delete a class.

```http
DELETE /api/instructor/class/:class_id
```

**Parameters:**
- `class_id` (path) - Class identifier

**Response:**
```json
{
  "status": "success",
  "message": "Class deleted successfully"
}
```

---

### Create Quiz

Create a new quiz for a class and module.

```http
POST /api/instructor/quiz
```

**Request Body:**
```json
{
  "class": "class_name",
  "module": "1",
  "title": "Quiz Title",
  "description": "Quiz description",
  "questions": [
    {
      "question_num": 1,
      "question": "Question text",
      "answer": "Correct answer"
    },
    {
      "question_num": 2,
      "question": "Another question",
      "answer": "Another answer"
    }
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "quiz_id": "new_quiz_id"
  },
  "message": "Quiz created successfully"
}
```

---

### Get Quiz for Edit

Get quiz details for editing.

```http
GET /api/instructor/quiz/:quiz_id
```

**Parameters:**
- `quiz_id` (path) - Quiz identifier

**Response:**
```json
{
  "status": "success",
  "data": {
    "quiz": {
      "id": "quiz_id",
      "class": "class_name",
      "module": "1",
      "title": "Quiz Title",
      "description": "Quiz description",
      "questions": [
        {
          "question_num": 1,
          "question": "Question text",
          "answer": "Correct answer"
        }
      ]
    }
  }
}
```

---

### Update Quiz

Update an existing quiz.

```http
PUT /api/instructor/quiz/:quiz_id
```

**Parameters:**
- `quiz_id` (path) - Quiz identifier

**Request Body:**
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "questions": [
    {
      "question_num": 1,
      "question": "Updated question",
      "answer": "Updated answer"
    }
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Quiz updated successfully"
}
```

---

### Delete Quiz

Delete a quiz.

```http
DELETE /api/instructor/quiz/:quiz_id
```

**Parameters:**
- `quiz_id` (path) - Quiz identifier

**Response:**
```json
{
  "status": "success",
  "message": "Quiz deleted successfully"
}
```

---

### Get Class Grades

Get grades for all students in a class.

```http
GET /api/instructor/grades/:class_id
```

**Parameters:**
- `class_id` (path) - Class identifier

**Response:**
```json
{
  "status": "success",
  "data": {
    "class": "class_name",
    "students": [
      {
        "user_id": "student_email",
        "name": "Student Name",
        "progress": {
          "completion_percentage": 75.0,
          "overall_correctness": 85.0
        },
        "module_summary": [
          {
            "module": "1",
            "answered_questions": 8,
            "total_questions": 10,
            "correct_questions": 7,
            "percentage": 70.0
          }
        ]
      }
    ]
  }
}
```

---

### Get Class Modules

Get module structure for a class.

```http
GET /api/instructor/modules/:class_id
```

**Parameters:**
- `class_id` (path) - Class identifier

**Response:**
```json
{
  "status": "success",
  "data": {
    "class_modules": [
      {
        "module": "1",
        "module_name": "Module Name",
        "is_open": true,
        "quiz": {
          "quiz_id": "quiz_id",
          "title": "Quiz Title",
          "question_count": 10
        }
      }
    ]
  }
}
```

---

### Generate Token

Generate access token for resources.

```http
POST /api/instructor/token
```

**Request Body:**
```json
{
  "class": "class_name",
  "module": "1",
  "expiry": "2025-12-31T23:59:59Z"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "token": "generated_token_string"
  }
}
```

---

### Analyze Assignment

Analyze assignment performance.

```http
POST /api/instructor/analyze
```

**Request Body:**
```json
{
  "class": "class_name",
  "module": "1"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "analysis": {
      "total_students": 25,
      "students_submitted": 20,
      "avg_score": 82.5,
      "student_breakdown": [
        {
          "student": "student_email",
          "score": 85.0,
          "attempts": 2,
          "submitted": true
        }
      ]
    }
  }
}
```

---

### Exercise Review

Review exercise submissions.

```http
POST /api/instructor/review
```

**Request Body:**
```json
{
  "class": "class_name",
  "module": "1",
  "question_num": 1
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "review": {
      "question": "Question text",
      "correct_answer": "Correct answer",
      "total_students": 25,
      "correct_students": 18,
      "submissions": [
        {
          "student": "student_email",
          "answer": "Student answer",
          "is_correct": true,
          "attempts": 1
        }
      ]
    }
  }
}
```

---

## Class Management Endpoints

### List Class Members

Get all members of a class.

```http
GET /api/class/:class_id/members
```

**Parameters:**
- `class_id` (path) - Class identifier

**Response:**
```json
{
  "status": "success",
  "data": {
    "members": [
      {
        "user_id": "user_email",
        "name": "User Name",
        "role": "student",
        "created_at": "2025-11-01T12:00:00Z"
      }
    ]
  }
}
```

---

### Add Class Member

Add a user to a class.

```http
POST /api/class/:class_id/members
```

**Parameters:**
- `class_id` (path) - Class identifier

**Request Body:**
```json
{
  "user_id": "user_email",
  "role": "student"
}
```

**Roles:**
- `student` - Regular student access
- `ta` - Teaching assistant access
- `instructor` - Full instructor access

**Response:**
```json
{
  "status": "success",
  "message": "User user_email added to class class_id as student"
}
```

---

### Remove Class Member

Remove a user from a class.

```http
DELETE /api/class/:class_id/members/:user_id
```

**Parameters:**
- `class_id` (path) - Class identifier
- `user_id` (path) - User email

**Response:**
```json
{
  "status": "success",
  "message": "User user_id removed from class class_id"
}
```

---

### Update Member Role

Update a user's role in a class.

```http
PUT /api/class/:class_id/members/:user_id
```

**Parameters:**
- `class_id` (path) - Class identifier
- `user_id` (path) - User email

**Request Body:**
```json
{
  "role": "ta"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "User user_id role updated to ta in class class_id"
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "status": "error",
  "error": "Error message describing what went wrong",
  "details": "Optional additional error details"
}
```

### Common Errors

**401 Unauthorized**
```json
{
  "status": "error",
  "error": "Authentication required"
}
```

**403 Forbidden**
```json
{
  "status": "error",
  "error": "Insufficient permissions to perform this action"
}
```

**404 Not Found**
```json
{
  "status": "error",
  "error": "Resource not found"
}
```

**400 Bad Request**
```json
{
  "status": "error",
  "error": "Invalid request parameters",
  "details": {
    "field_name": "Error message for specific field"
  }
}
```

---

## Rate Limiting

Currently, there are no rate limits enforced. This may change in future versions.

## Pagination

Endpoints that return lists of resources may support pagination in future versions. Currently, all results are returned in a single response.

## Versioning

The API is currently at version 1.0. Future breaking changes will be versioned with a new URL path (e.g., `/api/v2/`).

---

**Last Updated**: November 2025
**API Version**: 1.0
