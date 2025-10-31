
from sqlalchemy import Column, Integer, BigInteger, Text, String, JSON, DateTime
from sqlalchemy.sql import func
from app.db.session import Base

JSONType = JSON

class UnitIngestJob(Base):
    __tablename__ = "unit_ingest_jobs"
    id = Column(BigInteger, primary_key=True)
    book_id = Column(BigInteger, nullable=False)
    chapter_id = Column(BigInteger, nullable=False)
    unit_id = Column(BigInteger, nullable=False)
    page_start = Column(Integer, nullable=False)
    page_end = Column(Integer, nullable=False)
    start_text = Column(Text)
    end_text = Column(Text)
    start_match_idx = Column(Integer)
    end_match_idx = Column(Integer)
    language_code = Column(String(16), default="en")
    subject = Column(String(64))
    grade_level = Column(String(32))
    teacher_extra = Column(JSONType)
    unit_prompt_instructions = Column(Text)
    status = Column(String(16), default="queued")
    error = Column(Text)
    preview_json = Column(JSONType)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class UnitChunk(Base):
    __tablename__ = "unit_chunks"
    id = Column(BigInteger, primary_key=True)
    unit_id = Column(BigInteger, nullable=False)
    chunk_uid = Column(String(64), nullable=False)
    ord = Column(Integer, nullable=False)
    text = Column(Text)
    latex = Column(Text)
    tokens = Column(Integer)
    image_refs = Column(JSONType)
    teacher_extra = Column(JSONType)
    language_code = Column(String(16))
    subject = Column(String(64))
    grade_level = Column(String(32))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ImageCatalog(Base):
    __tablename__ = "images_catalog"
    id = Column(BigInteger, primary_key=True)
    unit_id = Column(BigInteger, nullable=False)
    page_no = Column(Integer, nullable=False)
    image_id = Column(String(64), nullable=False)
    s3_uri = Column(Text)
    caption = Column(Text)
    bbox = Column(JSONType)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
