# backend/app/services/content/router.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.db.models import Publication
from app.api.dependencies import get_current_user, require_module

router = APIRouter()

# Schema for incoming data
class PublicationCreate(BaseModel):
    title: str
    year: int
    type: str
    journal: str | None = None
    link: str | None = None
    external_link: str | None = None
    thumbnail: str | None = None

# 1. CREATE Publication (Requires Login AND the 'publications' module)
@router.post("/publications")
async def create_publication(
    payload: PublicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_module("publications")) # 🛡️ The Paywall Guardian!
):
    # Notice we automatically attach the tenant_id from the JWT! No faking data.
    new_pub = Publication(
    tenant_id=current_user["tenant_id"],
    title=payload.title,
    year=payload.year,
    type=payload.type,
    journal=payload.journal,
    link=payload.link,
    external_link=payload.external_link,
    thumbnail=payload.thumbnail
)
    
    db.add(new_pub)
    await db.commit()
    await db.refresh(new_pub)
    
    return {"message": "Publication added successfully", "data": new_pub}

# 2. READ Publications (Public route, anyone can view a professor's publications)
@router.get("/publications/{tenant_id}")
async def get_tenant_publications(tenant_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Publication).where(Publication.tenant_id == tenant_id))
    publications = result.scalars().all()
    
    return {"publications": publications}



@router.put("/publications/{id}")
async def update_publication(
    id: str,
    payload: PublicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_module("publications"))
):
    result = await db.execute(
        select(Publication).where(
            Publication.id == id,
            Publication.tenant_id == current_user["tenant_id"]
        )
    )

    pub = result.scalars().first()

    if not pub:
        raise HTTPException(status_code=404, detail="Publication not found")

    for key, value in payload.dict().items():
        setattr(pub, key, value)

    await db.commit()
    await db.refresh(pub)

    return pub



@router.delete("/publications/{id}")
async def delete_publication(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_module("publications"))
):
    result = await db.execute(
        select(Publication).where(
            Publication.id == id,
            Publication.tenant_id == current_user["tenant_id"]
        )
    )

    pub = result.scalars().first()

    if not pub:
        raise HTTPException(status_code=404, detail="Not found")

    await db.delete(pub)
    await db.commit()

    return {"message": "Deleted"}



@router.get("/publications")
async def get_my_publications(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_module("publications"))
):
    result = await db.execute(
        select(Publication)
        .where(Publication.tenant_id == current_user["tenant_id"])
        .order_by(Publication.year.desc())
    )

    publications = result.scalars().all()

    return {"publications": publications}