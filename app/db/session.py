# backend/app/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings

# Create the async engine
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# Create the session factory
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session