# 🚀 DevCrew - AI Software Development Agency

A **DevCrew** egy CrewAI alapú, többszintű ügynökcsapat, amely szoftveres specifikációkat és forráskódot generál. A moduláris felépítésnek köszönhetően könnyen skálázható és az egyedi fejlesztési igényekhez igazítható.

## 🏗️ Projekt Struktúra

```text
DevCrew
├── dev_crew/
│   ├── app/
│   │   ├── agents/
│   │   │   └── factory.py        # Ügynökök (PO, Dev, QA, Security) definíciói
│   │   ├── config/
│   │   │   └── models.py         # LLM modellek és API beállítások
│   │   ├── tasks/
│   │   │   └── workflow.py       # Feladatok definíciói és végrehajtási logika
│   │   ├── utils/
│   │   │   ├── file_io.py        # Fájlkezelés (mentés, betöltés, állapot)
│   │   │   └── ui.py             # Felhasználói interakciók és visszajelzés
│   │   └── main.py              # Belépési pont (Manager)
│   └── requirements.txt         # Projekt függőségek
├── project_state/               # Generált projektek mentési helye (docs, spec, src)
└── .env                         # API kulcsok (OPENROUTER_API_KEY, GROQ_API_KEY)
```

## 🌟 Főbb Funkciók

- **Iteratív Tervezés:** Lehetőség van a specifikációk több körös finomítására a fejlesztés megkezdése előtt.
- **Kontextus-aware Visszajelzés:** Automatikusan felismeri, melyik dokumentumhoz fűzöl észrevételt.
- **Moduláris Architektúra:** Különválasztott felelősségi körök az ügynökök, feladatok és segédprogramok között.
- **Multi-Model Support:** Különböző LLM-ek (OpenRouter, Groq) használata feladattól függően.
- **Release Candidate (RC) Mód:** Opcionális mély tesztelés (QA) és biztonsági audit szakaszok.

## 🛠️ Telepítés és Futtatás

### 1. Előfeltételek
- Python 3.10+
- Virtuális környezet (.venv javasolt)

### 2. Telepítés
```bash
# Függőségek telepítése
pip install -r dev_crew/requirements.txt
```

### 3. Futtatás
A projekt gyökérkönyvtárából futtasd:
```bash
export PYTHONPATH=. 
python3 dev_crew/app/main.py
```

## 🤖 Aktív Ügynökök

1. **Product Owner:** Feladatok prioritizálása, specifikációk írása.
2. **Prompt Optimalizáló:** Technikai specifikációk és optimalizált promptok készítése.
3. **Senior Python Fejlesztő:** Forráskód generálása a specifikációk alapján.
4. **QA Mérnök:** Tesztek futtatása (Unit, E2E, UAT).
5. **Security Auditor:** Biztonsági rések keresése és audit jelentés készítése.
6. **Triage Specialista:** Hiba esetén a javítási stratégia meghatározása.

## 📂 Kimenetek
A generált fájlok a `project_state/<projekt_nev>/` mappába kerülnek:
- `docs/`: Üzleti specifikációk, audit jelentések.
- `spec/`: Technikai, optimalizált promptok.
- `src/`: Forráskód.
- `test/`: Teszt kódok és riportok.
- `summary.json`: Iterációs napló.
