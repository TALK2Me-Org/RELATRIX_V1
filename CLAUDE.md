# CLAUDE.md - Assistant Memory File

This file contains important information for Claude to remember across sessions.

## Pracuję z Nati! 👋
Nati (Natalia Rybarczyk) jest vibecoderką i potrzebuje prostych wyjaśnień technicznych.

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

## Ważne pliki do śledzenia

### Przy każdej sesji sprawdzaj i aktualizuj:
1. **PROGRESS_TRACKER.md** - aktualizuj po każdym wykonanym zadaniu
2. **TASK_LIST.md** - sprawdzaj co do zrobienia (zawiera dokładny plan implementacji każdej fazy!)
3. **RAILWAY_CONFIG.md** - sprawdzaj konfigurację deploymentu
4. **ARCHITECTURE.md** - aktualizuj przy zmianach architektury

### Workflow:
1. Na początku sesji: przeczytaj PROGRESS_TRACKER.md
2. Sprawdź TASK_LIST.md co jest do zrobienia (szczególnie Task 4.2 dla autentykacji!)
3. Po wykonaniu zadania: natychmiast aktualizuj PROGRESS_TRACKER.md
4. Przy zmianach architektury: aktualizuj ARCHITECTURE.md
5. Używaj TodoWrite/TodoRead do śledzenia bieżących zadań

### Strefa czasowa:
- **ZAWSZE używaj czasu polskiego (Europe/Warsaw, UTC+1/UTC+2)**
- W PROGRESS_TRACKER.md i innych dokumentach timestamp w formacie: `[YYYY-MM-DD HH:MM PL]`

## Memory Modes System

### Overview
RELATRIX używa 4 trybów pracy pamięci, które balansują między kosztami i dokładnością:

1. **Cache First** (domyślny) - Minimalne koszty, 1 retrieval per sesja
2. **Always Fresh** - Maksymalna dokładność, retrieval per wiadomość  
3. **Smart Triggers** - Balans, retrieval przy triggerach
4. **Test Mode** - Testowanie z pełnym logowaniem

### API Endpoints
```bash
# Set memory mode
POST /api/memory/mode
{
  "mode": "smart_triggers",
  "use_preset": "balanced"  # lub custom_config
}

# Get current mode
GET /api/memory/mode?session_id=xxx

# Get metrics
GET /api/memory/metrics/{session_id}

# Clear cache
POST /api/memory/cache/clear
```

### Monitoring
- Sprawdzaj metryki: cache hit rate, koszt per sesja, triggery
- W Test Mode wszystko jest logowane dla analizy
- Smart Triggers konfigurowalne per sesja

## System Autoryzacji (DZIAŁA!)

### Status: ✅ W pełni działający
- Backend: Supabase Auth + JWT
- Frontend: React Context + localStorage
- Tokeny: 'relatrix_access_token' i 'relatrix_refresh_token'
- Email verification: Wymaga potwierdzenia (link w mailu)

### Testowanie autoryzacji:
```bash
# Rejestracja (wymaga prawdziwego emaila, nie @example.com)
curl -X POST https://relatrix-backend.up.railway.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@gmail.com", "password": "test123456"}'

# Logowanie (po potwierdzeniu emaila)
curl -X POST https://relatrix-backend.up.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@gmail.com", "password": "test123456"}'

# Test z tokenem
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://relatrix-backend.up.railway.app/api/memory/mode
```

### Known Issues:
- Email verification links odnoszą się do localhost (do naprawy w Supabase Dashboard)
- Mem0 nie jest aktywne mimo że user_id jest przekazywany

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

## Developer Tools

### Katalog _dev_tools/
Zawiera tymczasowe skrypty używane podczas development:
- Skrypty migracyjne (test_db_migration.py, simple_migration.py, etc.)
- Narzędzia pomocnicze które mogą się przydać w przyszłości
- NIE commitować do repozytorium (dodane do .gitignore)

Jeśli potrzebujesz wykonać migrację, użyj:
1. HTTP endpoint: `POST /api/admin/run-memory-modes-migration-v2`
2. Lub skryptów z _dev_tools/ jako wzorca

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