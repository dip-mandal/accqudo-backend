# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.redis import redis_client

from app.services.tenant.router import router as tenant_router
from app.services.auth.router import router as auth_router
from app.services.content.router import router as content_router

from app.services.media.router import router as media_router


from app.services.billing.router import router as billing_router

from app.services.projects.router import router as projects_router

from app.services.core_cv.router import router as core_cv_router

from app.services.students.router import router as students_router

from app.services.research.router import router as research_router

from app.services.working_papers.router import router as working_papers_router

from app.services.patents.router import router as patents_router

from app.services.books.router import router as books_router

from app.services.book_chapters.router import router as book_chapters_router

from app.services.teaching_service.router import router as teaching_router

from app.services.activities.router import router as activities_router

from app.services.industry.router import router as industry_router

from app.services.outputs.router import router as outputs_router

from app.services.outreach.router import router as outreach_router

from app.services.system_tools.router import router as system_router

from app.services.ai_suite.router import router as ai_suite_router

from app.services.contact.router import router as contact_router

from app.services.cv_parser.router import router as cv_router

from app.services.admin.router import router as admin_router

from app.services.scholar_import.router import router as scholar_router







from app.services.superadmin.router import router as superadmin_router



# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Verify Redis connection
    await redis_client.ping()
    print("✅ Successfully connected to Redis!")
    yield
    # Shutdown: Clean up connections
    await redis_client.aclose()
    print("🛑 Disconnected from Redis.")

# Initialize FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS configuration (crucial for frontend communication)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://accqudo-backend.onrender.com",
        "https://accqudo.vercel.app",
        "http://localhost:3000",
    ],
    allow_origin_regex=r"https://.*\.accqudo.vercel.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# A simple health check route
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Backend is running!"}


app.include_router(tenant_router, prefix="/api/tenants", tags=["Tenants"])

app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])

app.include_router(content_router, prefix="/api/content", tags=["Content Modules"])

app.include_router(media_router, prefix="/api/media", tags=["Media Service"])

app.include_router(billing_router, prefix="/api/billing", tags=["Billing & Upgrades"])

app.include_router(projects_router, prefix="/api/projects", tags=["Projects"])

app.include_router(core_cv_router, prefix="/api/cv", tags=["Core CV"])

app.include_router(students_router, prefix="/api/students", tags=["Students"])

app.include_router(research_router, prefix="/api/research", tags=["Research Interests"])

app.include_router(working_papers_router, prefix="/api/working-papers", tags=["Working Papers"])

app.include_router(patents_router, prefix="/api/patents", tags=["Patents"])

app.include_router(books_router, prefix="/api/books", tags=["Books"])

app.include_router(book_chapters_router, prefix="/api/book-chapters", tags=["Book Chapters"])

app.include_router(teaching_router, prefix="/api")

app.include_router(activities_router, prefix="/api/activities")

app.include_router(industry_router, prefix="/api/industry")

app.include_router(outputs_router, prefix="/api/outputs")

app.include_router(outreach_router, prefix="/api/outreach")

app.include_router(system_router, prefix="/api/system")

app.include_router(ai_suite_router, prefix="/api/suite")

app.include_router(contact_router, prefix="/api/contact", tags=["Contact"])

app.include_router(cv_router, prefix="/api/cv-parser", tags=["AI CV Parser"])

app.include_router(admin_router, prefix="/api/admin", tags=["Admin Tools"])

app.include_router(superadmin_router, prefix="/api/platform", tags=["Super Admin"])

app.include_router(scholar_router, prefix="/api/scholar", tags=["Scholar Import"])
