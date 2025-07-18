# AWS Bedrock - Aktualizacja i Plan Rozwoju

## ✅ Co zrobiliśmy dzisiaj (2025-01-17):

### 1. **Dodanie AWS Bedrock jako 4. okienko w Playground**
- Utworzono `playground_bedrock.py` - nowy endpoint dla AWS Bedrock
- Dodano zakładkę "AWS Bedrock" w Playground (obok No Memory, Mem0, Zep)
- Skonfigurowano zmienne środowiskowe AWS w Railway

### 2. **Rozwiązanie problemów z blokowaniem**
- **Problem**: boto3 jest synchroniczny i blokował FastAPI event loop
- **Pierwsze podejście**: ThreadPoolExecutor - nie rozwiązało problemu
- **Finalne rozwiązanie**: Zamiana boto3 na AsyncAnthropicBedrock (prawdziwy async)
- Teraz wszystkie 4 okienka działają równolegle bez blokowania

### 3. **Naprawienie identyfikatorów modeli**
- AsyncAnthropicBedrock używa standardowych nazw Anthropic (np. `claude-3-5-sonnet-20240620`)
- Nie wymaga pełnych ID AWS jak boto3

### 4. **Konfiguracja**
- Dodano `anthropic>=0.25.0` do requirements.txt
- Zmienne w Railway: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION

## 📋 Zadania do zrobienia w następnej sesji:

### 1. **Wybór modeli dla AWS Bedrock**
- [ ] Dodać listę dostępnych modeli Claude (Haiku, Sonnet, Opus)
- [ ] Umożliwić wybór modelu z dropdown w Playground
- [ ] Dynamicznie pobierać listę modeli z AWS (jeśli API to umożliwia)

### 2. **Poprawienie listy modeli OpenAI**
- [ ] Znaleźć gdzie jest zahardkodowana lista modeli w Playground
- [ ] Przenieść definicję modeli do konfiguracji lub bazy danych
- [ ] Umożliwić dodawanie nowych modeli OpenAI bez zmiany kodu
- [ ] Zsynchronizować listę modeli między Playground a Agent Prompts

### 3. **Przeprojektowanie systemu wyboru modeli**
- [ ] Stworzyć centralne miejsce definicji modeli (config lub DB)
- [ ] Wspólny komponent SelectModel dla całej aplikacji
- [ ] Różne listy modeli per provider (OpenAI, Anthropic/Bedrock)
- [ ] Możliwość ustawienia domyślnego modelu per agent

### 4. **AWS Agents - implementacja pamięci**
- [ ] Stworzyć AWS Agent w konsoli AWS z włączoną pamięcią
- [ ] Zmienić API z `invoke_model` na `invoke_agent`
- [ ] Implementacja zarządzania sessionId i memoryId
- [ ] Konfiguracja Knowledge Base (opcjonalnie)
- [ ] Dokumentacja jak skonfigurować agenta po stronie AWS

### 5. **Refaktoryzacja i optymalizacje**
- [ ] Wydzielić wspólną logikę streamingu do osobnego modułu
- [ ] Ujednolicić format odpowiedzi między różnymi providerami
- [ ] Dodać retry logic dla AWS Bedrock
- [ ] Lepsze logowanie i obsługa błędów

### 6. **UI/UX improvements**
- [ ] Wskaźnik który model jest używany w każdym okienku
- [ ] Możliwość różnych modeli dla różnych okienek
- [ ] Zapisywanie preferencji modeli w localStorage
- [ ] Porównanie kosztów między modelami

## 🔧 Techniczne szczegóły AWS Agents:

### Konfiguracja pamięci w AWS:
1. **Utworzenie agenta**:
   - Amazon Bedrock Console → Agents → Create agent
   - Włączyć "Memory" w konfiguracji
   - Ustawić retention period (1-365 dni)

2. **API Changes**:
   ```python
   # Zamiast:
   bedrock_client.messages.create(...)
   
   # Będzie:
   bedrock_agent_runtime.invoke_agent(
       agentId='AGENT_ID',
       sessionId='unique-session-id',
       memoryId='user-specific-memory-id',
       inputText=message
   )
   ```

3. **Zarządzanie sesjami**:
   - sessionId - dla pojedynczej konwersacji
   - memoryId - dla użytkownika (cross-session)
   - Automatyczne podsumowania długich konwersacji

## 📝 Notatki:
- AWS Bedrock w eu-central-1 (Frankfurt) ma dostępne modele Claude
- Limit SSE connections w przeglądarce (6 dla HTTP/1.1, 100 dla HTTP/2)
- Railway używa HTTP/2, więc limit nie jest problemem
- AsyncAnthropicBedrock to oficjalny async client od Anthropic