from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models
from database import engine, SessionLocal
from pydantic import BaseModel
from typing import List

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class FAQRequest(BaseModel):
    question: str
    answer: str

class FAQResponse(FAQRequest):
    id: int
    class Config:
        from_attributes = True

@app.get("/faqs", response_model=List[FAQResponse])
async def get_faqs(db: Session = Depends(get_db)):
    faqs = db.query(models.FAQs).all()
    return faqs

@app.post("/faqs", response_model=FAQResponse)
async def create_faq(faq: FAQRequest, db: Session = Depends(get_db)):
    existing_faq = db.query(models.FAQs).filter(models.FAQs.question == faq.question).first()
    if existing_faq:
        raise HTTPException(status_code=400, detail="FAQ with this question already exists")

    new_faq = models.FAQs(question=faq.question, answer=faq.answer)
    db.add(new_faq)
    db.commit()
    db.refresh(new_faq)
    return new_faq

@app.get("/faqs/{question}", response_model=List[FAQResponse])
async def get_faq(question: str, db: Session = Depends(get_db)):
    faqs = db.query(models.FAQs).filter(models.FAQs.question.ilike(f"%{question}%")).all()
    if not faqs:
        raise HTTPException(status_code=404, detail="No matching FAQ found")
    return faqs
