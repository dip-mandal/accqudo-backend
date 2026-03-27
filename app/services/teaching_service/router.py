# backend/app/services/teaching_service/router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Optional
from app.db.session import get_db
from app.db.models import Course, TeachingMaterial, Presentation, AcademicService
from app.api.dependencies import get_current_user

router = APIRouter()

# --- SCHEMAS (Updated to match your exact models) ---
class CourseSchema(BaseModel):
    course_name: str
    course_code: str
    level: str
    semester: str
    year: int
    syllabus_link: Optional[str] = None
    thumbnail_url: Optional[str] = None

class MaterialSchema(BaseModel): 
    title: str
    type: str
    course_name: Optional[str] = None
    link: Optional[str] = None
    thumbnail_url: Optional[str] = None

class PresentationSchema(BaseModel): 
    title: str
    event_name: str
    location: Optional[str] = None
    type: str
    year: int
    link: Optional[str] = None

class ServiceSchema(BaseModel): 
    role: str
    organization: str
    start_year: int
    end_year: Optional[int] = None

# --- FACTORY FUNCTION ---
def create_crud_routes(model, schema, prefix, tags):
    r = APIRouter(prefix=prefix, tags=tags)
    
    @r.get("/")
    async def get_all(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        # Determine which column to sort by
        order_col = getattr(model, 'year', getattr(model, 'start_year', getattr(model, 'title', None)))
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
        order_col = getattr(model, 'year', getattr(model, 'start_year', getattr(model, 'title', None)))
        query = select(model).where(model.tenant_id == tenant_id)
        if order_col: query = query.order_by(order_col.desc())
        res = await db.execute(query)
        return res.scalars().all()
    
    return r

router.include_router(create_crud_routes(Course, CourseSchema, "/courses", ["Courses"]))
router.include_router(create_crud_routes(TeachingMaterial, MaterialSchema, "/materials", ["Teaching Materials"]))
router.include_router(create_crud_routes(Presentation, PresentationSchema, "/presentations", ["Presentations"]))
router.include_router(create_crud_routes(AcademicService, ServiceSchema, "/services", ["Academic Service"]))