from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Optional
from app.db.session import get_db
from app.db.models import Book
from app.api.dependencies import get_current_user

router = APIRouter()

class BookSchema(BaseModel):
    title: str
    publisher: str
    year: int
    isbn: Optional[str] = None

    file_link: Optional[str] = None
    external_link: Optional[str] = None
    thumbnail: Optional[str] = None

@router.get("/")
async def get_books(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book).where(Book.tenant_id == current_user["tenant_id"]).order_by(Book.year.desc()))
    return result.scalars().all()

@router.post("/")
async def add_book(data: BookSchema, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    new_item = Book(tenant_id=current_user["tenant_id"], **data.dict())
    db.add(new_item)
    await db.commit()
    return new_item

@router.put("/{id}")
async def update_book(id: str, data: BookSchema, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book).where(Book.id == id, Book.tenant_id == current_user["tenant_id"]))
    db_item = result.scalars().first()
    if not db_item: raise HTTPException(status_code=404)
    for key, value in data.dict(exclude_unset=True).items(): setattr(db_item, key, value)
    await db.commit()
    return db_item

@router.delete("/{id}")
async def delete_book(id: str, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book).where(Book.id == id, Book.tenant_id == current_user["tenant_id"]))
    item = result.scalars().first()
    if not item: raise HTTPException(status_code=404)
    await db.delete(item)
    await db.commit()
    return {"message": "Deleted"}

@router.get("/public/{tenant_id}")
async def get_public_books(tenant_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book).where(Book.tenant_id == tenant_id).order_by(Book.year.desc()))
    return result.scalars().all()