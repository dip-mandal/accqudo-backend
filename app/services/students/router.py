from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Optional

from app.db.session import get_db
from app.db.models import Student
from app.api.dependencies import get_current_user

router = APIRouter()

# Schema exactly matches your database columns
class StudentCreate(BaseModel):
    name: str
    degree: str
    department: Optional[str] = None
    thesis_title: Optional[str] = None
    graduation_year: Optional[int] = None
    is_alumni: bool = False
    avatar_url: Optional[str] = None
    profile_link: Optional[str] = None

@router.get("/")
async def get_students(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Sort so that ongoing students (null year) appear first, then recent graduates
    result = await db.execute(
        select(Student)
        .where(Student.tenant_id == current_user["tenant_id"])
        .order_by(Student.is_alumni.asc(), Student.graduation_year.desc())
    )
    return result.scalars().all()

@router.post("/")
async def add_student(student: StudentCreate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    new_student = Student(tenant_id=current_user["tenant_id"], **student.dict())
    db.add(new_student)
    await db.commit()
    await db.refresh(new_student)
    return new_student

@router.delete("/{id}")
async def delete_student(id: str, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Student).where(Student.id == id, Student.tenant_id == current_user["tenant_id"]))
    student = result.scalars().first()
    if not student: raise HTTPException(status_code=404, detail="Not found")
    await db.delete(student)
    await db.commit()
    return {"message": "Deleted"}

# Public Endpoint for the edge portfolio
@router.get("/public/{tenant_id}")
async def get_public_students(tenant_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Student)
        .where(Student.tenant_id == tenant_id)
        .order_by(Student.is_alumni.asc(), Student.graduation_year.desc())
    )
    return result.scalars().all()


@router.put("/{id}")
async def update_student(
    id: str,
    student: StudentCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Student).where(Student.id == id, Student.tenant_id == current_user["tenant_id"])
    )

    db_student = result.scalars().first()

    if not db_student:
        raise HTTPException(status_code=404)

    for key, value in student.dict(exclude_unset=True).items():
        setattr(db_student, key, value)

    await db.commit()
    await db.refresh(db_student)

    return db_student