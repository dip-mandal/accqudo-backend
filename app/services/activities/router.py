# backend/app/services/activities/router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Optional
from app.db.session import get_db
from app.db.models import TeachingPhilosophy, AdministrativeRole, ConferenceOrganization, ReviewerRole
from app.api.dependencies import get_current_user

router = APIRouter()

class PhilosophySchema(BaseModel): title: str; content: str; link: Optional[str] = None
class AdminSchema(BaseModel): role: str; institution: str; start_year: int; end_year: Optional[int] = None
class ConfSchema(BaseModel): role: str; conference_name: str; year: int; link: Optional[str] = None
class ReviewerSchema(BaseModel): journal_name: str; publisher: Optional[str] = None; year: Optional[int] = None

def create_crud_routes(model, schema, prefix, tags):
    r = APIRouter(prefix=prefix, tags=tags)
    
    @r.get("/")
    async def get_all(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        order_col = getattr(model, 'year', getattr(model, 'start_year', None))
        query = select(model).where(model.tenant_id == current_user["tenant_id"])
        if order_col: query = query.order_by(order_col.desc())
        res = await db.execute(query)
        return res.scalars().all()

    @r.post("/")
    async def create(data: schema, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        item = model(tenant_id=current_user["tenant_id"], **data.dict())
        db.add(item); await db.commit(); await db.refresh(item)
        return item

    @r.put("/{id}")
    async def update(id: str, data: schema, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        res = await db.execute(select(model).where(model.id == id, model.tenant_id == current_user["tenant_id"]))
        item = res.scalars().first()
        if not item: raise HTTPException(404)
        for k, v in data.dict(exclude_unset=True).items(): setattr(item, k, v)
        await db.commit(); await db.refresh(item)
        return item

    @r.delete("/{id}")
    async def delete(id: str, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        res = await db.execute(select(model).where(model.id == id, model.tenant_id == current_user["tenant_id"]))
        item = res.scalars().first()
        if not item: raise HTTPException(404)
        await db.delete(item); await db.commit()
        return {"msg": "Deleted"}

    @r.get("/public/{tenant_id}")
    async def get_public(tenant_id: str, db: AsyncSession = Depends(get_db)):
        order_col = getattr(model, 'year', getattr(model, 'start_year', None))
        query = select(model).where(model.tenant_id == tenant_id)
        if order_col: query = query.order_by(order_col.desc())
        res = await db.execute(query)
        return res.scalars().all()
    
    return r

router.include_router(create_crud_routes(TeachingPhilosophy, PhilosophySchema, "/philosophy", ["Teaching Philosophy"]))
router.include_router(create_crud_routes(AdministrativeRole, AdminSchema, "/administrative", ["Administrative Roles"]))
router.include_router(create_crud_routes(ConferenceOrganization, ConfSchema, "/conferences", ["Conference Organization"]))
router.include_router(create_crud_routes(ReviewerRole, ReviewerSchema, "/reviewer", ["Reviewer Roles"]))