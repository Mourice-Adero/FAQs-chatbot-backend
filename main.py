from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import models
from database import engine, SessionLocal
from pydantic import BaseModel
from typing import List, Optional
from openai import OpenAI, OpenAIError
import openai
import os
from dotenv import load_dotenv

app = FastAPI(
    title="Smart Chatbot API",
    description="A FastAPI-based chatbot for answering FAQs using OpenAI's GPT API and a PostgreSQL database.",
    version="1.0.0",
    contact={
        "name": "Mourice Adero",
        "url": "https://github.com/Mourice-Adero/FAQs-chatbot.git",
        "email": "aderomourice7@gmail.com",
    },
    license_info={"name": "MTech Solutions"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

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

class AIResponse(BaseModel):
    ai_answer: Optional[str] = None
    ai_error: Optional[str] = None

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OpenAI API key is missing. Set it in the .env file.")

client = OpenAI(api_key=openai.api_key)

async def get_ai_response(question: str) -> AIResponse:
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": question},
            ]
        )

        ai_response = response.choices[0].message.content.strip() if response.choices else None

        if not ai_response:
            return AIResponse(ai_error="AI response is empty or invalid.")

        return AIResponse(ai_answer=ai_response)

    except OpenAIError as e:
        return AIResponse(ai_error=f"OpenAI API Error: {str(e)}")

    except Exception as e:
        return AIResponse(ai_error=f"Unexpected Error: {str(e)}")

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

    if faqs:
        return faqs

    ai_response = await get_ai_response(question)

    if ai_response.ai_error:
        raise HTTPException(status_code=500, detail=ai_response.ai_error)

    if ai_response.ai_answer:
        new_faq = models.FAQs(question=question, answer=ai_response.ai_answer)
        db.add(new_faq)
        db.commit()
        db.refresh(new_faq)
        return [new_faq]

    raise HTTPException(status_code=500, detail="AI did not provide a valid response.")

@app.delete("/faqs/{faq_id}")
async def delete_faq(faq_id: int, db: Session = Depends(get_db)):
    faq = db.query(models.FAQs).filter(models.FAQs.id == faq_id).first()

    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")

    db.delete(faq)
    db.commit()
    return {"message": "FAQ deleted successfully"}