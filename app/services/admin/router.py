from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
import secrets

from app.db.session import get_db
from app.db.models import APIKey, SupportTicket, TeamMember
from app.api.dependencies import get_current_user

router = APIRouter()

# --- API KEYS ---
@router.get("/api-keys")
async def get_keys(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(APIKey).where(APIKey.tenant_id == current_user["tenant_id"]))
    return res.scalars().all()

@router.post("/api-keys")
async def generate_key(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Generate a real secure API key
    raw_key = "sk_live_" + secrets.token_urlsafe(32)
    prefix = raw_key[:12] + "..." + raw_key[-4:]
    
    new_key = APIKey(tenant_id=current_user["tenant_id"], key_prefix=prefix)
    db.add(new_key)
    await db.commit()
    # Only return the full raw key ONCE during creation!
    return {"raw_key": raw_key, "key_prefix": prefix, "id": new_key.id}

@router.delete("/api-keys/{id}")
async def delete_key(id: str, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(APIKey).where(APIKey.id == id, APIKey.tenant_id == current_user["tenant_id"]))
    k = res.scalars().first()
    if k: await db.delete(k); await db.commit()
    return {"status": "deleted"}

# --- SUPPORT TICKETS ---
class TicketSchema(BaseModel): subject: str; description: str

@router.get("/tickets")
async def get_tickets(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(SupportTicket).where(SupportTicket.tenant_id == current_user["tenant_id"]).order_by(SupportTicket.created_at.desc()))
    return res.scalars().all()

@router.post("/tickets")
async def create_ticket(data: TicketSchema, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ticket = SupportTicket(tenant_id=current_user["tenant_id"], **data.dict())
    db.add(ticket)
    await db.commit()
    return ticket

# --- TEAM MEMBERS ---
class TeamSchema(BaseModel): email: str; role: str

@router.get("/team")
async def get_team(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(TeamMember).where(TeamMember.tenant_id == current_user["tenant_id"]))
    return res.scalars().all()

@router.post("/team")
async def invite_member(data: TeamSchema, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    member = TeamMember(tenant_id=current_user["tenant_id"], **data.dict())
    db.add(member)
    await db.commit()
    return member

@router.delete("/team/{id}")
async def remove_member(id: str, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(TeamMember).where(TeamMember.id == id, TeamMember.tenant_id == current_user["tenant_id"]))
    m = res.scalars().first()
    if m: await db.delete(m); await db.commit()
    return {"status": "deleted"}