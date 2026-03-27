from sqlalchemy import select
from app.db.models import TenantModule, Module


async def get_active_modules(db, tenant_id):

    result = await db.execute(
        select(Module.key)
        .join(TenantModule, Module.id == TenantModule.module_id)
        .where(
            TenantModule.tenant_id == tenant_id,
            TenantModule.is_active == True
        )
    )

    rows = result.fetchall()

    return {r[0] for r in rows}