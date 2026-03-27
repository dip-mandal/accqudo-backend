from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Optional

from app.db.session import get_db
from app.db.models import Patent
from app.api.dependencies import get_current_user

router = APIRouter()

class PatentCreate(BaseModel):
    title: str
    patent_number: Optional[str] = None
    year: int
    status: str = "Granted"
    description: Optional[str] = None
    link: Optional[str] = None

class PatentUpdate(BaseModel):
    title: Optional[str] = None
    patent_number: Optional[str] = None
    year: Optional[int] = None
    status: Optional[str] = None
    description: Optional[str] = None
    link: Optional[str] = None

@router.get("/")
async def get_patents(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Patent).where(Patent.tenant_id == current_user["tenant_id"]).order_by(Patent.year.desc()))
    return result.scalars().all()

@router.post("/")
async def add_patent(patent: PatentCreate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    new_patent = Patent(tenant_id=current_user["tenant_id"], **patent.dict())
    db.add(new_patent)
    await db.commit()
    await db.refresh(new_patent)
    return new_patent

@router.put("/{id}")
async def update_patent(id: str, patent: PatentUpdate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Patent).where(Patent.id == id, Patent.tenant_id == current_user["tenant_id"]))
    db_patent = result.scalars().first()
    if not db_patent: raise HTTPException(status_code=404, detail="Not found")

    for key, value in patent.dict(exclude_unset=True).items():
        setattr(db_patent, key, value)

    await db.commit()
    await db.refresh(db_patent)
    return db_patent

@router.delete("/{id}")
async def delete_patent(id: str, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Patent).where(Patent.id == id, Patent.tenant_id == current_user["tenant_id"]))
    patent = result.scalars().first()
    if not patent: raise HTTPException(status_code=404, detail="Not found")
    await db.delete(patent)
    await db.commit()
    return {"message": "Deleted"}

@router.get("/public/{tenant_id}")
async def get_public_patents(tenant_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Patent).where(Patent.tenant_id == tenant_id).order_by(Patent.year.desc()))
    return result.scalars().all()