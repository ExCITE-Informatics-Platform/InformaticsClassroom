# Informatics Classroom

A comprehensive educational platform for teaching biomedical informatics with modern web technologies and Azure cloud integration.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![React 19](https://img.shields.io/badge/react-19.1-blue.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/typescript-5.9-blue.svg)](https://www.typescriptlang.org/)
[![Flask 3.1](https://img.shields.io/badge/flask-3.1-green.svg)](https://flask.palletsprojects.com/)

## Overview

The Informatics Classroom provides an integrated learning environment for biomedical informatics education, featuring:

- 🎓 **Role-Based Learning**: Student, TA, and Instructor roles with tailored experiences
- 📚 **Interactive Quizzes**: Real-time feedback and progress tracking
- 👥 **Class Management**: Create and manage classes with granular permissions
- 📊 **Analytics Dashboard**: Track student progress and performance
- ☁️ **Cloud-Native**: Built for Azure with PostgreSQL support for local development
- 🔐 **Enterprise Authentication**: Azure AD integration with OAuth 2.0
- 📱 **Modern UI**: Responsive React interface with Tailwind CSS

## Quick Start

### Prerequisites

- Python 3.9+ (tested on 3.13)
- Node.js 18+
- Docker (for local PostgreSQL)
- Azure subscription (for production deployment)

### 1. Start the Backend

```bash
# Clone and setup
git clone <repository-url>
cd InformaticsClassroom

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start PostgreSQL (local dev)
docker start informatics-postgres

# Run the application
python3 app.py
```

Backend will be available at `http://localhost:5001`

### 2. Start the Frontend

```bash
# In a new terminal
cd informatics-classroom-ui

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at `http://localhost:5173`

For detailed setup instructions, see [SETUP.md](SETUP.md) or [QUICK_START.md](QUICK_START.md).

## Features

### For Students
- Access course materials organized by modules
- Take interactive quizzes with immediate feedback
- Track progress across all enrolled classes
- View personalized dashboard with completion metrics
- Multiple attempts with detailed feedback

### For Instructors
- Create and manage multiple classes
- Design and deploy quizzes for each module
- Monitor student progress in real-time
- Generate secure access tokens for resources
- Analyze assignment performance with detailed metrics
- Review individual student submissions

### For Administrators
- Full platform control and user management
- Class enrollment and permission management
- Audit trail for all platform activities
- System-wide analytics and reporting

## Tech Stack

**Backend:**
- Flask 3.1.2 (Python)
- PostgreSQL / Azure Cosmos DB
- MSAL (Azure AD authentication)
- SQLAlchemy ORM
- Azure Blob Storage

**Frontend:**
- React 19.1 + TypeScript 5.9
- Vite 7.1 (build tool)
- Tailwind CSS 3.4
- Zustand (state management)
- TanStack Query (server state)
- React Router v7
- Radix UI + Headless UI

## Project Structure

```
InformaticsClassroom/
├── informatics_classroom/    # Backend Python package
│   ├── auth/                # Authentication & authorization
│   ├── classroom/           # Core classroom functionality
│   ├── database/            # Database abstraction layer
│   ├── imageupload/         # File upload handling
│   └── scripts/             # Utility scripts
├── informatics-classroom-ui/ # Frontend React application
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/         # Page-level components
│   │   ├── services/      # API service layer
│   │   ├── store/         # State management
│   │   └── hooks/         # Custom React hooks
├── migrations/              # Database migrations
├── tests/                   # Test suite
├── claudedocs/              # Project documentation
├── app.py                   # Application entry point
└── requirements.txt         # Python dependencies
```

## Documentation

Comprehensive documentation is available in the [`docs/`](docs/) directory:

- **[Documentation Index](docs/INDEX.md)** - Complete documentation guide
- **[Project Overview](docs/README.md)** - Comprehensive project documentation
- **[API Reference](docs/API_DOCUMENTATION.md)** - Complete REST API documentation
- **[Architecture](docs/ARCHITECTURE.md)** - System architecture and design patterns
- **[User Workflows](docs/WORKFLOWS.md)** - Role-based workflow guides
- **[Testing Guide](docs/TEST_SUMMARY.md)** - Testing strategy and practices

### Setup Guides

- **[SETUP.md](SETUP.md)** - Detailed setup with Azure configuration
- **[QUICK_START.md](QUICK_START.md)** - Quick start for local development

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
pytest --cov=informatics_classroom --cov-report=html tests/
```

### Code Quality

```bash
# Backend: Follow PEP 8 guidelines
# Frontend: Run linter
cd informatics-classroom-ui
npm run lint

# Build for production
npm run build
```

### Database Management

```bash
# Start PostgreSQL
docker start informatics-postgres

# Access database
docker exec -it informatics-postgres psql -U informatics_admin -d informatics_classroom

# Import data
python3 migrations/import_to_postgres.py

# Seed resources
python3 seed_resources.py
```

## Environment Configuration

The application requires environment variables for configuration. Create a `.env` file:

```bash
# Database
DATABASE_TYPE=postgres  # or 'cosmos' for production

# PostgreSQL (Development)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=informatics_classroom
POSTGRES_USER=informatics_admin
POSTGRES_PASSWORD=<password>

# Flask
FLASK_SECRET_KEY=<generate-with-secrets.token_hex(32)>
FLASK_DEBUG=False

# Azure AD (Production)
AZURE_CLIENT_ID=<client-id>
AZURE_CLIENT_SECRET=<client-secret>
AZURE_AUTHORITY=https://login.microsoftonline.com/common

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

⚠️ **Never commit `.env` to version control!** See `.env.example` for the template.

## Testing

The project uses Pytest with custom markers for test organization:

- `@pytest.mark.workflow` - Complete user workflow tests
- `@pytest.mark.permission` - Permission and access control
- `@pytest.mark.student` - Student functionality
- `@pytest.mark.instructor` - Instructor functionality
- `@pytest.mark.admin` - Admin functionality
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.slow` - Long-running tests

```bash
# Run specific test categories
pytest -m "workflow and student"
pytest -m "not slow"
```

## Deployment

### Development Deployment
- **Backend**: Flask development server (port 5001)
- **Frontend**: Vite dev server (port 5173)
- **Database**: PostgreSQL in Docker (port 5432)

### Production Deployment
- **Platform**: Azure App Service
- **Backend**: Gunicorn WSGI server
- **Frontend**: Built with Vite, served by Flask
- **Database**: Azure Cosmos DB
- **Authentication**: Azure AD
- **Storage**: Azure Blob Storage

For production deployment:
```bash
# Build frontend
cd informatics-classroom-ui
npm run build

# Deploy with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "informatics_classroom:create_app()"
```

## Architecture Highlights

### Database Adapter Pattern
Switch seamlessly between PostgreSQL (development) and Azure Cosmos DB (production) without changing business logic:

```python
# Use the same interface for both databases
db = get_database_adapter()
users = db.query('users')
```

### Modern Frontend Architecture
- Component-based UI with React 19
- TypeScript for type safety
- Zustand for lightweight state management
- TanStack Query for server state caching
- Tailwind CSS for utility-first styling

### Security-First Design
- Azure AD OAuth 2.0 authentication
- Session-based security with HTTP-only cookies
- Role-based access control (RBAC)
- Class-level permission checking
- Environment-based configuration

## Contributing

1. Follow the existing code style:
   - Python: PEP 8
   - TypeScript: ESLint configuration
2. Write tests for new functionality
3. Update documentation as needed
4. Ensure all tests pass: `pytest`

## Common Issues

### "Database connection failed"
```bash
# Start PostgreSQL
docker start informatics-postgres
```

### "Port 5001 already in use"
```bash
# Kill the process
lsof -ti:5001 | xargs kill -9
```

### "ModuleNotFoundError"
```bash
# Activate virtual environment
source venv/bin/activate
```

### Frontend build errors
```bash
# Clean and reinstall
cd informatics-classroom-ui
rm -rf node_modules package-lock.json
npm install
npm run build
```

## Support & Contact

For issues, questions, or contributions:
- Open an issue on GitHub
- Contact the development team

## License

[Add license information]

## Acknowledgments

Built for biomedical informatics education at Johns Hopkins University.

---

**Last Updated**: November 2025
**Version**: 1.0.0
**Python**: 3.9+
**Node.js**: 18+
