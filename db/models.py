from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from db.session import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)  # Removed length limit
    password_hash = Column(String, nullable=False)  # Removed length limit
    is_pro = Column(Boolean, default=False, nullable=False)  # NEW: Pro subscription status
    created_at = Column(DateTime, server_default=func.now())  # NEW: Track user registration
    resumes = relationship("Resume", back_populates="owner", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="owner", cascade="all, delete-orphan")

class Resume(Base):
    __tablename__ = "resumes"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)  # Removed length limit
    original_filename = Column(String, nullable=True)  # NEW: Keep original upload name
    path = Column(String, nullable=False)  # Removed length limit
    text = Column(Text, nullable=True)
    file_size = Column(Integer, nullable=True)  # NEW: Track file size in bytes
    file_type = Column(String, nullable=True)  # NEW: pdf, docx, etc.
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())  # NEW: Track updates
    
    owner = relationship("User", back_populates="resumes")
    analyses = relationship("Analysis", back_populates="resume", cascade="all, delete-orphan")

class Analysis(Base):
    __tablename__ = "analyses"
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"))
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    job_description = Column(Text, nullable=True)
    result_json = Column(Text, nullable=False)
    score = Column(Integer, nullable=True)  # NEW: Overall match score (0-100)
    analysis_type = Column(String, default="ats", nullable=False)  # NEW: ats, skills, grammar, etc.
    created_at = Column(DateTime, server_default=func.now())
    
    resume = relationship("Resume", back_populates="analyses")
    owner = relationship("User", back_populates="analyses")

# NEW: Subscription model for future payment features
class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    stripe_customer_id = Column(String, unique=True, nullable=True)
    stripe_subscription_id = Column(String, unique=True, nullable=True)
    status = Column(String, default="inactive", nullable=False)  # active, canceled, past_due
    current_period_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    user = relationship("User")