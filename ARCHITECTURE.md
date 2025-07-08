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
└── memory.py          # Prosta integracja z Mem0 v2 (201 linii)
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

### Memory Architecture - "Mem0 Native" (Uproszczone 2025-07-08)

**Filozofia: Let Mem0 handle all the complexity**

1. **Mem0 v2** (główna pamięć)
   - Automatyczne zarządzanie kontekstem
   - Inteligentne wybieranie wspomnień
   - Zapisywanie każdej pary (user + assistant)
   - Używamy: version="v2", async_mode=True

2. **Redis** (tylko session state)
   - Tymczasowe dane sesji (24h TTL)
   - NIE cache'ujemy kontekstu
   - Minimalne wykorzystanie

**Prosty flow:**
```python
# Przy każdej wiadomości:
1. Pobierz wspomnienia: memory.search(query, user_id)
2. Wyślij do OpenAI: [system_prompt, memories, user_message]
3. Zapisz do Mem0: memory.add([user, assistant], user_id)
```

**Co usunęliśmy:**
- ❌ 4 Memory Modes (CACHE_FIRST, ALWAYS_FRESH, etc.)
- ❌ Smart Triggers (message count, time, emotions)
- ❌ Metryki i cache'owanie kontekstu
- ❌ 11 metod w memory.py
- ❌ API endpointy /api/memory/*

**Rezultat:**
- memory.py: 650 → 201 linii (-70%)
- Tylko 5 metod: initialize, add, search, save/load_session_state
- Niższe koszty (mniej tokenów do OpenAI)
- Lepsza jakość (Mem0 v2 wybiera najlepszy kontekst)

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
   - Mem0 używa przestarzałego v1 API - konieczna migracja do v2
   - v1 aktualizuje oryginalne wspomnienia zamiast je zachowywać

## Known Issues & Workarounds

### 1. Duplicate Configuration Files
**Problem**: Istnieją dwa pliki konfiguracyjne:
- `app/config.py` - używany przez agent_service.py i main.py
- `app/core/config.py` - używany przez inne moduły

**Rozwiązanie**: Docelowo należy ujednolicić do jednego pliku, ale wymaga to refaktoryzacji importów.

### 2. Authentication Dependencies
**Problem**: System autentykacji wymaga dodatkowych pakietów:
- `PyJWT` - dla tokenów JWT (używany w core/security.py)
- `email-validator` - dla walidacji EmailStr w Pydantic

**Rozwiązanie**: Dodane do requirements.txt. Przy używaniu EmailStr w nowych modułach upewnij się że email-validator jest zainstalowany.

### 3. Supabase JWT Configuration
**Problem**: Używamy dwóch różnych sekretów JWT:
- `jwt_secret_key` - dla własnych tokenów
- `supabase_jwt_secret` - dla weryfikacji tokenów Supabase

**Rozwiązanie**: Upewnij się że oba są poprawnie skonfigurowane w Railway.

## Future Improvements

1. **🔴 PILNE: Migracja Mem0 do v2 API**
   - Dodać version="v2" do wszystkich wywołań
   - v2 automatycznie zarządza kontekstem
   - Rozwiąże problem aktualizowania wspomnień

2. **Implementacja transfer logic**
   - Regex matching dla triggers
   - Inteligentne przełączanie kontekstu

3. **Pełna integracja Mem0 v2**
   - Długoterminowa pamięć z właściwym kontekstem
   - Cross-session insights

3. **Admin panel**
   - Zarządzanie agentami
   - Monitoring kosztów
   - Analytics

4. **Enhanced security**
   - Supabase auth
   - Rate limiting
   - Request validation