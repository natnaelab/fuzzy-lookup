from fastapi import UploadFile
from sqlalchemy.orm import Session
from ..models import User, UserFile
from pathlib import Path
import uuid
import os
import re
from typing import List


class FileService:
    ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}
    MAX_FILENAME_LENGTH = 255

    def __init__(self):
        self.upload_dir = Path("data/uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def is_allowed_file(self, filename: str) -> bool:
        return "." in filename and filename.rsplit(".", 1)[1].lower() in self.ALLOWED_EXTENSIONS

    def sanitize_filename(self, filename: str) -> str:
        sanitized = re.sub(r"[^\w\s.-]", "", filename)
        sanitized = re.sub(r"[\s]+", "_", sanitized)
        if len(sanitized) > self.MAX_FILENAME_LENGTH:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[: self.MAX_FILENAME_LENGTH - len(ext)] + ext
        return sanitized

    def generate_secure_filename(self, user_id: int, original_filename: str) -> str:
        unique_id = str(uuid.uuid4())
        sanitized_filename = self.sanitize_filename(original_filename)
        return f"{unique_id}_{sanitized_filename}"

    def get_user_directory(self, user_id: int) -> Path:
        user_dir = self.upload_dir / f"user_{user_id}"
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir

    async def save_uploaded_file(self, file: UploadFile, user: User, db: Session) -> UserFile:
        try:
            if not file.filename:
                raise ValueError("No filename provided")

            if not self.is_allowed_file(file.filename):
                raise ValueError(f"File type not allowed. Allowed types: {', '.join(self.ALLOWED_EXTENSIONS)}")

            file_content = await file.read()
            file_size = len(file_content)

            if file_size == 0:
                raise ValueError("Empty file not allowed")

            user_dir = self.get_user_directory(user.id)
            unique_subdir = user_dir / f"{file.filename}_{uuid.uuid4()}"
            unique_subdir.mkdir(parents=True, exist_ok=True)

            secure_filename = self.generate_secure_filename(user.id, file.filename)
            file_path = unique_subdir / secure_filename

            with open(file_path, "wb") as f:
                f.write(file_content)

            file_extension = Path(file.filename).suffix.lower()

            user_file = UserFile(
                user_id=user.id,
                original_filename=file.filename,
                stored_filename=secure_filename,
                file_path=str(file_path),
                file_size_bytes=file_size,
                file_type=file_extension.lstrip("."),
            )

            db.add(user_file)
            db.commit()
            db.refresh(user_file)

            return user_file

        except Exception as e:
            db.rollback()
            raise

    def get_user_files(self, user: User, db: Session, limit: int = 50, offset: int = 0) -> List[UserFile]:
        return (
            db.query(UserFile)
            .filter(UserFile.user_id == user.id)
            .order_by(UserFile.upload_date.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_file_by_id(self, file_id: int, user: User, db: Session) -> UserFile:
        user_file = db.query(UserFile).filter(UserFile.id == file_id, UserFile.user_id == user.id).first()

        if not user_file:
            raise ValueError("File not found or access denied")

        return user_file

    def delete_file(self, file_id: int, user: User, db: Session) -> bool:
        user_file = self.get_file_by_id(file_id, user, db)

        if os.path.exists(user_file.file_path):
            os.remove(user_file.file_path)
            try:
                Path(user_file.file_path).parent.rmdir()
            except OSError:
                pass

        db.delete(user_file)
        db.commit()
        return True
