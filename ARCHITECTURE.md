# RELATRIX Architecture Documentation

## System Overview

RELATRIX to wieloagentowy system AI do terapii relacji, wykorzystujący 7 wyspecjalizowanych agentów którzy automatycznie się przełączają w zależności od kontekstu rozmowy.

## High-Level Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                        User Browser                             │
│                    (React + TypeScript)                         │
└───────────────────────────┬────────────────────────────────────┘
                            │ HTTPS
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                    Railway Load Balancer                        │
└───────────────────────────┬────────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌─────────────────┐                    ┌─────────────────┐
│    Frontend     │                    │     Backend     │
│   (Railway)     │                    │    (Railway)    │
│   PORT: 8080    │───────SSE─────────▶│   PORT: 8080    │
└─────────────────┘                    └────────┬────────┘
                                               │
                    ┌──────────────────────────┼──────────────────┐
                    │                          │                  │
                    ▼                          ▼                  ▼
            ┌──────────────┐          ┌──────────────┐   ┌──────────────┐
            │  PostgreSQL  │          │    Redis     │   │  External    │
            │  (Railway)   │          │  (Railway)   │   │   APIs       │
            │              │          │              │   │              │
            │ - agents     │          │ - sessions   │   │ - OpenAI     │
            │ - sessions   │          │ - cache      │   │ - Mem0       │
            │ - transfers  │          │              │   │              │
            └──────────────┘          └──────────────┘   └──────────────┘
```

## Component Details

### Frontend (React Application)

**Główne komponenty:**
- `ChatInterface.tsx` - UI czatu z agentami
- `api.ts` - Warstwa komunikacji z backendem

**Technologie:**
- React 18 + TypeScript
- Tailwind CSS dla stylów
- Server-Sent Events (SSE) dla streamingu

**Flow:**
1. User pisze wiadomość
2. Frontend wysyła POST do `/api/chat/stream`
3. Odbiera stream odpowiedzi przez SSE
4. Wyświetla w real-time

### Backend (FastAPI + Multi-Agent Orchestrator)

**Struktura Orchestratora:**
```
orchestrator/
├── orchestrator.py    # Główny kontroler
├── registry.py        # Zarządzanie agentami
├── streaming.py       # SSE streaming
├── transfer.py        # Logika przełączania (TODO)
└── memory.py          # Pamięć krótko i długoterminowa
```

**Flow przetwarzania wiadomości:**
1. **Receive** → `/api/chat/stream` endpoint
2. **Session** → Orchestrator sprawdza/tworzy sesję
3. **Agent** → Registry wybiera aktualnego agenta
4. **Memory** → Ładuje kontekst z Redis/Mem0
5. **Process** → Wysyła do OpenAI z system prompt
6. **Stream** → Streamuje odpowiedź do frontendu
7. **Transfer?** → Sprawdza czy przełączyć agenta
8. **Save** → Zapisuje do pamięci

### Agent Registry

**Jak działają agenci:**
```python
class Agent:
    id: UUID
    slug: str                    # np. "misunderstanding_protector"
    name: str                    # np. "Misunderstanding Protector"
    system_prompt: str           # Instrukcje dla GPT-4
    transfer_triggers: List[str] # Frazy wyzwalające transfer
    openai_model: str           # "gpt-4-turbo-preview"
    temperature: float          # 0.7
```

**7 Agentów w systemie:**
1. **Misunderstanding Protector** - Wykrywa nieporozumienia
2. **Empathy Amplifier** - Wzmacnia empatię  
3. **Conflict Solver** - Mediator konfliktów
4. **Solution Finder** - Tworzy plany działania
5. **Communication Simulator** - Trening rozmów
6. **Attachment Analyzer** - Analiza wzorców przywiązania
7. **Relationship Upgrader** - Ulepszanie relacji

### Transfer Logic (⚠️ NIE ZAIMPLEMENTOWANE)

**Planowany flow:**
```python
# W transfer.py
def check_transfer_triggers(message: str, current_agent: Agent):
    for trigger in current_agent.transfer_triggers:
        if re.search(trigger, message, re.IGNORECASE):
            # Znajdź target agent
            # Wykonaj transfer
            return TransferEvent(...)
```

**Przykład transfer triggers:**
- "ready for solutions" → Solution Finder
- "need to practice" → Communication Simulator
- "too emotional" → Empathy Amplifier

### Memory Architecture

**Dwupoziomowa pamięć z 4 trybami pracy:**

1. **Redis** (krótkoterminowa)
   - Cache sesji z konfiguralnym TTL
   - Stan konwersacji
   - Szybki dostęp bez dodatkowych kosztów

2. **Mem0 API** (długoterminowa)
   - Historia relacji
   - Wzorce zachowań
   - Insights między sesjami

**Memory Modes:**
- **Cache First**: Minimalne koszty, 1 retrieval per sesja
- **Always Fresh**: Maksymalna dokładność, retrieval per wiadomość
- **Smart Triggers**: Balans - retrieval przy ważnych eventach
- **Test Mode**: Porównanie wydajności wszystkich trybów

**Smart Triggers** (konfigurowalne):
- Co N wiadomości
- Po X minutach
- Przy zmianie agenta
- Przy skoku emocji (keywords)
- Przy zmianie tematu
- Przy ważnych informacjach (decyzje)

**Memory Modes Implementation**:
```python
# W memory.py
- set_global_mode() - ustaw tryb globalny
- set_session_mode() - ustaw tryb dla sesji
- should_refresh_memory() - sprawdź triggery
- retrieve_user_context() - pobierz z cache/Mem0
- Metryki: cache hits, koszty, czas

# API endpoints (/api/memory)
- POST /mode - ustaw tryb
- GET /mode - pobierz konfigurację
- GET /metrics/{session_id} - metryki sesji
- POST /cache/clear - wyczyść cache
- GET /modes - lista trybów
```

### Database Schema

```sql
-- Agenci
agents (
    id UUID PRIMARY KEY,
    slug VARCHAR(50) UNIQUE,
    name VARCHAR(100),
    system_prompt TEXT,
    transfer_triggers JSONB,
    ...
)

-- Sesje
chat_sessions (
    id UUID PRIMARY KEY,
    user_id UUID,
    current_agent_slug VARCHAR(50),
    context JSONB,
    ...
)

-- Historia transferów
agent_transfers (
    id UUID PRIMARY KEY,
    session_id UUID,
    from_agent_slug VARCHAR(50),
    to_agent_slug VARCHAR(50),
    reason TEXT,
    ...
)
```

## Security & Performance

### Security
- JWT tokens dla autoryzacji (podstawowa)
- CORS skonfigurowany dla Railway domains
- Environment variables dla secretów
- SQL injection protection (SQLAlchemy)

### Performance
- Agent registry cache w pamięci
- Redis dla szybkiego dostępu do sesji
- Streaming responses (brak buforowania)
- Connection pooling do PostgreSQL

## Deployment Architecture

### Railway Services
1. **relatrix-backend** - FastAPI aplikacja
2. **frontend** - React build serwowany przez Node
3. **Postgres** - Managed PostgreSQL
4. **redis** - Managed Redis

### Environment Variables
```
# Backend
DATABASE_URL          # PostgreSQL connection
REDIS_URL            # Redis connection  
OPENAI_API_KEY       # GPT-4 access
MEM0_API_KEY         # Memory API
JWT_SECRET_KEY       # Auth tokens

# Frontend
REACT_APP_API_URL    # Backend URL
```

## Known Limitations

1. **Brak automatycznego przełączania agentów**
   - Transfer logic niezaimplementowana
   - Agenci nie reagują na trigger phrases

2. **Podstawowa autoryzacja**
   - Brak integracji z Supabase
   - Prosty JWT bez refresh tokens

3. **Brak telemetrii**
   - Nie śledzimy kosztów OpenAI
   - Brak metryk użycia

4. **Memory limitations**
   - Mem0 niezarejestrowane
   - Tylko Redis cache działa

## Future Improvements

1. **Implementacja transfer logic**
   - Regex matching dla triggers
   - Inteligentne przełączanie kontekstu

2. **Pełna integracja Mem0**
   - Długoterminowa pamięć
   - Cross-session insights

3. **Admin panel**
   - Zarządzanie agentami
   - Monitoring kosztów
   - Analytics

4. **Enhanced security**
   - Supabase auth
   - Rate limiting
   - Request validation