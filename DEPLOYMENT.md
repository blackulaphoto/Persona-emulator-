# Deployment Guide - Persona Evolution Simulator

Complete guide to deploying both backend and frontend for production use.

## Architecture Overview

```
Frontend (Next.js)          Backend (FastAPI)
    ↓                            ↓
Vercel/Railway           Railway/Render/AWS
Port 3000                    Port 8000
    ↓                            ↓
    └────────────────────────────┘
         REST API Calls
```

## Quick Start (Local Development)

### 1. Start Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Backend will be available at `http://localhost:8000`
API docs at `http://localhost:8000/docs`

### 2. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at `http://localhost:3000`

## Production Deployment

### Option A: Railway (Recommended - Easiest)

**Why Railway?**
- Single platform for both frontend and backend
- Automatic SSL certificates
- Built-in PostgreSQL
- Simple environment variable management
- $5-10/month for hobby projects

#### Step 1: Deploy Backend

```bash
cd backend

# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create project
railway init

# Add PostgreSQL
railway add postgresql

# Set environment variables
railway variables set OPENAI_API_KEY=sk-...
railway variables set ANTHROPIC_API_KEY=sk-ant-...

# Deploy
railway up
```

Railway will give you a URL like: `https://your-backend.railway.app`

#### Step 2: Deploy Frontend

```bash
cd frontend

# Create new Railway project
railway init

# Set backend URL
railway variables set NEXT_PUBLIC_API_URL=https://your-backend.railway.app

# Deploy
railway up
```

Railway will give you a URL like: `https://your-frontend.railway.app`

### Option B: Vercel (Frontend) + Railway (Backend)

**Why This Combo?**
- Vercel is optimized for Next.js
- Free tier for frontend
- Railway handles backend well

#### Backend on Railway

(Same as Option A, Step 1)

#### Frontend on Vercel

```bash
cd frontend

# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
vercel

# Set environment variables
vercel env add NEXT_PUBLIC_API_URL
# Enter: https://your-backend.railway.app

# Deploy production
vercel --prod
```

### Option C: Self-Hosted (Docker)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/personas
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - db
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=personas
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Then:

```bash
docker-compose up -d
```

## Environment Variables

### Backend (.env)

```bash
# Required
DATABASE_URL=postgresql://user:pass@host:5432/dbname
OPENAI_API_KEY=sk-...

# Optional
ANTHROPIC_API_KEY=sk-ant-...  # If using Claude
LOG_LEVEL=INFO
PORT=8000
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

## Database Migration (SQLite → PostgreSQL)

When moving to production:

```bash
# 1. Export from SQLite
cd backend
python scripts/export_data.py > data.json

# 2. Set new DATABASE_URL
export DATABASE_URL=postgresql://...

# 3. Create tables
python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"

# 4. Import data
python scripts/import_data.py < data.json
```

## Health Checks

Both services should expose health endpoints:

**Backend**: `GET /health`
```json
{
  "status": "healthy",
  "database": "connected"
}
```

**Frontend**: `GET /api/health`
```json
{
  "status": "ok"
}
```

## Monitoring

### Backend Monitoring

Add to Railway/Render:
- CPU usage alerts
- Memory usage alerts
- Error rate monitoring
- API response time tracking

### Frontend Monitoring

Use Vercel Analytics (free):
```bash
# Add to package.json
npm install @vercel/analytics

# Add to app/layout.tsx
import { Analytics } from '@vercel/analytics/react'

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  )
}
```

## Scaling Considerations

### Backend Scaling

**Vertical Scaling** (Recommended first):
- Increase Railway instance size
- 512MB RAM → 1GB RAM (~$10/month)

**Horizontal Scaling** (If needed):
- Add load balancer
- Multiple FastAPI instances
- Shared PostgreSQL database

### Frontend Scaling

Vercel automatically handles this with CDN edge caching.

### Database Scaling

PostgreSQL on Railway:
- Starts at 256MB ($5/month)
- Scales to 8GB ($50/month)
- Connection pooling built-in

## Cost Estimates

### Hobby/Personal Project
- **Backend**: Railway Starter ($5/month)
- **Frontend**: Vercel Free Tier ($0/month)
- **Database**: Railway PostgreSQL ($5/month)
- **OpenAI API**: ~$5-20/month (depends on usage)
- **Total**: ~$15-30/month

### Production (100 users)
- **Backend**: Railway Pro ($20/month)
- **Frontend**: Vercel Pro ($20/month)
- **Database**: Railway PostgreSQL ($20/month)
- **OpenAI API**: ~$100-500/month (depends on usage)
- **Total**: ~$160-560/month

## Security Checklist

- [ ] Enable HTTPS (Railway/Vercel provide free SSL)
- [ ] Set CORS origins (don't use `*` in production)
- [ ] Rotate API keys monthly
- [ ] Use environment variables (never commit secrets)
- [ ] Enable rate limiting on backend
- [ ] Add authentication (T18 in backend)
- [ ] Set up monitoring/alerts
- [ ] Regular backups (Railway auto-backups enabled)

## Troubleshooting

### Frontend can't reach backend

1. Check NEXT_PUBLIC_API_URL is set correctly
2. Verify backend is running: `curl https://your-backend.railway.app/health`
3. Check CORS settings in backend allow your frontend domain

### Database connection fails

1. Verify DATABASE_URL is correct
2. Check PostgreSQL is running
3. Ensure database tables exist: `alembic upgrade head`

### OpenAI API errors

1. Check API key is valid
2. Verify billing is enabled on OpenAI account
3. Check rate limits haven't been exceeded

### High OpenAI costs

1. Implement caching for repeated analyses
2. Add user rate limiting
3. Consider batching requests
4. Monitor token usage with logging

## Backup Strategy

### Database Backups

Railway automatic backups:
- Daily snapshots (retained 7 days)
- Point-in-time recovery available

Manual backup:
```bash
pg_dump $DATABASE_URL > backup-$(date +%Y%m%d).sql
```

### Code Backups

Use Git + GitHub:
```bash
git remote add origin https://github.com/your-username/persona-evolution.git
git push -u origin main
```

## Rollback Procedure

If deployment fails:

### Railway
```bash
# List deployments
railway logs

# Rollback to previous
railway rollback
```

### Vercel
```bash
# View deployments
vercel ls

# Rollback
vercel rollback
```

## Next Steps

After successful deployment:

1. **Set up monitoring**: Add error tracking (Sentry)
2. **Enable analytics**: Track user behavior
3. **Add authentication**: Implement user accounts (T18)
4. **Create documentation**: API docs, user guide
5. **Marketing**: Share with therapy professionals, researchers

---

Need help? Check the documentation:
- Railway: https://docs.railway.app
- Vercel: https://vercel.com/docs
- FastAPI: https://fastapi.tiangolo.com
- Next.js: https://nextjs.org/docs
