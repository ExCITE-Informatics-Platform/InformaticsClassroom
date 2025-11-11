# System Architecture

Comprehensive architectural overview of the Informatics Classroom platform.

## Table of Contents
- [Overview](#overview)
- [Architecture Patterns](#architecture-patterns)
- [System Components](#system-components)
- [Data Flow](#data-flow)
- [Database Design](#database-design)
- [Authentication & Authorization](#authentication--authorization)
- [API Design](#api-design)
- [Frontend Architecture](#frontend-architecture)
- [Deployment Architecture](#deployment-architecture)
- [Security Considerations](#security-considerations)
- [Scalability & Performance](#scalability--performance)

## Overview

The Informatics Classroom follows a modern three-tier architecture:

```
┌─────────────────────────────────────────────────┐
│           Frontend (React/TypeScript)           │
│   - Single Page Application (SPA)             │
│   - Component-based UI                         │
│   - Client-side state management               │
└──────────────────┬──────────────────────────────┘
                   │ REST API (HTTPS)
┌──────────────────▼──────────────────────────────┐
│              Backend (Flask/Python)             │
│   - RESTful API endpoints                      │
│   - Business logic                             │
│   - Authentication & authorization             │
│   - Database abstraction                       │
└──────────────────┬──────────────────────────────┘
                   │ Database Protocol
┌──────────────────▼──────────────────────────────┐
│            Database Layer                       │
│   - PostgreSQL (Development)                   │
│   - Azure Cosmos DB (Production)               │
│   - Azure Blob Storage (File storage)          │
└─────────────────────────────────────────────────┘
```

## Architecture Patterns

### 1. Adapter Pattern (Database Abstraction)

The system uses the Adapter pattern to support multiple database backends:

```python
# Abstract interface
class DatabaseAdapter(ABC):
    @abstractmethod
    def query(self, table: str) -> List[Dict]:
        pass

    @abstractmethod
    def insert(self, table: str, data: Dict) -> str:
        pass

    @abstractmethod
    def update(self, table: str, id: str, data: Dict) -> bool:
        pass

# Concrete implementations
class PostgresAdapter(DatabaseAdapter):
    """PostgreSQL implementation using SQLAlchemy"""

class CosmosAdapter(DatabaseAdapter):
    """Azure Cosmos DB implementation using azure-cosmos SDK"""

# Factory pattern for instantiation
def get_database_adapter() -> DatabaseAdapter:
    if Config.DATABASE_TYPE == "postgres":
        return PostgresAdapter()
    elif Config.DATABASE_TYPE == "cosmos":
        return CosmosAdapter()
```

**Benefits:**
- Switch databases without changing business logic
- Test with local PostgreSQL, deploy with Cosmos DB
- Maintain consistent API across different backends
- Easy to add new database implementations

### 2. Blueprint Pattern (Flask Modularization)

Flask Blueprints organize the application into modular components:

```
informatics_classroom/
├── auth/              # Authentication blueprint
│   ├── routes.py     # Web routes
│   └── api_routes.py # API endpoints
├── classroom/         # Classroom blueprint
│   ├── routes.py     # Web routes
│   └── api_routes.py # API endpoints
└── imageupload/       # Image upload blueprint
    └── routes.py     # Upload endpoints
```

Each blueprint is independently registered:

```python
from flask import Flask

def create_app():
    app = Flask(__name__)

    # Register blueprints
    from informatics_classroom.auth import auth_bp
    from informatics_classroom.classroom import classroom_bp
    from informatics_classroom.imageupload import imageupload_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(classroom_bp, url_prefix='/classroom')
    app.register_blueprint(imageupload_bp, url_prefix='/upload')

    return app
```

### 3. Repository Pattern (Data Access)

Database operations are centralized through adapters:

```python
# Instead of direct database calls
# Bad: Direct database access in routes
@app.route('/users')
def get_users():
    users = db.execute("SELECT * FROM users")

# Good: Use adapter pattern
@app.route('/users')
def get_users():
    db = get_database_adapter()
    users = db.query('users')
```

### 4. Dependency Injection (Configuration)

Configuration is injected rather than hardcoded:

```python
class Config:
    # Load from environment
    FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
    DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'postgres')

    # Azure configuration
    COSMOS_URL = os.getenv('COSMOS_URL')
    AZURE_CLIENT_ID = os.getenv('AZURE_CLIENT_ID')

app.config.from_object(Config)
```

## System Components

### Backend Components

#### 1. Authentication Module (`auth/`)

**Responsibilities:**
- Azure AD OAuth2 authentication
- Session management
- JWT token generation and validation
- Permission checking
- Class-based authorization

**Key Files:**
- `routes.py` - Web authentication flows
- `api_routes.py` - API authentication endpoints
- `permissions.py` - Permission decorators and checking
- `class_auth.py` - Class membership validation
- `jwt_utils.py` - JWT encoding/decoding

#### 2. Classroom Module (`classroom/`)

**Responsibilities:**
- Quiz creation and management
- Student answer submission
- Progress tracking
- Grade calculation
- Resource management

**Key Files:**
- `routes.py` - Web classroom routes
- `api_routes.py` - Classroom API endpoints
- `forms.py` - WTForms for validation
- `helpers.py` - Utility functions
- `resources_routes.py` - Resource access endpoints

#### 3. Database Module (`database/`)

**Responsibilities:**
- Database abstraction
- CRUD operations
- Transaction management
- Connection pooling

**Key Files:**
- `interface.py` - DatabaseAdapter ABC
- `postgres_adapter.py` - PostgreSQL implementation
- `cosmos_adapter.py` - Cosmos DB implementation
- `factory.py` - Adapter factory

#### 4. Image Upload Module (`imageupload/`)

**Responsibilities:**
- File upload handling
- Azure Blob Storage integration
- Image processing
- Access control

### Frontend Components

#### 1. Component Architecture

```
components/
├── auth/              # Authentication components
│   ├── Login.tsx
│   └── ProtectedRoute.tsx
├── common/            # Reusable UI components
│   ├── Button.tsx
│   ├── Input.tsx
│   ├── Modal.tsx
│   └── Table.tsx
├── layout/            # Layout components
│   ├── Sidebar.tsx
│   ├── Header.tsx
│   └── Footer.tsx
├── permissions/       # Permission management
│   ├── PermissionMatrix.tsx
│   └── RoleEditor.tsx
└── users/             # User management
    ├── UserTable.tsx
    └── UserForm.tsx
```

#### 2. State Management

**Client State (Zustand):**
- UI state (sidebar, modals, toasts)
- Authentication state
- User preferences

**Server State (TanStack Query):**
- API data caching
- Automatic refetching
- Optimistic updates
- Background synchronization

```typescript
// Zustand store
const useAuthStore = create((set) => ({
  user: null,
  isAuthenticated: false,
  login: (user) => set({ user, isAuthenticated: true }),
  logout: () => set({ user: null, isAuthenticated: false }),
}));

// TanStack Query usage
const { data, isLoading, error } = useQuery({
  queryKey: ['users'],
  queryFn: fetchUsers,
  staleTime: 5 * 60 * 1000, // 5 minutes
});
```

#### 3. Service Layer

API calls are abstracted into service modules:

```typescript
// services/api.ts
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  withCredentials: true,
});

// services/users.ts
export const fetchUsers = () =>
  api.get('/api/users').then(res => res.data);

export const createUser = (data) =>
  api.post('/api/users', data).then(res => res.data);
```

## Data Flow

### Authentication Flow

```
1. User clicks "Login"
   ↓
2. Frontend calls /api/auth/login
   ↓
3. Backend returns Azure AD auth URL
   ↓
4. User redirected to Azure AD
   ↓
5. Azure AD authenticates user
   ↓
6. User redirected back with auth code
   ↓
7. Frontend calls /api/auth/callback with code
   ↓
8. Backend exchanges code for tokens
   ↓
9. Backend creates session
   ↓
10. Backend returns user info + session cookie
    ↓
11. Frontend stores user in state
    ↓
12. User authenticated
```

### Quiz Submission Flow

```
1. Student answers question
   ↓
2. Frontend validates input
   ↓
3. POST /api/student/submit-answer
   ↓
4. Backend validates session
   ↓
5. Backend checks class membership
   ↓
6. Backend validates answer
   ↓
7. Backend updates database:
   - Increment attempt count
   - Store answer
   - Update progress
   ↓
8. Backend returns result:
   - Correct/incorrect
   - Feedback
   - Attempt count
   ↓
9. Frontend updates UI:
   - Show feedback
   - Update progress indicator
   - Disable/enable retry
```

### Class Creation Flow

```
1. Instructor fills out form
   ↓
2. Frontend validates input
   ↓
3. POST /api/instructor/class
   ↓
4. Backend validates session
   ↓
5. Backend checks instructor permission
   ↓
6. Backend creates class:
   - Generate unique ID
   - Set owner
   - Initialize metadata
   ↓
7. Backend adds instructor membership
   ↓
8. Backend returns class data
   ↓
9. Frontend updates class list
   ↓
10. Frontend redirects to class page
```

## Database Design

### Core Tables/Collections

#### 1. Users
```sql
CREATE TABLE users (
    id VARCHAR PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. Classes
```sql
CREATE TABLE classes (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    owner VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner) REFERENCES users(id)
);
```

#### 3. Class Memberships
```sql
CREATE TABLE class_memberships (
    id VARCHAR PRIMARY KEY,
    class_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    role VARCHAR NOT NULL, -- 'student', 'ta', 'instructor'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (class_id) REFERENCES classes(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(class_id, user_id)
);
```

#### 4. Quizzes
```sql
CREATE TABLE quiz (
    id VARCHAR PRIMARY KEY,
    class VARCHAR NOT NULL,
    module VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(class, module)
);
```

#### 5. Answers
```sql
CREATE TABLE answer (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    quiz_id VARCHAR NOT NULL,
    question_num INTEGER NOT NULL,
    answer TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL,
    attempt_count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (quiz_id) REFERENCES quiz(id)
);
```

#### 6. Tokens
```sql
CREATE TABLE tokens (
    id VARCHAR PRIMARY KEY,
    class VARCHAR NOT NULL,
    module VARCHAR NOT NULL,
    token VARCHAR UNIQUE NOT NULL,
    expiry TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Database Adapter Mapping

**PostgreSQL → Cosmos DB**

| PostgreSQL | Cosmos DB |
|------------|-----------|
| Table | Container |
| Row | Document |
| Primary Key | id + PartitionKey |
| Foreign Key | Document reference |
| Transaction | Batch operation |

## Authentication & Authorization

### Multi-Level Security

#### 1. Session-Based Authentication
- Server-side session storage (Flask-Session)
- HTTP-only session cookies
- CSRF protection

#### 2. JWT Tokens (Optional)
- For API-only access
- 1-hour expiration
- Refresh token support

#### 3. Azure AD Integration
- OAuth 2.0 flow
- Microsoft identity platform
- Multi-tenant support

### Permission System

#### Role Hierarchy
```
Admin
  ↓
Instructor
  ↓
Teaching Assistant (TA)
  ↓
Student
```

#### Permission Decorators

```python
from functools import wraps

def require_permission(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not has_permission(current_user, permission):
                return jsonify({'error': 'Forbidden'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/admin/users')
@require_permission('admin')
def admin_users():
    # Only accessible to admins
    pass
```

#### Class-Based Authorization

```python
def check_class_access(user_id, class_id, required_role='student'):
    """
    Check if user has required role in class.

    Args:
        user_id: User identifier
        class_id: Class identifier
        required_role: Minimum required role

    Returns:
        bool: True if user has access
    """
    membership = get_class_membership(user_id, class_id)
    if not membership:
        return False

    role_hierarchy = ['student', 'ta', 'instructor', 'admin']
    user_role_level = role_hierarchy.index(membership.role)
    required_level = role_hierarchy.index(required_role)

    return user_role_level >= required_level
```

## API Design

### RESTful Principles

#### Resource-Based URLs
```
/api/users              # User collection
/api/users/:id          # Specific user
/api/classes            # Class collection
/api/classes/:id        # Specific class
/api/classes/:id/members # Nested resource
```

#### HTTP Methods
- `GET` - Retrieve resources
- `POST` - Create resources
- `PUT` - Update resources
- `DELETE` - Delete resources

#### Status Codes
- `2xx` - Success
- `4xx` - Client errors
- `5xx` - Server errors

### API Versioning Strategy

Current: No versioning (implicit v1)

Future: URL-based versioning
```
/api/v1/users
/api/v2/users
```

## Frontend Architecture

### Component Structure

```
App.tsx
├── AuthProvider (context)
├── QueryClientProvider (TanStack Query)
├── Router
│   ├── PublicRoute
│   │   └── Login
│   └── ProtectedRoute
│       ├── Dashboard
│       ├── Classes
│       ├── Quizzes
│       └── Profile
```

### State Management Strategy

**Local State:**
- Form inputs
- Modal visibility
- Temporary UI state

**Global Client State (Zustand):**
- Authentication
- User preferences
- UI state (sidebar, theme)

**Server State (TanStack Query):**
- API data
- Cached responses
- Background updates

### Routing Architecture

```typescript
const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { path: 'login', element: <Login /> },
      {
        path: 'dashboard',
        element: <ProtectedRoute><Dashboard /></ProtectedRoute>
      },
      {
        path: 'classes',
        element: <ProtectedRoute><Classes /></ProtectedRoute>
      },
      // ... more routes
    ]
  }
]);
```

## Deployment Architecture

### Development Environment
```
┌────────────────────┐
│   Developer PC     │
│                    │
│  ┌──────────────┐ │
│  │   Frontend   │ │  Port 5173
│  │  Vite Dev    │ │
│  └──────────────┘ │
│                    │
│  ┌──────────────┐ │
│  │   Backend    │ │  Port 5001
│  │  Flask Dev   │ │
│  └──────────────┘ │
│                    │
│  ┌──────────────┐ │
│  │  PostgreSQL  │ │  Port 5432
│  │    Docker    │ │
│  └──────────────┘ │
└────────────────────┘
```

### Production Environment (Azure)
```
                    ┌───────────────────┐
                    │   Azure AD        │
                    │  Authentication   │
                    └─────────┬─────────┘
                              │
┌─────────────────────────────▼──────────────────────────────┐
│                     Azure App Service                      │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Flask Application (Gunicorn)                        │ │
│  │  - Serves React build                                │ │
│  │  - Handles API requests                              │ │
│  └──────────────────────────────────────────────────────┘ │
└─────────────┬─────────────────────┬────────────────────────┘
              │                     │
     ┌────────▼────────┐   ┌────────▼────────┐
     │  Cosmos DB      │   │  Blob Storage   │
     │  - User data    │   │  - Images       │
     │  - Classes      │   │  - Files        │
     │  - Quizzes      │   │                 │
     └─────────────────┘   └─────────────────┘
```

## Security Considerations

### 1. Authentication Security
- Azure AD OAuth 2.0
- HTTP-only session cookies
- CSRF tokens on state-changing operations
- Secure session storage

### 2. Authorization Security
- Role-based access control (RBAC)
- Class-based permissions
- Permission decorators on all endpoints
- Principle of least privilege

### 3. Data Security
- Environment variables for secrets
- Azure Key Vault integration (production)
- Parameterized database queries (SQL injection prevention)
- Input validation and sanitization

### 4. Transport Security
- HTTPS in production
- Secure cookie flags (HttpOnly, Secure, SameSite)
- CORS configuration

### 5. Application Security
- Input validation (frontend + backend)
- Output encoding (XSS prevention)
- Rate limiting (future)
- Logging and monitoring

## Scalability & Performance

### Backend Scalability

**Horizontal Scaling:**
- Stateless application design
- Session storage in external store (Azure Table Storage)
- Database connection pooling
- Load balancer ready

**Vertical Scaling:**
- Gunicorn worker processes
- Thread pool for blocking I/O
- Async operations where appropriate

### Frontend Performance

**Build Optimization:**
- Code splitting
- Tree shaking
- Minification
- Compression (gzip/brotli)

**Runtime Optimization:**
- React.memo for expensive components
- Lazy loading routes
- Virtual scrolling for large lists
- Image optimization

### Database Performance

**PostgreSQL:**
- Indexes on frequently queried columns
- Connection pooling
- Query optimization

**Cosmos DB:**
- Partition key strategy
- Indexing policy
- Request Unit (RU) optimization
- Caching layer

### Caching Strategy

**Client-Side:**
- TanStack Query cache
- Browser cache for static assets
- Service Worker (future)

**Server-Side:**
- Session cache
- Database query cache (future)
- CDN for static assets (future)

---

**Last Updated**: November 2025
**Version**: 1.0
