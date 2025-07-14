# ZEP TOKEN FIX - Szczegółowy Plan Naprawy

Data: 2025-07-14
Status: Do implementacji w następnej sesji

## 🔴 PROBLEM: Eksplozja tokenów w Zep

### Objawy:
1. Przy nowej sesji - wszystko OK (np. 200 tokenów)
2. Po załadowaniu sesji - tokeny eksplodują (np. 800+ tokenów na wiadomość)
3. System prompt rośnie z każdą wiadomością

### Przyczyna:
Zep API zwraca obiekt `memories` który zawiera:
- `context` - podsumowanie faktów o użytkowniku
- `messages` - PEŁNA HISTORIA rozmowy

My używamy tylko `context`, ale Zep może wewnętrznie dodawać historię do promptu!

## 📍 OBECNY STAN KODU

### backend/playground_zep.py (linie 88-113)
```python
# OBECNY KOD:
memories = await zep_client.memory.get(session_id=session_id)

# Budujemy system prompt
system_content = system_prompt
if memories and memories.context:
    system_content += f"\n\nUser context and facts:\n{memories.context}"

messages = [
    {"role": "system", "content": system_content},
    {"role": "user", "content": message}
]

# Wysyłamy do OpenAI
stream = await openai.chat.completions.create(
    model=model,
    messages=messages,  # Tylko 2 wiadomości!
    temperature=temperature,
    stream=True
)
```

### Problem:
- Wysyłamy tylko 2 wiadomości (system + user)
- ALE Zep może dodawać historię wewnętrznie!
- Nie wiemy co dokładnie Zep robi z naszym promptem

## 🛠️ PLAN NAPRAWY

### 1. Dodać szczegółowe logowanie (PRIORYTET)
```python
# W playground_zep.py, po linii 88:
memories = await zep_client.memory.get(session_id=session_id)

# DODAĆ:
logger.info(f"[ZEP DEBUG] ========= SESSION: {session_id} =========")
logger.info(f"[ZEP DEBUG] memories type: {type(memories)}")
logger.info(f"[ZEP DEBUG] memories dir: {dir(memories) if memories else 'None'}")
logger.info(f"[ZEP DEBUG] Has messages: {hasattr(memories, 'messages')}")
if hasattr(memories, 'messages') and memories.messages:
    logger.info(f"[ZEP DEBUG] Message count: {len(memories.messages)}")
    logger.info(f"[ZEP DEBUG] First message: {memories.messages[0] if memories.messages else 'None'}")
logger.info(f"[ZEP DEBUG] Context length: {len(memories.context) if memories and memories.context else 0}")
logger.info(f"[ZEP DEBUG] =====================================")

# Po counting tokens (linia 124):
logger.info(f"[ZEP DEBUG] Input tokens we count: {input_tokens}")
logger.info(f"[ZEP DEBUG] Our messages: {json.dumps(messages, indent=2)}")
```

### 2. Sprawdzić dokumentację Zep
- Czy Zep automatycznie dodaje historię?
- Czy powinniśmy używać innego endpointu?
- Może jest parametr do kontroli historii?

### 3. Zmienić ikonkę "oka" w SessionsTab.tsx
```typescript
// OBECNY KOD (linia 128):
<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
</svg>

// ZMIENIĆ NA (strzałka w prawo):
<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
</svg>

// I zmienić title z "Load session" na:
title="Load session history"
```

## ⚠️ WAŻNE - Czego NIE robić

1. **NIE modyfikować API Zep** - używamy oryginalnego API
2. **NIE dodawać parametru history** - to byłoby obejście
3. **NIE mieszać różnych trybów** - każdy tryb ma swoją logikę

## 📊 Oczekiwane rezultaty

Po naprawie:
1. Tokeny nie będą eksplodować po załadowaniu sesji
2. Będziemy wiedzieć dokładnie co Zep robi z historią
3. Użytkownik będzie wiedział że ikona ładuje historię

## 🔍 Jak testować

1. Utwórz nową sesję w Zep - zapisz liczbę tokenów
2. Wyślij 3-4 wiadomości
3. Załaduj inną sesję, potem wróć do pierwszej
4. Sprawdź czy tokeny nie eksplodują
5. Sprawdź logi [ZEP DEBUG] co się dzieje

## 📝 Dodatkowe uwagi

- Problem występuje TYLKO w Zep (Mem0 i FullContext działają OK)
- Zep jest jedynym trybem który zarządza sesjami
- To może być feature Zep, nie bug - musimy to zrozumieć