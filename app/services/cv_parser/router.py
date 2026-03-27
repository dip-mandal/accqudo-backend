from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.dependencies import get_current_user

from app.services.usage_limiter import check_cv_usage
from app.services.module_access import get_active_modules

from app.services.cv_parser.file_parser import extract_text
from app.services.cv_parser.ai_parser import parse_cv_advanced

from app.db.models import Education, Experience, Publication, Tenant

router = APIRouter()


def safe_int(v):

    try:
        return int(v)
    except:
        return 0


@router.post("/parse")
async def parse_cv(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):

    tenant_id = current_user["tenant_id"]

    allowed = await check_cv_usage(db, tenant_id)

    if not allowed:

        raise HTTPException(
            status_code=429,
            detail="Daily AI CV limit reached (3/day)"
        )

    file_bytes = await file.read()

    text = extract_text(file.filename, file_bytes)

    text = text[:15000]

    parsed = parse_cv_advanced(text)

    return {"parsed_data": parsed}


@router.post("/bulk-insert")
async def bulk_insert(
    data: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):

    tenant_id = current_user["tenant_id"]

    modules = await get_active_modules(db, tenant_id)

    if "education" in modules:

        for edu in data.get("education",[]):

            db.add(Education(
                tenant_id=tenant_id,
                degree=edu.get("degree",""),
                institution=edu.get("institution",""),
                graduation_year=safe_int(edu.get("graduation_year")),
                thesis_title=edu.get("thesis_title","")
            ))

    if "experience" in modules:

        for exp in data.get("experience",[]):

            db.add(Experience(
                tenant_id=tenant_id,
                title=exp.get("title",""),
                institution=exp.get("institution",""),
                start_year=safe_int(exp.get("start_year")),
                end_year=safe_int(exp.get("end_year")),
                department=exp.get("department","")
            ))

    if "publications" in modules:

        for pub in data.get("publications",[]):

            db.add(Publication(
                tenant_id=tenant_id,
                title=pub.get("title",""),
                year=safe_int(pub.get("year")),
                type=pub.get("type","Journal"),
                journal=pub.get("journal","")
            ))

    if data.get("summary"):

        from sqlalchemy.future import select

        result = await db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )

        tenant = result.scalars().first()

        if tenant:
            tenant.bio = data.get("summary")

    await db.commit()

    return {"status":"success"}