# backend/app/services/outreach/router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Optional
from app.db.session import get_db
from app.db.models import MediaCoverage, BlogArticle, GalleryItem, VideoLecture
from app.api.dependencies import get_current_user

router = APIRouter()

class MediaSchema(BaseModel): title: str; outlet_name: str; year: int; link: Optional[str] = None
class BlogSchema(BaseModel): title: str; platform: Optional[str] = None; year: int; description: Optional[str] = None; link: Optional[str] = None
class GallerySchema(BaseModel): title: str; year: int; description: Optional[str] = None; image_url: str
class VideoSchema(BaseModel): title: str; event_name: Optional[str] = None; year: int; video_url: str

def create_crud_routes(model, schema, prefix, tags):
    r = APIRouter(prefix=prefix, tags=tags)
    
    @r.get("/")
    async def get_all(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        res = await db.execute(select(model).where(model.tenant_id == current_user["tenant_id"]).order_by(model.year.desc()))
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
        res = await db.execute(select(model).where(model.tenant_id == tenant_id).order_by(model.year.desc()))
        return res.scalars().all()
    
    return r

router.include_router(create_crud_routes(MediaCoverage, MediaSchema, "/media", ["Media Coverage"]))
router.include_router(create_crud_routes(BlogArticle, BlogSchema, "/blog", ["Blog Articles"]))
router.include_router(create_crud_routes(GalleryItem, GallerySchema, "/gallery", ["Gallery"]))
router.include_router(create_crud_routes(VideoLecture, VideoSchema, "/videos", ["Video Lectures"]))