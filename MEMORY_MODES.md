# Memory Modes Documentation

## Status implementacji (2025-07-07 16:00 PL)
- ✅ Naprawiono save_conversation_memory() - wysyła rzeczywiste wiadomości zamiast podsumowań
- ✅ ALWAYS_FRESH: zapisuje ostatnią parę wiadomości (user + assistant)
- ✅ CACHE_FIRST: zapisuje całą paczkę wiadomości na końcu sesji
- ✅ SMART_TRIGGERS: zapisuje paczki co N wiadomości
- ✅ Używamy agent_id (taguje assistant messages) i run_id (dla sesyjnych memories)
- 🔧 Do przetestowania z live Mem0 API

## Overview
System pamięci RELATRIX oferuje 4 tryby pracy, które balansują między kosztami, wydajnością i dokładnością kontekstu.

## Memory Modes

### Mode A: "Cache First" (Domyślny)
**Filozofia**: Minimalizuj koszty, używaj cache maksymalnie

**Flow:**
```
START → [Mem0 Retrieval] → [Save to Redis] → Chat → Chat → Chat → [Save to Mem0] → END
         1x cost           TTL: 30 min                              1x cost
```

**Charakterystyka:**
- 1 retrieval z Mem0 na początku sesji
- Cache w Redis przez całą sesję (TTL konfiguralny)
- 1 save do Mem0 na końcu sesji
- **Koszt**: ~$0.02 per sesja (2 operacje Mem0)
- **Latency**: Bardzo niska (50ms) po pierwszej wiadomości
- **Use case**: Większość rozmów, szczególnie kontynuacje

### Mode B: "Always Fresh"
**Filozofia**: Maksymalna dokładność, zawsze świeży kontekst

**Flow:**
```
MSG1 → [Mem0 Retrieval] → [Process] → [Mem0 Save]
MSG2 → [Mem0 Retrieval] → [Process] → [Mem0 Save]
MSG3 → [Mem0 Retrieval] → [Process] → [Mem0 Save]
       2x cost per message!
```

**Charakterystyka:**
- Retrieval przy KAŻDEJ wiadomości
- Zawsze najnowszy kontekst
- Save po każdej wiadomości (ostatnia para: user + assistant)
- **Koszt**: ~$0.02 per wiadomość
- **Latency**: Wysoka (250ms) każda wiadomość
- **Use case**: Krytyczne rozmowy, terapia kryzysowa
- **ZMIANA 2025-07-07**: Zapisuje parę wiadomości (user + assistant) zamiast podsumowania

### Mode C: "Smart Triggers"
**Filozofia**: Inteligentny balans, retrieval gdy potrzebny

**Flow:**
```
START → [Retrieval] → Chat → Chat → [TRIGGER] → [Retrieval] → Chat → [Save] → END
         1x cost                     1x cost                           1x cost
```

**Charakterystyka:**
- Retrieval na start + przy triggerach
- Konfigurowalne triggery
- Save przy ważnych momentach + koniec
- **Koszt**: ~$0.06 per sesja (avg 3-4 operacje)
- **Latency**: Mieszana (50-250ms)
- **Use case**: Dłuższe, złożone rozmowy

### Mode D: "Test Mode"
**Filozofia**: Zbieraj dane, porównuj tryby

**Charakterystyka:**
- Wykonuje retrievale według wybranej strategii
- Loguje WSZYSTKO do analizy
- Symuluje koszty innych trybów
- Generuje raporty porównawcze
- **Use case**: Optymalizacja, wybór najlepszego trybu

## Smart Triggers Configuration

### Trigger Types

#### 1. Message Count Trigger
```python
"message_count": {
    "enabled": true,
    "threshold": 5,  # Co 5 wiadomości
    "description": "Refresh context every N messages"
}
```

#### 2. Time Elapsed Trigger
```python
"time_elapsed": {
    "enabled": true,
    "minutes": 15,  # Co 15 minut
    "description": "Refresh if session is long"
}
```

#### 3. Agent Transfer Trigger
```python
"agent_transfer": {
    "enabled": true,
    "description": "Always refresh on agent change"
}
```

#### 4. Emotion Spike Trigger
```python
"emotion_spike": {
    "enabled": true,
    "keywords": ["wściekła", "płaczę", "kryzys", "nie mogę"],
    "description": "Refresh on emotional intensity"
}
```

#### 5. Topic Change Trigger
```python
"topic_change": {
    "enabled": false,
    "keywords": ["inna sprawa", "zmieniam temat", "a propos"],
    "description": "Refresh when topic shifts"
}
```

#### 6. Important Info Trigger
```python
"important_info": {
    "enabled": true,
    "keywords": ["zdecydowałam", "postanowiłam", "powiem mu"],
    "description": "Save immediately on decisions"
}
```

## Cost Analysis

### Przykładowa sesja (10 wiadomości, 20 minut)

| Mode | Retrievals | Saves | Total Mem0 Ops | Cost | Latency Avg |
|------|------------|-------|----------------|------|-------------|
| Cache First | 1 | 1 | 2 | $0.02 | 50ms |
| Always Fresh | 10 | 10 | 20 | $0.20 | 250ms |
| Smart Triggers | 3 | 3 | 6 | $0.06 | 120ms |

### Miesięczna projekcja (1000 sesji)

| Mode | Total Cost | Savings vs Always Fresh |
|------|------------|-------------------------|
| Cache First | $20 | 90% |
| Always Fresh | $200 | 0% |
| Smart Triggers | $60 | 70% |

## Configuration Examples

### Conservative Setup (Oszczędny)
```json
{
  "mode": "cache_first",
  "cache_ttl": 45,
  "triggers": {
    "message_count": { "enabled": false },
    "time_elapsed": { "enabled": true, "minutes": 30 },
    "agent_transfer": { "enabled": true }
  }
}
```

### Balanced Setup (Zbalansowany)
```json
{
  "mode": "smart_triggers",
  "cache_ttl": 30,
  "triggers": {
    "message_count": { "enabled": true, "threshold": 5 },
    "time_elapsed": { "enabled": true, "minutes": 15 },
    "agent_transfer": { "enabled": true },
    "emotion_spike": { "enabled": true }
  }
}
```

### Premium Setup (Dokładny)
```json
{
  "mode": "always_fresh",
  "cache_ttl": 60,
  "save_every_message": true
}
```

## Implementation Details

### Session Lifecycle

#### 1. Session Start
```python
async def start_session(user_id: str, mode: MemoryMode):
    if mode in [CACHE_FIRST, SMART_TRIGGERS]:
        # Single retrieval
        context = await mem0.retrieve_all(user_id)
        await redis.set(f"session:{session_id}", context, ttl=1800)
    elif mode == ALWAYS_FRESH:
        # Retrieval will happen per message
        pass
```

#### 2. During Session
```python
async def process_message(message: str, session: Session):
    if session.mode == CACHE_FIRST:
        # Use Redis cache
        context = await redis.get(f"session:{session.id}")
    
    elif session.mode == ALWAYS_FRESH:
        # Fresh retrieval
        context = await mem0.retrieve_all(session.user_id)
    
    elif session.mode == SMART_TRIGGERS:
        # Check triggers
        if await should_refresh(session):
            context = await mem0.retrieve_all(session.user_id)
            await redis.set(f"session:{session.id}", context)
        else:
            context = await redis.get(f"session:{session.id}")
```

#### 3. Session End
```python
async def end_session(session: Session):
    if session.mode in [CACHE_FIRST, SMART_TRIGGERS]:
        # Save accumulated changes
        # ZMIANA 2025-07-07: Wysyła rzeczywiste wiadomości, nie podsumowanie
        messages = format_messages_for_mem0(session.conversation_history)
        await mem0.add(messages, user_id=session.user_id, 
                      agent_id=session.current_agent, 
                      run_id=session.id)
    # Mode ALWAYS_FRESH saves continuously
    
    # Cleanup
    await redis.delete(f"session:{session.id}")
```

## Monitoring & Metrics

### Key Metrics to Track
1. **Retrieval Count** - per session, per user
2. **Cache Hit Rate** - % using Redis vs Mem0
3. **Average Latency** - per mode
4. **Cost per Session** - per mode
5. **Context Relevance** - user satisfaction

### Dashboard View
```
┌─ Memory Performance (Last 24h) ───────────────┐
│                                               │
│ Mode Distribution:                            │
│ Cache First:    65% ████████████░            │
│ Smart Triggers: 30% ██████░                  │
│ Always Fresh:    5% █░                       │
│                                               │
│ Average Cost per Session:                    │
│ • Overall: $0.04                             │
│ • Cache First: $0.02                         │
│ • Smart Triggers: $0.06                      │
│ • Always Fresh: $0.18                        │
│                                               │
│ Cache Effectiveness: 87%                     │
│ Trigger Hit Rate: 23%                        │
│                                               │
└───────────────────────────────────────────────┘
```

## Best Practices

1. **Start with Cache First** - najniższe koszty, dobra wydajność
2. **Monitor rzeczywiste użycie** - Test Mode pomoże wybrać optymalny tryb
3. **Dostosuj triggery** - każdy user może mieć inne potrzeby
4. **Regularnie review koszty** - szczególnie przy Always Fresh
5. **Cache TTL** - 30 min to dobry balans

## FAQ

**Q: Kiedy używać Always Fresh?**
A: Tylko przy krytycznych rozmowach gdzie każdy szczegół ma znaczenie (np. kryzys, decyzje życiowe)

**Q: Czy mogę zmienić tryb w trakcie sesji?**
A: Tak, ale wymaga to manual refresh i może zwiększyć koszty

**Q: Co się stanie gdy Redis padnie?**
A: System automatycznie przełączy się na Always Fresh jako fallback

**Q: Jak wybrać optymalne triggery?**
A: Użyj Test Mode przez tydzień i analizuj raporty