# Railway Configuration Guide

## Project Information
- **Project Name**: RelatriX_v1
- **Project ID**: f343e0db-3825-4fa9-a273-0b9ed7600771
- **Organization**: Fidziu's Projects
- **Environment**: production

## Services Configuration

### 1. relatrix-backend (Backend API)
- **Type**: Docker (Nixpacks)
- **Port**: 8080 (via $PORT)
- **URL**: https://relatrix-backend.up.railway.app
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check**: `/health`
- **Source**: `./backend`

### 2. frontend (React App)
- **Type**: Docker (Nixpacks)
- **Port**: 8080 (via $PORT)
- **URL**: https://relatrix-frontend.up.railway.app
- **Start Command**: `serve -s build -l ${PORT:-8080}`
- **Source**: `./frontend`

### 3. Postgres (Database)
- **Type**: Railway Postgres Plugin
- **Plan**: hobby
- **Internal URL**: postgres.railway.internal:5432
- **Database**: railway

### 4. redis (Cache)
- **Type**: Railway Redis Plugin
- **Plan**: hobby
- **Internal URL**: redis.railway.internal:6379

## Environment Variables

### Backend Service (relatrix-backend)

#### Database & Cache
```bash
DATABASE_URL                 # PostgreSQL connection string (auto-generated)
REDIS_URL                    # Redis connection string (auto-generated)
```

#### API Keys
```bash
OPENAI_API_KEY              # OpenAI API key for GPT-4
MEM0_API_KEY                # Mem0 memory service API key
MEM0_USER_ID                # Mem0 organization ID
```

#### Authentication
```bash
JWT_SECRET_KEY              # Secret for JWT tokens (auto-generated)
ADMIN_EMAIL                 # Admin login email
ADMIN_PASSWORD              # Admin login password
```

#### Supabase (Optional - not used yet)
```bash
SUPABASE_URL                # Supabase project URL
SUPABASE_ANON_KEY          # Supabase anonymous key
SUPABASE_SERVICE_ROLE_KEY   # Supabase service role key
```

#### Cost Management
```bash
MONTHLY_BUDGET_LIMIT        # Monthly budget cap (default: 100.0)
COST_ALERT_THRESHOLD        # Alert threshold % (default: 0.8)
```

#### Railway Auto-Generated
```bash
RAILWAY_ENVIRONMENT         # "production"
RAILWAY_PROJECT_ID          # Project UUID
RAILWAY_SERVICE_ID          # Service UUID
RAILWAY_PUBLIC_DOMAIN       # Public URL
RAILWAY_PRIVATE_DOMAIN      # Internal domain
PORT                        # Dynamic port assignment
```

### Frontend Service

```bash
REACT_APP_API_URL           # https://relatrix-backend.up.railway.app
REACT_APP_SUPABASE_URL      # Supabase URL (optional)
REACT_APP_SUPABASE_ANON_KEY # Supabase anon key (optional)
GENERATE_SOURCEMAP          # false (for production)
PORT                        # Dynamic port assignment
```

## Railway CLI Commands

### Setup
```bash
# Install CLI
npm install -g @railway/cli

# Login with API token
export RAILWAY_API_TOKEN="8e1fd103-093b-4366-968e-289fc33e6ede"

# Link to project
railway link -p f343e0db-3825-4fa9-a273-0b9ed7600771
```

### Common Commands
```bash
# View logs
railway logs -s relatrix-backend
railway logs -s frontend
railway logs -s Postgres
railway logs -s redis

# View variables
railway variables -s relatrix-backend

# Deploy
git push origin main  # Auto-deploys on push

# Run commands in service
railway run -s relatrix-backend env
```

## Deployment Configuration (railway.json)

```json
{
  "services": {
    "backend": {
      "source": "./backend",
      "deploy": {
        "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
        "healthcheckPath": "/health"
      }
    },
    "frontend": {
      "source": "./frontend",
      "deploy": {
        "startCommand": "npm run build && npx serve -s build -l $PORT"
      }
    }
  },
  "plugins": {
    "postgresql": { "plan": "hobby" },
    "redis": { "plan": "hobby" }
  }
}
```

## Important Notes

1. **Auto-Deploy**: Każdy push do `main` branch automatycznie deployuje
2. **Port Configuration**: Railway dynamicznie przypisuje PORT - zawsze używaj $PORT
3. **Internal Networking**: Serwisy komunikują się przez `.railway.internal` domains
4. **SSL/HTTPS**: Railway automatycznie zapewnia SSL dla public domains
5. **Logs Retention**: Logi są przechowywane przez 7 dni na planie hobby

## Troubleshooting

### Frontend nie ładuje się
- Sprawdź czy PORT jest ustawiony na 8080 w Dockerfile
- Verify REACT_APP_API_URL wskazuje na backend

### Backend nie łączy się z DB
- Check DATABASE_URL w variables
- Verify PostgreSQL service jest running

### Redis connection failed
- Check REDIS_URL format
- Ensure redis service jest aktywny

## Cost Optimization

1. **Sleep on Inactivity**: Services automatycznie usypiają po 10 min nieaktywności
2. **Resource Limits**: Hobby plan = 512MB RAM, 0.5 vCPU per service
3. **Database Size**: 1GB limit na hobby PostgreSQL
4. **Bandwidth**: 100GB/month included

## Security Best Practices

1. **Never commit secrets** - używaj Railway variables
2. **Rotate keys regularly** - szczególnie JWT_SECRET_KEY
3. **Use private networking** - dla internal communication
4. **Enable 2FA** - na Railway account
5. **Audit logs** - regularnie sprawdzaj logi