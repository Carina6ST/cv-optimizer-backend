from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from db.session import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    resumes = relationship("Resume", back_populates="owner")
    analyses = relationship("Analysis", back_populates="owner")

class Resume(Base):
    __tablename__ = "resumes"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    path = Column(String(512), nullable=False)
    text = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    owner = relationship("User", back_populates="resumes")
    analyses = relationship("Analysis", back_populates="resume")

class Analysis(Base):
    __tablename__ = "analyses"
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"))
    owner_id = Column(Integer, ForeignKey("users.id"))
    job_description = Column(Text, nullable=True)
    result_json = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    resume = relationship("Resume", back_populates="analyses")
    owner = relationship("User", back_populates="analyses")
