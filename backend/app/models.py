from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    files = relationship("UserFile", back_populates="user", cascade="all, delete-orphan")
    fuzzy_jobs = relationship("FuzzyJob", back_populates="user", cascade="all, delete-orphan")

class UserFile(Base):
    __tablename__ = "user_files"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    file_type = Column(String, nullable=False)  # csv, xlsx, xls
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    is_processed = Column(Boolean, default=False)

    # Relationship
    user = relationship("User", back_populates="files")
    fuzzy_jobs = relationship("FuzzyJob", back_populates="file", primaryjoin="UserFile.id == FuzzyJob.file_id")


class FuzzyJob(Base):
    __tablename__ = "fuzzy_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_id = Column(Integer, ForeignKey("user_files.id"), nullable=True)
    file_1_id = Column(Integer, ForeignKey("user_files.id"), nullable=True)
    file_2_id = Column(Integer, ForeignKey("user_files.id"), nullable=True)
    job_type = Column(String, nullable=False)  # single_file, multi_file
    status = Column(String, default="pending")  # pending, processing, completed, failed

    # Job parameters
    file_1_column = Column(String, nullable=True)
    file_2_column = Column(String, nullable=True)
    threshold = Column(Float, nullable=False)
    delimiter = Column(String, default=",")
    output_type = Column(String, default="csv")

    # Results
    output_filename = Column(String, nullable=True)
    output_path = Column(String, nullable=True)
    matches_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="fuzzy_jobs")
    file = relationship("UserFile", back_populates="fuzzy_jobs", primaryjoin="FuzzyJob.file_id == UserFile.id", viewonly=False)
    file_1 = relationship("UserFile", primaryjoin="FuzzyJob.file_1_id == UserFile.id", post_update=True)
    file_2 = relationship("UserFile", primaryjoin="FuzzyJob.file_2_id == UserFile.id", post_update=True)
