from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from app.db.session import get_db
from app.db.models import ContactMessage
from app.api.dependencies import get_current_user

router = APIRouter()

class MessageSchema(BaseModel):
    sender_name: str
    sender_email: str
    message: str

# PUBLIC ROUTE: Visitors sending a message
@router.post("/public/{tenant_id}")
async def send_message(tenant_id: str, data: MessageSchema, db: AsyncSession = Depends(get_db)):
    msg = ContactMessage(tenant_id=tenant_id, **data.dict())
    db.add(msg)
    await db.commit()
    return {"status": "success"}

# PRIVATE ROUTE: Dashboard viewing messages
@router.get("/")
async def get_messages(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(ContactMessage).where(ContactMessage.tenant_id == current_user["tenant_id"]).order_by(ContactMessage.created_at.desc()))
    return res.scalars().all()

@router.delete("/{id}")
async def delete_message(id: str, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(ContactMessage).where(ContactMessage.id == id, ContactMessage.tenant_id == current_user["tenant_id"]))
    msg = res.scalars().first()
    if msg:
        await db.delete(msg)
        await db.commit()
    return {"status": "deleted"}