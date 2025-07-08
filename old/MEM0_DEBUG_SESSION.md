# MEM0 DEBUG SESSION - 2025-07-08

## 🔍 PROBLEM GŁÓWNY
Mem0 NIE zwraca nowych wspomnień w kontekście, mimo że prawdopodobnie je zapisuje. 
Przykład: "Lubię lody waniliowe" nie pojawiło się w "Relevant user context" przy kolejnych zapytaniach.

## 🎯 CO ODKRYLIŚMY

### 1. **"Echo Chamber" Problem**
- AI powtarza informacje z kontekstu
- Mem0 zapisuje odpowiedzi AI jako nowe fakty o użytkowniku
- Przykład: "Planujesz zrobić makaron" (z wczoraj) pojawia się jako fakt dzisiaj

### 2. **Mieszanie Kontekstów (agent_id problem)**
Używaliśmy WSZYSTKIE 3 ID jednocześnie:
```python
# ŹLE - powodowało przecieki
await self.memory.add(
    messages=messages_to_save,
    user_id=session.user_id,
    agent_id=current_agent.slug,  # TO BYŁO PROBLEMEM!
    run_id=session.session_id
)
```

### 3. **Brak memory_id w Response**
```
WARNING:app.orchestrator.orchestrator:Failed to save to Mem0 - no memory_id returned
```
Mem0 przyjmuje request (200 OK) ale nie zwraca ID zapisanego wspomnienia.

## ✅ CO ZROBILIŚMY

### 1. **Usunęliśmy agent_id**
```python
# TERAZ - zgodnie z dokumentacją Mem0
await self.memory.add(
    messages=messages_to_save,
    user_id=session.user_id,
    run_id=session.session_id  # Tylko user_id + run_id
)
```

### 2. **Dodaliśmy Szczegółowe Logowanie**
```python
logger.info(f"Mem0 add called with params: user_id={user_id}, run_id={run_id}")
logger.info(f"Messages being saved: {json.dumps(messages, indent=2)}")

# Ostrzeżenie o echo
if any(phrase in response_content.lower() for phrase in ["wiem że", "nazywasz się"]):
    logger.warning("Assistant may be echoing context - watch for duplicates in Mem0")
```

## ❌ GDZIE STOIMY - PROBLEM Z RETRIEVAL

### Symptomy:
- Mem0 znajduje 7 wspomnień, ale BEZ nowych informacji
- "Lody waniliowe" nie pojawiły się mimo zapisania
- Kontekst się nie aktualizuje między wiadomościami

### Możliwe Przyczyny:
1. **run_id izoluje wspomnienia** - każda sesja ma swoją pamięć?
2. **async_mode=True** - może wspomnienia nie zdążyły się zaindeksować?
3. **Search query problem** - szukamy złym tekstem?

## 📚 MEM0 - MOŻLIWOŚCI I KOMBINACJE

### Oficjalne Kombinacje ID:
1. **Tylko `user_id`** - długoterminowa pamięć użytkownika (cross-session)
2. **`user_id + run_id`** - pamięć konkretnej sesji
3. **Tylko `agent_id`** - pamięć agenta
4. **Tylko `run_id`** - pamięć sesji bez użytkownika

### Parametry API:
```python
client.add(
    messages=[...],           # Lista wiadomości
    user_id="user123",       # ID użytkownika
    run_id="session123",     # ID sesji (opcjonalne)
    version="v2",            # Wersja API
    async_mode=True,         # Asynchroniczny zapis
    infer=True,              # Wnioskowanie faktów (domyślnie)
    output_format="v1.1"     # Format odpowiedzi
)
```

## 🚀 NASTĘPNE KROKI - PLAN DEBUG

### 1. **HIPOTEZA: run_id izoluje wspomnienia**
```python
# Test 1: Zapisuj TYLKO z user_id (cross-session)
await self.memory.add(
    messages=messages_to_save,
    user_id=session.user_id
    # BEZ run_id!
)
```

### 2. **Debug Response Structure**
```python
# Sprawdź co dokładnie zwraca Mem0
result = self.mem0_client.add(messages, **params)
logger.info(f"Mem0 response type: {type(result)}")
logger.info(f"Mem0 response content: {json.dumps(result) if result else 'None'}")
```

### 3. **Wyłącz async_mode**
```python
params = {
    "user_id": user_id,
    "run_id": run_id,
    "version": "v2",
    "async_mode": False,  # Czekaj na zapis!
    "output_format": "v1.1"
}
```

### 4. **Użyj get_all() zamiast search()**
```python
# Pobierz WSZYSTKIE wspomnienia użytkownika
memories = await client.get_all(
    filters={"AND": [{"user_id": user_id}]},
    version="v2",
    page_size=20
)
logger.info(f"ALL memories: {json.dumps(memories, indent=2)}")
```

### 5. **Test Flow**
1. Usuń run_id z zapisywania
2. Napisz: "Lubię lody czekoladowe"
3. Sprawdź logi - czy jest memory_id?
4. Zapytaj: "Jakie lody lubię?"
5. Sprawdź czy kontekst zawiera obie informacje (waniliowe + czekoladowe)

## 💡 WAŻNE PYTANIE ARCHITEKTONICZNE

**Czy chcemy pamięć PER SESSION czy CROSS-SESSION?**

- **PER SESSION** (z run_id): Każda rozmowa jest izolowana
- **CROSS-SESSION** (bez run_id): Użytkownik ma jedną ciągłą historię

Dla aplikacji terapeutycznej prawdopodobnie **CROSS-SESSION jest lepsze** - terapeuta powinien pamiętać wszystko z poprzednich sesji!

## 🔧 QUICK FIX DO PRZETESTOWANIA

```python
# W orchestrator.py - usuń run_id:
memory_id = await self.memory.add(
    messages=messages_to_save,
    user_id=session.user_id
    # BEZ run_id - pamięć cross-session!
)
```

To powinno rozwiązać problem z brakiem nowych wspomnień w kontekście!