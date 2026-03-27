# backend/app/db/models.py

from sqlalchemy import String, Boolean, Float, ForeignKey, DateTime, func, Integer, Text, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import uuid

from sqlalchemy.sql import func

from app.db.base import Base


# =========================================================
# 🏢 TENANT & USERS (Core Architecture)
# =========================================================

# backend/app/db/models.py

class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    subdomain: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    custom_domain: Mapped[str] = mapped_column(String, unique=True, nullable=True)
    subscription_status: Mapped[str] = mapped_column(String, default="active")
    
    email = Column(String, unique=True, index=True, nullable=True) 
    hashed_password = Column(String, nullable=True)
    
    # --- ADD THIS NEW FIELD ---
    razorpay_subscription_id: Mapped[str] = mapped_column(String, nullable=True) 
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    modules = relationship("TenantModule", back_populates="tenant", cascade="all, delete-orphan")
    


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    role: Mapped[str] = mapped_column(String, default="owner")  # owner, admin, viewer

    tenant = relationship("Tenant", back_populates="users")


# =========================================================
# 🧩 MODULE MARKETPLACE (Billing & Access)
# =========================================================

class Module(Base):
    __tablename__ = "modules"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    base_price: Mapped[float] = mapped_column(Float, default=0.0)
    description: Mapped[str] = mapped_column(String, nullable=True)
    name = Column(String, default="Custom Module")
    

class TenantModule(Base):
    __tablename__ = "tenant_modules"

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), primary_key=True)
    module_id: Mapped[str] = mapped_column(ForeignKey("modules.id"), primary_key=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    tenant = relationship("Tenant", back_populates="modules")


# =========================================================
# 📜 CORE CV & BIOGRAPHY
# =========================================================

class Education(Base):
    __tablename__ = "education"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    
    degree: Mapped[str] = mapped_column(String)
    institution: Mapped[str] = mapped_column(String)
    graduation_year: Mapped[int] = mapped_column(Integer)
    thesis_title: Mapped[str] = mapped_column(String, nullable=True)

class Experience(Base):
    __tablename__ = "experience"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    
    title: Mapped[str] = mapped_column(String)
    institution: Mapped[str] = mapped_column(String)
    department: Mapped[str] = mapped_column(String, nullable=True)
    start_year: Mapped[int] = mapped_column(Integer)
    end_year: Mapped[int] = mapped_column(Integer, nullable=True)


# =========================================================
# 📚 RESEARCH & PUBLICATIONS
# =========================================================

class Publication(Base):
    __tablename__ = "publications"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)

    type: Mapped[str] = mapped_column(String)
    year: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String)

    journal: Mapped[str] = mapped_column(String, nullable=True)

    # PDF or file
    link: Mapped[str] = mapped_column(String, nullable=True)

    # NEW
    external_link: Mapped[str] = mapped_column(String, nullable=True)

    # NEW Cover Image
    thumbnail: Mapped[str] = mapped_column(String, nullable=True)





# =========================================================
# 🔬 FUNDING, IP & INDUSTRY
# =========================================================

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    title: Mapped[str] = mapped_column(String)
    funding_agency: Mapped[str] = mapped_column(String)
    amount: Mapped[str] = mapped_column(String, nullable=True)
    start_year: Mapped[int] = mapped_column(Integer)
    end_year: Mapped[int] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String, default="Ongoing")



class TechTransfer(Base):
    __tablename__ = "tech_transfers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    technology_name: Mapped[str] = mapped_column(String)
    industry_partner: Mapped[str] = mapped_column(String)
    year: Mapped[int] = mapped_column(Integer)

class DatasetSoftware(Base):
    __tablename__ = "datasets_software"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String) # Dataset, Software
    description: Mapped[str] = mapped_column(Text, nullable=True)
    link: Mapped[str] = mapped_column(String, nullable=True)
    year: Mapped[int] = mapped_column(Integer)




# =========================================================
# 🎓 TEACHING & MENTORSHIP
# =========================================================



class Student(Base):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)

    name: Mapped[str] = mapped_column(String)
    degree: Mapped[str] = mapped_column(String)

    department: Mapped[str] = mapped_column(String, nullable=True)

    thesis_title: Mapped[str] = mapped_column(String, nullable=True)
    graduation_year: Mapped[int] = mapped_column(Integer, nullable=True)

    is_alumni: Mapped[bool] = mapped_column(Boolean, default=False)

    avatar_url: Mapped[str] = mapped_column(String, nullable=True)

    profile_link: Mapped[str] = mapped_column(String, nullable=True)




# =========================================================
# 🏛️ ACADEMIC SERVICE & AWARDS
# =========================================================





class Award(Base):
    __tablename__ = "awards"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    title: Mapped[str] = mapped_column(String)
    organization: Mapped[str] = mapped_column(String)
    year: Mapped[int] = mapped_column(Integer)


# =========================================================
# 🎤 MEDIA, OUTREACH & PRESENTATIONS
# =========================================================





class BlogPost(Base):
    __tablename__ = "blog_posts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    title: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)

class GalleryImage(Base):
    __tablename__ = "gallery_images"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    image_url: Mapped[str] = mapped_column(String) # R2 Link
    caption: Mapped[str] = mapped_column(String, nullable=True)
    year: Mapped[int] = mapped_column(Integer, nullable=True)
    

# Add this at the bottom of backend/app/db/models.py

class Profile(Base):
    __tablename__ = "profiles"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # About / Biography
    bio = Column(Text, nullable=True)
    avatar_url = Column(String, nullable=True)
    
    # Contact Info
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    
    # Social & Academic Links
    google_scholar = Column(String, nullable=True)
    linkedin = Column(String, nullable=True)
    twitter = Column(String, nullable=True)
    github = Column(String, nullable=True)
    facebook = Column(String, nullable=True)
    instagram = Column(String, nullable=True)
    
    
    


# Add to the bottom of backend/app/db/models.py
class ResearchInterest(Base):
    __tablename__ = "research_interests"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    
    topic = Column(String, nullable=False) # e.g., "Deep Learning"
    description = Column(Text, nullable=True) # e.g., "Applying neural networks to..."
    media_url = Column(String, nullable=True)
    
    
    

    
class WorkingPaper(Base):
    __tablename__ = "working_papers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    title: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="In Preparation") # Under Review, Preprint
    year: Mapped[int] = mapped_column(Integer)
    link: Mapped[str] = mapped_column(String, nullable=True)
    abstract = Column(Text, nullable=True)
    
    


# Add to the bottom of backend/app/db/models.py
class Patent(Base):
    __tablename__ = "patents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    
    title = Column(String, nullable=False)
    patent_number = Column(String, nullable=True) # e.g., "US10234567B2"
    year = Column(Integer, nullable=False)
    status = Column(String, default="Granted") # e.g., "Granted", "Pending", "Filed"
    description = Column(Text, nullable=True)
    link = Column(String, nullable=True) # Media URL for the PDF upload
    
    



# Add to the bottom of backend/app/db/models.py
class Book(Base):
    __tablename__ = "books"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    
    title = Column(String, nullable=False)
    publisher = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    isbn = Column(String, nullable=True)

    # uploaded PDF / DOCX
    file_link = Column(String, nullable=True)

    # external book link (Amazon / DOI / publisher)
    external_link = Column(String, nullable=True)

    # cover image / thumbnail
    thumbnail = Column(String, nullable=True)

class BookChapter(Base):
    __tablename__ = "book_chapters"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    
    chapter_title = Column(String, nullable=False)
    book_title = Column(String, nullable=False)
    publisher = Column(String, nullable=False)
    year = Column(Integer, nullable=False)

    # uploaded chapter file
    file_link = Column(String, nullable=True)

    # external chapter link (publisher/doi)
    external_link = Column(String, nullable=True)

    # chapter thumbnail
    thumbnail = Column(String, nullable=True)





# Add to the bottom of backend/app/db/models.py


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)

    course_code: Mapped[str] = mapped_column(String)
    course_name: Mapped[str] = mapped_column(String)

    level: Mapped[str] = mapped_column(String)
    semester: Mapped[str] = mapped_column(String)
    year: Mapped[int] = mapped_column(Integer)

    syllabus_link: Mapped[str] = mapped_column(String, nullable=True)  # handwritten notes
    thumbnail_url: Mapped[str] = mapped_column(String, nullable=True)  # NEW


class TeachingMaterial(Base):
    __tablename__ = "teaching_materials"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    title = Column(String, nullable=False)
    type = Column(String, nullable=False) # Syllabus, Slides, Notes, etc.
    course_name = Column(String, nullable=True)
    link = Column(String, nullable=True) # Cloudflare R2 Media link
    thumbnail_url: Mapped[str] = mapped_column(String, nullable=True)




class Presentation(Base):
    __tablename__ = "presentations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    title: Mapped[str] = mapped_column(String)
    event_name: Mapped[str] = mapped_column(String)
    location: Mapped[str] = mapped_column(String, nullable=True)
    type: Mapped[str] = mapped_column(String)
    year: Mapped[int] = mapped_column(Integer)
    link: Mapped[str] = mapped_column(String, nullable=True)


    


class AcademicService(Base):
    __tablename__ = "academic_services"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    role: Mapped[str] = mapped_column(String)
    organization: Mapped[str] = mapped_column(String)
    start_year: Mapped[int] = mapped_column(Integer)
    end_year: Mapped[int] = mapped_column(Integer, nullable=True)




# Add to the bottom of backend/app/db/models.py

class TeachingPhilosophy(Base):
    __tablename__ = "teaching_philosophies"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    title = Column(String, default="Teaching Philosophy")
    content = Column(Text, nullable=False)
    link = Column(String, nullable=True) # Optional PDF upload

class AdministrativeRole(Base):
    __tablename__ = "administrative_roles"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    role = Column(String, nullable=False)
    institution = Column(String, nullable=False)
    start_year = Column(Integer, nullable=False)
    end_year = Column(Integer, nullable=True)

class ConferenceOrganization(Base):
    __tablename__ = "conference_organizations"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    role = Column(String, nullable=False)
    conference_name = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    link = Column(String, nullable=True)

class ReviewerRole(Base):
    __tablename__ = "reviewer_roles"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    journal_name = Column(String, nullable=False)
    publisher = Column(String, nullable=True)
    year = Column(Integer, nullable=True) # Null if ongoing



# Add to the bottom of backend/app/db/models.py

class IndustryCollaboration(Base):
    __tablename__ = "industry_collaborations"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    partner_name = Column(String, nullable=False) # e.g., "Google Research"
    project_title = Column(String, nullable=False)
    start_year = Column(Integer, nullable=False)
    end_year = Column(Integer, nullable=True) # Null = Ongoing
    description = Column(Text, nullable=True)
    link = Column(String, nullable=True) # Optional PDF/Link
    
    
    
class Consultancy(Base):
    __tablename__ = "consultancies"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    client_name = Column(String, nullable=False)
    role = Column(String, nullable=False) # e.g., "Technical Advisor"
    start_year = Column(Integer, nullable=False)
    end_year = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    link = Column(String, nullable=True)

class StartupInvolvement(Base):
    __tablename__ = "startup_involvements"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    startup_name = Column(String, nullable=False)
    role = Column(String, nullable=False) # e.g., "Co-Founder", "Board Member"
    founded_year = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    link = Column(String, nullable=True) # e.g., Link to company website or PDF

class TechnologyTransfer(Base):
    __tablename__ = "technology_transfers"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    technology_name = Column(String, nullable=False)
    partner = Column(String, nullable=True) # Who it was licensed to
    year = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    link = Column(String, nullable=True) # License agreement / Media URL
    

# Add to the bottom of backend/app/db/models.py

class Postdoc(Base):
    __tablename__ = "postdocs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    name = Column(String, nullable=False)
    research_topic = Column(String, nullable=True)
    start_year = Column(Integer, nullable=False)
    end_year = Column(Integer, nullable=True)
    is_alumni = Column(Boolean, default=False)
    avatar_url = Column(String, nullable=True) # Profile picture
    profile_link = Column(String, nullable=True)
    


class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    year = Column(Integer, nullable=False)
    link = Column(String, nullable=True) # R2 zip file or Kaggle link

class SoftwareTool(Base):
    __tablename__ = "software_tools"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    year = Column(Integer, nullable=False)
    link = Column(String, nullable=True) # R2 file or GitHub link

class CitationMetric(Base):
    __tablename__ = "citation_metrics"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    source = Column(String, default="Google Scholar")
    total_citations = Column(Integer, nullable=False)
    h_index = Column(Integer, nullable=False)
    i10_index = Column(Integer, nullable=True)
    year = Column(Integer, nullable=False) # Year recorded
    


# Add to the bottom of backend/app/db/models.py

class MediaCoverage(Base):
    __tablename__ = "media_coverage"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    title = Column(String, nullable=False)
    outlet_name = Column(String, nullable=False) # e.g., "New York Times", "BBC"
    year = Column(Integer, nullable=False)
    link = Column(String, nullable=True) # Web link or PDF clipping


    
    
class BlogArticle(Base):
    __tablename__ = "blog_articles"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    title = Column(String, nullable=False)
    platform = Column(String, nullable=True) # e.g., "Medium", "Personal Blog"
    year = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    link = Column(String, nullable=True)

class GalleryItem(Base):
    __tablename__ = "gallery_items"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    title = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String, nullable=False) # R2 Media Link (Required)

class VideoLecture(Base):
    __tablename__ = "video_lectures"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    title = Column(String, nullable=False)
    event_name = Column(String, nullable=True)
    year = Column(Integer, nullable=False)
    video_url = Column(String, nullable=False) # YouTube / Vimeo link



# Add to the bottom of backend/app/db/models.py

class GrantSummary(Base):
    __tablename__ = "grants_summaries"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), unique=True)
    total_funding = Column(String, nullable=False) # e.g., "$2.5M"
    active_grants = Column(Integer, nullable=False)
    summary_text = Column(Text, nullable=True)

class SiteSetting(Base):
    __tablename__ = "site_settings"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), unique=True)
    meta_title = Column(String, nullable=True)
    meta_description = Column(String, nullable=True)
    google_analytics_id = Column(String, nullable=True) # e.g., "G-XXXXXXX"
    

class NewsletterSubscriber(Base):
    __tablename__ = "newsletter_subscribers"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    email = Column(String, nullable=False)
    subscribed_at = Column(DateTime(timezone=True), server_default=func.now())
    

class ContactMessage(Base):
    __tablename__ = "contact_messages"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    sender_name = Column(String, nullable=False)
    sender_email = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    



class APIKey(Base):
    __tablename__ = "api_keys"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    key_prefix = Column(String, nullable=False) # e.g. "sk_live_..."
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SupportTicket(Base):
    __tablename__ = "support_tickets"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    subject = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, default="Open") # Open, Resolved
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TeamMember(Base):
    __tablename__ = "team_members"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    email = Column(String, nullable=False)
    role = Column(String, default="Editor")
    status = Column(String, default="Pending")
    


# Add to the bottom of backend/app/db/models.py

class OTPCode(Base):
    __tablename__ = "otp_codes"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, index=True, nullable=False)
    code = Column(String, nullable=False) # e.g., "482910"
    purpose = Column(String, nullable=False) # "register", "reset_password"
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False)
    

class FeatureUsage(Base):
    __tablename__ = "feature_usage"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    tenant_id = Column(
        String,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        index=True
    )

    feature = Column(String, nullable=False)

    usage_count = Column(Integer, default=0)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    



