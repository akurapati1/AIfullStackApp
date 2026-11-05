from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import Settings, get_settings
from .db import Database
from .llm import LLMClient, LLMError, build_client
from .schemas import ChatRequest, ChatResponse, Conversation, Message

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def create_app(settings: Settings | None = None, llm: LLMClient | None = None) -> FastAPI:
    settings = settings or get_settings()
    db = Database(settings.database_path)
    client = llm or build_client(settings)

    app = FastAPI(title="AIfullStackApp", version="1.0.0", description="Full-stack AI chat application")

    def get_db() -> Database:
        return db

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok", "provider": settings.llm_provider, "model": settings.llm_model}

    @app.get("/api/conversations", response_model=list[Conversation])
    def list_conversations(database: Database = Depends(get_db)):
        return database.list_conversations()

    @app.get("/api/conversations/{cid}/messages", response_model=list[Message])
    def get_messages(cid: str, database: Database = Depends(get_db)):
        if not database.get_conversation(cid):
            raise HTTPException(404, "Conversation not found")
        return database.get_messages(cid)

    @app.delete("/api/conversations/{cid}", status_code=204)
    def delete_conversation(cid: str, database: Database = Depends(get_db)):
        if not database.delete_conversation(cid):
            raise HTTPException(404, "Conversation not found")

    @app.post("/api/chat", response_model=ChatResponse)
    def chat(req: ChatRequest, database: Database = Depends(get_db)):
        text = req.message.strip()
        if not text:
            raise HTTPException(422, "Message must not be blank")
        if req.conversation_id:
            if not database.get_conversation(req.conversation_id):
                raise HTTPException(404, "Conversation not found")
            cid = req.conversation_id
        else:
            cid = database.create_conversation(text)["id"]

        history = database.get_messages(cid, limit=settings.history_window)
        payload = [{"role": "system", "content": settings.system_prompt}]
        payload += [{"role": m["role"], "content": m["content"]} for m in history]
        payload.append({"role": "user", "content": text})

        try:
            reply = client.complete(payload)
        except LLMError as exc:
            raise HTTPException(502, str(exc)) from exc

        database.add_message(cid, "user", text)
        database.add_message(cid, "assistant", reply)
        return ChatResponse(conversation_id=cid, reply=reply)

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC_DIR / "index.html")

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app

