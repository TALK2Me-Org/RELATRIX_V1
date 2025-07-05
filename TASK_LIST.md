# RELATRIX - Task List Implementation Plan

## ⚠️ WAŻNE INSTRUKCJE DLA CLAUDE CODE ⚠️

**UWAGA: Pracujesz z VIBECODERKĄ (nie programistą)!**

### Kiedy prosić o pomoc zewnętrzną:
- **Railway setup** - nowy projekt, konfiguracja services
- **API keys** - rejestracja w zewnętrznych serwisach (OpenAI, Mem0, Supabase)
- **Domain setup** - konfiguracja domen i SSL
- **Payment setup** - konfiguracja płatności w serwisach
- **External service configuration** - ustawienia które wymagają logowania do dashboardów

### Format prośby o pomoc:
```
🚨 POTRZEBUJĘ POMOCY VIBECODERKI:
[Opisz dokładnie co trzeba zrobić]
[Podaj linki i instrukcje krok po kroku]
[Wyjaśnij dlaczego Claude nie może tego zrobić sam]
```

### Co Claude robi SAM:
- Pisanie kodu
- Tworzenie plików konfiguracyjnych
- Dokumentacja
- Testy
- Wszystko co nie wymaga logowania do zewnętrznych serwisów

---

## FAZA 1: SETUP & INFRASTRUCTURE 🏗️

### Task 1.1: Project Structure & Environment
**Polecenie dla Claude Code:**
```
Stwórz podstawową strukturę projektu RELATRIX zgodnie z planem:
- Utwórz wszystkie główne foldery (backend, mcp_server, frontend, docs)
- Stwórz .gitignore, .env.example, README.md
- Dodaj requirements.txt z wszystkimi zależnościami
- Stwórz package.json dla frontendu
```
**Oczekiwany rezultat:** Kompletna struktura folderów i podstawowe pliki konfiguracyjne

### Task 1.2: Docker & Railway Configuration
**Polecenie dla Claude Code:**
```
Stwórz konfigurację deployment:
- docker-compose.yml dla local development
- railway.json dla Railway deployment
- redis_config.py dla Redis setup
- Skonfiguruj wszystkie services (PostgreSQL, Redis, Backend, MCP, Frontend)
```
**⚠️ UWAGA:** Po stworzeniu railway.json, Claude poprosi vibecoderkę o setup Railway projektu
**Oczekiwany rezultat:** Gotowe środowisko development i deployment config

### Task 1.3: Basic Configuration Files
**Polecenie dla Claude Code:**
```
Zaimplementuj backend/app/config.py:
- Supabase configuration (URL, keys) - placeholder values
- OpenAI API settings - placeholder values
- Mem0 API configuration - placeholder values
- Redis connection settings
- Railway environment variables
- Admin panel settings
```
**⚠️ UWAGA:** Claude stworzy config z placeholderami, potem poprosi vibecoderkę o API keys
**Oczekiwany rezultat:** Centralna konfiguracja aplikacji

---

## FAZA 2: CORE MCP SERVER 🤖

### Task 2.1: MCP Server Foundation
**Polecenie dla Claude Code:**
```
Stwórz mcp_server/server.py:
- Podstawowy MCP server z agent registry
- Session management dla conversations
- Agent switching logic
- Integration z OpenAI API
- Error handling i logging
```
**Oczekiwany rezultat:** Działający MCP server gotowy na agentów

### Task 2.2: Transfer Protocols System
**Polecenie dla Claude Code:**
```
Zaimplementuj mcp_server/transfer_protocols.py:
- TRANSFER_TRIGGERS dictionary z wszystkimi wzorcami
- Parsing logic dla transfer commands
- Handoff protocol structure
- Agent switching mechanisms
- Context preservation podczas transferów
```
**Oczekiwany rezultat:** System rozpoznawania i obsługi transfer triggers

### Task 2.3: Memory Manager (Mem0 + Redis)
**Polecenie dla Claude Code:**
```
Stwórz mcp_server/memory_manager.py:
- Mem0 API client integration
- Redis caching layer
- Context optimization dla token savings
- Memory categorization (relationship patterns, communication styles)
- Cost optimization strategies
```
**Oczekiwany rezultat:** Inteligentne zarządzanie pamięcią i kontekstem

### Task 2.4: MCP Tools Implementation
**Polecenie dla Claude Code:**
```
Zaimplementuj mcp_server/tools.py:
- Agent switching tool
- Memory retrieval/storage tools
- Session management tools
- Telemetry collection tools
- User notification tools
```
**Oczekiwany rezultat:** Kompletny zestaw narzędzi dla agentów

---

## FAZA 3: SPECIALIZED AGENTS 🎭

### Task 3.1: Misunderstanding Protector Agent
**Polecenie dla Claude Code:**
```
Stwórz mcp_server/agents/misunderstanding_agent.py:
- System prompt z 4-card analysis instructions
- Transfer triggers do innych agentów
- Logic dla detecting communication issues
- Integration z memory manager
- Response formatting dla 4 kolorowych kart
```
**Oczekiwany rezultat:** Pierwszy działający agent z transfer capabilities

### Task 3.2: Emotional Vomit Dumper Agent
**Polecenie dla Claude Code:**
```
Zaimplementuj mcp_server/agents/emotional_vomit_agent.py:
- System prompt dla emotional release
- Ephemeral processing (no memory storage)
- Transfer triggers gdy user jest ready
- Calming techniques i emotional regulation
- Privacy-first approach
```
**Oczekiwany rezultat:** Agent do bezpiecznego emotional dumping

### Task 3.3: Conflict Solver Agent
**Polecenie dla Claude Code:**
```
Stwórz mcp_server/agents/conflict_solver_agent.py:
- System prompt dla mediation
- Partner readiness assessment
- Separate conversation management
- Transfer triggers po resolution
- Session state tracking
```
**Oczekiwany rezultat:** Mediator agent dla conflict resolution

### Task 3.4: Solution Finder Agent
**Polecenie dla Claude Code:**
```
Zaimplementuj mcp_server/agents/solution_finder_agent.py:
- System prompt dla action planning
- Concrete plan generation
- Progress tracking capabilities
- Transfer triggers dla implementation issues
- Integration z plan storage
```
**Oczekiwany rezultat:** Agent tworzący actionable plans

### Task 3.5: Communication Simulator Agent
**Polecenie dla Claude Code:**
```
Stwórz mcp_server/agents/communication_simulator_agent.py:
- System prompt dla conversation practice
- Partner simulation based on context
- Feedback generation
- Scenario management
- Skill development tracking
```
**Oczekiwany rezultat:** Training agent dla communication skills

### Task 3.6: Relationship Upgrader Agent
**Polecenie dla Claude Code:**
```
Zaimplementuj mcp_server/agents/relationship_upgrader_agent.py:
- System prompt dla relationship enhancement
- Challenge i ritual generation
- Gamification elements
- Progress celebration
- Transfer triggers dla detected issues
```
**Oczekiwany rezultat:** Agent do relationship improvement

### Task 3.7: Breakthrough Manager Agent
**Polecenie dla Claude Code:**
```
Stwórz mcp_server/agents/breakthrough_manager_agent.py:
- System prompt dla crisis management
- Breakup support protocols
- Decision-making assistance
- Recovery planning
- Sensitive situation handling
```
**Oczekiwany rezultat:** Crisis support agent

---

## FAZA 4: BACKEND API & DATABASE 💾

### Task 4.1: Database Models
**Polecenie dla Claude Code:**
```
Zaimplementuj backend/app/models.py:
- User model (minimal for Supabase sync)
- ConversationLog model dla backup
- AdminSettings model
- UsageMetrics model dla telemetry
- Alembic migration setup
```
**Oczekiwany rezultat:** Database schema i models

### Task 4.2: Supabase Authentication
**Polecenie dla Claude Code:**
```
Stwórz backend/app/auth.py:
- Supabase client initialization
- User registration/login endpoints
- Token validation middleware
- Session management
- Admin authentication
```
**⚠️ UWAGA:** Claude użyje placeholder Supabase keys, potem poprosi vibecoderkę o setup Supabase projektu
**Oczekiwany rezultat:** Kompletna autoryzacja przez Supabase

### Task 4.3: Main FastAPI Application
**Polecenie dla Claude Code:**
```
Zaimplementuj backend/app/main.py:
- FastAPI app initialization
- CORS middleware
- Router registration
- Health check endpoints
- MCP server integration
- Error handling
```
**Oczekiwany rezultat:** Działający backend API

### Task 4.4: Chat API Endpoints
**Polecenie dla Claude Code:**
```
Stwórz backend/app/chat_api.py:
- WebSocket endpoint dla real-time chat
- REST endpoints dla message history
- Integration z MCP server
- Session management
- Message validation
```
**Oczekiwany rezultat:** API do komunikacji z agentami

### Task 4.5: Telemetry System
**Polecenie dla Claude Code:**
```
Zaimplementuj backend/app/telemetry.py:
- Usage tracking dla każdego agent interaction
- Cost monitoring (OpenAI + Mem0)
- Performance metrics
- User behavior analytics
- Alert system dla budget thresholds
```
**Oczekiwany rezultat:** Kompletny system monitorowania

---

## FAZA 5: FRONTEND & ADMIN PANEL 🖥️

### Task 5.1: Basic Chat Interface
**Polecenie dla Claude Code:**
```
Stwórz frontend/src/pages/chat.tsx:
- Simple chat UI z message bubbles
- WebSocket connection
- Agent indicator
- Message history
- Real-time typing indicators
- Mobile-responsive design
```
**Oczekiwany rezultat:** Działający chat interface do testów

### Task 5.2: Chat Components
**Polecenie dla Claude Code:**
```
Zaimplementuj frontend/src/components/ChatInterface.tsx:
- Reusable chat component
- Message formatting
- Agent switching indicators
- File upload support
- Accessibility features
```
**Oczekiwany rezultat:** Reusable chat components

### Task 5.3: API Service Layer
**Polecenie dla Claude Code:**
```
Stwórz frontend/src/services/api.ts:
- Axios configuration
- Supabase auth integration
- Chat API endpoints
- WebSocket management
- Error handling
- Type definitions
```
**Oczekiwany rezultat:** Type-safe API layer

### Task 5.4: Admin Dashboard
**Polecenie dla Claude Code:**
```
Zaimplementuj frontend/src/pages/admin/dashboard.tsx:
- Real-time metrics display
- Cost monitoring charts
- User activity overview
- Agent performance metrics
- System health indicators
```
**Oczekiwany rezultat:** Comprehensive admin dashboard

### Task 5.5: Admin User Management
**Polecenie dla Claude Code:**
```
Stwórz frontend/src/pages/admin/users.tsx:
- User list z search/filtering
- Individual user profiles
- Usage statistics per user
- Account management actions
- Conversation history access
```
**Oczekiwany rezultat:** User management interface

### Task 5.6: Admin Settings Panel
**Polecenie dla Claude Code:**
```
Zaimplementuj frontend/src/pages/admin/settings.tsx:
- API key management
- System configuration
- Cost thresholds setup
- Agent prompt management
- Security settings
```
**Oczekiwany rezultat:** System configuration interface

### Task 5.7: Admin API Endpoints
**Polecenie dla Claude Code:**
```
Stwórz backend/app/admin_api.py:
- User management endpoints
- Analytics data endpoints
- System configuration API
- Cost monitoring endpoints
- Agent performance metrics
```
**Oczekiwany rezultat:** Complete admin API

---

## FAZA 6: TESTING & DEPLOYMENT 🚀

### Task 6.1: Basic Testing Setup
**Polecenie dla Claude Code:**
```
Stwórz backend/tests/test_mcp_server.py:
- Unit tests dla MCP server
- Agent switching tests
- Transfer trigger parsing tests
- Memory manager tests
- Integration tests z OpenAI API (mock)
```
**Oczekiwany rezultat:** Basic test coverage

### Task 6.2: Documentation
**Polecenie dla Claude Code:**
```
Stwórz dokumentację w docs/:
- docs/agent-architecture.md
- docs/transfer-triggers-examples.md
- docs/memory-optimization.md
- docs/deployment-railway.md
- API documentation
```
**Oczekiwany rezultat:** Complete project documentation

### Task 6.3: Railway Deployment Preparation
**Polecenie dla Claude Code:**
```
Przygotuj deployment na Railway:
- Sprawdź railway.json configuration
- Setup environment variables template
- Database migration scripts
- Health check endpoints
- Monitoring setup
```
**🚨 POTRZEBUJĘ POMOCY VIBECODERKI:**
- Stworzenie nowego projektu Railway
- Konfiguracja PostgreSQL i Redis services
- Upload environment variables
- Deploy aplikacji
**Oczekiwany rezultat:** Ready for production deployment

### Task 6.4: External Services Setup
**🚨 POTRZEBUJĘ POMOCY VIBECODERKI:**

**OpenAI API:**
1. Idź na https://platform.openai.com/
2. Stwórz konto/zaloguj się
3. Idź do API Keys
4. Stwórz nowy API key
5. Skopiuj key do Railway environment variables jako OPENAI_API_KEY

**Mem0 API:**
1. Idź na https://mem0.ai/
2. Stwórz konto
3. Idź do dashboard
4. Skopiuj API key i User ID
5. Dodaj do Railway jako MEM0_API_KEY i MEM0_USER_ID

**Supabase:**
1. Idź na https://supabase.com/
2. Stwórz nowy projekt
3. Skopiuj Project URL i anon key
4. Dodaj do Railway jako SUPABASE_URL i SUPABASE_ANON_KEY
5. Skopiuj service role key jako SUPABASE_SERVICE_ROLE_KEY

### Task 6.5: End-to-End Testing
**Polecenie dla Claude Code:**
```
Przetestuj complete flow:
- User registration przez Supabase
- Chat conversation z agent switching
- Memory persistence przez Mem0
- Admin panel functionality
- Cost tracking i telemetry
```
**Oczekiwany rezultat:** Fully tested system

---

## INSTRUKCJE UŻYCIA:

1. **Wykonuj taski sekwencyjnie** - każdy task buduje na poprzednich
2. **Claude robi wszystko SAM** - oprócz zewnętrznych serwisów
3. **Gdy Claude prosi o pomoc** - wykonaj dokładnie instrukcje
4. **Testuj po każdej fazie** - upewnij się że wszystko działa
5. **Używaj konkretnych poleceń** - kopiuj polecenia dla Claude Code dokładnie

## PRZYKŁAD UŻYCIA:
```
Claude Code, wykonaj Task 1.1:
Stwórz podstawową strukturę projektu RELATRIX zgodnie z planem:
- Utwórz wszystkie główne foldery (backend, mcp_server, frontend, docs)
- Stwórz .gitignore, .env.example, README.md
- Dodaj requirements.txt z wszystkimi zależnościami
- Stwórz package.json dla frontendu
```

**Status Tracking:**
- [ ] Faza 1: Setup & Infrastructure
- [ ] Faza 2: Core MCP Server  
- [ ] Faza 3: Specialized Agents
- [ ] Faza 4: Backend API & Database
- [ ] Faza 5: Frontend & Admin Panel
- [ ] Faza 6: Testing & Deployment