from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, StudySession, QuizAttempt, Document
from app.schemas import AnalyticsOverview

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
def overview(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    total_minutes = db.query(func.coalesce(func.sum(StudySession.minutes), 0)).filter(
        StudySession.owner_id == user.id
    ).scalar() or 0

    attempts = db.query(QuizAttempt).filter(QuizAttempt.user_id == user.id).all()
    answered = sum(a.total for a in attempts)
    avg = round(sum(a.score for a in attempts) / len(attempts), 2) if attempts else 0.0

    docs = db.query(Document).filter(Document.owner_id == user.id).all()
    subject_counts = {}
    for d in docs:
        subject_counts[d.subject] = subject_counts.get(d.subject, 0) + 1

    subjects = []
    for subj, cnt in subject_counts.items():
        subj_attempts = [a for a in attempts if any(subj.lower() in t.lower() for t in (a.weak_topics or []))]
        score = (sum(a.score for a in subj_attempts) / len(subj_attempts)) if subj_attempts else (avg or 0)
        subjects.append({"name": subj, "score": round(score, 1), "documents": cnt})

    weak_topics = {}
    for a in attempts:
        for t in (a.weak_topics or []):
            weak_topics[t] = weak_topics.get(t, 0) + 1
    sorted_weak = sorted(weak_topics.items(), key=lambda kv: kv[1], reverse=True)
    strongest = max(subjects, key=lambda s: s["score"], default={"name": "-", "score": 0})["name"]
    weakest = sorted_weak[0][0] if sorted_weak else (min(subjects, key=lambda s: s["score"], default={"name": "-"})["name"])

    insights = {
        "strongest_area": strongest,
        "needs_improvement": weakest,
        "weak_topics": [{"topic": t, "misses": c} for t, c in sorted_weak[:5]],
        "suggested_next_steps": [
            f"Review {weakest}",
            f"Complete 10 practice questions on {weakest}",
            "Take an adaptive quiz to confirm improvement",
        ],
    }

    return AnalyticsOverview(
        study_time_minutes=int(total_minutes),
        questions_answered=int(answered),
        quiz_average=float(avg),
        streak_days=user.streak_days or 0,
        xp=user.xp or 0,
        level=user.level or 1,
        subjects=subjects,
        insights=insights,
    )


@router.get("/recent")
def recent_activity(limit: int = 10, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    rows = (
        db.query(StudySession)
        .filter(StudySession.owner_id == user.id)
        .order_by(StudySession.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {"activity": r.activity, "minutes": r.minutes, "created_at": r.created_at}
        for r in rows
    ]
