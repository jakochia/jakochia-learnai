import json
from typing import List, Dict
from app.config import settings


def _make_client():
    """Build the OpenAI client fresh — reads settings at call time, not import time."""
    if not settings.OPENAI_API_KEY:
        return None
    try:
        from openai import OpenAI
        return OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )
    except Exception as e:
        print(f"[ai.py] client init failed: {e}")
        return None


def chat_completion(messages: List[Dict[str, str]], temperature: float = 0.3) -> str:
    client = _make_client()
    if client:
        try:
            resp = client.chat.completions.create(
                model=settings.CHAT_MODEL,
                messages=messages,
                temperature=temperature,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            print(f"\n[ai.py] Groq call failed:")
            print(f"        model  = {settings.CHAT_MODEL}")
            print(f"        error  = {type(e).__name__}: {e}\n")
            return ""
    user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
    return (
        "No API key configured - returning stub answer.\n\n"
        f"You asked: {user_msg}\n\n"
        "Set OPENAI_API_KEY in backend/.env to get real AI answers."
    )


DIFFICULTY_PROMPTS = {
    "beginner": "Explain like the student is a complete beginner. Use simple analogies. Avoid jargon.",
    "highschool": "Explain at a high-school level. Clear, friendly, with a real-world example.",
    "college": "Explain at a college level. Precise terminology with brief clarification.",
    "technical": "Explain technically, assuming domain knowledge. Use correct terminology.",
    "expert": "Explain at expert level. Be dense, precise, and reference deeper implications.",
}


def answer_with_context(question: str, context_chunks: List[Dict], difficulty: str) -> str:
    style = DIFFICULTY_PROMPTS.get(difficulty, DIFFICULTY_PROMPTS["college"])
    context = "\n\n---\n\n".join(
        f"[{i+1}] (from {c['filename']} page {c['page']}, section '{c['section']}')\n{c['content']}"
        for i, c in enumerate(context_chunks)
    )
    system = (
        "You are Jakochia LearnAI, a study assistant. Answer the student's question USING ONLY the "
        "provided context. If the context doesn't cover it, say so honestly. "
        "Cite sources inline like [1], [2]. Be concise and structured.\n\n"
        f"STYLE: {style}"
    )
    user = f"CONTEXT:\n{context}\n\nQUESTION: {question}"
    return chat_completion(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.2,
    )


def generate_quiz_json(context: str, num_questions: int, difficulty: str, types: List[str]) -> List[dict]:
    system = (
        "You are a quiz generator. Output ONLY valid JSON: an array of question objects. "
        "Each object: {id:int, type:'multiple_choice'|'true_false'|'short_answer', "
        "question:str, options?:[str], answer:str, topic:str}. No commentary."
    )
    user = (
        f"Generate {num_questions} {difficulty} questions from this material. "
        f"Allowed types: {types}.\n\nMATERIAL:\n{context[:4000]}"
    )
    raw = chat_completion(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.5,
    )
    return _safe_json_list(raw)


def generate_flashcards_json(context: str, count: int) -> List[dict]:
    system = (
        "You are a flashcard generator. Output ONLY valid JSON: an array of "
        "{front:str, back:str, topic:str}. No commentary."
    )
    user = f"Create {count} flashcards from:\n\n{context[:4000]}"
    raw = chat_completion(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.5,
    )
    return _safe_json_list(raw)


def generate_plan_json(subject: str, exam_date: str, hours_per_day: float, weak_topics: List[str]) -> List[dict]:
    system = (
        "You are a study planner. Output ONLY valid JSON: array of weeks "
        "[{week:int, focus:str, topics:[str], tasks:[str]}]. No commentary."
    )
    user = (
        f"Create a study plan for subject '{subject}', exam on {exam_date}, "
        f"{hours_per_day} hours/day. Weak topics to emphasize: {weak_topics}."
    )
    raw = chat_completion(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.5,
    )
    return _safe_json_list(raw)


def _safe_json_list(raw: str) -> List[dict]:
    if not raw:
        print("[ai.py] AI returned empty string")
        return []
    text = raw.strip()
    if text.startswith("```"):
        text = text[3:]
        if text[:4].lower() == "json":
            text = text[4:]
        if text.endswith("```"):
            text = text[:-3]
    text = text.strip()
    try:
        obj = json.loads(text)
        if isinstance(obj, list):
            return obj
        if isinstance(obj, dict) and "questions" in obj:
            return obj["questions"]
    except Exception:
        pass
    start, end = text.find("["), text.rfind("]")
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except Exception as e:
            print(f"[ai.py] JSON slice parse failed: {e}")
    print(f"[ai.py] Could not parse JSON. First 600 chars:\n{raw[:600]}")
    return []