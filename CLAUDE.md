# CLAUDE.md - Assistant Memory File

This file contains important information for Claude to remember across sessions.

## 🚨 DO ZROBIENIA - Następna sesja:

### ✅ ZROBIONE (2025-07-13):
1. **Tworzenie nowych agentów** - przycisk "Nowy Agent", modal z formularzem
2. **Usuwanie agentów** - przycisk "Usuń" przy każdym agencie
3. **Wybór domyślnego agenta** - radio button, zapisuje w settings

### 📋 POZOSTAŁO DO ZROBIENIA:

### 🔥 0. ZEP INTEGRATION (PRIORYTET!) - [2025-07-13 20:30]
- **WAŻNE**: Integracja z Zep Memory API w Playground
- **Plik z instrukcjami**: ZEP_INTEGRATION.md (szczegółowy guide)
- **Co to da**: Trzecie okienko do porównania Mem0 vs Zep
- **Czas**: 1-2 godziny
- **Railway**: Nati musi dodać ZEP_API_KEY

### 1. System logów w Admin Panel
- Viewer błędów Mem0 (z fire-and-forget)
- Statystyki performance
- Real-time monitoring
- Export logów

### 2. Ulepszenia UX (opcjonalne)
- Potwierdzenie przed usunięciem agenta
- Walidacja unikalności slug przy tworzeniu
- Lepsze komunikaty o błędach

### 📊 OPTYMALIZACJE DO ZROBIENIA:

#### 1. Łączenie API calls przy starcie chatu (30 min) 🚀
- **Pliki**: backend/main.py, frontend/src/Chat.tsx, frontend/src/api.ts
- **Problem**: 2 osobne zapytania przy starcie (getAgents + getSettings)
- **Rozwiązanie**: 
  - Nowy endpoint GET /api/init zwracający {agents, settings}
  - Jeden call w Chat.tsx zamiast dwóch
- **Implementacja**:
  ```python
  @app.get("/api/init")
  async def get_init_data(db: Session = Depends(get_db)):
      agents = db.query(Agent).filter(Agent.is_active == True).all()
      return {
          "agents": agents,
          "settings": system_settings
      }
  ```
  - W Chat.tsx: zamienić loadData() na jeden getInitData()
  - W api.ts: dodać `getInitData()` function

#### 2. Indeksy w bazie danych (30 min) 🗄️
- **Plik**: backend/database.py lub nowy endpoint migracyjny
- **Problem**: Brak indeksu na agents.slug (wolne wyszukiwanie)
- **Rozwiązanie**: 
  ```python
  # Dodać endpoint w agents.py:
  @agents_router.post("/migrate-indexes")
  async def add_indexes(db: Session = Depends(get_db)):
      db.execute(text("CREATE INDEX IF NOT EXISTS idx_agents_slug ON agents(slug)"))
      db.execute(text("CREATE INDEX IF NOT EXISTS idx_agents_is_active ON agents(is_active)"))
      db.commit()
  ```
- **Wykonać przez Admin Panel lub curl po deploy**

#### 3. Code splitting dla Admin Panel (1h) 📦
- **Pliki**: frontend/src/App.tsx
- **Problem**: Admin ładuje się dla wszystkich (niepotrzebne 200KB)
- **Rozwiązanie**: 
  ```typescript
  // Zamiast: import AdminNew from './AdminNew'
  const AdminNew = lazy(() => import('./AdminNew'))
  
  // W Route:
  <Suspense fallback={<div>Loading admin...</div>}>
    <AdminNew />
  </Suspense>
  ```
- **Podobnie dla**: Auth.tsx gdy user jest zalogowany

#### 4. Optymalizacja Mem0 - kolejka zadań (2-3h) 🧠
- **Pliki**: backend/memory_service.py, backend/chat.py
- **Problem**: Unlimited fire-and-forget tasks mogą zapchać serwer
- **Rozwiązanie kompleksowe**:
  ```python
  # memory_service.py
  import asyncio
  from functools import lru_cache
  from datetime import datetime, timedelta
  
  # Kolejka zadań
  memory_queue = asyncio.Queue(maxsize=10)
  
  # Cache dla search z TTL
  @lru_cache(maxsize=100)
  def cached_search(query_hash: str, user_id: str):
      # Zwraca (results, timestamp)
      pass
  
  # Worker do przetwarzania
  async def memory_worker():
      while True:
          task = await memory_queue.get()
          try:
              await add_memory_internal(task['messages'], task['user_id'])
          except Exception as e:
              logger.error(f"Memory worker error: {e}")
  
  # Zmodyfikowana funkcja add_memory
  async def add_memory(messages, user_id):
      try:
          await memory_queue.put({
              'messages': messages,
              'user_id': user_id
          }, timeout=1.0)
      except asyncio.QueueFull:
          logger.warning("Memory queue full, skipping save")
  ```
- **Startować worker w main.py przy starcie**

#### 5. Buforowanie React updates (1-2h) ⚛️
- **Plik**: frontend/src/Chat.tsx
- **Problem**: Re-render na każdy chunk (100+ razy na wiadomość)
- **Rozwiązanie krok po kroku**:
  ```typescript
  // 1. Bufor dla chunków
  const chunkBuffer = useRef('')
  const flushTimer = useRef<NodeJS.Timeout>()
  
  const flushBuffer = () => {
    if (chunkBuffer.current) {
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1].content += chunkBuffer.current
        return updated
      })
      chunkBuffer.current = ''
    }
  }
  
  // 2. W onChunk zamiast bezpośredniego update:
  chunkBuffer.current += chunk
  clearTimeout(flushTimer.current)
  flushTimer.current = setTimeout(flushBuffer, 100)
  
  // 3. React.memo dla wiadomości
  const Message = React.memo(({ message }) => (
    <div>...</div>
  ))
  ```

#### 6. Auto-reconnect SSE (2h) 🔄
- **Plik**: frontend/src/api.ts
- **Problem**: Połączenie pada = trzeba refresh
- **Rozwiązanie z retry logic**:
  ```typescript
  let retryCount = 0
  const maxRetries = 5
  
  const connectSSE = async () => {
    try {
      const eventSource = new EventSource(url)
      retryCount = 0 // Reset on success
      
      eventSource.onerror = () => {
        eventSource.close()
        if (retryCount < maxRetries) {
          const delay = Math.min(1000 * Math.pow(2, retryCount), 10000)
          setTimeout(connectSSE, delay)
          retryCount++
        }
      }
    } catch (error) {
      // Handle error
    }
  }
  ```
- **Dodać status indicator**: 🟢 Connected | 🟡 Reconnecting | 🔴 Offline

## Pracuję z Nati! 👋
Nati (Natalia Rybarczyk) jest vibecoderką i potrzebuje prostych wyjaśnień technicznych.

## WAŻNE: Praca zespołowa z Maciejem
- **ZAWSZE rozpocznij sesję od `git pull`** - Maciej może wprowadzać zmiany ze swojego komputera
- Po każdej sesji pushuj zmiany na git
- Workflow:
  ```bash
  # Na początku każdej sesji:
  git pull origin main
  
  # Po zakończeniu pracy:
  git add -A
  git commit -m "feat: opis zmian"
  git push origin main
  ```

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
- **Agents**: 7 agentów (misunderstanding_protector, emotional_vomit, solution_finder, conflict_solver, communication_simulator, relationship_upgrader, breakthrough_manager)

### Important Notes
- Frontend runs on port 8080 in Railway (not 3000)
- Backend needs proper DATABASE_URL to connect to PostgreSQL
- Agents are loaded from database, falls back to defaults if connection fails
- System ma 7 agentów (było 8, usunięto empathy_amplifier i attachment_analyzer)

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

## Memory System - RELATRIX v2.0 (2025-07-08)

### Architektura
- Używamy oficjalnego Mem0 AsyncMemoryClient
- Brak custom wrapperów - bezpośrednie API calls
- Cała logika w `memory_service.py` (30 linii!)

### Implementacja:
```python
# memory_service.py
from mem0 import AsyncMemoryClient

client = AsyncMemoryClient(api_key=settings.mem0_api_key)

async def search_memories(query: str, user_id: str):
    return await client.search(query=query, user_id=user_id)

async def add_memory(messages: list, user_id: str):
    return await client.add(messages=messages, user_id=user_id, version="v2")
```

### Co się zmieniło w v2.0 (2025-07-08 23:45):
- ✅ Całkowicie przepisane od zera
- ✅ Usunięto ~50 plików starej architektury
- ✅ Backend: 8 plików zamiast 30+
- ✅ Frontend: 5 plików zamiast 20+
- ✅ Brak Redis, brak cache'owania
- ✅ Agent switching przez JSON detection

### Status:
- ✅ AsyncMemoryClient zaimplementowany
- ⚠️ Brak logów z Mem0 (do debugowania)
- ⚠️ Agent switching nie przetestowane

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
- ⚠️ Mem0 nie pokazuje aktywności w logach (do debugowania)
- ⚠️ Agent switching nie przetestowane (do weryfikacji)

## RELATRIX v2.0 - Status (2025-07-08 23:45)

### 🎆 COMPLETE REWRITE - Ultra Clean Architecture!
- **Backend**: 8 plików (~600 linii) - FastAPI minimalistyczny
- **Frontend**: 5 plików (~500 linii) - React + TypeScript + Vite  
- **Deployment**: Działa na Railway!
- **Chat**: Działa z SSE streaming
- **Auth**: Działa (Supabase)

### Aktualne Problemy do Rozwiązania (2025-07-09)

#### 1. Mem0 Integration Debug
- **Problem**: Brak widocznej aktywności Mem0 w logach
- **Możliwe przyczyny**:
  - Mem0 działa ale nie loguje
  - User ID nie jest poprawnie przekazywany
  - API key problem
- **Do sprawdzenia**: Mem0 dashboard, logi, user_id flow

#### 2. Agent Switching Testing  
- **Problem**: Nie przetestowane czy działa
- **Implementacja**: JSON detection `{"agent": "slug_name"}`
- **Fallback**: GPT-3.5 dla wykrywania agenta
- **Do zrobienia**: Testy z różnymi promptami

### Architektura v2.0
```
backend/
├── main.py              # FastAPI app + routers
├── config.py            # Pydantic settings  
├── database.py          # SQLAlchemy + agents
├── auth.py              # Supabase auth
├── chat.py              # SSE streaming endpoint
├── agents.py            # Agents CRUD
├── memory_service.py    # Mem0 AsyncClient
└── agent_parser.py      # JSON detection

frontend/src/
├── App.tsx              # Router
├── Chat.tsx             # Main chat UI
├── Auth.tsx             # Login/Register
├── api.ts               # API client
└── index.tsx            # Entry point
```

## ⚠️ WAŻNE: Migracja bazy danych (2025-07-12)

### Po deploy dodaj kolumny do bazy:
1. Zaloguj się do admin panel
2. Otwórz konsolę przeglądarki (F12)
3. Wykonaj:
```javascript
fetch('https://relatrix-backend.up.railway.app/api/agents/migrate-model-columns', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('relatrix_access_token'),
    'Content-Type': 'application/json'
  }
}).then(r => r.json()).then(console.log)
```

Alternatywnie przez Railway PostgreSQL:
```sql
ALTER TABLE agents ADD COLUMN model VARCHAR(50) DEFAULT 'gpt-4-turbo-preview';
ALTER TABLE agents ADD COLUMN temperature FLOAT DEFAULT 0.7;
```

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