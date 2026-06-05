import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Fallback to local SQLite for development
    DATABASE_URL = "sqlite:///./auditor.db"
elif DATABASE_URL.startswith("postgres://"):
    # Fix Heroku/Railway Postgres URL syntax if needed
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    content_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    audits = relationship("AuditRun", back_populates="file")

class AuditRun(Base):
    __tablename__ = "audit_runs"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("uploaded_files.id"), nullable=False)
    status = Column(String(50), default="in_progress")  # in_progress, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)

    file = relationship("UploadedFile", back_populates="audits")
    cards = relationship("AuditCard", back_populates="audit")

class AuditCard(Base):
    __tablename__ = "audit_cards"

    id = Column(Integer, primary_key=True, index=True)
    audit_id = Column(Integer, ForeignKey("audit_runs.id"), nullable=False)
    severity = Column(String(50), nullable=False)  # High, Med, Low
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    contradiction_details = Column(Text, nullable=False)  # JSON-wrapped or raw text contradiction details
    created_at = Column(DateTime, default=datetime.utcnow)

    audit = relationship("AuditRun", back_populates="cards")

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
