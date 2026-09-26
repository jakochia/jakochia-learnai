from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, StudyPlan, Document
from app.schemas import PlanRequest
from app.ai import generate_plan_json

router = APIRouter(prefix="/api/planner", tags=["planner"])


@router.post("/generate")
def generate(req: PlanRequest, db: Session = Depends(get_db),
             user: User = Depends(get_current_user)):
    weak = req.weak_topics or []
    if not weak:
        docs = db.query(Document).filter(Document.owner_id == user.id).all()
        for d in docs:
            weak.extend(d.topics or [])
        weak = list(dict.fromkeys(weak))[:6]

    plan = generate_plan_json(req.subject, req.exam_date, req.hours_per_day, weak)
    if not plan:
        raise HTTPException(status_code=502, detail="AI failed. Check OPENAI_API_KEY.")

    sp = StudyPlan(
        owner_id=user.id,
        subject=req.subject,
        exam_date=req.exam_date,
        hours_per_day=req.hours_per_day,
        plan=plan,
    )
    db.add(sp)
    db.commit()
    db.refresh(sp)
    return {"id": sp.id, "plan": sp.plan, "subject": sp.subject, "exam_date": sp.exam_date}


@router.get("/latest")
def latest(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sp = (
        db.query(StudyPlan)
        .filter(StudyPlan.owner_id == user.id)
        .order_by(StudyPlan.created_at.desc())
        .first()
    )
    if not sp:
        return {"plan": None}
    return {"id": sp.id, "plan": sp.plan, "subject": sp.subject,
            "exam_date": sp.exam_date, "hours_per_day": sp.hours_per_day}
