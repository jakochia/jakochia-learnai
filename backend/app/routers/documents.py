import os
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, Document, Chunk
from app.schemas import DocumentOut
from app.documents import extract_text, chunk_text, detect_metadata
from app.rag import store_chunks
from app.config import settings

router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED = {".pdf", ".docx", ".doc", ".pptx", ".ppt", ".txt", ".md",
           ".png", ".jpg", ".jpeg", ".webp", ".bmp"}


@router.get("", response_model=List[DocumentOut])
def list_documents(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    docs = (
        db.query(Document)
        .filter(Document.owner_id == user.id)
        .order_by(Document.created_at.desc())
        .all()
    )
    return docs


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ext = os.path.splitext(file.filename.lower())[1]
    if ext not in ALLOWED:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        text, page_count = extract_text(file.filename, data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse file: {e}")

    meta = detect_metadata(file.filename, text)

    doc = Document(
        owner_id=user.id,
        filename=file.filename,
        subject=meta["subject"],
        topics=meta["topics"],
        difficulty=meta["difficulty"],
        page_count=page_count,
        char_count=len(text),
        content=text[:200_000],
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    try:
        chunks = chunk_text(text, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
        store_chunks(db, doc.id, chunks)
    except Exception as e:
        print(f"[warn] chunk store failed for doc {doc.id}: {e}")

    return doc


@router.delete("/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id, Document.owner_id == user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    db.query(Chunk).filter(Chunk.document_id == doc.id).delete()
    db.delete(doc)
    db.commit()
    return {"ok": True}
