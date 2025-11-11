# Documentation Index

Complete guide to the Informatics Classroom platform documentation.

## Quick Links

### Getting Started
- **[Project README](../README.md)** - Project overview and quick start
- **[Setup Guide](../SETUP.md)** - Detailed installation and configuration
- **[Quick Start](../QUICK_START.md)** - Fast local development setup

### Core Documentation
- **[README](README.md)** - Comprehensive project documentation
- **[API Documentation](API_DOCUMENTATION.md)** - Complete REST API reference
- **[Architecture](ARCHITECTURE.md)** - System design and patterns
- **[Workflows](WORKFLOWS.md)** - User role workflows and use cases
- **[Testing](TEST_SUMMARY.md)** - Testing strategy and guidelines

## Documentation by Audience

### For Developers

**Getting Started:**
1. [Project README](../README.md) - Overview and tech stack
2. [Quick Start](../QUICK_START.md) - Get running in 5 minutes
3. [Setup Guide](../SETUP.md) - Complete environment setup

**Development:**
- [Architecture](ARCHITECTURE.md) - Understand system design
- [API Documentation](API_DOCUMENTATION.md) - API endpoints reference
- [Testing](TEST_SUMMARY.md) - How to write and run tests

**Reference:**
- Backend code: `informatics_classroom/`
- Frontend code: `informatics-classroom-ui/src/`
- Tests: `tests/`

### For Users

**Understanding the Platform:**
- [README](README.md#features) - Feature overview by role
- [Workflows](WORKFLOWS.md) - How to accomplish common tasks

**Specific Workflows:**
- [Student Workflows](WORKFLOWS.md#student-workflows)
- [Instructor Workflows](WORKFLOWS.md#instructor-workflows)
- [Admin Workflows](WORKFLOWS.md#admin-workflows)

### For System Administrators

**Deployment:**
- [Setup Guide](../SETUP.md) - Azure services configuration
- [Architecture](ARCHITECTURE.md#deployment-architecture) - Infrastructure overview

**Configuration:**
- Environment variables: [README](README.md#environment-configuration)
- Database setup: [Quick Start](../QUICK_START.md#database-access)
- Security: [Architecture](ARCHITECTURE.md#security-considerations)

## Documentation by Topic

### API & Integration
- **[API Documentation](API_DOCUMENTATION.md)** - Complete API reference
  - Authentication endpoints
  - Student endpoints
  - Instructor endpoints
  - Class management
  - Error handling

### System Architecture
- **[Architecture](ARCHITECTURE.md)** - Comprehensive architecture guide
  - Architecture patterns
  - System components
  - Data flow
  - Database design
  - Security
  - Scalability

### User Guides
- **[Workflows](WORKFLOWS.md)** - Role-based workflows
  - Student workflows
  - Instructor workflows
  - Admin workflows
  - Common scenarios

### Testing & Quality
- **[Testing](TEST_SUMMARY.md)** - Testing documentation
  - Test categories
  - Running tests
  - Test coverage
  - CI/CD integration

## Project Structure

```
InformaticsClassroom/
├── README.md                 # Project overview
├── SETUP.md                  # Setup guide
├── QUICK_START.md           # Quick start
├── docs/                     # 👈 Public documentation
│   ├── INDEX.md             # This file
│   ├── README.md            # Comprehensive overview
│   ├── API_DOCUMENTATION.md # API reference
│   ├── ARCHITECTURE.md      # System architecture
│   ├── WORKFLOWS.md         # User workflows
│   └── TEST_SUMMARY.md      # Testing guide
├── informatics_classroom/   # Backend code
├── informatics-classroom-ui/ # Frontend code
└── tests/                   # Test suite
```

## How to Use This Documentation

### New Developer Onboarding
1. Read [Project README](../README.md) for overview
2. Follow [Quick Start](../QUICK_START.md) to get running
3. Study [Architecture](ARCHITECTURE.md) to understand design
4. Review [API Documentation](API_DOCUMENTATION.md) for endpoints
5. Check [Testing](TEST_SUMMARY.md) for test practices

### Adding New Features
1. Review [Architecture](ARCHITECTURE.md) for patterns
2. Check [API Documentation](API_DOCUMENTATION.md) for conventions
3. Follow existing code structure
4. Write tests (see [Testing](TEST_SUMMARY.md))
5. Update relevant documentation

### Troubleshooting
1. Check [Quick Start](../QUICK_START.md#troubleshooting)
2. Review [README](../README.md#common-issues)
3. Consult [Workflows](WORKFLOWS.md) for expected behavior
4. See [Testing](TEST_SUMMARY.md) for test issues

## Contributing to Documentation

When making changes to the codebase:

### Always Update
- New API endpoint → [API Documentation](API_DOCUMENTATION.md)
- Architecture change → [Architecture](ARCHITECTURE.md)
- New env variable → [README](README.md), [Setup Guide](../SETUP.md)
- New feature → [README](README.md), possibly [Workflows](WORKFLOWS.md)

### Documentation Standards
- Use Markdown for all docs
- Include code examples with syntax highlighting
- Add table of contents for long documents
- Use consistent heading hierarchy
- Cross-reference related documents

## External Resources

### Technologies Used
- **Flask**: https://flask.palletsprojects.com/
- **React**: https://react.dev/
- **TypeScript**: https://www.typescriptlang.org/
- **Tailwind CSS**: https://tailwindcss.com/
- **TanStack Query**: https://tanstack.com/query/latest
- **Azure**: https://docs.microsoft.com/azure/

### Learning Resources
- **Python/Flask**: Official Flask documentation
- **React/TypeScript**: React documentation + TypeScript handbook
- **Azure Services**: Microsoft Learn paths
- **Testing**: Pytest documentation

## Quick Reference

### Essential Commands
```bash
# Backend
python3 app.py              # Start backend
pytest                      # Run tests
pytest -m workflow          # Run workflow tests

# Frontend
cd informatics-classroom-ui
npm run dev                 # Start dev server
npm run build               # Production build
npm run lint                # Lint check

# Database
docker start informatics-postgres   # Start PostgreSQL
docker exec -it informatics-postgres psql -U informatics_admin -d informatics_classroom
```

### Key Configuration Files
- `.env` - Environment variables (never commit!)
- `.env.example` - Environment template
- `requirements.txt` - Python dependencies
- `package.json` - Node.js dependencies
- `pytest.ini` - Test configuration

### Important Directories
- `informatics_classroom/auth/` - Authentication
- `informatics_classroom/classroom/` - Core functionality
- `informatics_classroom/database/` - Database adapters
- `informatics-classroom-ui/src/components/` - React components
- `informatics-classroom-ui/src/services/` - API services
- `tests/` - Test suite

## Support

For questions or issues:
1. Check documentation (start here!)
2. Review existing GitHub issues
3. Ask the development team
4. Create new issue with details

---

**Last Updated**: November 2025
**Documentation Version**: 1.0

*Keep documentation current - it's part of the code!*
