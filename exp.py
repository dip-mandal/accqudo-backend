# backend/seed_ai_modules.py

import asyncio
import uuid
from sqlalchemy.future import select
from app.db.session import AsyncSessionLocal # 👈 Using your exact session name
from app.db.models import Module


async def seed_new_modules():
    async with AsyncSessionLocal() as db:
        print("🔍 Checking existing AI modules...")

        ai_modules = [
            {
                "key": "ai_insert_cv",
                "description": "One-click to insertion of all data into database from your CV.",
                "base_price": 299.00,
            }
        ]

        # Check existing module keys
        result = await db.execute(select(Module.key))
        existing_keys = set(result.scalars().all())

        new_entries = []

        for mod in ai_modules:
            if mod["key"] not in existing_keys:
                new_entries.append(
                    Module(
                        id=str(uuid.uuid4()),
                        key=mod["key"],
                        description=mod["description"],
                        base_price=mod["base_price"],
                    )
                )

        if new_entries:
            db.add_all(new_entries)
            await db.commit()
            print(f"✅ Added {len(new_entries)} AI modules successfully!")
        else:
            print("⚡ AI modules already exist. Nothing to add.")


if __name__ == "__main__":
    asyncio.run(seed_new_modules())