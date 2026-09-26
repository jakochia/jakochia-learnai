from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, Document, Quiz, QuizAttempt, StudySession
from app.schemas import QuizRequest, QuizOut, QuizSubmit, QuizResult
from app.ai import generate_quiz_json

router = APIRouter(prefix="/api/quizzes", tags=["quizzes"])


@router.post("/generate", response_model=QuizOut)
def generate(req: QuizRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(Document).filter(Document.owner_id == user.id)
    if req.document_id:
        q = q.filter(Document.id == req.document_id)
    docs = q.all()
    if not docs:
        raise HTTPException(status_code=400, detail="No matching documents")

    context = "\n\n".join(d.content[:6000] for d in docs)
    raw = generate_quiz_json(context, req.num_questions, req.difficulty, req.question_types)
    if not raw:
        raise HTTPException(status_code=502, detail="AI failed to generate quiz. Check OPENAI_API_KEY.")

    questions = []
    for i, item in enumerate(raw, start=1):
        questions.append({
            "id": i,
            "type": item.get("type", "multiple_choice"),
            "question": item.get("question", ""),
            "options": item.get("options") or [],
            "answer": str(item.get("answer", "")),
            "topic": item.get("topic", "General"),
        })

    quiz = Quiz(
        owner_id=user.id,
        document_id=req.document_id,
        title=f"{req.difficulty.title()} quiz - {req.num_questions} Q",
        difficulty=req.difficulty,
        questions=questions,
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    db.add(StudySession(owner_id=user.id, activity="quiz_generate", minutes=2))
    db.commit()
    return QuizOut(id=quiz.id, title=quiz.title, difficulty=quiz.difficulty, questions=quiz.questions)


@router.get("/{quiz_id}", response_model=QuizOut)
def get_quiz(quiz_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.owner_id == user.id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Not found")
    return QuizOut(id=quiz.id, title=quiz.title, difficulty=quiz.difficulty, questions=quiz.questions)


@router.post("/{quiz_id}/submit", response_model=QuizResult)
def submit(quiz_id: int, payload: QuizSubmit, db: Session = Depends(get_db),
           user: User = Depends(get_current_user)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.owner_id == user.id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Not found")

    correct = 0
    weak = []
    total = len(quiz.questions)
    for q, given in zip(quiz.questions, payload.answers):
        if _normalize(str(given)) == _normalize(str(q.get("answer", ""))):
            correct += 1
        else:
            t = q.get("topic", "General")
            if t not in weak:
                weak.append(t)

    score = round(100.0 * correct / max(total, 1), 2)
    attempt = QuizAttempt(
        quiz_id=quiz.id, user_id=user.id,
        score=score, total=total, correct=correct, weak_topics=weak,
    )
    db.add(attempt)

    user.xp = (user.xp or 0) + correct * 10
    user.level = 1 + (user.xp // 500)
    db.add(StudySession(owner_id=user.id, activity="quiz", minutes=max(2, total // 2)))
    db.commit()

    return QuizResult(score=score, correct=correct, total=total, weak_topics=weak)


def _normalize(s: str) -> str:
    return "".join(ch for ch in s.lower().strip() if ch.isalnum())
