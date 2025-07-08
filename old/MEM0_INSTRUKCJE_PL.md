# Dokumentacja Platformy Mem0 (PL)

## Contextual Add (ADD v2) - Kontekstowe Dodawanie

🔐 Mem0 jest teraz zgodny z SOC 2 i HIPAA! Jesteśmy zaangażowani w najwyższe standardy bezpieczeństwa i prywatności danych, umożliwiając bezpieczną pamięć dla przedsiębiorstw, opieki zdrowotnej i nie tylko.

Mem0 teraz obsługuje kontekstową wersję dodawania (v2). Aby jej użyć, ustaw version="v2" podczas wywołania add. Domyślna wersja to v1, która jest teraz przestarzała. Zalecamy migrację do v2 dla nowych aplikacji.

### Kluczowe różnice między v1 a v2

#### Wersja 1 (Przestarzała)
W v1 (domyślna), użytkownicy musieli przekazywać całą historię konwersacji lub ostatnie k wiadomości z każdą nową wiadomością, aby generować odpowiednio skontekstualizowane wspomnienia. To podejście wymagało:

- Ręcznego śledzenia i wysyłania poprzednich wiadomości używając podejścia okna przesuwnego
- Zwiększonych rozmiarów ładunku w miarę wydłużania się konwersacji, wymagając starannego zarządzania rozmiarem okna

Python:
```python
# Pierwsza interakcja
messages1 = [
    {"role": "user", "content": "Cześć, jestem Alex i mieszkam w San Francisco."},
    {"role": "assistant", "content": "Witaj Alex! Miło cię poznać. San Francisco to piękne miasto."}
]
client.add(messages1, user_id="alex")

# Druga interakcja - musi zawierać poprzednie wiadomości dla kontekstu
messages2 = [
    {"role": "user", "content": "Cześć, jestem Alex i mieszkam w San Francisco."},
    {"role": "assistant", "content": "Witaj Alex! Miło cię poznać. San Francisco to piękne miasto."},
    {"role": "user", "content": "Lubię jeść sushi, a wczoraj pojechałem do Sunnyvale zjeść sushi z przyjaciółmi."},
    {"role": "assistant", "content": "Sushi to naprawdę smaczny wybór. Co robiłeś w weekend?"}
]
client.add(messages2, user_id="alex")
```

#### Wersja 2 (Zalecana)
W v2, Mem0 automatycznie zarządza kontekstem konwersacji. Użytkownicy muszą tylko wysyłać nowe wiadomości, a system:

- Automatycznie pobierze odpowiednią historię konwersacji
- Wygeneruje odpowiednio skontekstualizowane wspomnienia
- Zmniejszy rozmiary ładunku i uprości integrację

Python:
```python
# Pierwsza interakcja
messages1 = [
    {"role": "user", "content": "Cześć, jestem Alex i mieszkam w San Francisco."},
    {"role": "assistant", "content": "Witaj Alex! Miło cię poznać. San Francisco to piękne miasto."}
]
client.add(messages1, user_id="alex", version="v2")

# Druga interakcja - wystarczy wysłać tylko nowe wiadomości
messages2 = [
    {"role": "user", "content": "Lubię jeść sushi, a wczoraj pojechałem do Sunnyvale zjeść sushi z przyjaciółmi."},
    {"role": "assistant", "content": "Sushi to naprawdę smaczny wybór. Co robiłeś w weekend?"}
]
client.add(messages2, user_id="alex", version="v2")
```

### Korzyści z używania v2
- Uproszczona integracja: Nie trzeba śledzić i zarządzać historią konwersacji
- Zmniejszony rozmiar ładunku: Wysyłaj tylko nowe wiadomości, nie całą konwersację
- Lepsza jakość pamięci: Automatyczne pobieranie kontekstu zapewnia lepsze generowanie pamięci

### Zrozumienie parametrów ID w v2
Używając kontekstowego dodawania v2, masz różne opcje organizowania i pobierania wspomnień:

#### Używanie tylko user_id
Gdy podajesz tylko user_id:

- Wspomnienia są powiązane z długoterminowym magazynem pamięci tego użytkownika
- System automatycznie pobierze odpowiedni kontekst ze wszystkich poprzednich konwersacji użytkownika
- Te wspomnienia utrzymują się bezterminowo we wszystkich sesjach użytkownika
- Idealne do utrzymywania trwałych informacji o użytkowniku (preferencje, dane osobowe itp.)

Python:
```python
# Dodawanie do długoterminowej pamięci użytkownika
messages = [
    {"role": "user", "content": "Jestem uczulony na orzeszki ziemne i owoce morza."},
    {"role": "assistant", "content": "Zanotowałem twoje alergie na orzeszki ziemne i owoce morza."}
]
client.add(messages, user_id="alex", version="v2")
```

#### Używanie user_id z run_id
Gdy podajesz zarówno user_id jak i run_id:

- Wspomnienia są powiązane z konkretną sesją konwersacji lub interakcją
- System pobierze kontekst głównie z tej konkretnej sesji
- Te wspomnienia są nadal powiązane z użytkownikiem, ale są zorganizowane według konkretnej sesji
- Idealne do utrzymywania kontekstu w ramach konkretnego przepływu konwersacji lub zadania
- Pomaga zapobiegać mieszaniu się kontekstu z różnych konwersacji

Python:
```python
# Dodawanie do konkretnej sesji konwersacji
messages = [
    {"role": "user", "content": "Podczas tej wycieczki do Paryża chcę skupić się na muzeach sztuki."},
    {"role": "assistant", "content": "Świetnie! Pomogę ci zaplanować wycieczkę do Paryża ze szczególnym uwzględnieniem muzeów sztuki."}
]
client.add(messages, user_id="alex", run_id="paris-trip-2024", version="v2")

# Później w tej samej sesji konwersacji
messages2 = [
    {"role": "user", "content": "Chciałbym odwiedzić Luwr w poniedziałek."},
    {"role": "assistant", "content": "Luwr to świetny wybór na poniedziałek. Czy chciałbyś informacje o godzinach otwarcia?"}
]
client.add(messages2, user_id="alex", run_id="paris-trip-2024", version="v2")
```

Używanie run_id pomaga organizować wspomnienia w logiczne sesje lub zadania, ułatwiając utrzymanie kontekstu dla konkretnych interakcji, jednocześnie nadal przypisując wszystko do ogólnego profilu użytkownika.

## Klient Asynchroniczny

Asynchroniczny klient dla Mem0

🔐 Mem0 jest teraz zgodny z SOC 2 i HIPAA!

AsyncMemoryClient to asynchroniczny klient do interakcji z API Mem0. Zapewnia podobną funkcjonalność do synchronicznego MemoryClient, ale pozwala na operacje nieblokujące, co może być korzystne w aplikacjach wymagających wysokiej współbieżności.

### Inicjalizacja
Aby użyć klienta asynchronicznego, najpierw musisz go zainicjalizować:

Python:
```python
import os
from mem0 import AsyncMemoryClient

os.environ["MEM0_API_KEY"] = "twój-klucz-api"

client = AsyncMemoryClient()
```

### Metody
AsyncMemoryClient udostępnia następujące metody:

#### Add (Dodaj)
Dodaj nową pamięć asynchronicznie.

Python:
```python
messages = [
    {"role": "user", "content": "Alicja uwielbia grać w badmintona"},
    {"role": "assistant", "content": "To świetnie! Alicja jest fanką fitnessu"},
]
await client.add(messages, user_id="alice")
```

#### Search (Szukaj)
Szukaj wspomnień na podstawie zapytania asynchronicznie.

Python:
```python
await client.search("Jaki jest ulubiony sport Alicji?", user_id="alice")
```

#### Get All (Pobierz wszystkie)
Pobierz wszystkie wspomnienia użytkownika asynchronicznie.

Python:
```python
await client.get_all(user_id="alice")
```

#### Delete (Usuń)
Usuń konkretną pamięć asynchronicznie.

Python:
```python
await client.delete(memory_id="id-pamięci-tutaj")
```

#### Delete All (Usuń wszystkie)
Usuń wszystkie wspomnienia użytkownika asynchronicznie.

Python:
```python
await client.delete_all(user_id="alice")
```

#### History (Historia)
Pobierz historię konkretnej pamięci asynchronicznie.

Python:
```python
await client.history(memory_id="id-pamięci-tutaj")
```

#### Users (Użytkownicy)
Pobierz wszystkich użytkowników, agentów i sesje, które mają powiązane wspomnienia asynchronicznie.

Python:
```python
await client.users()
```

#### Reset (Resetuj)
Zresetuj klienta, usuwając wszystkich użytkowników i wspomnienia asynchronicznie.

Python:
```python
await client.reset()
```

### Podsumowanie
AsyncMemoryClient zapewnia potężny sposób interakcji z API Mem0 asynchronicznie, umożliwiając bardziej wydajne i responsywne aplikacje. Używając tego klienta, możesz wykonywać operacje na pamięci bez blokowania wykonywania aplikacji.

## Zaawansowane Wyszukiwanie

🔐 Mem0 jest teraz zgodny z SOC 2 i HIPAA!

Zaawansowane Wyszukiwanie Mem0 zapewnia dodatkową kontrolę nad tym, jak wspomnienia są wybierane i rankingowane podczas wyszukiwania. Podczas gdy domyślne wyszukiwanie używa semantycznego podobieństwa opartego na embeddingach, Zaawansowane Wyszukiwanie wprowadza wyspecjalizowane opcje do poprawy przypominania, dokładności rankingu lub filtrowania w oparciu o konkretny przypadek użycia.

Możesz włączyć dowolny z następujących trybów niezależnie lub razem:

- Wyszukiwanie słów kluczowych
- Ponowne rankingowanie
- Filtrowanie

Każde ulepszenie można przełączać niezależnie za pomocą wywołania API search(). Te flagi są domyślnie wyłączone. Są przydatne podczas budowania agentów wymagających precyzyjnej kontroli wyszukiwania.

### Wyszukiwanie słów kluczowych
Wyszukiwanie słów kluczowych rozszerza zestaw wyników, włączając wspomnienia zawierające leksykalnie podobne terminy i ważne słowa kluczowe z zapytania, nawet jeśli nie są semantycznie podobne.

#### Kiedy używać
- Szukasz konkretnych podmiotów, nazw lub terminów technicznych
- Gdy potrzebujesz kompleksowego pokrycia tematu
- Chcesz szerszego przypominania kosztem niewielkiego szumu

#### Użycie API
```python
results = client.search(
    query="Jakie są moje preferencje żywieniowe?",
    keyword_search=True,
    user_id="alex"
)
```

#### Przykład
Bez keyword_search:
- "Wegetarianin. Uczulony na orzechy."
- "Preferuje ostre jedzenie i lubi kuchnię tajską"

Z keyword_search=True:
- "Wegetarianin. Uczulony na orzechy."
- "Preferuje ostre jedzenie i lubi kuchnię tajską"
- "Wspomniał o nielubienia owoców morza podczas dyskusji o restauracji"

#### Kompromisy
- Zwiększa przypominanie
- Może nieznacznie zmniejszyć precyzję
- Dodaje ~10ms opóźnienia

### Ponowne rankingowanie
Ponowne rankingowanie porządkuje pobrane wyniki używając głębokiego modelu semantycznej relewancji, który poprawia pozycję najbardziej odpowiednich dopasowań.

#### Kiedy używać
- Polegasz na precyzji top-1 lub top-N
- Gdy kolejność wyników jest krytyczna dla twojej aplikacji
- Chcesz spójnej jakości wyników między sesjami

#### Użycie API
```python
results = client.search(
    query="Jakie są moje plany podróży?",
    rerank=True,
    user_id="alex"
)
```

#### Przykład
Bez rerank:
- "Podróżowałem do Francji w zeszłym roku"
- "Planuję wycieczkę do Japonii w przyszłym miesiącu"
- "Zainteresowany odwiedzeniem restauracji w Tokio"

Z rerank=True:
- "Planuję wycieczkę do Japonii w przyszłym miesiącu"
- "Zainteresowany odwiedzeniem restauracji w Tokio"
- "Podróżowałem do Francji w zeszłym roku"

#### Kompromisy
- Znacząco poprawia dokładność kolejności wyników
- Zapewnia, że najbardziej istotne wspomnienia pojawiają się pierwsze
- Dodaje ~150-200ms opóźnienia
- Wyższy koszt obliczeniowy

### Filtrowanie
Filtrowanie pozwala zawęzić wyniki wyszukiwania poprzez zastosowanie konkretnych kryteriów ze zbioru pobranych wspomnień.

#### Kiedy używać
- Wymagasz bardzo konkretnych wyników
- Pracujesz z ogromną ilością danych, gdzie szum jest problematyczny
- Wymagasz jakości ponad ilością wyników

#### Użycie API
```python
results = client.search(
    query="Jakie są moje ograniczenia dietetyczne?",
    filter_memories=True,
    user_id="alex"
)
```

#### Przykład
Bez filtrowania:
- "Wegetarianin. Uczulony na orzechy."
- "Lubię gotować włoskie jedzenie w weekendy"
- "Wspomniał o nielubienia owoców morza podczas dyskusji o restauracji"
- "Preferuje jeść kolację o 19:00"

Z filter_memories=True:
- "Wegetarianin. Uczulony na orzechy."
- "Wspomniał o nielubienia owoców morza podczas dyskusji o restauracji"

#### Kompromisy
- Maksymalizuje precyzję (tylko bardzo istotne wyniki)
- Może zmniejszyć przypominanie (odfiltrowuje niektóre istotne wspomnienia)
- Dodaje ~200-300ms opóźnienia
- Najlepsze dla skupionych, konkretnych zapytań

### Łączenie trybów
Możesz połączyć wszystkie trzy tryby wyszukiwania według potrzeb:

```python
results = client.search(
    query="Jakie są moje plany podróży?",
    keyword_search=True,
    rerank=True,
    filter_memories=True,
    user_id="alex"
)
```

Ta konfiguracja poszerza pulę kandydatów słowami kluczowymi, poprawia kolejność poprzez ponowne rankingowanie, a na końcu odcina szum filtrowaniem.
Łączenie wszystkich trybów może dodać do ~450ms opóźnienia na zapytanie.

### Benchmarki wydajności
| Tryb | Przybliżone opóźnienie |
|------|----------------------|
| keyword_search | <10ms |
| rerank | 150-200ms |
| filter_memories | 200-300ms |

### Najlepsze praktyki i ograniczenia
- Użyj keyword_search dla szerszego przypominania, gdy kontekst zapytania jest ograniczony
- Użyj rerank, aby priorytetyzować najistotniejszy wynik
- Użyj filter_memories w agentach produkcyjnych lub krytycznych dla bezpieczeństwa
- Połącz filtrowanie i ponowne rankingowanie dla maksymalnej dokładności
- Filtry mogą wyeliminować wszystkie wyniki - zawsze obsługuj pusty zestaw z gracją
- Filtrowanie używa oceny LLM i może być ograniczone limitami w zależności od twojego planu
- Możesz włączać lub wyłączać te tryby wyszukiwania, przekazując odpowiednie parametry do metody search. Nie ma wymaganej sekwencji dla tych trybów i można używać dowolnej kombinacji w zależności od potrzeb.

## Wyszukiwanie z kryteriami

🔐 Mem0 jest teraz zgodny z SOC 2 i HIPAA!

Funkcja Wyszukiwania z kryteriami Mem0 pozwala pobierać wspomnienia na podstawie zdefiniowanych przez ciebie kryteriów. Wykracza poza ogólną semantyczną relewancję i rankinguje wspomnienia na podstawie tego, co ma znaczenie dla twojej aplikacji - ton emocjonalny, intencja, sygnały behawioralne lub inne niestandardowe cechy.

Zamiast tylko szukać "jak podobna jest pamięć do tego zapytania?", możesz zdefiniować, co naprawdę oznacza relewancja dla twojego projektu. Na przykład:

- Priorytetyzuj radosne wspomnienia podczas budowania asystenta wellness
- Obniż ranking negatywnych wspomnień w agencie skoncentrowanym na produktywności
- Podkreśl ciekawość w agencie nauczającym

Definiujesz kryteria - niestandardowe atrybuty jak "radość", "negatywność", "pewność" lub "pilność", i przypisujesz wagi kontrolujące ich wpływ na punktację. Gdy szukasz, Mem0 używa ich do ponownego rankingowania wspomnień, które są semantycznie istotne, faworyzując te, które lepiej pasują do twojej intencji.

To daje ci subtelne, świadome intencji wyszukiwanie pamięci, które dostosowuje się do twojego przypadku użycia.

### Kiedy używać wyszukiwania z kryteriami
Użyj wyszukiwania z kryteriami jeśli:

- Budujesz agenta, który powinien reagować na emocje lub sygnały behawioralne
- Chcesz kierować wyborem pamięci na podstawie kontekstu, a nie tylko treści
- Masz sygnały specyficzne dla domeny jak "ryzyko", "pozytywność", "pewność" itp., które kształtują przypominanie

### Konfiguracja wyszukiwania z kryteriami
Przejdźmy krok po kroku przez konfigurację i użycie wyszukiwania z kryteriami.

#### Zainicjuj klienta
Przed zdefiniowaniem jakichkolwiek kryteriów, upewnij się, że zainicjalizowałeś MemoryClient z twoimi danymi uwierzytelniającymi i ID projektu:

```python
from mem0 import MemoryClient

client = MemoryClient(
    api_key="twój_klucz_api_mem0",
    org_id="id_twojej_organizacji",
    project_id="id_twojego_projektu"
)
```

#### Zdefiniuj swoje kryteria
Każde kryterium zawiera:

- Nazwę (używaną w punktacji)
- Opis (interpretowany przez LLM)
- Wagę (jak bardzo wpływa na końcowy wynik)

```python
retrieval_criteria = [
    {
        "name": "radość",
        "description": "Zmierz intensywność pozytywnych emocji takich jak szczęście, ekscytacja lub rozbawienie wyrażone w zdaniu. Wyższy wynik odzwierciedla większą radość.",
        "weight": 3
    },
    {
        "name": "ciekawość",
        "description": "Oceń stopień, w jakim zdanie odzwierciedla dociekliwość, zainteresowanie eksplorowaniem nowych informacji lub zadawanie pytań. Wyższy wynik odzwierciedla silniejszą ciekawość.",
        "weight": 2
    },
    {
        "name": "emocja",
        "description": "Oceń obecność i głębię smutku lub negatywnego tonu emocjonalnego, w tym wyrażenia rozczarowania, frustracji lub żalu. Wyższy wynik odzwierciedla większy smutek.",
        "weight": 1
    }
]
```

#### Zastosuj kryteria do swojego projektu
Po zdefiniowaniu, zarejestruj kryteria w swoim projekcie:

```python
client.update_project(retrieval_criteria=retrieval_criteria)
```

Kryteria stosują się do całego projektu. Po ustawieniu wpływają na wszystkie wyszukiwania używające version="v2".

### Przykładowy przewodnik
Po skonfigurowaniu kryteriów możesz ich używać do filtrowania i pobierania wspomnień. Oto przykład:

#### Dodaj wspomnienia
```python
messages = [
    {"role": "user", "content": "Jaki piękny słoneczny dzień! Czuję się tak odświeżony i gotowy na wszystko!"},
    {"role": "user", "content": "Zawsze się zastanawiałem, jak powstają burze - co je wyzwala w atmosferze?"},
    {"role": "user", "content": "Pada już od dni, i to sprawia, że wszystko wydaje się cięższe."},
    {"role": "user", "content": "Wreszcie mam czas narysować coś dzisiaj, po długim czasie!! Jestem super szczęśliwy dzisiaj."}
]

client.add(messages, user_id="alice")
```

#### Porównaj standardowe vs. oparte na kryteriach wyszukiwanie
```python
# Z kryteriami
filters = {
    "AND": [
        {"user_id": "alice"}
    ]
}
results_with_criteria = client.search(
    query="Dlaczego czuję się szczęśliwy dzisiaj?",
    filters=filters,
    version="v2"
)

# Bez kryteriów
results_without_criteria = client.search(
    query="Dlaczego czuję się szczęśliwy dzisiaj?",
    user_id="alice"
)
```

#### Porównaj wyniki

Wyniki wyszukiwania (z kryteriami):
```json
[
    {"memory": "Użytkownik czuje się odświeżony i gotowy na wszystko w piękny słoneczny dzień", "score": 0.666, ...},
    {"memory": "Użytkownik wreszcie ma czas narysować coś po długim czasie", "score": 0.616, ...},
    {"memory": "Użytkownik jest szczęśliwy dzisiaj", "score": 0.500, ...},
    {"memory": "Użytkownik jest ciekawy jak powstają burze i co je wyzwala w atmosferze.", "score": 0.400, ...},
    {"memory": "Pada od dni, sprawiając że wszystko wydaje się cięższe.", "score": 0.116, ...}
]
```

Wyniki wyszukiwania (bez kryteriów):
```json
[
    {"memory": "Użytkownik jest szczęśliwy dzisiaj", "score": 0.607, ...},
    {"memory": "Użytkownik czuje się odświeżony i gotowy na wszystko w piękny słoneczny dzień", "score": 0.512, ...},
    {"memory": "Pada od dni, sprawiając że wszystko wydaje się cięższe.", "score": 0.4617, ...},
    {"memory": "Użytkownik jest ciekawy jak powstają burze i co je wyzwala w atmosferze.", "score": 0.340, ...},
    {"memory": "Użytkownik wreszcie ma czas narysować coś po długim czasie", "score": 0.336, ...},
]
```

#### Porównanie wyników wyszukiwania
- Kolejność pamięci: Z kryteriami, wspomnienia z wysokimi wynikami radości (jak odświeżenie i rysowanie) są rankingowane wyżej, podczas gdy bez kryteriów, najbardziej istotna pamięć ("Użytkownik jest szczęśliwy dzisiaj") pojawia się pierwsza.
- Rozkład wyników: Z kryteriami, wyniki są bardziej rozproszone (0.116 do 0.666) i odzwierciedlają wagi kryteriów, podczas gdy bez kryteriów, wyniki są bardziej skupione (0.336 do 0.607) i oparte wyłącznie na relewancji.
- Wrażliwość na cechy: Treść "deszczowy dzień" jest karana ze względu na negatywny ton. "Ciekawość burzy" jest rozpoznawana i odpowiednio punktowana.

### Kluczowe różnice vs. standardowe wyszukiwanie
| Aspekt | Standardowe wyszukiwanie | Wyszukiwanie z kryteriami |
|--------|-------------------------|--------------------------|
| Logika rankingu | Tylko podobieństwo semantyczne | Semantyczne + punktacja oparta na LLM |
| Kontrola nad relewancją | Brak | W pełni konfigurowalna z ważonymi kryteriami |
| Zmiana kolejności pamięci | Statyczna na podstawie podobieństwa | Dynamicznie ponownie rankingowana przez dopasowanie intencji |
| Wrażliwość emocjonalna | Brak świadomości tonu lub cech | Włącza emocje, ton lub niestandardowe zachowania |
| Wymagana wersja | Domyślna | search(version="v2") |

Jeśli nie zdefiniowano kryteriów dla projektu, version="v2" zachowuje się jak normalne wyszukiwanie.

### Najlepsze praktyki
- Wybierz 3-5 kryteriów, które odzwierciedlają intencję twojej aplikacji
- Stwórz jasne i wyraźne opisy, są interpretowane przez LLM
- Użyj silniejszych wag, aby wzmocnić wpływ ważnych cech
- Unikaj redundantnych lub niejednoznacznych kryteriów (np. "pozytywność" + "radość")
- Zawsze obsługuj puste zestawy wyników w logice aplikacji

### Jak to działa
1. Definicja kryteriów: Zdefiniuj niestandardowe kryteria z nazwą, opisem i wagą. Opisują one, co ma znaczenie w pamięci (np. radość, pilność, empatia).
2. Konfiguracja projektu: Zarejestruj te kryteria używając update_project(). Stosują się one na poziomie projektu i wpływają na wszystkie wyszukiwania używające version="v2".
3. Pobieranie pamięci: Gdy wykonujesz wyszukiwanie z version="v2", Mem0 najpierw pobiera istotne wspomnienia na podstawie zapytania i zdefiniowanych kryteriów.
4. Ważona punktacja: Każda pobrana pamięć jest oceniana i punktowana względem zdefiniowanych kryteriów i wag.

To pozwala priorytetyzować wspomnienia, które są zgodne z celami twojego agenta, a nie tylko te, które wyglądają podobnie do zapytania.

Wyszukiwanie z kryteriami jest obecnie obsługiwane tylko w search v2. Upewnij się, że używasz version="v2" podczas wykonywania wyszukiwań z niestandardowymi kryteriami.

### Podsumowanie
- Zdefiniuj co oznacza "istotne" używając kryteriów
- Zastosuj je na projekt przez update_project()
- Użyj version="v2", aby aktywować wyszukiwanie świadome kryteriów
- Buduj agentów, którzy rozumują nie tylko z relewancją, ale kontekstową ważnością

## Niestandardowe instrukcje

Ulepsz doświadczenie produktu dodając niestandardowe instrukcje dostosowane do twoich potrzeb

🔐 Mem0 jest teraz zgodny z SOC 2 i HIPAA!

### Wprowadzenie do niestandardowych instrukcji
Niestandardowe instrukcje pozwalają zdefiniować konkretne wytyczne dla twojego projektu. Ta funkcja pomaga zapewnić spójność i zapewnia jasny kierunek obsługi wymagań specyficznych dla projektu.

Niestandardowe instrukcje są szczególnie przydatne, gdy chcesz:

- Zdefiniować, jak informacje powinny być wydobywane z konwersacji
- Określić, jakie rodzaje danych powinny być przechwytywane lub ignorowane
- Ustawić zasady kategoryzowania i organizowania wspomnień
- Utrzymać spójną obsługę wymagań specyficznych dla projektu

Gdy niestandardowe instrukcje są ustawione na poziomie projektu, będą stosowane do wszystkich nowych wspomnień dodanych w ramach tego projektu. To zapewnia, że twoje dane są przetwarzane zgodnie ze zdefiniowanymi wytycznymi w całym projekcie.

### Ustawianie niestandardowych instrukcji
Możesz ustawić niestandardowe instrukcje dla swojego projektu używając następującej metody:

Kod:
```python
# Zaktualizuj niestandardowe instrukcje
prompt ="""
Twoje zadanie: Wydobyć TYLKO informacje związane ze zdrowiem z konwersacji, koncentrując się na następujących obszarach:

1. Stan zdrowia, objawy i diagnozy:
   - Choroby, zaburzenia lub objawy (np. gorączka, cukrzyca).
   - Potwierdzone lub podejrzewane diagnozy.

2. Leki, terapie i procedury:
   - Leki na receptę lub bez recepty (nazwy, dawki).
   - Terapie, zabiegi lub procedury medyczne.

3. Dieta, ćwiczenia i sen:
   - Nawyki żywieniowe, rutyny fitness i wzorce snu.

4. Wizyty lekarskie i terminy:
   - Przeszłe, nadchodzące lub regularne wizyty medyczne.

5. Metryki zdrowotne:
   - Dane takie jak waga, ciśnienie krwi, cholesterol lub poziom cukru.

Wytyczne:
- Skup się wyłącznie na treści związanej ze zdrowiem.
- Zachowaj jasność i dokładność kontekstu podczas rejestrowania.
"""
response = client.update_project(custom_instructions=prompt)
print(response)
```

Możesz również pobrać bieżące niestandardowe instrukcje:

Kod:
```python
# Pobierz bieżące niestandardowe instrukcje
response = client.get_project(fields=["custom_instructions"])
print(response)
```

## Czat grupowy

Włącz konwersacje wieloosobowe z automatycznym przypisywaniem pamięci do poszczególnych mówców

📢 Ogłaszamy naszą pracę badawczą: Mem0 osiąga o 26% wyższą dokładność niż OpenAI Memory, o 91% niższe opóźnienie i 90% oszczędności tokenów!

### Wprowadzenie do czatu grupowego

#### Przegląd
Funkcja czatu grupowego umożliwia Mem0 przetwarzanie konwersacji z udziałem wielu uczestników i automatyczne przypisywanie wspomnień do poszczególnych mówców. Pozwala to na precyzyjne śledzenie preferencji, cech i wkładów każdego uczestnika w dyskusjach zespołowych, spotkaniach zespołowych lub konwersacjach wieloagentowych.

Gdy podajesz wiadomości z nazwami uczestników, Mem0 automatycznie:

- Wydobywa wspomnienia z wiadomości każdego uczestnika osobno
- Przypisuje każdą pamięć do właściwego mówcy używając jego imienia jako user_id lub agent_id
- Utrzymuje indywidualne profile pamięci dla każdego uczestnika

#### Jak działa czat grupowy
Mem0 automatycznie wykrywa scenariusze czatu grupowego, gdy wiadomości zawierają pole name:

```json
{
  "role": "user",
  "name": "Alice",
  "content": "Hej zespół, myślę że powinniśmy użyć React do frontendu"
}
```

Gdy nazwy są obecne, Mem0:

- Formatuje wiadomości jako "Alice (user): treść" do przetwarzania
- Wydobywa wspomnienia z właściwą atrybucją do każdego mówcy
- Przechowuje wspomnienia z nazwą mówcy jako user_id (dla użytkowników) lub agent_id (dla asystentów/agentów)

#### Zasady przypisywania pamięci
- Wiadomości użytkownika: Pole name staje się user_id w przechowywanych wspomnieniach
- Wiadomości asystenta/agenta: Pole name staje się agent_id w przechowywanych wspomnieniach
- Wiadomości bez nazw: Wracają do standardowego przetwarzania używając roli jako identyfikatora

### Używanie czatu grupowego

#### Podstawowy czat grupowy
Dodaj wspomnienia z konwersacji wieloosobowej:

Python:
```python
from mem0 import MemoryClient

client = MemoryClient(api_key="twój-klucz-api")

# Czat grupowy z wieloma użytkownikami
messages = [
    {"role": "user", "name": "Alice", "content": "Hej zespół, myślę że powinniśmy użyć React do frontendu"},
    {"role": "user", "name": "Bob", "content": "Nie zgadzam się, Vue.js byłby lepszy dla naszego przypadku użycia"},
    {"role": "user", "name": "Charlie", "content": "A co z rozważeniem Angular? Ma świetne wsparcie korporacyjne"},
    {"role": "assistant", "content": "Wszystkie trzy frameworki mają swoje zalety. Pozwól mi podsumować plusy i minusy każdego."}
]

response = client.add(
    messages,
    run_id="czat_grupowy_1",
    output_format="v1.1",
    infer=True
)
print(response)
```

### Pobieranie wspomnień czatu grupowego

#### Pobierz wszystkie wspomnienia z sesji
Pobierz wszystkie wspomnienia z konkretnej sesji czatu grupowego:

Python:
```python
# Pobierz wszystkie wspomnienia dla konkretnego run_id
filters = {
    "AND": [
        {"user_id": "*"},
        {"run_id": "czat_grupowy_1"}
    ]
}

all_memories = client.get_all(version="v2", filters=filters, page=1)
print(all_memories)
```

#### Pobierz wspomnienia konkretnego uczestnika
Pobierz wspomnienia od konkretnego uczestnika w czacie grupowym:

Python:
```python
# Pobierz wspomnienia dla konkretnego uczestnika
filters = {
    "AND": [
        {"user_id": "charlie"},
        {"run_id": "czat_grupowy_1"}
    ]
}

charlie_memories = client.get_all(version="v2", filters=filters, page=1)
print(charlie_memories)
```

#### Szukaj w kontekście czatu grupowego
Szukaj konkretnych informacji w sesji czatu grupowego:

Python:
```python
# Szukaj w kontekście czatu grupowego
filters = {
    "AND": [
        {"user_id": "charlie"},
        {"run_id": "czat_grupowy_1"}
    ]
}

search_response = client.search(
    query="Jakie są zadania?",
    filters=filters,
    version="v2"
)
print(search_response)
```

### Obsługa trybu asynchronicznego
Czat grupowy obsługuje również przetwarzanie asynchroniczne dla lepszej wydajności:

Python:
```python
# Czat grupowy z trybem asynchronicznym
response = client.add(
    messages,
    run_id="czatgrupowy_async",
    output_format="v1.1",
    infer=True,
    async_mode=True
)
print(response)
```

### Wymagania formatu wiadomości

#### Wymagane pola
Każda wiadomość w czacie grupowym musi zawierać:

- role: Rola uczestnika ("user", "assistant", "agent")
- content: Treść wiadomości
- name: Nazwa uczestnika (wymagana do wykrycia czatu grupowego)

#### Przykładowa struktura wiadomości
```json
{
  "role": "user",
  "name": "Alice",
  "content": "Myślę że powinniśmy użyć React do frontendu"
}
```

#### Obsługiwane role
- user: Uczestnicy ludzcy (wspomnienia przechowywane z user_id)
- assistant: Asystenci AI (wspomnienia przechowywane z agent_id)

### Najlepsze praktyki
1. Spójne nazewnictwo: Używaj spójnych nazw dla uczestników między sesjami, aby utrzymać właściwe przypisanie pamięci.

2. Jasne przypisanie ról: Upewnij się, że każdy uczestnik ma prawidłową rolę (user, assistant lub agent) dla właściwej kategoryzacji pamięci.

3. Zarządzanie sesjami: Używaj znaczących wartości run_id do organizowania sesji czatu grupowego i umożliwienia łatwego pobierania.

4. Filtrowanie pamięci: Używaj filtrów do pobierania wspomnień od konkretnych uczestników lub sesji w razie potrzeby.

5. Przetwarzanie asynchroniczne: Użyj async_mode=True dla dużych konwersacji grupowych, aby poprawić wydajność.

6. Kontekst wyszukiwania: Wykorzystaj funkcjonalność wyszukiwania do znalezienia konkretnych informacji w kontekstach czatu grupowego.

### Przypadki użycia
- Spotkania zespołowe: Śledź indywidualne preferencje i wkłady członków zespołu
- Obsługa klienta: Utrzymuj oddzielne profile pamięci dla różnych klientów
- Systemy wieloagentowe: Zarządzaj konwersacjami z wieloma asystentami AI
- Projekty współpracy: Śledź indywidualne preferencje i obszary ekspertyzy
- Dyskusje grupowe: Utrzymuj kontekst dla punktów widzenia każdego uczestnika

Jeśli masz jakiekolwiek pytania, skontaktuj się z nami używając jednej z następujących metod: