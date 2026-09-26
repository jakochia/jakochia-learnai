from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, StudySession
from app.schemas import ChatRequest, ChatResponse, SourceRef
from app.rag import retrieve
from app.ai import answer_with_context

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    chunks = retrieve(db, req.question, user.id, req.document_ids)
    if not chunks:
        return ChatResponse(
            answer=(
                "I couldn't find anything in your uploaded materials about that. "
                "Try uploading a relevant document, or rephrase your question."
            ),
            sources=[],
        )
    answer = answer_with_context(req.question, chunks, req.difficulty)
    sources = [
        SourceRef(
            document_id=c["document_id"],
            filename=c["filename"],
            page=c["page"],
            section=c["section"],
            snippet=c["content"][:240],
        )
        for c in chunks
    ]
    db.add(StudySession(owner_id=user.id, activity="chat", minutes=1))
    db.commit()
    return ChatResponse(answer=answer, sources=sources)
