from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.api.dependencies import get_current_user

from app.db.models import (
    Publication,
    CitationMetric,
    ResearchInterest
)

from .schemas import ScholarImportRequest, ScholarConfirmRequest
from .scholar_scraper import get_scholar_profile
from .scholar_parser import parse_scholar_data


router = APIRouter()


def extract_user_id(url: str):
    return url.split("user=")[1].split("&")[0]


# --------------------------------------------------
# STEP 1: PREVIEW SCHOLAR PROFILE
# --------------------------------------------------

@router.post("/preview")
async def preview_scholar_import(
    payload: ScholarImportRequest,
    current_user: dict = Depends(get_current_user)
):

    scholar_url = payload.scholar_url

    user_id = extract_user_id(scholar_url)

    profile = get_scholar_profile(user_id)

    publications, top_papers, coauthors, interests, metrics = parse_scholar_data(profile)

    return {
        "publications": publications,
        "top_papers": top_papers,
        "coauthors": coauthors,
        "research_interests": interests,
        "citations": metrics["citations"],
        "h_index": metrics["h_index"],
        "i10_index": metrics["i10_index"],
        "citations_per_year": metrics["citations_per_year"]
    }


# --------------------------------------------------
# STEP 2: CONFIRM IMPORT
# --------------------------------------------------

@router.post("/confirm")
async def confirm_scholar_import(
    payload: ScholarConfirmRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):

    tenant_id = current_user["tenant_id"]

    inserted = 0

    for pub in payload.publications:

        result = await db.execute(
            select(Publication).where(
                Publication.tenant_id == tenant_id,
                Publication.title == pub.title
            )
        )

        exists = result.scalar()

        if exists:
            continue

        db.add(
            Publication(
                tenant_id=tenant_id,
                title=pub.title,
                year=pub.year,
                type=pub.type,
                journal=pub.journal
            )
        )

        inserted += 1

    # Save citation metrics
    db.add(
        CitationMetric(
            tenant_id=tenant_id,
            source="Google Scholar",
            total_citations=payload.citations,
            h_index=payload.h_index,
            i10_index=payload.i10_index,
            year=2025
        )
    )

    # Save research interests
    for topic in payload.research_interests:
        db.add(
            ResearchInterest(
                tenant_id=tenant_id,
                topic=topic
            )
        )

    await db.commit()

    return {
        "inserted_publications": inserted
    }