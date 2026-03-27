# backend/app/services/core_cv/router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Optional

from app.db.session import get_db
from app.db.models import Education, Experience
from app.api.dependencies import get_current_user

router = APIRouter()

# --- SCHEMAS ---
class EducationCreate(BaseModel):
    degree: str
    institution: str
    graduation_year: int
    thesis_title: Optional[str] = None

class ExperienceCreate(BaseModel):
    title: str
    institution: str
    department: Optional[str] = None
    start_year: int
    end_year: Optional[int] = None

# --- EDUCATION ENDPOINTS ---
@router.get("/education")
async def get_education(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Education).where(Education.tenant_id == current_user["tenant_id"]).order_by(Education.graduation_year.desc()))
    return result.scalars().all()

@router.post("/education")
async def add_education(edu: EducationCreate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    new_edu = Education(tenant_id=current_user["tenant_id"], **edu.dict())
    db.add(new_edu)
    await db.commit()
    await db.refresh(new_edu)
    return new_edu

@router.delete("/education/{id}")
async def delete_education(id: str, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Education).where(Education.id == id, Education.tenant_id == current_user["tenant_id"]))
    edu = result.scalars().first()
    if not edu: raise HTTPException(status_code=404, detail="Not found")
    await db.delete(edu)
    await db.commit()
    return {"message": "Deleted"}



@router.put("/education/{id}")
async def update_education(
    id: str,
    edu_data: EducationCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Education).where(Education.id == id, Education.tenant_id == current_user["tenant_id"])
    )
    edu = result.scalars().first()

    if not edu:
        raise HTTPException(status_code=404, detail="Not found")

    for key, value in edu_data.dict().items():
        setattr(edu, key, value)

    await db.commit()
    await db.refresh(edu)
    return edu





# --- EXPERIENCE ENDPOINTS ---
@router.get("/experience")
async def get_experience(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Experience).where(Experience.tenant_id == current_user["tenant_id"]).order_by(Experience.start_year.desc()))
    return result.scalars().all()

@router.post("/experience")
async def add_experience(exp: ExperienceCreate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    new_exp = Experience(tenant_id=current_user["tenant_id"], **exp.dict())
    db.add(new_exp)
    await db.commit()
    await db.refresh(new_exp)
    return new_exp

@router.delete("/experience/{id}")
async def delete_experience(id: str, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Experience).where(Experience.id == id, Experience.tenant_id == current_user["tenant_id"]))
    exp = result.scalars().first()
    if not exp: raise HTTPException(status_code=404, detail="Not found")
    await db.delete(exp)
    await db.commit()
    return {"message": "Deleted"}


@router.put("/experience/{id}")
async def update_experience(
    id: str,
    exp_data: ExperienceCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Experience).where(Experience.id == id, Experience.tenant_id == current_user["tenant_id"])
    )
    exp = result.scalars().first()

    if not exp:
        raise HTTPException(status_code=404, detail="Not found")

    for key, value in exp_data.dict().items():
        setattr(exp, key, value)

    await db.commit()
    await db.refresh(exp)
    return exp




# Add to the bottom of backend/app/services/core_cv/router.py

class ProfileUpdate(BaseModel):
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    google_scholar: Optional[str] = None
    linkedin: Optional[str] = None
    twitter: Optional[str] = None
    github: Optional[str] = None
    facebook: Optional[str] = None
    instagram: Optional[str] = None

from app.db.models import Profile

@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Profile).where(Profile.tenant_id == current_user["tenant_id"]))
    profile = result.scalars().first()
    if not profile:
        # If no profile exists yet, return an empty shell
        return {}
    return profile

@router.put("/profile")
async def update_profile(profile_data: ProfileUpdate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Profile).where(Profile.tenant_id == current_user["tenant_id"]))
    profile = result.scalars().first()
    
    if not profile:
        # Create it if it doesn't exist
        profile = Profile(tenant_id=current_user["tenant_id"], **profile_data.dict(exclude_unset=True))
        db.add(profile)
    else:
        # Update existing
        for key, value in profile_data.dict(exclude_unset=True).items():
            setattr(profile, key, value)
            
    await db.commit()
    await db.refresh(profile)
    return profile


# Add these to the very bottom of backend/app/services/core_cv/router.py

@router.get("/public/profile/{tenant_id}")
async def get_public_profile(tenant_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Profile).where(Profile.tenant_id == tenant_id))
    profile = result.scalars().first()
    return profile or {}

@router.get("/public/education/{tenant_id}")
async def get_public_education(tenant_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Education).where(Education.tenant_id == tenant_id).order_by(Education.graduation_year.desc()))
    return result.scalars().all()

@router.get("/public/experience/{tenant_id}")
async def get_public_experience(tenant_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Experience).where(Experience.tenant_id == tenant_id).order_by(Experience.start_year.desc()))
    return result.scalars().all()