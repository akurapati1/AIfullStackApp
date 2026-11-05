# AIfullStackApp

A compact, production-shaped **full-stack AI chat application**: a FastAPI backend, a dependency-free web UI, SQLite-backed conversation history, a pluggable LLM layer (any OpenAI-compatible API), tests, Docker and CI.

## Features
- Multi-conversation chat UI with persistent history (SQLite)
- Provider-agnostic LLM client — works with OpenAI, Groq, OpenRouter or a local Ollama server
- Offline `echo` provider so the app runs end-to-end with **no API key**
- Typed REST API with validation, proper 404/422/502 error handling and auto-generated docs at `/docs`
- Model output rendered with `textContent` (no XSS), sliding history window to bound prompt size
- Pytest suite, Dockerfile + compose, GitHub Actions CI

## Architecture
```
Browser (static/)  ──HTTP/JSON──▶  FastAPI (app/main.py)
                                      ├── app/db.py   SQLite: conversations, messages
                                      └── app/llm.py  LLMClient ▶ OpenAI-compatible /chat/completions
```

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # defaults to the offline echo provider
uvicorn app.main:create_app --factory --reload
```
Open <http://localhost:8000> (API docs at `/docs`).

### Use a real model
Edit `.env`:
```
LLM_PROVIDER=openai-compatible
LLM_BASE_URL=https://api.groq.com/openai/v1   # or https://api.openai.com/v1, http://localhost:11434/v1 ...
LLM_API_KEY=your-key
LLM_MODEL=llama-3.1-8b-instant
```

### Docker
```bash
docker compose up --build
```

## API
| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Liveness + active provider |
| POST | `/api/chat` | `{message, conversation_id?}` → `{conversation_id, reply}` |
| GET | `/api/conversations` | List conversations |
| GET | `/api/conversations/{id}/messages` | Conversation history |
| DELETE | `/api/conversations/{id}` | Delete a conversation |

## Tests
```bash
pip install -r requirements-dev.txt
pytest
```

## Roadmap
Streaming responses (SSE), auth/multi-user, retrieval-augmented answers.
