# Quick Start Guide

## Starting the Application Locally

### 1. Start PostgreSQL (if not running)
```bash
docker start informatics-postgres
```

**Check if running**:
```bash
docker ps | grep informatics-postgres
```

### 2. Start Flask Backend
```bash
cd /Users/robertbarrett/dev/ExCITE/InformaticsClassroom
source venv/bin/activate
python3 app.py
```

**Server will start on**: `http://localhost:5000`

### 3. Verify It's Working
```bash
# Test database connection
python3 -c "
from informatics_classroom.database.factory import get_database_adapter
db = get_database_adapter()
users = db.query('users')
print(f'✅ Connected! Found {len(users)} users')
"
```

---

## Stopping the Application

### Stop Flask
Press `Ctrl+C` in the terminal running Flask

### Stop PostgreSQL (optional)
```bash
docker stop informatics-postgres
```

---

## Troubleshooting

### "Database connection failed"
**Solution**: Start PostgreSQL
```bash
docker start informatics-postgres
```

### "Port 5000 already in use"
**Solution**: Find and kill the process
```bash
lsof -ti:5000 | xargs kill -9
```

### "ModuleNotFoundError"
**Solution**: Activate virtual environment
```bash
source venv/bin/activate
```

### "Database does not exist"
**Solution**: Re-run the import script
```bash
source venv/bin/activate
python3 migrations/import_to_postgres.py
```

---

## Database Access

### Using psql CLI
```bash
docker exec -it informatics-postgres psql -U informatics_admin -d informatics_classroom
```

### Common Queries
```sql
-- List all tables
\dt

-- Count records in each table
SELECT 'users' as table, COUNT(*) FROM users
UNION ALL SELECT 'tokens', COUNT(*) FROM tokens
UNION ALL SELECT 'quiz', COUNT(*) FROM quiz
UNION ALL SELECT 'answer', COUNT(*) FROM answer;

-- View a sample user
SELECT * FROM users LIMIT 1;

-- Exit psql
\q
```

---

## Configuration

### Current Settings (`.env`)
- **Database Type**: PostgreSQL
- **Database Name**: informatics_classroom
- **Host**: localhost:5432
- **User**: informatics_admin

### Switch Back to Cosmos DB (if needed)
Edit `.env`:
```bash
DATABASE_TYPE=cosmos
COSMOS_DATABASE_PROD="bids-class"
```

---

## What's Working
- ✅ Flask backend
- ✅ PostgreSQL database
- ✅ Database queries
- ✅ API endpoints
- ✅ Phase 3 features (TokenGenerator, AssignmentAnalysis, ExerciseReview)

## Known Issues
❌ React frontend build (TypeScript errors in old files)
- Frontend needs TypeScript errors fixed before building
- Backend API works independently

---

## Next Development Steps

1. **Fix Frontend Build**
   - Resolve TypeScript errors in Login.tsx, PermissionMatrix.tsx
   - Build with: `cd informatics-classroom-ui && npm run build`

2. **Test Full Application**
   - Start backend: `python3 app.py`
   - Frontend will be served at: `http://localhost:5000`

3. **Continue Development**
   - Phase 4: MLModelGame, NetworkBuilder, FHIRViewer
   - Phase 5: E2E testing and optimization
