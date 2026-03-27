# backend/app/services/ai_suite/router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
import ollama # 🌟 The Local AI engine

from app.db.session import get_db
from app.db.models import NewsletterSubscriber, Tenant
from app.api.dependencies import get_current_user

router = APIRouter()

class SubscriberSchema(BaseModel): email: str
class AIBioRequest(BaseModel): keywords: str
class AISummaryRequest(BaseModel): text: str

# --- NEWSLETTER (Unchanged) ---
@router.get("/newsletter")
async def get_subscribers(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(NewsletterSubscriber).where(NewsletterSubscriber.tenant_id == current_user["tenant_id"]).order_by(NewsletterSubscriber.subscribed_at.desc()))
    return res.scalars().all()

@router.post("/newsletter")
async def add_subscriber(data: SubscriberSchema, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    sub = NewsletterSubscriber(tenant_id=current_user["tenant_id"], email=data.email)
    db.add(sub); await db.commit(); await db.refresh(sub)
    return sub

@router.delete("/newsletter/{id}")
async def remove_subscriber(id: str, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(NewsletterSubscriber).where(NewsletterSubscriber.id == id, NewsletterSubscriber.tenant_id == current_user["tenant_id"]))
    sub = res.scalars().first()
    if sub: await db.delete(sub); await db.commit()
    return {"msg": "Deleted"}


# --- 🌟 REAL LOCAL AI ENDPOINTS 🌟 ---

@router.post("/ai/generate-bio")
async def generate_bio(req: AIBioRequest, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # 1. Fetch the user's REAL name from the database
    tenant_res = await db.execute(select(Tenant).where(Tenant.id == current_user["tenant_id"]))
    tenant = tenant_res.scalars().first()
    real_name = tenant.name if tenant else "the researcher"

    # 2. Inject the real name into a stricter prompt
    prompt = f"""
    Write a highly professional, academic biography (about 3 sentences long) for {real_name}, who specializes in: {req.keywords}. 
    Write in the third person. 
    Do NOT make up any fake universities, fake degrees, or fake affiliations. Keep it strictly focused on their expertise in the keywords provided.
    """
    
    # 3. Call Local AI
    response = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': prompt}])
    
    return {"generated_text": response['message']['content'].strip()}

@router.post("/ai/summarize")
async def summarize_research(req: AISummaryRequest, current_user: dict = Depends(get_current_user)):
    prompt = f"Summarize the following academic research text so that a general audience or undergraduate student can understand it. Keep it to one clear paragraph:\n\n{req.text}"
    
    response = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': prompt}])
    
    return {"generated_text": response['message']['content'].strip()}

@router.post("/ai/generate-cv")
async def generate_cv(current_user: dict = Depends(get_current_user)):
    # Note: True CV generation requires compiling a PDF (e.g., using pdfkit or LaTeX). 
    # For now, we will leave the mock URL here until we build the PDF generator logic.
    return {"download_url": "https://example.com/mock_cv_download.pdf"}