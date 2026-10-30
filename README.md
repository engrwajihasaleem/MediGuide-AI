# MediGuide AI

An educational Streamlit + LangChain prototype for structured, safety-focused symptom guidance.

> **Medical safety notice:** This project is not a medical device and is not a doctor, diagnosis, emergency service, or treatment. It must not be used to make medical decisions. Consult a qualified healthcare professional. For urgent or life-threatening symptoms, contact local emergency services immediately.

## 1. Requirements

- Python 3.10–3.12 recommended
- OpenAI API key with API access enabled
- Internet connection

## 2. Setup (Windows PowerShell)

```powershell
mkdir MediGuideAI
cd MediGuideAI
# Extract the project ZIP into this folder first.

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Run

When the app opens, enter your OpenAI API key on the login screen. MediGuide validates it with an authenticated OpenAI models-list request before showing the application. The key is held in Streamlit session memory only; it is not written to `.env`, source files, or a local key store. Use **Log out** to clear the session key.

Never share your key. Avoid entering real patient-identifiable information in this educational prototype.


```powershell
streamlit run app.py
```

## 4. Project structure

```text
mediguide_ai/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── data/                     # created automatically; cache database
├── docs/
└── src/
    ├── __init__.py
    ├── config.py
    ├── auth.py
    ├── prompts.py
    ├── chains.py
    ├── cache_manager.py
    └── utils.py
```

## 5. Assignment concepts implemented

- `ChatOpenAI` model integration
- Reusable `PromptTemplate` formats patient fields; `ChatPromptTemplate` adds the system safety role and human input
- `SystemMessage`, `HumanMessage`, and `AIMessage` demonstration
- `LLMChain` for assessment (included because the assignment explicitly requires it)
- JSON-only response instruction, safe parsing, and schema validation
- `.stream()` with `st.write_stream()` for the human-readable explanation
- Both `InMemoryCache` and `SQLiteCache`
- Streamlit form, sidebar, tabs, metrics, alerts, and JSON download
- English and Urdu response language selection

## 6. Cache comparison

| Cache | Storage | Survives process restart? |
|---|---|---|
| InMemoryCache | RAM | No |
| SQLiteCache | `data/llm_cache.db` | Yes |

LangChain checks the configured cache automatically for matching model calls. Cache hits depend on identical prompts and model parameters. Do not assume a cache makes every repeated request identical if any input or configuration changes.

## 7. Important implementation notes

- The simple emergency phrase screen is only a conservative extra safeguard. It is not comprehensive and cannot rule out emergencies.
- A model-generated urgency category is not clinical triage.
- Do not use real patient-identifiable information in this educational prototype.
- The application does not prescribe, diagnose, or recommend medication changes.
- The assignment's required LLMChain API is retained for learning. LangChain APIs evolve; if a future release removes this import, use a compatible LangChain 0.3 environment or migrate the chain while documenting the rubric deviation.

## 8. Next development phase: Medical RAG

The assignment does not require RAG. A future extension can add carefully curated medical reference documents, ingestion, chunking, embeddings, retrieval and citations. It must preserve the safety rules above and must not treat retrieved text as a diagnosis or treatment plan.
