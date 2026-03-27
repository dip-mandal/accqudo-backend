# backend/app/services/projects/router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Optional

from app.db.session import get_db
from app.db.models import Project
from app.api.dependencies import get_current_user

router = APIRouter()

# Pydantic schema for receiving data from Next.js
class ProjectCreate(BaseModel):
    title: str
    funding_agency: str
    amount: Optional[str] = None
    start_year: int
    end_year: Optional[int] = None
    status: str = "Ongoing"

@router.get("/")
async def get_projects(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Fetch all projects for the logged-in user."""
    result = await db.execute(select(Project).where(Project.tenant_id == current_user["tenant_id"]))
    return result.scalars().all()

@router.post("/")
async def create_project(project: ProjectCreate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Add a new research project."""
    new_project = Project(
        tenant_id=current_user["tenant_id"],
        **project.dict()
    )
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    return new_project

@router.delete("/{project_id}")
async def delete_project(project_id: str, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Delete a specific project."""
    result = await db.execute(select(Project).where(Project.id == project_id, Project.tenant_id == current_user["tenant_id"]))
    project = result.scalars().first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    await db.delete(project)
    await db.commit()
    return {"message": "Project deleted successfully"}




@router.put("/{project_id}")
async def update_project(
    project_id: str,
    project: ProjectCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing research project."""
    
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.tenant_id == current_user["tenant_id"]
        )
    )

    existing_project = result.scalars().first()

    if not existing_project:
        raise HTTPException(status_code=404, detail="Project not found")

    for key, value in project.dict().items():
        setattr(existing_project, key, value)

    await db.commit()
    await db.refresh(existing_project)

    return existing_project