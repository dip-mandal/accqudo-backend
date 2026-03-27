# backend/app/services/research/router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Optional

from app.db.session import get_db
from app.db.models import ResearchInterest
from app.api.dependencies import get_current_user

router = APIRouter()

class InterestCreate(BaseModel):
    topic: str
    description: Optional[str] = None
    media_url: Optional[str] = None

class InterestUpdate(BaseModel):
    topic: Optional[str] = None
    description: Optional[str] = None
    media_url: Optional[str] = None

@router.get("/")
async def get_interests(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ResearchInterest).where(ResearchInterest.tenant_id == current_user["tenant_id"]))
    return result.scalars().all()

@router.post("/")
async def add_interest(interest: InterestCreate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    new_interest = ResearchInterest(tenant_id=current_user["tenant_id"], **interest.dict())
    db.add(new_interest)
    await db.commit()
    await db.refresh(new_interest)
    return new_interest

# 🌟 NEW: EDIT ENDPOINT
@router.put("/{id}")
async def update_interest(id: str, interest: InterestUpdate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ResearchInterest).where(ResearchInterest.id == id, ResearchInterest.tenant_id == current_user["tenant_id"]))
    db_interest = result.scalars().first()
    if not db_interest: raise HTTPException(status_code=404, detail="Not found")

    for key, value in interest.dict(exclude_unset=True).items():
        setattr(db_interest, key, value)

    await db.commit()
    await db.refresh(db_interest)
    return db_interest

@router.delete("/{id}")
async def delete_interest(id: str, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ResearchInterest).where(ResearchInterest.id == id, ResearchInterest.tenant_id == current_user["tenant_id"]))
    interest = result.scalars().first()
    if not interest: raise HTTPException(status_code=404, detail="Not found")
    await db.delete(interest)
    await db.commit()
    return {"message": "Deleted"}

@router.get("/public/{tenant_id}")
async def get_public_interests(tenant_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ResearchInterest).where(ResearchInterest.tenant_id == tenant_id))
    return result.scalars().all()