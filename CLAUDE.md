# CLAUDE.md - Assistant Memory File

This file contains important information for Claude to remember across sessions.

## Railway CLI Configuration

### Authentication
- **Account Token**: `8e1fd103-093b-4366-968e-289fc33e6ede`
- **Account Email**: biuro@nataliarybarczyk.pl
- **Account Name**: Natalia

### Project Information
- **Project Name**: RelatriX_v1
- **Organization**: Fidziu's Projects
- **Other Projects**: T2M Backend API, T2M Backoffice Django

### Usage
```bash
# Set the API token
export RAILWAY_API_TOKEN="8e1fd103-093b-4366-968e-289fc33e6ede"

# Verify authentication
railway whoami

# List all projects
railway list

# Check service logs
railway logs -s backend
railway logs -s frontend
railway logs -s postgres
railway logs -s redis

# View environment variables
railway variables -s backend
railway variables -s frontend

# Execute commands in service
railway run -s backend env
```

### Services in RelatriX_v1
- backend
- frontend
- postgres
- redis

## Project Structure

### Key Technologies
- **Backend**: FastAPI, Python, Multi-Agent Orchestrator
- **Frontend**: React, TypeScript, Tailwind CSS
- **Database**: PostgreSQL (Railway), Supabase (for agents)
- **Memory**: Mem0 Cloud API
- **AI**: OpenAI GPT-4
- **Cache**: Redis

### Important Notes
- Frontend runs on port 8080 in Railway (not 3000)
- Backend needs proper DATABASE_URL to connect to PostgreSQL
- Agents are loaded from database, falls back to defaults if connection fails

## Common Commands

### Git Commands
```bash
# Always run lint and typecheck before committing
npm run lint
npm run typecheck

# Commit with co-author
git commit -m "feat: Your message

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Development Workflow
1. Check todo list frequently with TodoRead
2. Update task status immediately when starting/completing
3. Test thoroughly before marking as complete
4. Always verify Railway deployments after pushing

## Environment Variables Needed

### Backend (Railway)
- DATABASE_URL (PostgreSQL connection)
- OPENAI_API_KEY
- MEM0_API_KEY
- MEM0_USER_ID
- SUPABASE_URL
- SUPABASE_ANON_KEY
- SUPABASE_SERVICE_ROLE_KEY
- REDIS_URL
- JWT_SECRET_KEY

### Frontend (Railway)
- REACT_APP_API_URL (set to backend URL)
- REACT_APP_SUPABASE_URL
- REACT_APP_SUPABASE_ANON_KEY