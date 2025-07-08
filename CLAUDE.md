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

### WAŻNE: Zasady edycji dokumentów MD:
- **NIGDY nie usuwaj** zawartości z PROGRESS_TRACKER.md, TASK_LIST.md, ARCHITECTURE.md
- **Tylko dodawaj** nowe wpisy lub **zmieniaj status** (np. z ❌ na ✅)
- Używaj ~~przekreślenia~~ żeby oznaczyć że coś jest nieaktualne
- Dodawaj datę przy statusie: [2025-MM-DD HH:MM PL]

### Strefa czasowa:
- **ZAWSZE używaj czasu polskiego (Europe/Warsaw, UTC+1/UTC+2)**
- W PROGRESS_TRACKER.md i innych dokumentach timestamp w formacie: `[YYYY-MM-DD HH:MM PL]`

## Memory System - "Mem0 Native" (Uproszczone 2025-07-08)

### Filozofia
Mem0 v2 sam zarządza całą złożonością - my tylko przekazujemy dane.

### Jak to działa:
```python
# Przy każdej wiadomości:
1. Jeśli user zalogowany - pobierz wspomnienia:
   memories = memory.search(user_message, user_id)

2. Wyślij do OpenAI minimalny kontekst:
   - System prompt agenta
   - Wspomnienia z Mem0 (jeśli są)
   - Aktualna wiadomość użytkownika

3. Po odpowiedzi zapisz do Mem0:
   memory.add([user_msg, assistant_msg], user_id)
```

### Co się zmieniło (2025-07-08):
- ✅ Usunięto całą logikę Memory Modes
- ✅ memory.py: 650 → 201 linii (-70%)
- ✅ Brak cache'owania kontekstu w Redis
- ✅ Mem0 v2 automatycznie zarządza kontekstem
- ✅ Niższe koszty - wysyłamy minimum tokenów

### Status Mem0:
- ✅ Używamy Mem0 v2 API (version="v2")
- ✅ Async mode włączony (nie blokuje odpowiedzi)
- ✅ Każda para wiadomości zapisywana osobno
- ✅ Mem0 sam decyduje co jest ważne

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
- 🔴 Mem0 v1 aktualizuje oryginalne wspomnienia - konieczna migracja do v2 API!
- Rozwiązanie: Dodać version="v2" do wszystkich wywołań Mem0

## Aktualny Problem do Rozwiązania (2025-07-08)

### Mem0 Async Integration
- **Problem 1**: Mem0 client jest synchroniczny - blokuje całą aplikację
- **Problem 2**: Mem0 add() zwraca `{'results': []}` - nic nie zapisuje
- **Problem 3**: Chat jest wolny przez synchroniczne wywołania Mem0
- **Rozwiązanie**: Implementacja AsyncMem0Client używając httpx
- **Lokalizacja**: backend/app/orchestrator/orchestrator.py
- **Szczegóły**: Zobacz MEM0_ASYNC_PLAN.md

### Stan po uproszczeniu (2025-07-08):
- Usunięto ~700 linii kodu
- Bezpośrednie użycie Mem0 i OpenAI API
- Brak warstw abstrakcji
- memory.py i transfer.py usunięte
- orchestrator.py: 384 → 164 linii

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