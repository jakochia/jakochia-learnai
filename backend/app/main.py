from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routers import auth, documents, chat, quizzes, flashcards, analytics, planner

app = FastAPI(
    title="Jakochia LearnAI API",
    description="AI-powered learning platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    try:
        init_db()
        print("[startup] DB initialized")
    except Exception as e:
        print(f"[startup] DB init failed: {e}")


@app.get("/")
def root():
    return {"app": "Jakochia LearnAI", "status": "online", "docs": "/docs"}


@app.get("/health")
def health():
    return {"ok": True}


app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(quizzes.router)
app.include_router(flashcards.router)
app.include_router(analytics.router)
app.include_router(planner.router)
