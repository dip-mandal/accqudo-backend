from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Optional

from app.db.session import get_db
from app.db.models import WorkingPaper
from app.api.dependencies import get_current_user

router = APIRouter()

# Schema updated to match your exact columns
class PaperCreate(BaseModel):
    title: str
    year: int
    status: Optional[str] = "In Preparation"
    abstract: Optional[str] = None
    link: Optional[str] = None

class PaperUpdate(BaseModel):
    title: Optional[str] = None
    year: Optional[int] = None
    status: Optional[str] = None
    abstract: Optional[str] = None
    link: Optional[str] = None

@router.get("/")
async def get_papers(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WorkingPaper).where(WorkingPaper.tenant_id == current_user["tenant_id"]).order_by(WorkingPaper.year.desc()))
    return result.scalars().all()

@router.post("/")
async def add_paper(paper: PaperCreate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    new_paper = WorkingPaper(tenant_id=current_user["tenant_id"], **paper.dict())
    db.add(new_paper)
    await db.commit()
    await db.refresh(new_paper)
    return new_paper

@router.put("/{id}")
async def update_paper(id: str, paper: PaperUpdate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WorkingPaper).where(WorkingPaper.id == id, WorkingPaper.tenant_id == current_user["tenant_id"]))
    db_paper = result.scalars().first()
    if not db_paper: raise HTTPException(status_code=404, detail="Not found")

    for key, value in paper.dict(exclude_unset=True).items():
        setattr(db_paper, key, value)

    await db.commit()
    await db.refresh(db_paper)
    return db_paper

@router.delete("/{id}")
async def delete_paper(id: str, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WorkingPaper).where(WorkingPaper.id == id, WorkingPaper.tenant_id == current_user["tenant_id"]))
    paper = result.scalars().first()
    if not paper: raise HTTPException(status_code=404, detail="Not found")
    await db.delete(paper)
    await db.commit()
    return {"message": "Deleted"}

@router.get("/public/{tenant_id}")
async def get_public_papers(tenant_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WorkingPaper).where(WorkingPaper.tenant_id == tenant_id).order_by(WorkingPaper.year.desc()))
    return result.scalars().all()