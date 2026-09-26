from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    theme: str
    xp: int
    level: int
    streak_days: int
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class DocumentOut(BaseModel):
    id: int
    filename: str
    subject: str
    topics: List[str]
    difficulty: str
    page_count: int
    char_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    question: str
    difficulty: str = "college"
    document_ids: Optional[List[int]] = None


class SourceRef(BaseModel):
    document_id: int
    filename: str
    page: int
    section: str
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceRef]


class QuizRequest(BaseModel):
    document_id: Optional[int] = None
    topic: Optional[str] = None
    num_questions: int = 10
    difficulty: str = "easy"
    question_types: List[str] = ["multiple_choice"]


class QuizQuestion(BaseModel):
    id: int
    type: str
    question: str
    options: Optional[List[str]] = None
    answer: str
    topic: Optional[str] = "General"


class QuizOut(BaseModel):
    id: int
    title: str
    difficulty: str
    questions: List[QuizQuestion]

    class Config:
        from_attributes = True


class QuizSubmit(BaseModel):
    answers: List[str]


class QuizResult(BaseModel):
    score: float
    correct: int
    total: int
    weak_topics: List[str]


class FlashcardOut(BaseModel):
    id: int
    front: str
    back: str
    topic: str
    ease: float
    interval: int
    repetitions: int

    class Config:
        from_attributes = True


class FlashcardReview(BaseModel):
    rating: int


class FlashcardGenerate(BaseModel):
    document_id: int
    count: int = 10


class PlanRequest(BaseModel):
    subject: str
    exam_date: str
    hours_per_day: float = 1.0
    weak_topics: Optional[List[str]] = None


class AnalyticsOverview(BaseModel):
    study_time_minutes: int
    questions_answered: int
    quiz_average: float
    streak_days: int
    xp: int
    level: int
    subjects: List[dict]
    insights: dict
