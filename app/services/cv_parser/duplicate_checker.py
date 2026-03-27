from sqlalchemy import select
from app.db.models import Publication, Education, Experience


async def publication_exists(db, tenant_id, title):

    result = await db.execute(
        select(Publication).where(
            Publication.tenant_id == tenant_id,
            Publication.title == title
        )
    )

    return result.scalar() is not None


async def education_exists(db, tenant_id, degree, institution):

    result = await db.execute(
        select(Education).where(
            Education.tenant_id == tenant_id,
            Education.degree == degree,
            Education.institution == institution
        )
    )

    return result.scalar() is not None


async def experience_exists(db, tenant_id, title, institution):

    result = await db.execute(
        select(Experience).where(
            Experience.tenant_id == tenant_id,
            Experience.title == title,
            Experience.institution == institution
        )
    )

    return result.scalar() is not None