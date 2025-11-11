# Informatics Classroom

A comprehensive educational platform for teaching biomedical informatics with modern web technologies and Azure cloud integration.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)

## Overview

The Informatics Classroom is an educational platform designed to facilitate biomedical informatics education through:
- **Role-based access control** for students, teaching assistants, and instructors
- **Interactive quizzes and assessments** with real-time feedback
- **Class and module management** with granular permission controls
- **Progress tracking and analytics** for both students and instructors
- **Azure cloud integration** for scalable, enterprise-grade functionality

## Features

### For Students
- Access course materials and modules
- Take interactive quizzes with immediate feedback
- Track progress across courses and modules
- View personalized dashboard with completion metrics
- Submit answers with attempt tracking

### For Instructors
- Create and manage classes
- Design and deploy quizzes
- Monitor student progress and grades
- Generate access tokens for resources
- Analyze assignment performance
- Review exercise submissions

### For Administrators
- Full platform control
- User and permission management
- Class enrollment management
- Audit trail access
- System configuration

## Tech Stack

### Backend
- **Framework**: Flask 3.1.2 (Python 3.9+)
- **Database**:
  - PostgreSQL (development)
  - Azure Cosmos DB (production)
- **Authentication**: MSAL + Azure AD
- **Storage**: Azure Blob Storage
- **Session**: Flask-Session
- **ORM**: SQLAlchemy 2.0.43

### Frontend
- **Framework**: React 19.1.1
- **Language**: TypeScript 5.9.3
- **Build Tool**: Vite 7.1.12
- **Styling**: Tailwind CSS 3.4.17
- **State Management**:
  - Zustand 5.0.8 (client state)
  - TanStack Query 5.90.6 (server state)
- **UI Components**: Radix UI + Headless UI
- **Routing**: React Router v7.9.5
- **HTTP**: Axios 1.13.1

### Infrastructure
- **Cloud Provider**: Microsoft Azure
- **Services**:
  - Azure AD (authentication)
  - Cosmos DB (NoSQL database)
  - Blob Storage (file storage)
  - Table Storage (session storage)

## Getting Started

### Prerequisites
- Python 3.9+ (currently using 3.13)
- Node.js 18+
- Docker (for PostgreSQL local development)
- Azure subscription (for production deployment)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd InformaticsClassroom
   ```

2. **Set up backend**
   ```bash
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate

   # Install dependencies
   pip install -r requirements.txt

   # Copy environment file
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start PostgreSQL (local development)**
   ```bash
   docker start informatics-postgres
   ```

4. **Run backend**
   ```bash
   python3 app.py
   # Runs on http://localhost:5001
   ```

5. **Set up frontend** (in new terminal)
   ```bash
   cd informatics-classroom-ui
   npm install
   npm run dev
   # Runs on http://localhost:5173
   ```

For detailed setup instructions, see [SETUP.md](../SETUP.md) and [QUICK_START.md](../QUICK_START.md).

## Project Structure

```
InformaticsClassroom/
├── informatics_classroom/       # Backend Python package
│   ├── __init__.py             # Flask app factory
│   ├── config.py               # Configuration management
│   ├── auth/                   # Authentication & authorization
│   │   ├── routes.py          # Web auth routes
│   │   ├── api_routes.py      # Auth API endpoints
│   │   ├── permissions.py     # Permission checking
│   │   ├── class_auth.py      # Class-based auth
│   │   └── jwt_utils.py       # JWT token handling
│   ├── classroom/              # Core classroom functionality
│   │   ├── routes.py          # Web routes
│   │   ├── api_routes.py      # Classroom API endpoints
│   │   ├── resources_routes.py # Resource management
│   │   ├── forms.py           # WTForms definitions
│   │   └── helpers.py         # Utility functions
│   ├── database/               # Database abstraction
│   │   ├── interface.py       # Abstract base class
│   │   ├── cosmos_adapter.py  # Cosmos DB implementation
│   │   ├── postgres_adapter.py # PostgreSQL implementation
│   │   └── factory.py         # Adapter factory
│   ├── imageupload/            # Image upload handling
│   └── scripts/                # Utility scripts
├── informatics-classroom-ui/    # Frontend React application
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/            # Page-level components
│   │   ├── services/         # API service layer
│   │   ├── store/            # Zustand stores
│   │   ├── hooks/            # Custom React hooks
│   │   ├── types/            # TypeScript definitions
│   │   └── utils/            # Utility functions
│   ├── package.json
│   └── vite.config.ts
├── migrations/                  # Database migrations
├── tests/                       # Pytest test suite
├── claudedocs/                  # Project documentation
├── app.py                       # Application entry point
├── requirements.txt             # Python dependencies
└── pytest.ini                   # Test configuration
```

## Documentation

- **[SETUP.md](../SETUP.md)** - Detailed setup and configuration guide
- **[QUICK_START.md](../QUICK_START.md)** - Quick start guide for local development
- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Complete API reference
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and design patterns
- **[WORKFLOWS.md](WORKFLOWS.md)** - User role workflows
- **[TESTING.md](TEST_SUMMARY.md)** - Testing strategy and guidelines

## Development

### Running Tests
```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run specific test categories
pytest -m workflow        # Workflow tests
pytest -m permission      # Permission tests
pytest -m unit            # Unit tests

# Run with coverage
pytest --cov=informatics_classroom --cov-report=html
```

### Code Quality
```bash
# Backend (Python)
# Follow PEP 8 style guide
# Use type hints where appropriate

# Frontend (TypeScript/React)
cd informatics-classroom-ui
npm run lint              # ESLint
npm run build             # Type checking + build
```

### Database Management
```bash
# Start PostgreSQL
docker start informatics-postgres

# Access PostgreSQL CLI
docker exec -it informatics-postgres psql -U informatics_admin -d informatics_classroom

# Import data
python3 migrations/import_to_postgres.py
```

## Testing

The project uses Pytest for backend testing with the following markers:
- `@pytest.mark.workflow` - Complete user workflow tests
- `@pytest.mark.permission` - Permission and access control tests
- `@pytest.mark.student` - Student functionality tests
- `@pytest.mark.instructor` - Instructor functionality tests
- `@pytest.mark.admin` - Admin functionality tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.slow` - Long-running tests

See [TEST_SUMMARY.md](TEST_SUMMARY.md) for detailed testing documentation.

## Deployment

### Development
- Backend: `python3 app.py` (port 5001)
- Frontend: `npm run dev` (port 5173)
- Database: PostgreSQL via Docker (port 5432)

### Production
- Backend: Gunicorn WSGI server
- Frontend: Build with `npm run build`, served by Flask
- Database: Azure Cosmos DB
- Authentication: Azure AD
- Storage: Azure Blob Storage

For production deployment details, see [SETUP.md](../SETUP.md).

## Environment Variables

Create a `.env` file with the following variables:

```bash
# Flask Configuration
FLASK_SECRET_KEY=<strong-random-secret>
FLASK_DEBUG=False
FLASK_TESTING=False

# Database
DATABASE_TYPE=postgres  # or 'cosmos' for production

# PostgreSQL (Development)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=informatics_classroom
POSTGRES_USER=informatics_admin
POSTGRES_PASSWORD=<password>

# Azure AD / MSAL (Production)
AZURE_CLIENT_ID=<client-id>
AZURE_CLIENT_SECRET=<client-secret>
AZURE_AUTHORITY=https://login.microsoftonline.com/common
AZURE_REDIRECT_PATH=/getAToken

# Azure Cosmos DB (Production)
COSMOS_URL=<cosmos-url>
COSMOS_KEY=<cosmos-key>
COSMOS_DATABASE_PROD=bids-class

# Azure Storage (Production)
AZURE_STORAGE_ACCOUNT_NAME=<account-name>
AZURE_STORAGE_KEY=<storage-key>
AZURE_BLOB_CONTAINER_NAME=figures
AZURE_BLOB_CONNECT_STR=<connection-string>
```

See `.env.example` for the complete list of environment variables.

## Contributing

1. Follow the existing code style and conventions
2. Write tests for new functionality
3. Update documentation as needed
4. Ensure all tests pass before submitting

## License

[Add license information]

## Support

For issues or questions, please contact [add contact information].

---

**Last Updated**: November 2025
**Version**: 1.0.0
