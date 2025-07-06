# RELATRIX Admin Panel Specification

## Overview
Panel administracyjny do zarządzania systemem RELATRIX, monitorowania wydajności i testowania agentów AI.

## Funkcjonalności

### 🎯 1. Dashboard – Skróty i KPI

#### Kluczowe wskaźniki:
- 🧑‍🤝‍🧑 Liczba wszystkich użytkowników / aktywnych w ciągu 24h
- 💬 Liczba wiadomości (24h / 7 dni)
- ⏱️ Średnia długość sesji
- 🧠 Zużycie tokenów in/out (per model) / per user / per sesja
- 💰 Koszt API OpenAI / Claude (dzienny i miesięczny)
- 💸 Koszt Mem0
- 🧪 Najczęściej uruchamiane modele / ilość uruchomień

#### Widoki:
- Top 100 userów (według aktywności)
- Wykresy trendów (liniowe 7/30 dni)
- Real-time monitoring aktywnych sesji

---

### 👩‍❤️‍👨 2. Kartoteki Użytkowników

#### Co zawiera każda kartoteka:

**Dane użytkownika:**
- Wiek, płeć, lokalizacja (wyciągane z rozmów)
- Status relacji (w związku / po rozwodzie / singiel)
- Liczba dzieci
- Typ subskrypcji (darmowa / PRO)
- Email, login, imię

**Historia relacji:**
- Lista sesji z datami
- Wykorzystane agenty
- Długość rozmów
- Koszty per sesja

**Insights** (bez AI analizy):
- Ulubione agenty (najczęściej używane)
- Style komunikacji (krótkie/długie wiadomości)
- Częstotliwość wizyt

---

### 💡 3. Sandbox & Testowanie AI

#### Funkcje:
- Główne okienko do wysyłania wiadomości do AI
- 7 kafelków z modelami (Misunderstanding, Conflict Solver itd.)
- Odpowiedzi na wiadomość w 7 wersjach (przy każdym modelu)
- Możliwość przełączania modeli (Claude 3.5, GPT-4o etc)
- Regulowanie temperatury
- Edycja promptów w real-time

#### Dodatkowo:
- Ilość tokenów per odpowiedź
- Czas odpowiedzi
- Koszt per odpowiedź
- Export wyników do CSV

---

### 📈 4. Analityka & Statystyki

#### Statystyki techniczne (per user / dziennie / godz / miesięcznie):
- Liczba wiadomości
- Tokeny in/out do OpenAI (ogólnie, per agent, per sesja)
- Tokeny in/out wszystkie (ogólnie, per agent, per sesja)
- Długość sesji
- Modele używane najczęściej i najrzadziej
- Ilość wspomnień w Mem0
- Ilość retrievali w Mem0

---

### 🧱 5. Monitoring Systemów

#### 🔴 Redis – monitoring pamięci tymczasowej
- **Redis Cache Usage**: aktualne użycie pamięci (MB / % limitu)
- **Hit / Miss ratio**: skuteczność cache (powinno być > 90%)
- **Liczba zapytań/min**: tempo użycia w czasie rzeczywistym
- **Ilość zapisanych sesji**: per user
- **Akcje**: Przycisk "Wyczyść Redis Cache"

#### 🟡 Supabase
- Ilość sesji
- Ilość wiadomości
- Status połączenia

#### 🟢 PostgreSQL
- Liczba rekordów w tabelach
- Połączenia aktywne
- Query performance

#### 🟢 Mem0
- Ilość wspomnień
- Czas retrieval (avg)
- API usage / limits

#### 📊 Widok zbiorczy
- Wykresy live: Redis usage, PG connections
- Kolorowe wskaźniki: 🔵 ok / 🟡 warning / 🔴 alert
- Error logs ostatnie 24h

---

### 🧠 6. Konfiguracja Redis/Mem0

#### Redis Strategy Settings:
```
Initial Retrieval:
○ Full retrieval (wszystko z Mem0)
● Smart retrieval (ostatnie X dni)  
○ Minimal retrieval (tylko podstawy)

Session Cache TTL: [30] minut

Update Strategy:
□ Save to Mem0 after each message
☑ Save to Mem0 at session end
☑ Save critical moments immediately

Retrieval Depth: [14] dni wstecz
```

#### Cost Control:
```
Max Context per Message: [2000] tokens
Memory Compression:
☑ Summarize old memories (>30 dni)
☑ Remove duplicates

Retrieval Limits:
Max memories per retrieval: [10]
Max retrieval size: [1000] tokens
```

---

## Architektura techniczna

### Backend API Endpoints

```python
# Dashboard
GET  /api/admin/dashboard/stats      # Główne KPI
GET  /api/admin/dashboard/trends     # Wykresy 7/30 dni
GET  /api/admin/dashboard/live       # Real-time metrics

# Users
GET  /api/admin/users               # Lista z paginacją
GET  /api/admin/users/:id           # Kartoteka użytkownika
GET  /api/admin/users/:id/sessions  # Historia sesji
PUT  /api/admin/users/:id           # Update danych

# Sandbox
POST /api/admin/sandbox/test        # Test wszystkich modeli
POST /api/admin/sandbox/single      # Test pojedynczego agenta
PUT  /api/admin/sandbox/prompt      # Update prompt tymczasowy

# Monitoring
GET  /api/admin/monitoring/redis    # Redis stats
GET  /api/admin/monitoring/pg       # PostgreSQL stats
GET  /api/admin/monitoring/mem0     # Mem0 stats
GET  /api/admin/monitoring/errors   # Error logs

# Settings
GET  /api/admin/settings/memory     # Konfiguracja Redis/Mem0
PUT  /api/admin/settings/memory     # Update konfiguracji
POST /api/admin/cache/clear         # Clear Redis
```

### Frontend Components

```typescript
// Struktura komponentów
admin/
├── Dashboard/
│   ├── StatsGrid.tsx      // KPI cards
│   ├── TrendsChart.tsx    // Wykresy
│   └── LiveMetrics.tsx    // Real-time
├── Users/
│   ├── UserList.tsx       // Tabela użytkowników
│   ├── UserProfile.tsx    // Kartoteka
│   └── SessionHistory.tsx // Historia
├── Sandbox/
│   ├── MessageInput.tsx   // Input area
│   ├── ModelGrid.tsx      // 7 modeli
│   └── ModelCard.tsx      // Pojedynczy model
├── Analytics/
│   ├── TokenUsage.tsx     // Statystyki tokenów
│   └── ModelStats.tsx     // Wykorzystanie modeli
├── Monitoring/
│   ├── SystemGrid.tsx     // 4 systemy
│   ├── RedisCard.tsx      // Redis details
│   └── ErrorLog.tsx       // Logi błędów
└── Settings/
    ├── MemoryConfig.tsx   // Redis/Mem0 settings
    └── CostControl.tsx    // Limity tokenów
```

### Database Schema dla Admin

```sql
-- Metryki dashboard (cache'owane co 5 min)
CREATE TABLE admin_metrics (
    id UUID PRIMARY KEY,
    metric_name VARCHAR(50),    -- 'daily_users', 'total_messages'
    metric_value NUMERIC,
    metric_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Logi błędów
CREATE TABLE error_logs (
    id UUID PRIMARY KEY,
    error_type VARCHAR(50),
    error_message TEXT,
    service VARCHAR(20),       -- 'backend', 'redis', 'mem0'
    user_id UUID,
    session_id UUID,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sandbox results (opcjonalne zapisywanie)
CREATE TABLE sandbox_tests (
    id UUID PRIMARY KEY,
    admin_id UUID,
    test_message TEXT,
    test_results JSONB,        -- wyniki wszystkich modeli
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Workflow implementacji

### Faza 1: Backend (1-2 dni)
1. Admin authentication middleware
2. Dashboard endpoints z metrykami
3. User management endpoints
4. Monitoring endpoints

### Faza 2: Frontend podstawy (1-2 dni)
1. Admin layout i routing
2. Dashboard z KPI
3. User list i profile

### Faza 3: Sandbox (1 dzień)
1. Multi-model testing endpoint
2. UI z 7 modelami
3. Prompt editing

### Faza 4: Monitoring (1 dzień)
1. System status endpoints
2. Monitoring UI
3. Error logs

### Faza 5: Settings (1 dzień)
1. Memory configuration
2. Cost controls
3. Cache management

## Security

- Admin panel wymaga osobnej autoryzacji
- Rate limiting na sandbox (max 10 req/min)
- Audit log wszystkich zmian
- Read-only dostęp dla niektórych adminów
- IP whitelist (opcjonalne)