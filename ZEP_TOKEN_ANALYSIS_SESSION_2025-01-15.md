# Analiza Eksplozji Tokenów w Zep - Sesja 2025-01-15

## 🔍 Problem: Eksplozja tokenów w Zep

### Objawy:
- Nowa sesja: ~200 tokenów ✅
- Po załadowaniu starej sesji: 800+ tokenów ❌
- Po 21 wiadomościach: 47,700 tokenów (vs 11,700 w Mem0)

### Przykład z logów OpenAI (Zep):
```
Input:
system: You are the Relationship Upgrader, focused on taking good relationships to great ones...
User context and facts:
FACTS and ENTITIES represent relevant context to the current conversation.
# These are the most relevant facts and their valid date ranges
# format: FACT (Date range: from - to)
<FACTS>
- diamond da62 to naprawde fajna 2 silnikowa maszyna (2025-07-15 00:41:14 - present)
- ai (assistant) asked about the user's impressions from testing Diamond DA62 (2025-07-15 00:39:14 - 2025-07-15 00:41:14)
- ai (assistant) describes diamond da62 as a twin-engine design providing safety and comfort during flight (2025-07-15 00:41:14 - present)
- playground_user_1752539929106 ostatnio testował diamond da62 (2025-07-15 00:39:14 - present)
[... 19 faktów total ...]
</FACTS>

# These are the most relevant entities
# ENTITY_NAME: entity summary
<ENTITIES>
- playground_user_1752539929106: Użytkownik o ID playground_user_1752539929106 jest rolą human...
- diamond da62: The entity 'diamond da62' was mentioned in a message...
- ai (assistant): The entity is an AI assistant named 'ai (assistant)'...
[... 8 encji total ...]
</ENTITIES>

user: myslalem ze pamietasz moje imie
```

## 📊 Analiza tokenów

### Porównanie Zep vs Mem0:
- **Zep context**: ~1200-1400 tokenów (19 faktów + 8 encji z długimi opisami)
- **Mem0 memories**: ~350-400 tokenów (5 krótkich wspomnień)
- **Różnica**: ~1000 tokenów więcej w Zep!

### Porównanie po 21 wiadomościach:
| System | Input Tokens | Stosunek |
|--------|--------------|----------|
| **Zep** | 47,700 | 4x więcej niż Mem0! |
| **Mem0** | 11,700 | Baseline |
| **Full Context** | 64,600 | 5.5x więcej niż Mem0 |

## 🧩 Jak działa Zep

### Zep automatycznie buduje graf wiedzy:
1. Ekstraktuje fakty z każdej wiadomości
2. Tworzy encje (osoby, miejsca, rzeczy)
3. Dodaje timestamps do wszystkiego
4. Kumuluje wszystko w `memories.context`

### Nasz kod (playground_zep.py):
```python
# Pobieramy memories
memories = await zep_client.memory.get(session_id=session_id)

# Dodajemy context do system prompt
if memories and memories.context:
    system_content += f"\n\nUser context and facts:\n{memories.context}"

# Wysyłamy do OpenAI tylko 2 wiadomości
messages = [
    {"role": "system", "content": system_content},
    {"role": "user", "content": message}
]
```

### Problem: Context rośnie z każdą wiadomością!
- Po 1 wiadomości: kilka faktów
- Po 10 wiadomościach: dziesiątki faktów + rozbudowane encje
- Po 20 wiadomościach: setki faktów = eksplozja tokenów

## 💡 Rozwiązania omawiane

### 1. Smart Context z graph.search() (REKOMENDOWANE)
```python
# Zamiast memory.get() który zwraca wszystko
# Używamy targeted search
facts_results = await zep_client.graph.search(
    user_id=user_id,
    query=message,  # bieżąca wiadomość jako query
    limit=5,        # tylko 5 najważniejszych faktów
    search_type="edge",
    reranker="mmr"  # dla różnorodności
)

# Budujemy mały, relevant context (200-500 tokenów zamiast 2000)
```

### 2. Function Calling - Zep jako Tool
```python
tools = [{
    "type": "function",
    "function": {
        "name": "search_user_memory",
        "description": "Search for information from previous conversations",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            }
        }
    }
}]

# Model sam decyduje kiedy potrzebuje pamięci
# 80% przypadków: nie wywołuje = szybsze i tańsze
# 20% przypadków: wywołuje = podobny czas jak teraz
```

#### Przykład flow z Function Calling:
1. User: "Pamiętasz jak mam na imię?"
2. Model: Wywołuje `search_user_memory("user name")`
3. My: Wykonujemy search w Zep
4. Zep: "User's name is Rafał"
5. Model: "Tak, masz na imię Rafał!"

### 3. Przycinanie context (najprostsze)
```python
if memories and memories.context:
    context = memories.context
    if len(context) > 1000:
        context = context[:1000] + "\n[...context truncated...]"
    system_content += f"\n\n=== CONDENSED HISTORY ===\n{context}\n=== END ===\n"
```

### 4. Wyłączenie context całkowicie
```python
# Zakomentować:
# if memories and memories.context:
#     system_content += f"\n\nUser context and facts:\n{memories.context}"
```

## 📚 Dokumentacja Zep API

### memory.get()
- Zwraca: `context` (string z faktami/encjami), `messages`, `facts`
- Brak parametrów kontroli wielkości
- Automatycznie decyduje co jest "relevant"

### graph.search() (bardziej elastyczne)
```python
results = await zep_client.graph.search(
    user_id=user_id,
    query="diamond da62",  
    limit=5,              # kontrola ilości
    search_type="edge",   # lub "node" dla encji
    reranker="mmr"        # różne algorytmy rankingu
)
```

### Typy rerankerów:
- `rrf` (default) - Reciprocal Rank Fusion
- `mmr` - Maximum Marginal Relevance (dla różnorodności)
- `cross_encoder` - dokładniejsze scorowanie

## 🐛 Odkryty bug w Mem0

### Problem:
Playground_mem0.py wysyłał do Mem0 całe messages włącznie z system prompt:
```python
# BYŁO:
messages = [
    {"role": "system", "content": system_prompt + memory_context},
    {"role": "user", "content": message}
]
messages.append({"role": "assistant", "content": full_response})
await add_memory(messages, user_id)  # ❌ System prompt też leciał!
```

### Naprawiono:
```python
# JEST:
await add_memory([
    {"role": "user", "content": message},
    {"role": "assistant", "content": full_response}
], user_id)  # ✅ Tylko konwersacja!
```

## 🎯 Wnioski

### Zep vs Mem0:
- **Zep**: Potężny graf wiedzy, ale drogi (4x więcej tokenów)
- **Mem0**: Prostsze wspomnienia, tańsze
- **Trade-off**: Jakość vs Koszty

### Zalety Zep:
- Model "wie praktycznie wszystko"
- Fakty są datowane
- Automatyczna ekstrakcja encji
- Świetne dla złożonych, długich konwersacji

### Wady Zep:
- 1500-2000 tokenów per wiadomość
- Brak kontroli wielkości context
- Może przekroczyć limity przy długich sesjach

## 📝 Do zrobienia:

1. **Implementacja Smart Context** z graph.search()
2. **Debugowanie** - dodać logi wielkości context
3. **Testing Function Calling** jako alternatywa
4. **Naprawić liczenie tokenów** - zmienić `str(msg)` na `msg['content']`
5. **UI feedback** - zmienić ikonę w SessionsTab.tsx

## 🔗 Linki i zasoby:
- https://help.getzep.com/concepts#memory-context
- https://help.getzep.com/searching-the-graph
- Zep graph API dla większej kontroli

## 💭 Przemyślenia:
- Zep jest zaprojektowany do automatycznego zarządzania kontekstem
- W niektórych przypadkach to za dużo automatyzacji
- Function Calling może być najlepszym kompromisem
- Warto monitorować koszty przy produkcyjnym użyciu

## 🎣 Przykład rozmowy - Marek i ryby (5 wiadomości)

### Przebieg:
1. User: "witam :)"
2. User: "bylem na rybach z januszem a nazwyam sie Marek"
3. User: "zlowilismy fajnego karpia nad jeziorem kierskim niedaleko poznania"
4. User: "to byla wspaniala chwila, a smieszne bylo to ze zabraklo nam benzyny w naszej łodzi i znajomy Lukasz przywiozl nam kajakiem paliwo:))))"
5. User: "troche nam sie wylalo podczas tankowania ale to chyba nie powinno zaszkodzic rybka w jeziorze?"

### Co Zep wygenerował:

#### FAKTY (7 faktów z duplikacjami):
- Łukasz przywiozl paliwo kajakiem dla Marka, gdy zabraklo benzyny w lodzi
- Paliwo do łódki zostało dostarczone kajakiem (DUPLIKAT!)
- Marek był na rybach z Januszem
- jezioro kierskie jest niedaleko Poznania
- Janusz i karp nad jeziorem Kierskim
- Marek is a duplicate of playground_user_1752550332860
- karp został złowiony nad jeziorem kierskim

#### ENCJE (7 encji - każda powtarza całą historię!):
- **Marek**: pełny opis całej wyprawy
- **jezioro**: znowu cała historia
- **playground_user_1752550332860**: znowu Marek
- **karp**: znowu cała historia z różnych perspektyw
- **jezioro kierskie**: osobna encja dla tego samego jeziora!
- **Janusz**: osobna encja
- **Poznań**: znowu cała historia

### Analiza duplikacji:
- Ta sama informacja (Marek, Janusz, ryby, jezioro, brak benzyny, Łukasz) powtórzona 7-8 razy!
- ~1500 tokenów dla 5 prostych wiadomości
- Gdyby rozmowa trwała 20 wiadomości, byłoby to 6000+ tokenów samego contextu

### Wnioski:
- Zep generuje masywne duplikacje
- Każda encja zawiera pełną historię
- Brak deduplikacji informacji
- To wyjaśnia eksplozję tokenów