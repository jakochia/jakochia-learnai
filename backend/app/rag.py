import re
from collections import Counter
from math import log
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import Chunk, Document

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "of", "to", "in", "on", "for", "with", "at", "by", "from", "as",
    "and", "or", "but", "if", "then", "so", "than", "that", "this",
    "these", "those", "it", "its", "i", "you", "he", "she", "we", "they",
    "what", "which", "who", "whom", "whose", "when", "where", "why", "how",
    "do", "does", "did", "done", "have", "has", "had", "will", "would",
    "can", "could", "should", "may", "might", "must", "not", "no", "yes",
}


def tokenize(text: str) -> List[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in words if len(w) > 1 and w not in STOPWORDS]


def store_chunks(db: Session, document_id: int, chunks: List[str], pages: Optional[List[int]] = None):
    if not chunks:
        return
    for i, content in enumerate(chunks):
        page = pages[i] if pages and i < len(pages) else 1
        tokens = " ".join(tokenize(content))
        db.add(Chunk(
            document_id=document_id,
            content=content,
            page=page,
            section="",
            tokens=tokens,
        ))
    db.commit()


def retrieve(
    db: Session,
    question: str,
    user_id: int,
    document_ids: Optional[List[int]] = None,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    query_tokens = tokenize(question)
    if not query_tokens:
        return []

    q = (
        db.query(Chunk, Document)
        .join(Document, Document.id == Chunk.document_id)
        .filter(Document.owner_id == user_id)
    )
    if document_ids:
        q = q.filter(Document.id.in_(document_ids))
    rows = q.all()
    if not rows:
        return []

    df = Counter()
    tokenized_chunks = []
    for chunk, doc in rows:
        toks = chunk.tokens.split() if chunk.tokens else tokenize(chunk.content)
        tokenized_chunks.append((chunk, doc, toks))
        for t in set(toks):
            df[t] += 1

    n_docs = len(tokenized_chunks)
    query_set = list(dict.fromkeys(query_tokens))

    scored = []
    for chunk, doc, toks in tokenized_chunks:
        if not toks:
            continue
        tf = Counter(toks)
        score = 0.0
        for qt in query_set:
            if qt in tf:
                idf = log((n_docs + 1) / (df[qt] + 1)) + 1.0
                score += tf[qt] * idf
        if len(query_tokens) > 1:
            phrase = " ".join(query_tokens)
            if phrase in " ".join(toks):
                score += 5.0
        if score > 0:
            scored.append((score, chunk, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:top_k]

    max_score = top[0][0] if top else 1.0
    return [
        {
            "chunk_id": c.id,
            "content": c.content,
            "page": c.page or 1,
            "section": c.section or "",
            "document_id": d.id,
            "filename": d.filename,
            "score": round(s / max_score, 4),
        }
        for s, c, d in top
    ]
