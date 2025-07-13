# Plan Refaktoryzacji Playground - Separacja Mem0 i Zep

## 🔴 Problem aktualny (2025-07-13 22:45):
- Kod Zep i Mem0 się pomieszał w playground.py
- Błąd: `AsyncMemoryClient.get() got an unexpected keyword argument 'user_id'`
- AsyncMemoryClient to klasa z Mem0, ale pojawia się w kodzie Zep!
- Dziwny komentarz w linii 400: `)# This file will be appended to playground.py`
- Trudne debugowanie, niejasne które komponenty się ze sobą łączą

## ✅ Plan separacji - 3 niezależne moduły:

### 1. **backend/playground.py** (zostaje jak był)
- Tylko podstawowy playground (bez pamięci)
- Endpoint: `/api/playground/sse`
- Czyste SSE z OpenAI
- Bez importów Mem0 i Zep

### 2. **backend/playground_mem0.py** (NOWY PLIK)
```python
from fastapi import APIRouter, Query, Depends
from memory_service import search_memories, add_memory

mem0_router = APIRouter()

@mem0_router.get("/sse")
async def playground_mem0_sse(...):
    # Cała logika Mem0 tutaj
```
- Endpoint: `/api/playground-mem0/sse`
- Własny router
- Import tylko memory_service

### 3. **backend/playground_zep.py** (NOWY PLIK)
```python
from fastapi import APIRouter, Query, Depends
from zep_cloud.client import AsyncZep

zep_router = APIRouter()

@zep_router.get("/sse")
async def playground_zep_sse(...):
    # Cała logika Zep tutaj
```
- Endpoint: `/api/playground-zep/sse`
- Własny router
- Import tylko zep_cloud

### 4. **backend/main.py** - opcjonalne włączanie
```python
# Podstawowy playground zawsze włączony
from playground import playground_router
app.include_router(playground_router, prefix="/api/playground")

# Mem0 - opcjonalnie
if settings.mem0_api_key:
    from playground_mem0 import mem0_router
    app.include_router(mem0_router, prefix="/api/playground-mem0")
    logger.info("Mem0 playground enabled")

# Zep - opcjonalnie
if settings.zep_api_key:
    from playground_zep import zep_router
    app.include_router(zep_router, prefix="/api/playground-zep")
    logger.info("Zep playground enabled")
```

### 5. **Frontend zmiany w Playground.tsx**:

Zmienić URLe w funkcjach:
```typescript
// startStream() - bez zmian
`${API_URL}/api/playground/sse?${params}`

// startMem0Stream() - ZMIANA
`${API_URL}/api/playground-mem0/sse?${params}`  // było: /playground/mem0-sse

// startZepStream() - ZMIANA
`${API_URL}/api/playground-zep/sse?${params}`   // było: /playground/zep-sse
```

## 🎯 Korzyści:
- Całkowita separacja kodu
- Łatwe debugowanie (każdy plik osobno)
- Można włączać/wyłączać moduły przez ENV
- Brak konfliktów importów
- Czysty, czytelny kod

## 🐛 Problemy do naprawienia w Zep:
1. Usunąć dziwny komentarz z linii 400
2. Poprawić `memory.get()` - prawdopodobnie używać `session_id`
3. Zarządzanie sesjami - nie tworzyć nowej co click
4. Debugować czemu pojawia się AsyncMemoryClient z Mem0

## 📋 Kolejność implementacji:
1. Utworzyć `playground_mem0.py` z kodem Mem0 z playground.py
2. Utworzyć `playground_zep.py` z kodem Zep z playground.py  
3. Wyczyścić `playground.py` - usunąć kod Mem0 i Zep
4. Zaktualizować `main.py` z opcjonalnymi routerami
5. Zaktualizować URLe w `Playground.tsx`
6. Przetestować każdy moduł osobno