# backend/seed_all_modules.py

import asyncio
import uuid
from sqlalchemy.future import select
from app.db.session import async_session
from app.db.models import Module


async def seed_all_modules():
    async with async_session() as db:
        print("🔍 Checking existing modules...")

        comprehensive_modules = [

            # =====================================================
            # 🏠 CORE FOUNDATION (FREE)
            # =====================================================
            {"key": "home", "desc": "Landing page & short academic bio", "price": 0},
            {"key": "about", "desc": "Detailed CV and biography", "price": 0},
            {"key": "education", "desc": "Academic qualifications", "price": 0},
            {"key": "experience", "desc": "Professional experience", "price": 0},
            {"key": "contact", "desc": "Basic contact information", "price": 0},

            # =====================================================
            # 📚 RESEARCH & PUBLICATIONS
            # =====================================================
            {"key": "publications", "desc": "Journal and conference publications", "price": 0},
            {"key": "books", "desc": "Books and edited volumes", "price": 499},
            {"key": "book_chapters", "desc": "Book chapters authored", "price": 299},
            {"key": "projects", "desc": "Funded research projects", "price": 599},
            {"key": "research_interests", "desc": "Research domains and keywords", "price": 199},
            {"key": "working_papers", "desc": "Preprints and manuscripts", "price": 299},
            {"key": "citations_metrics", "desc": "h-index, i10-index, Scopus metrics", "price": 299},

            # =====================================================
            # 🔬 INTELLECTUAL PROPERTY
            # =====================================================
            {"key": "patents", "desc": "Patent portfolio", "price": 499},
            {"key": "technology_transfer", "desc": "Commercialized technologies", "price": 499},
            {"key": "datasets", "desc": "Research datasets", "price": 299},
            {"key": "software_tools", "desc": "Developed software & repositories", "price": 299},

            # =====================================================
            # 🎓 TEACHING & MENTORSHIP
            # =====================================================
            {"key": "courses", "desc": "Courses taught", "price": 399},
            {"key": "teaching_materials", "desc": "Lecture notes & syllabus uploads", "price": 399},
            {"key": "students", "desc": "PhD & Masters supervision", "price": 399},
            {"key": "postdocs", "desc": "Postdoctoral supervision", "price": 399},
            {"key": "teaching_philosophy", "desc": "Teaching statement", "price": 199},

            # =====================================================
            # 🏛️ ACADEMIC SERVICE & LEADERSHIP
            # =====================================================
            {"key": "academic_services", "desc": "Editorial & committee roles", "price": 299},
            {"key": "administrative_roles", "desc": "Dean, HoD, Director roles", "price": 299},
            {"key": "conference_organization", "desc": "Organized conferences/workshops", "price": 299},
            {"key": "reviewer_roles", "desc": "Journal & grant reviewing activity", "price": 199},

            # =====================================================
            # 🎤 OUTREACH & VISIBILITY
            # =====================================================
            {"key": "presentations", "desc": "Talks & keynote presentations", "price": 199},
            {"key": "media_coverage", "desc": "News & press coverage", "price": 199},
            {"key": "blog", "desc": "Academic blog system", "price": 199},
            {"key": "gallery", "desc": "Photos & lab gallery", "price": 199},
            {"key": "videos", "desc": "Embedded lecture & seminar videos", "price": 199},

            # =====================================================
            # 💰 FUNDING & INDUSTRY
            # =====================================================
            {"key": "grants_summary", "desc": "Total funding overview dashboard", "price": 399},
            {"key": "industry_collaboration", "desc": "Industry partnerships", "price": 399},
            {"key": "consultancy", "desc": "Consulting engagements", "price": 399},
            {"key": "startup_involvement", "desc": "Startup mentorship & founder roles", "price": 399},

            # =====================================================
            # 📊 ANALYTICS & DIGITAL
            # =====================================================
            {"key": "analytics", "desc": "Visitor analytics dashboard", "price": 299},
            {"key": "seo_optimization", "desc": "Advanced SEO tools", "price": 399},
            {"key": "custom_domain", "desc": "Connect personal domain", "price": 499},
            {"key": "newsletter", "desc": "Email newsletter integration", "price": 299},

            # =====================================================
            # 🤖 FUTURE AI FEATURES (Premium)
            # =====================================================
            {"key": "ai_cv_generator", "desc": "Auto-generate academic CV", "price": 599},
            {"key": "ai_bio_writer", "desc": "AI-generated professional bio", "price": 499},
            {"key": "ai_research_summary", "desc": "AI research summarizer", "price": 599},

            # =====================================================
            # 🏢 ENTERPRISE FEATURES
            # =====================================================
            {"key": "department_dashboard", "desc": "Department-level analytics", "price": 999},
            {"key": "multi_user_admin", "desc": "Multiple admin access", "price": 499},
            {"key": "priority_support", "desc": "Dedicated support", "price": 299},
            {"key": "api_access", "desc": "Public API access", "price": 599},
        ]

        result = await db.execute(select(Module.key))
        existing_keys = set(result.scalars().all())

        new_modules = []

        for mod in comprehensive_modules:
            if mod["key"] not in existing_keys:
                new_modules.append(
                    Module(
                        id=str(uuid.uuid4()),
                        key=mod["key"],
                        description=mod["desc"],
                        base_price=mod["price"],
                    )
                )

        if new_modules:
            db.add_all(new_modules)
            await db.commit()
            print(f"✅ Added {len(new_modules)} new modules!")
        else:
            print("⚡ All modules already exist.")


if __name__ == "__main__":
    asyncio.run(seed_all_modules())