# Informatics Classroom - Primary Workflows

This document describes the core workflows supported by the Informatics Classroom application for students, instructors, and administrators.

## User Roles

The system supports four distinct roles with hierarchical permissions:

- **Admin**: Full system access, user management, impersonation capabilities
- **Instructor**: Class creation, quiz management, grade viewing, member management
- **TA (Teaching Assistant)**: Quiz creation/editing, grade viewing within assigned classes
- **Student**: Quiz taking, progress tracking, resource access

## Authentication Workflow

### User Login
1. User navigates to application
2. System redirects to Microsoft Entra ID (formerly Azure AD) login
3. User authenticates with institutional credentials
4. System receives OAuth token and user claims
5. JWT token generated with user ID, email, display name, and roles
6. Token stored and used for all subsequent API requests

**Key Endpoints:**
- `GET /api/auth/status` - Check authentication status
- `GET /api/auth/login` - Initiate Entra ID login flow
- `GET /api/auth/callback` - Handle OAuth callback
- `POST /api/auth/refresh` - Refresh JWT token

---

## Student Workflows

### 1. Class Access and Registration

**Workflow:**
1. Student logs in to system
2. System displays dashboard with accessible classes based on class_memberships
3. Student can access classes assigned by instructor/admin

**Key Pages:**
- Dashboard (`/dashboard`)
- Student Center (`/student-center`)

**Key Endpoints:**
- `GET /api/student/courses` - Retrieve accessible classes
- `GET /api/student/dashboard` - Get dashboard with course summaries

**Data Flow:**
- User authenticates → System queries user's class_memberships → Returns list of classes → Displays course cards with progress

### 2. Quiz Taking

**Workflow:**
1. Student selects class and module from Student Center
2. System retrieves quiz for selected class/module
3. Student views questions and submits answers
4. System validates answers and provides immediate feedback
5. Student can retry incorrect answers (attempts tracked)
6. Progress automatically saved to database

**Key Pages:**
- Student Center (`/student-center`)
- Quiz Taking (`/quiz-taking`)

**Key Endpoints:**
- `GET /api/quiz/details?course=X&module=Y` - Get quiz questions
- `POST /api/quiz/submit-answer` - Submit individual answer
  - Body: `{ course, module, question_num, answer }`
  - Returns: `{ correct, feedback, is_open }`

**Data Flow:**
- Select course/module → Fetch quiz with previous answers → Display questions → Submit answer → Validate → Store in answer table → Update UI

### 3. Progress Tracking

**Workflow:**
1. Student accesses Student Center or Dashboard
2. System calculates progress across all accessible classes
3. Displays completion percentage and correctness metrics per module
4. Student can drill down into specific courses to see question-level details

**Key Pages:**
- Dashboard (`/dashboard`)
- Student Center (`/student-center`)

**Key Endpoints:**
- `GET /api/student/progress?course=X` - Get detailed module progress
- `GET /api/student/exercise-review` - Get complete progress across all classes

**Data Flow:**
- Request progress → Query quizzes for class → Query user's answers → Calculate metrics (answered/total, correct/total) → Return progress data

### 4. Resource Access

**Workflow:**
1. Student navigates to Resources page
2. System displays resources filtered by student's accessible classes
3. Resources organized by category (general, course-specific)
4. Student can view documents, videos, and other learning materials

**Key Pages:**
- Resources (`/resources`)

**Key Endpoints:**
- `GET /api/resources?class=X` - Get resources for class
- `GET /api/resources/stats` - Get resource statistics

**Data Flow:**
- Access resources page → Filter resources by class membership → Display organized by category

---

## Instructor Workflows

### 1. Class Management

**Workflow:**
1. Instructor creates new class
2. System assigns instructor role automatically
3. Instructor can view all classes they manage
4. Instructor can delete classes (with confirmation)

**Key Pages:**
- Class Selector (`/class-selector`)
- Class Management (`/class/:classId`)

**Key Endpoints:**
- `GET /api/instructor/classes` - Get all managed classes with metadata
- `POST /api/classes` - Create new class
  - Body: `{ name }`
  - Returns: `{ class: { id, name, owner, role, ... } }`
- `DELETE /api/classes/:classId` - Delete class and all associated data

**Data Flow:**
- Create class → Assign instructor role in class_memberships → Class appears in managed list

### 2. Quiz/Assignment Creation

**Workflow:**
1. Instructor selects class from Class Selector
2. Navigates to Quiz Builder
3. Creates quiz with title, description, module number
4. Adds questions with:
   - Question text
   - Multiple choice answers
   - Correct answer designation
   - Open-ended flag (if applicable)
5. Saves quiz to database
6. Quiz immediately available to students in that class

**Key Pages:**
- Quiz Builder (`/quiz-builder`)
- Class Management - Assignments Tab (`/class/:classId`)

**Key Endpoints:**
- `POST /api/quizzes/create` - Create new quiz
  - Body: `{ class, module, title, description, questions: [{question_num, question_text, answers: [], correct_answer, open}] }`
- `GET /api/quizzes/:quizId/edit` - Get quiz for editing
- `PUT /api/quizzes/:quizId/update` - Update existing quiz
  - Tracks changes in change_log for audit trail
- `DELETE /api/quizzes/:quizId` - Delete quiz

**Data Flow:**
- Create quiz → Validate instructor/TA role → Store in quiz table → Available to class members

### 3. Student Progress and Grade Viewing

**Workflow:**
1. Instructor navigates to Class Management for specific class
2. Selects Grades tab
3. System displays grade matrix:
   - Rows: Students (teams)
   - Columns: Quizzes (modules)
   - Cells: Score/Total and percentage
4. Instructor can see submission status and scores
5. Can export or analyze grade data

**Key Pages:**
- Class Management - Grades Tab (`/class/:classId`)
- Assignment Analysis (`/assignment-analysis`)

**Key Endpoints:**
- `GET /api/classes/:classId/grades` - Get complete grade matrix
  - Returns: `{ students: [], quizzes: [], grades: {student_id: {quiz_id: {score, total, percentage, submitted}}} }`
- `POST /api/assignments/analyze` - Analyze assignment performance
  - Body: `{ class_name, module_number, year_filter }`
  - Returns: Question-level breakdown with correctness and attempt statistics

**Data Flow:**
- Select class → Query all quizzes for class → Query all answers → Build grade matrix → Calculate scores per student/quiz

### 4. Class Member Management

**Workflow:**
1. Instructor navigates to Class Management - Students tab
2. Views current class members and their roles
3. Can add new members by user ID
4. Assigns role (instructor, TA, student)
5. Can update member roles
6. Can remove members from class

**Key Pages:**
- Class Management - Students Tab (`/class/:classId`)

**Key Endpoints:**
- `GET /api/classes/:classId/members` - List all class members
- `POST /api/classes/:classId/members` - Add member
  - Body: `{ user_id, role }`
- `PUT /api/classes/:classId/members/:userId` - Update member role
  - Body: `{ role }`
- `DELETE /api/classes/:classId/members/:userId` - Remove member

**Data Flow:**
- Add member → Update user's class_memberships array → Member gains access to class resources

### 5. Resource Management

**Workflow:**
1. Instructor navigates to Resources Admin page
2. Creates new resource with:
   - Title and description
   - Category
   - Resource type (document, video, link)
   - URL or file upload
   - Class association (general or specific class)
   - Icon selection
3. Resources immediately visible to appropriate students
4. Can edit or delete resources

**Key Pages:**
- Resources Admin (`/resources-admin`)

**Key Endpoints:**
- `POST /api/resources` - Create new resource
- `PUT /api/resources/:resourceId` - Update resource
- `DELETE /api/resources/:resourceId` - Delete resource

---

## Admin Workflows

### 1. User Management

**Workflow:**
1. Admin navigates to Users page
2. Views all users with pagination and filtering
3. Can filter by role, search by name/email
4. Can edit user details:
   - Display name
   - Email
   - Global role (admin, instructor, student)
5. Can view user's class memberships
6. Can assign/remove global roles

**Key Pages:**
- Users (`/users`)

**Key Endpoints:**
- `GET /api/users` - List all users with pagination
  - Query params: `page, pageSize, role, search, active`
- `PUT /api/users/:userId` - Update user details
  - Body: `{ email, display_name, role }`
- `GET /api/users/:userId/permissions` - Get user's detailed permissions

**Data Flow:**
- Load users → Query with filters → Display paginated table → Edit user → Update user record

### 2. Permission Management

**Workflow:**
1. Admin accesses Permission Matrix page
2. Views permission matrix showing role-permission mappings
3. Can see which permissions each role has:
   - Quiz management (view, create, modify, delete)
   - User management
   - Class administration
   - Analytics viewing
   - System administration
4. Matrix provides reference for permission structure

**Key Pages:**
- Permission Matrix (`/permission-matrix`)

**Key Endpoints:**
- `GET /api/permissions/check` - Check specific permission for user
  - Query params: `user_id, permission, class_id`

**Data Model:**
```
Permissions:
- QUIZ_VIEW, QUIZ_CREATE, QUIZ_MODIFY, QUIZ_DELETE
- USER_MANAGE, USER_VIEW
- TOKEN_GENERATE
- CLASS_ADMIN, CLASS_VIEW_ANALYTICS
- SYSTEM_ADMIN, SYSTEM_VIEW_LOGS
```

### 3. User Impersonation

**Workflow:**
1. Admin selects user to impersonate from dropdown
2. System switches context to impersonated user
3. Admin experiences application as that user
4. Impersonation banner displayed at top of screen
5. Admin can exit impersonation to return to admin view

**Key Pages:**
- All pages (when impersonating)

**Key Endpoints:**
- `POST /api/auth/impersonate` - Start impersonation
  - Body: `{ target_user_id }`
- `POST /api/auth/exit-impersonation` - Exit impersonation

**Data Flow:**
- Select user → Create impersonation session → Issue new JWT with impersonated user context → Banner displayed → Exit returns to admin context

### 4. Audit Log Viewing

**Workflow:**
1. Admin navigates to Audit Logs page
2. Views system activity logs with filtering:
   - Action type (create, update, delete, login, etc.)
   - User ID
   - Date range
   - Class ID
3. Can see detailed audit trail for compliance and troubleshooting

**Key Pages:**
- Audit Logs (`/audit-logs`)

**Key Endpoints:**
- `GET /api/audit/logs` - Get paginated audit logs
  - Query params: `page, pageSize, action, user_id, class_id, start_date, end_date`

**Data Flow:**
- Load audit page → Query logs with filters → Display chronological activity → Can drill into specific events

### 5. Token Management

**Workflow:**
1. Admin can generate access tokens for classes/modules
2. Tokens provide 24-hour access without re-authentication
3. Used for sharing quiz access temporarily
4. Tokens tied to specific class and module

**Key Pages:**
- Token Generator (`/token-generator`)

**Key Endpoints:**
- `POST /api/tokens/generate` - Generate access token
  - Body: `{ class_val, module_val }`
  - Returns: `{ token, expiry }`

---

## Cross-Role Workflows

### Class Membership Model

**Structure:**
- Users have global roles (admin, instructor, student)
- Users have class-specific roles via class_memberships array
- Class roles: class_admin, class_instructor, class_ta, class_student, class_viewer

**Access Control:**
1. User authenticates and receives global role
2. For class-specific operations, system checks class_memberships
3. Permission decorators validate both global and class roles
4. Hierarchical permissions: admin > instructor > TA > student

### Quiz Lifecycle

**States:**
1. **Created** - Instructor creates quiz with questions
2. **Active** - Available to students for taking
3. **In Progress** - Students submitting answers
4. **Completed** - All students finished (or deadline passed)
5. **Modified** - Instructor edits quiz (change_log tracks modifications)
6. **Archived** - Deleted (quizzes removed, answers preserved)

### Data Persistence

**Tables:**
- `users` - User profiles and global roles
- `quiz` - Quiz definitions with questions
- `answer` - Student answer submissions with correctness and timestamps
- `class_memberships` - User-class-role associations (stored in user records)
- `resources` - Learning materials
- `tokens` - Access tokens for temporary authentication

---

## Security and Permission Model

### Permission Decorators

**Function-level security:**
- `@require_jwt_token` - Validates JWT on all protected endpoints
- `@require_role(['admin', 'instructor'])` - Global role check
- `@require_class_role(['instructor', 'ta'], class_from='body.class')` - Class-specific role check
- `@require_class_permission('view_analytics', class_from='path.class_id')` - Permission-based check
- `@require_quiz_permission('manage_quizzes')` - Quiz-specific permission check

### Permission Hierarchy

**Admin:**
- Full system access
- Can impersonate any user
- Can manage all users, classes, and resources

**Instructor:**
- Create and manage own classes
- Create, edit, delete quizzes in managed classes
- View grades and analytics for managed classes
- Manage class members (add/remove students and TAs)

**TA:**
- Create and edit quizzes in assigned classes
- View grades and analytics for assigned classes
- Cannot delete quizzes or manage class members

**Student:**
- Access assigned classes
- Take quizzes and view personal progress
- Access resources for enrolled classes
- Cannot view other students' grades

---

## Error Handling and Edge Cases

### Quiz Taking
- **No quiz found**: Returns 404 with error message
- **Invalid answer format**: Returns 400 with validation error
- **Multiple attempts**: System stores all attempts, calculates best score
- **Open-ended questions**: Always marked correct, stored for instructor review

### Class Management
- **Duplicate class name**: Returns 400, prevents creation
- **Deleting class with students**: Removes all quizzes, preserves historical answer data
- **Permission denied**: Returns 403 with clear permission requirements

### User Management
- **Invalid role assignment**: Returns 400 with valid role list
- **User not found**: Returns 404
- **Concurrent edits**: Last write wins, change_log tracks modifications

---

## Performance Considerations

### Caching Strategy
- JWT tokens cached client-side with 1-hour expiration
- Class membership data refreshed on login and permission changes
- Quiz data fetched per-module to minimize payload size

### Database Optimization
- Partition key on answer table: `{class}_{module}` for efficient querying
- Indexes on user_id, class, module for fast lookups
- Pagination on all list endpoints (default: 50 items per page)

### Scalability
- Stateless JWT authentication enables horizontal scaling
- Database adapter pattern supports PostgreSQL and Cosmos DB
- Background jobs for grade calculation on large datasets
