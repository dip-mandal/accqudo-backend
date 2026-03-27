from datetime import date
from sqlalchemy.future import select
from app.db.models import FeatureUsage

MAX_DAILY_USAGE = 3


async def check_cv_usage(db, tenant_id):

    result = await db.execute(
        select(FeatureUsage).where(
            FeatureUsage.tenant_id == tenant_id,
            FeatureUsage.feature == "cv_import"
        )
    )

    usage = result.scalars().first()

    if usage:

        if usage.usage_count >= MAX_DAILY_USAGE:
            return False

        usage.usage_count += 1

    else:

        usage = FeatureUsage(
            tenant_id=tenant_id,
            feature="cv_import",
            usage_count=1
        )

        db.add(usage)

    await db.commit()

    return True