from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status

from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..services.file import FileService
from ..services.license import LicenseService
from ..services.fuzzy import FuzzyService
from ..dependencies import get_current_user, get_file_service, get_license_service, get_fuzzy_service

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    file_service: FileService = Depends(get_file_service),
    license_service: LicenseService = Depends(get_license_service),
):
    try:
        file_content = await file.read()
        file_size = len(file_content)
        await file.seek(0)

        license_service.check_file_upload_permissions(current_user, db, file_size)
        user_file = await file_service.save_uploaded_file(file, current_user, db)

        return {
            "id": user_file.id,
            "original_filename": user_file.original_filename,
            "stored_filename": user_file.stored_filename,
            "file_size_bytes": user_file.file_size_bytes,
            "file_type": user_file.file_type,
            "upload_date": user_file.upload_date.isoformat(),
            "message": "File uploaded successfully",
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload file")


@router.get("/list")
async def list_user_files(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    file_service: FileService = Depends(get_file_service),
    limit: int = 50,
    offset: int = 0,
):
    try:
        files = file_service.get_user_files(current_user, db, limit, offset)

        file_list = []
        for file in files:
            file_dict = {
                "id": file.id,
                "original_filename": file.original_filename,
                "stored_filename": file.stored_filename,
                "file_size_bytes": file.file_size_bytes,
                "file_size_mb": round(file.file_size_bytes / (1024 * 1024), 2),
                "file_type": file.file_type,
                "upload_date": file.upload_date.isoformat(),
                "is_processed": file.is_processed,
            }
            file_list.append(file_dict)

        return {"files": file_list, "total": len(files), "limit": limit, "offset": offset}

    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve file list")


@router.get("/{file_id}")
async def get_file_info(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    file_service: FileService = Depends(get_file_service),
):
    try:
        user_file = file_service.get_file_by_id(file_id, current_user, db)

        return {
            "id": user_file.id,
            "original_filename": user_file.original_filename,
            "stored_filename": user_file.stored_filename,
            "file_size_bytes": user_file.file_size_bytes,
            "file_size_mb": round(user_file.file_size_bytes / (1024 * 1024), 2),
            "file_type": user_file.file_type,
            "upload_date": user_file.upload_date.isoformat(),
            "is_processed": user_file.is_processed,
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve file information"
        )


@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    file_service: FileService = Depends(get_file_service),
):
    try:
        success = file_service.delete_file(file_id, current_user, db)

        if success:
            return {"message": "File deleted successfully"}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete file")

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete file")


@router.get("/{file_id}/columns")
async def get_file_columns(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    file_service: FileService = Depends(get_file_service),
    fuzzy_service: FuzzyService = Depends(get_fuzzy_service),
    sheet_name: str = None
):
    try:
        user_file = file_service.get_file_by_id(file_id, current_user, db)

        column_names, sheet_names, resolved_sheet = fuzzy_service.get_column_names(
            user_file.file_path, sheet_name
        )

        return {
            "file_id": file_id,
            "original_filename": user_file.original_filename,
            "column_names": column_names,
            "sheet_names": sheet_names,
            "sheet_name": resolved_sheet,
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve file columns"
        )


@router.get("/storage/usage")
async def get_storage_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    file_service: FileService = Depends(get_file_service),
    license_service: LicenseService = Depends(get_license_service),
):
    try:
        files = file_service.get_user_files(current_user, db, limit=1000)

        total_files = len(files)
        total_size_bytes = sum(file.file_size_bytes for file in files)
        total_size_mb = round(total_size_bytes / (1024 * 1024), 2)

        file_types = {}
        for file in files:
            if file.file_type in file_types:
                file_types[file.file_type] += 1
            else:
                file_types[file.file_type] = 1

        license = license_service.get_user_active_license(current_user, db)
        max_file_size_mb = license.max_file_size_mb if license else 0

        return {
            "total_files": total_files,
            "total_size_bytes": total_size_bytes,
            "total_size_mb": total_size_mb,
            "max_file_size_mb": max_file_size_mb,
            "file_types": file_types,
            "recent_uploads": [
                {
                    "filename": file.original_filename,
                    "size_mb": round(file.file_size_bytes / (1024 * 1024), 2),
                    "upload_date": file.upload_date.isoformat(),
                    "type": file.file_type,
                }
                for file in files[:5]
            ],
        }

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve storage usage"
        )
