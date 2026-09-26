from datetime import datetime, timedelta, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, Document, Flashcard
from app.schemas import FlashcardOut, FlashcardReview, FlashcardGenerate
from app.ai import generate_flashcards_json

router = APIRouter(prefix="/api/flashcards", tags=["flashcards"])


@router.get("", response_model=List[FlashcardOut])
def list_cards(due_only: bool = False, db: Session = Depends(get_db),
               user: User = Depends(get_current_user)):
    q = db.query(Flashcard).filter(Flashcard.owner_id == user.id)
    if due_only:
        q = q.filter(Flashcard.due_at <= datetime.now(timezone.utc))
    return q.order_by(Flashcard.due_at.asc()).all()


@router.post("/generate", response_model=List[FlashcardOut])
def generate(req: FlashcardGenerate, db: Session = Depends(get_db),
             user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == req.document_id,
                                    Document.owner_id == user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    raw = generate_flashcards_json(doc.content[:12000], req.count)
    if not raw:
        raise HTTPException(status_code=502, detail="AI failed. Check OPENAI_API_KEY.")

    created = []
    for item in raw:
        fc = Flashcard(
            owner_id=user.id,
            document_id=doc.id,
            front=item.get("front", "").strip(),
            back=item.get("back", "").strip(),
            topic=item.get("topic", doc.subject),
        )
        if not fc.front or not fc.back:
            continue
        db.add(fc)
        created.append(fc)
    db.commit()
    for fc in created:
        db.refresh(fc)
    return created


@router.post("/{card_id}/review", response_model=FlashcardOut)
def review(card_id: int, payload: FlashcardReview,
           db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    fc = db.query(Flashcard).filter(Flashcard.id == card_id,
                                    Flashcard.owner_id == user.id).first()
    if not fc:
        raise HTTPException(status_code=404, detail="Not found")

    q = payload.rating
    if q == 0:
        fc.repetitions = 0
        fc.interval = 1
        fc.ease = max(1.3, (fc.ease or 2.5) - 0.2)
    else:
        fc.repetitions = (fc.repetitions or 0) + 1
        if fc.repetitions == 1:
            fc.interval = 1
        elif fc.repetitions == 2:
            fc.interval = 3
        else:
            fc.interval = int(round((fc.interval or 1) * (fc.ease or 2.5)))
        fc.ease = min(3.0, (fc.ease or 2.5) + (0.15 if q == 3 else 0.0))

    fc.due_at = datetime.now(timezone.utc) + timedelta(days=max(1, fc.interval))
    db.commit()
    db.refresh(fc)
    return fc
