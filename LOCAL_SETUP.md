# RELATRIX - Lokalne Środowisko Developerskie

## 🚀 Szybki Start

### Opcja 1: Kliknij RELATRIX na pulpicie
Po prostu **kliknij dwukrotnie** plik `RELATRIX.command` na pulpicie.

### Opcja 2: Terminal
```bash
cd /Users/maciejfiedler\ 1/Desktop/Projects/RELATRIX_V1
./scripts/start-relatrix.sh
```

## 🛠️ Pierwsza Instalacja (tylko raz)

### 1. Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Frontend
```bash
cd frontend
npm install
```

## 📋 Struktura Plików

```
RELATRIX_V1/
├── backend/
│   └── .env                 # Zmienne środowiskowe (NIE commituj!)
├── frontend/
│   └── .env                 # Zmienne środowiskowe (NIE commituj!)
├── scripts/
│   └── start-relatrix.sh    # Główny skrypt uruchamiający
└── LOCAL_SETUP.md          # Ten plik
```

## 🔐 Pliki .env

### Co zawierają:
- **backend/.env** - wszystkie klucze API, hasła, konfiguracja
- **frontend/.env** - URL do backendu i klucze Supabase

### WAŻNE:
- Te pliki **NIE są w Git** (są w .gitignore)
- Musisz je **skopiować ręcznie** między komputerami
- Zawierają **prawdziwe klucze API** - nie udostępniaj!

## 🖥️ Porty

- **Backend**: http://localhost:8001
- **Frontend**: http://localhost:3001
- **API Docs**: http://localhost:8001/docs

## 📊 Różnice: Lokalnie vs Railway

| Aspekt | Lokalnie | Railway |
|--------|----------|---------|
| Baza danych | SQLite (plik .db) | PostgreSQL |
| Redis | Opcjonalny | Wymagany |
| Porty | Backend: 8001, Frontend: 3001 | Oba: 8080 |
| Zmiany kodu | Natychmiastowe (hot reload) | Po git push (2-3 min) |
| Logi | W terminalu na żywo | railway logs |

## 🔄 Praca z Git

### Bezpieczny push:
```bash
git add .
git commit -m "feat: opis zmian"
git push origin main
```

**Git automatycznie pominie**:
- Pliki .env (klucze API)
- relatrix.db (baza SQLite)
- node_modules/, venv/

### Po git pull na innym komputerze:
1. Skopiuj pliki .env z poprzedniego komputera
2. Lub utworz nowe z .env.example i uzupełnij klucze

## 🐛 Rozwiązywanie Problemów

### "Virtual environment not found"
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### "Node modules not found"
```bash
cd frontend
npm install
```

### Port zajęty
Edytuj w plikach .env:
- Backend: zmień port 8001 na inny
- Frontend: automatycznie wybierze 3002 jeśli 3001 zajęty

### Brak kluczy API
Skopiuj z Railway lub poproś o klucze zespół.

## 💡 Przydatne Komendy

### Zobacz logi bazy SQLite:
```bash
sqlite3 backend/relatrix.db ".tables"
```

### Restart tylko backendu:
Ctrl+C w terminalu z backendem, potem:
```bash
cd backend && source venv/bin/activate && uvicorn main:app --port 8001 --reload
```

### Dodaj alias 'relatrix' (opcjonalne):
```bash
echo 'alias relatrix="~/Desktop/Projects/RELATRIX_V1/scripts/start-relatrix.sh"' >> ~/.zshrc
source ~/.zshrc
```

Potem możesz wpisać w terminalu tylko: `relatrix`

## 📝 Notatki

- SQLite automatycznie utworzy plik `relatrix.db` przy pierwszym uruchomieniu
- Hot reload działa dla obu: backend (Python) i frontend (React)
- Możesz mieć otwarte Railway i lokalne środowisko jednocześnie
- Zmiany w kodzie nie wpływają na Railway dopóki nie zrobisz push