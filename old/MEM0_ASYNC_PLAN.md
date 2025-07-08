# MEM0 ASYNC IMPLEMENTATION PLAN

## 🎯 CEL
Zastąpić synchroniczny MemoryClient asynchronicznym klientem używającym httpx, aby przyspieszyć chat.

## 🔴 OBECNE PROBLEMY

### 1. Synchroniczny client blokuje aplikację
```python
# TERAZ w orchestrator.py:
from mem0 import MemoryClient
self.mem0 = MemoryClient(api_key=settings.mem0_api_key)

# Blokujące wywołania:
memories = self.mem0.search(query=message, user_id=user_id, limit=5)
result = self.mem0.add(messages=[...], user_id=user_id, version="v2")
```

### 2. Mem0 add() nie działa
- Zwraca: `{'results': []}`
- Nic nie jest zapisywane
- Możliwe że brakuje parametrów lub złe API endpoint

### 3. Limit=5 jest za mały
- Ogranicza ilość zwracanych wspomnień
- Powinno być 10-20 dla lepszego kontekstu

## ✅ IMPLEMENTACJA AsyncMem0Client

### Lokalizacja: `backend/app/orchestrator/orchestrator.py`

### Krok 1: Dodaj import httpx
```python
import httpx
```

### Krok 2: Stwórz AsyncMem0Client class
```python
class AsyncMem0Client:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.mem0.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def search(self, query: str, user_id: str, limit: int = 20):
        """Async search memories"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/memories/search/",
                headers=self.headers,
                json={
                    "query": query,
                    "user_id": user_id,
                    "limit": limit
                },
                timeout=10.0  # 10 sekund timeout
            )
            response.raise_for_status()
            return response.json()
    
    async def add(self, messages: list, user_id: str, **kwargs):
        """Async add memories"""
        async with httpx.AsyncClient() as client:
            # Sprawdź różne warianty API
            payload = {
                "messages": messages,
                "user_id": user_id,
                "version": "v2",
                "output_format": "v1.1"
            }
            payload.update(kwargs)
            
            response = await client.post(
                f"{self.base_url}/memories/",
                headers=self.headers,
                json=payload,
                timeout=10.0
            )
            response.raise_for_status()
            
            # Debug response
            result = response.json()
            logger.info(f"Mem0 add response: {json.dumps(result, indent=2)}")
            return result
```

### Krok 3: Zamień w __init__
```python
def __init__(self):
    self.registry = AgentRegistry()
    self.mem0 = None  # Będzie AsyncMem0Client
    self.openai = AsyncOpenAI(api_key=settings.openai_api_key)
    self._initialized = False
```

### Krok 4: Zamień w initialize()
```python
async def initialize(self):
    if self._initialized:
        return
        
    await self.registry.load_agents()
    
    # Initialize Async Mem0
    if hasattr(settings, 'mem0_api_key') and not settings.mem0_api_key.startswith('m0-placeholder'):
        try:
            self.mem0 = AsyncMem0Client(api_key=settings.mem0_api_key)
            logger.info("Async Mem0 client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Mem0: {e}")
            self.mem0 = None
    
    self._initialized = True
```

### Krok 5: Zaktualizuj process_message()
```python
# Zmień limit na 20:
memories = await self.mem0.search(
    query=message,
    user_id=user_id,
    limit=20  # Było 5
)

# Add też będzie async:
result = await self.mem0.add(
    messages=[
        {"role": "user", "content": message},
        {"role": "assistant", "content": full_response}
    ],
    user_id=user_id
)
```

## 🧪 TESTOWANIE

### 1. Test search
```bash
curl -X POST https://relatrix-backend.up.railway.app/api/chat/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message": "Cześć, jak się masz?"}'
```

### 2. Sprawdź logi
- Powinny pokazać "Async Mem0 client initialized"
- Search powinien być szybszy
- Add powinien zwrócić coś więcej niż {'results': []}

## 📝 DODATKOWE UWAGI

### Requirements.txt
Upewnij się że masz:
```
httpx>=0.24.0
```

### Alternatywne endpointy do sprawdzenia
Jeśli add() nadal nie działa, spróbuj:
- POST `/memories/` (obecny)
- POST `/memories/add/` 
- POST `/memory/` (singular)

### Debug tips
1. Loguj pełną odpowiedź z Mem0
2. Sprawdź status code (powinien być 200/201)
3. Sprawdź czy potrzebne są dodatkowe parametry

## ⏱️ OCZEKIWANE REZULTATY

1. **Szybkość**: Chat powinien odpowiadać 2-3x szybciej
2. **Nieblokujące**: Aplikacja nie zawiesza się podczas Mem0 calls
3. **Więcej kontekstu**: 20 wspomnień zamiast 5
4. **Działający zapis**: Mem0 add() powinien zwracać ID zapisanych wspomnień