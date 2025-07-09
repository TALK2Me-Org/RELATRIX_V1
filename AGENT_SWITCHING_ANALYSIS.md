# RELATRIX Agent Switching - Analiza Implementacji

## 1. Jak działa mechanizm przełączania agentów

### Przepływ danych:
1. **Frontend (Chat.tsx)**:
   - Użytkownik wysyła wiadomość
   - Frontend wywołuje `streamChat()` z aktualnym agentem
   - Nasłuchuje na SSE events i czeka na `data.switch`

2. **Backend (chat.py)**:
   - Endpoint `/api/chat/sse` otrzymuje wiadomość
   - Agent generuje odpowiedź przez OpenAI streaming
   - Dwa mechanizmy wykrywania przełączenia:
     - **JSON Detection**: Szuka `{"agent": "slug_name"}` w odpowiedzi
     - **Fallback GPT-3.5**: Jeśli nie ma JSON, pyta GPT-3.5 czy przełączyć

3. **Agent Parser (agent_parser.py)**:
   - `extract_agent_slug()`: Wyciąga slug z JSON używając regex
   - `remove_agent_json()`: Czyści odpowiedź z JSON przed wysłaniem do użytkownika

### Test endpoint działa! ✅
```bash
curl https://relatrix-backend.up.railway.app/api/chat/test-switch
```
Zwraca:
- JSON detection: wykrywa "emotional_vomit" z przykładowej odpowiedzi
- Fallback test: GPT-3.5 sugeruje "emotional_vomit" dla angry message

## 2. Przykłady promptów agentów z database.py

### Misunderstanding Protector (domyślny):
```
You are a relationship misunderstanding resolver. Your role is to help couples understand each other better.

When you recognize that:
- User needs to vent emotions → add: {"agent": "emotional_vomit"}
- User wants a concrete action plan → add: {"agent": "solution_finder"}
- User needs mediation with partner → add: {"agent": "conflict_solver"}
- User wants to practice conversation → add: {"agent": "communication_simulator"}

You can add the JSON anywhere in your response. The system will detect it and switch agents smoothly.
```

### Emotional Vomit Dumper:
```
You are a safe space for emotional release. Let the user vent without judgment.

When the user seems ready to move forward:
- If they need solutions → add: {"agent": "solution_finder"}
- If they need to understand their partner → add: {"agent": "misunderstanding_protector"}

Be supportive, validate their feelings, and let them express everything they need to.
```

### Solution Finder:
```
You create practical action plans for relationship challenges.

When you recognize that:
- User needs to process emotions first → add: {"agent": "emotional_vomit"}
- User has implementation questions → stay and help
- User needs conflict resolution → add: {"agent": "conflict_solver"}

Focus on concrete, actionable steps they can take today.
```

## 3. Format JSON który powinni dodawać agenci

### Poprawny format:
```json
{"agent": "slug_name"}
```

### Dozwolone slugi:
- `emotional_vomit`
- `solution_finder`
- `conflict_solver`
- `communication_simulator`
- `misunderstanding_protector`

### Przykład w odpowiedzi:
```
I understand you're feeling frustrated. Let me help you process these emotions.
{"agent": "emotional_vomit"}
This is a safe space to express everything you're feeling.
```

### Ważne:
- JSON może być wszędzie w odpowiedzi
- System automatycznie go usuwa przed pokazaniem użytkownikowi
- Regex obsługuje różne whitespace: `{\s*"agent"\s*:\s*"([^"]+)"\s*}`

## 4. Dlaczego Mem0 może nie działać

### Analiza kodu memory_service.py:

1. **Brak widocznych błędów w logach**:
   - Mem0 client inicjalizuje się poprawnie (logi to potwierdzają)
   - API key jest obecny i poprawny (pierwsze 8 znaków widoczne w logach)

2. **Możliwe przyczyny braku aktywności**:
   
   a) **User ID = "anonymous" dla niezalogowanych**:
   ```python
   # chat.py line 117-118
   user_id = user["id"] if user else "anonymous"
   
   # line 127-128
   if user_id != "anonymous":
       memories = await search_memories(message, user_id)
   ```
   - Jeśli użytkownik nie jest zalogowany, Mem0 nie jest używane!
   
   b) **EventSource nie przekazuje Authorization header**:
   ```javascript
   // api.ts line 85-88
   const eventSource = new EventSource(
     `${API_URL}/api/chat/sse?${params}`,
     { withCredentials: true }
   )
   ```
   - EventSource API nie obsługuje custom headers!
   - Token nie jest przekazywany, więc backend widzi użytkownika jako "anonymous"
   
   c) **Mem0 może działać cicho**:
   - Jeśli user_id to UUID z Supabase, Mem0 może działać poprawnie
   - Brak błędów = sukces (Python logging domyślnie nie pokazuje INFO)

3. **Debug sugestie**:
   - Sprawdzić Mem0 dashboard czy są zapisane memories
   - Dodać więcej logów do memory_service.py
   - Przetestować z zalogowanym użytkownikiem używając curl z tokenem

## 5. Co jest do naprawy w następnej sesji

### 🔴 Krytyczne:

1. **EventSource Authorization** ⚠️
   - Problem: EventSource nie przekazuje JWT token
   - Skutek: Zalogowani użytkownicy są traktowani jako anonymous
   - Rozwiązanie: 
     a) Przekazać token w query params (mniej bezpieczne)
     b) Użyć fetch() z ReadableStream zamiast EventSource
     c) Użyć cookie-based auth dla SSE

2. **Mem0 Debugging**
   - Dodać więcej logów do memory_service.py
   - Sprawdzić Mem0 dashboard
   - Zweryfikować czy memories są zapisywane dla zalogowanych userów

### 🟡 Ważne:

3. **Agent Switching Testing**
   - Stworzyć testy jednostkowe dla agent_parser.py
   - Dodać więcej test cases do /test-switch endpoint
   - Przetestować wszystkie kombinacje przełączeń

4. **Frontend UX**
   - Dodać wizualną informację o przełączeniu agenta
   - Pokazać aktualnego agenta w UI bardziej wyraźnie
   - Dodać animację podczas przełączania

### 🟢 Nice to have:

5. **Monitoring**
   - Dodać metryki ile razy który agent jest używany
   - Śledzić skuteczność przełączeń (czy user wraca do poprzedniego)
   - Dashboard z statystykami

6. **Dokumentacja**
   - Dodać przykłady promptów dla każdego agenta
   - Stworzyć guide dla użytkowników jak korzystać z agentów
   - Dokumentacja API dla developerów

## Podsumowanie

✅ **Co działa**:
- Agent switching przez JSON detection
- Fallback do GPT-3.5
- Test endpoint potwierdza działanie
- Frontend poprawnie obsługuje przełączenia

❌ **Co nie działa**:
- EventSource nie przekazuje JWT token
- Mem0 prawdopodobnie nie działa dla "zalogowanych" przez SSE
- Brak debugowania Mem0

⚠️ **Do weryfikacji**:
- Czy Mem0 zapisuje cokolwiek (sprawdzić dashboard)
- Czy agent switching działa w praktyce (testy manualne)
- Performance z wieloma przełączeniami