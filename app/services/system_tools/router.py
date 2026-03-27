# backend/app/services/system_tools/router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Optional
from app.db.session import get_db
from app.db.models import GrantSummary, SiteSetting, Tenant
from app.api.dependencies import get_current_user

router = APIRouter()

class GrantSchema(BaseModel): total_funding: str; active_grants: int; summary_text: Optional[str] = None
class SettingsSchema(BaseModel): meta_title: Optional[str] = None; meta_description: Optional[str] = None; google_analytics_id: Optional[str] = None
class DomainSchema(BaseModel): custom_domain: str

# --- GRANTS SUMMARY ---
@router.get("/grants-summary")
async def get_grants(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(GrantSummary).where(GrantSummary.tenant_id == current_user["tenant_id"]))
    return res.scalars().first() or {}

@router.put("/grants-summary")
async def update_grants(data: GrantSchema, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(GrantSummary).where(GrantSummary.tenant_id == current_user["tenant_id"]))
    item = res.scalars().first()
    if not item:
        item = GrantSummary(tenant_id=current_user["tenant_id"], **data.dict())
        db.add(item)
    else:
        for k, v in data.dict(exclude_unset=True).items(): setattr(item, k, v)
    await db.commit(); await db.refresh(item)
    return item

@router.get("/grants-summary/public/{tenant_id}")
async def public_grants(tenant_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(GrantSummary).where(GrantSummary.tenant_id == tenant_id))
    return res.scalars().first() or {}

# --- SITE SETTINGS (SEO & Analytics) ---
@router.get("/settings")
async def get_settings(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(SiteSetting).where(SiteSetting.tenant_id == current_user["tenant_id"]))
    return res.scalars().first() or {}

@router.put("/settings")
async def update_settings(data: SettingsSchema, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(SiteSetting).where(SiteSetting.tenant_id == current_user["tenant_id"]))
    item = res.scalars().first()
    if not item:
        item = SiteSetting(tenant_id=current_user["tenant_id"], **data.dict(exclude_unset=True))
        db.add(item)
    else:
        for k, v in data.dict(exclude_unset=True).items(): setattr(item, k, v)
    await db.commit(); await db.refresh(item)
    return item

# --- CUSTOM DOMAIN ---
@router.get("/domain")
async def get_domain(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Tenant).where(Tenant.id == current_user["tenant_id"]))
    t = res.scalars().first()
    return {"custom_domain": t.custom_domain} if t else {}

@router.put("/domain")
async def update_domain(data: DomainSchema, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Tenant).where(Tenant.id == current_user["tenant_id"]))
    t = res.scalars().first()
    t.custom_domain = data.custom_domain
    await db.commit()
    return {"custom_domain": t.custom_domain}