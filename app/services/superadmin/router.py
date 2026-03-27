# backend/app/services/superadmin/router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from pydantic import BaseModel
import os
import uuid
import psutil # 🌟 NEW: For server health metrics

from app.db.session import get_db
from app.db.models import Tenant, Module, TenantModule
from app.api.dependencies import get_current_user

router = APIRouter()

# 🛡️ Bulletproof God Mode Security Check
def verify_superadmin(current_user = Depends(get_current_user)):
    superadmin_email = os.getenv("SUPERADMIN_EMAIL")
    
    if not superadmin_email:
        raise HTTPException(status_code=500, detail="Superadmin email not configured on server.")
        
    user_email = ""
    if isinstance(current_user, dict):
        user_email = current_user.get("sub") or current_user.get("email")
    else:
        user_email = getattr(current_user, "email", "")
        
    # 🌟 NEW: Force lowercase and strip hidden spaces/quotes
    safe_superadmin = str(superadmin_email).replace('"', '').replace("'", "").strip().lower()
    safe_user = str(user_email).strip().lower()
    
    # Print exactly what the backend sees to the terminal!
    print(f"\nGOD MODE CHECK: Token [{safe_user}] vs .env [{safe_superadmin}]\n")
    
    if safe_user != safe_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=f"Access Denied: {safe_user} is not the Super Admin."
        )
        
    return current_user

# --- 1. Platform Analytics & Server Health ---
@router.get("/stats", dependencies=[Depends(verify_superadmin)])
async def get_platform_stats(db: AsyncSession = Depends(get_db)):
    users_count = await db.execute(select(func.count(Tenant.id)))
    modules_count = await db.execute(select(func.count(Module.id)))
    
    # Calculate server load
    cpu_usage = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory()
    
    return {
        "total_users": users_count.scalar() or 0,
        "total_modules": modules_count.scalar() or 0,
        "server_health": {
            "cpu_percent": cpu_usage,
            "ram_percent": ram.percent,
            "ram_used_gb": round(ram.used / (1024**3), 2),
            "ram_total_gb": round(ram.total / (1024**3), 2)
        }
    }

# --- 2. User Management ---
@router.get("/users", dependencies=[Depends(verify_superadmin)])
async def get_all_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tenant).order_by(Tenant.created_at.desc()))
    users = result.scalars().all()
    return [{"id": u.id, "name": u.name, "email": u.email, "subdomain": u.subdomain, "created_at": u.created_at} for u in users]

@router.delete("/users/{user_id}", dependencies=[Depends(verify_superadmin)])
async def delete_user(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tenant).where(Tenant.id == user_id))
    user = result.scalars().first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await db.commit()
    return {"message": "User deleted."}

# --- 3. Module Management ---
class ModuleCreateUpdate(BaseModel):
    key: str = None
    name: str
    description: str
    base_price: float

@router.get("/modules", dependencies=[Depends(verify_superadmin)])
async def get_all_modules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Module).order_by(Module.key))
    return result.scalars().all()

@router.post("/modules", dependencies=[Depends(verify_superadmin)])
async def create_module(payload: ModuleCreateUpdate, db: AsyncSession = Depends(get_db)):
    if not payload.key: raise HTTPException(status_code=400, detail="Key required")
    existing = await db.execute(select(Module).where(Module.key == payload.key))
    if existing.scalars().first(): raise HTTPException(status_code=400, detail="Key exists")

    new_module = Module(
        id=str(uuid.uuid4()), key=payload.key, name=payload.name,
        description=payload.description, base_price=payload.base_price
    )
    db.add(new_module)
    await db.commit()
    return new_module

@router.put("/modules/{module_id}", dependencies=[Depends(verify_superadmin)])
async def update_module(module_id: str, payload: ModuleCreateUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalars().first()
    if not module: raise HTTPException(status_code=404, detail="Module not found")
    
    module.name = payload.name
    module.description = payload.description
    module.base_price = payload.base_price
    await db.commit()
    return {"message": "Updated"}

@router.delete("/modules/{module_id}", dependencies=[Depends(verify_superadmin)])
async def delete_module(module_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalars().first()
    if not module: raise HTTPException(status_code=404, detail="Module not found")
    
    await db.execute(TenantModule.__table__.delete().where(TenantModule.module_id == module_id))
    await db.delete(module)
    await db.commit()
    return {"message": "Deleted"}