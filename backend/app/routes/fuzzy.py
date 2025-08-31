from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, FuzzyJob, UserFile
from app.services.fuzzy import FuzzyService, SingleFileFuzzyRequest, FuzzyLookupRequest, ColumnNamesResponse, OutputDataframe, FileProcessingHandler
from app.services.license import LicenseService
from app.services.file import FileService
from app.dependencies import get_current_user, get_fuzzy_service, get_license_service, get_file_service
from string_grouper import group_similar_strings, match_strings
import os
import pandas as pd
import Levenshtein
import time
from datetime import datetime

router = APIRouter()


@router.post("/column_names", response_model=ColumnNamesResponse)
async def get_column_names(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    license_svc: LicenseService = Depends(get_license_service),
    file_svc: FileService = Depends(get_file_service),
    fuzzy_svc: FuzzyService = Depends(get_fuzzy_service)
):
    license_svc.check_file_upload_permissions(current_user, db, file.size or 0)
    user_file = await file_svc.save_uploaded_file(file, current_user, db)
    column_names = fuzzy_svc.get_column_names(user_file.file_path)
    
    return ColumnNamesResponse(
        filename=user_file.stored_filename,
        column_names=column_names
    )

@router.post("/lookup_single_file")
async def lookup_single_file(
    request: SingleFileFuzzyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    license_service: LicenseService = Depends(get_license_service),
    fuzzy_service: FuzzyService = Depends(get_fuzzy_service)
):
    license_service.check_operation_permissions(current_user, db)
    output_path = fuzzy_service.process_single_file_fuzzy_lookup(request, current_user, db)
    license_service.increment_operation_count(current_user, db)
    
    return FileResponse(
        path=output_path,
        media_type='text/csv',
        filename=os.path.basename(output_path)
    )


@router.post("/lookup_multi_file")
async def lookup_multi_file(
    request: FuzzyLookupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    license_service: LicenseService = Depends(get_license_service),
    fuzzy_service: FuzzyService = Depends(get_fuzzy_service)
):
    license_service.check_operation_permissions(current_user, db)

    try:
        output_path = fuzzy_service.process_multi_file_fuzzy_lookup(request, current_user, db)
        license_service.increment_operation_count(current_user, db)

        return FileResponse(
            path=output_path,
            media_type=f'text/{request.output_type}',
            filename=os.path.basename(output_path)
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.post("/query_dataframe")
async def query_dataframe_api(
    file: UploadFile = File(...),
    query_column: str = Form(...),
    search_term: str = Form(...),
    threshold: float = Form(0.8),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    license_service: LicenseService = Depends(get_license_service),
    file_service: FileService = Depends(get_file_service)
):
    license_service.check_file_upload_permissions(current_user, db, file.size or 0)
    license_service.check_operation_permissions(current_user, db)
    
    user_file = await file_service.save_uploaded_file(file, current_user, db)
    df = OutputDataframe(user_file.file_path).convert_to_dataframe()
    
    if query_column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Column '{query_column}' not found")
    
    matches = match_strings(
        pd.Series([search_term]),
        df[query_column].astype(str).dropna(),
        ignore_index=True,
        min_similarity=threshold
    )
    
    if len(matches) > 0:
        matched_indices = matches[f'right_{query_column}'].values
        matched_rows = df[df[query_column].isin(matched_indices)].copy()
        similarity_map = dict(zip(matches[f'right_{query_column}'], matches['similarity']))
        matched_rows['similarity_score'] = matched_rows[query_column].map(similarity_map)
        matched_rows = matched_rows.sort_values('similarity_score', ascending=False)
        results = matched_rows.to_dict('records')
    else:
        results = []
    
    license_service.increment_operation_count(current_user, db)
    
    return {
        "query_term": search_term,
        "query_column": query_column,
        "threshold": threshold,
        "matches_found": len(results),
        "results": results
    }


@router.get("/jobs")
async def get_user_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    jobs = db.query(FuzzyJob).filter(
        FuzzyJob.user_id == current_user.id
    ).order_by(FuzzyJob.created_at.desc()).offset(offset).limit(limit).all()
    
    job_list = [{
        "id": job.id,
        "job_type": job.job_type,
        "status": job.status,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "matches_count": job.matches_count,
        "threshold": job.threshold,
        "output_filename": job.output_filename,
        "error_message": job.error_message
    } for job in jobs]
    
    return {
        "jobs": job_list,
        "total": len(jobs),
        "offset": offset,
        "limit": limit
    }


@router.get("/download/{job_id}")
async def download_job_result(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(FuzzyJob).filter(
        FuzzyJob.id == job_id,
        FuzzyJob.user_id == current_user.id,
        FuzzyJob.status == "completed"
    ).first()
    
    if not job or not job.output_path or not os.path.exists(job.output_path):
        raise HTTPException(status_code=404, detail="Job or output file not found")
    
    return FileResponse(
        path=job.output_path,
        media_type='application/octet-stream',
        filename=job.output_filename or os.path.basename(job.output_path)
    )


@router.post("/upload_and_lookup_single_file_api")
async def upload_and_lookup_single_file_api(
    file: UploadFile = File(...),
    column_1: str = Form(...),
    column_2: str = Form(...),
    threshold: float = Form(0.8),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    license_service: LicenseService = Depends(get_license_service),
    file_service: FileService = Depends(get_file_service)
):
    license_service.check_file_upload_permissions(current_user, db, file.size or 0)
    license_service.check_operation_permissions(current_user, db)

    try:
        user_file = await file_service.save_uploaded_file(file, current_user, db)

        output_df = OutputDataframe(user_file.file_path)
        df = output_df.convert_to_dataframe()

        if column_1 not in df.columns:
            raise HTTPException(status_code=400, detail=f"Column '{column_1}' not found in uploaded file")
        if column_2 not in df.columns:
            raise HTTPException(status_code=400, detail=f"Column '{column_2}' not found in uploaded file")

        file_processor = FileProcessingHandler(df, threshold)
        processed_df = file_processor.pre_process_dataframe(column_1, column_2)

        if 'similarity' in processed_df.columns:
            processed_df['similarity'] = processed_df['similarity'].round(4)

        data = processed_df.to_dict('records')
        columns = list(processed_df.columns)

        job = FuzzyJob(
            user_id=current_user.id,
            file_id=user_file.id,
            job_type="upload_and_lookup_api",
            status="completed",
            file_1_column=column_1,
            file_2_column=column_2,
            threshold=threshold,
            matches_count=len(data),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        db.add(job)

        license_service.increment_operation_count(current_user, db)
        db.commit()

        return {
            "data": data,
            "columns": columns,
            "metadata": {
                "original_filename": file.filename,
                "stored_filename": user_file.stored_filename,
                "file_id": user_file.id,
                "column_1": column_1,
                "column_2": column_2,
                "threshold": threshold,
                "matches_found": len(data),
                "total_rows_processed": len(df),
                "job_id": job.id,
                "available_columns": list(df.columns)
            }
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.post("/lookup_single_file_api")
async def lookup_single_file_api(
    request: SingleFileFuzzyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    license_service: LicenseService = Depends(get_license_service),
    fuzzy_service: FuzzyService = Depends(get_fuzzy_service)
):
    license_service.check_operation_permissions(current_user, db)
    
    try:
        user_file = (
            db.query(UserFile)
            .filter(UserFile.user_id == current_user.id, UserFile.stored_filename == request.filename)
            .first()
        )

        if not user_file:
            raise HTTPException(status_code=404, detail="File not found")
        
        output_df = OutputDataframe(user_file.file_path)
        df = output_df.convert_to_dataframe()
        
        if request.column_1 not in df.columns:
            raise HTTPException(status_code=400, detail=f"Column '{request.column_1}' not found")
        if request.column_2 not in df.columns:
            raise HTTPException(status_code=400, detail=f"Column '{request.column_2}' not found")
        
        file_processor = FileProcessingHandler(df, request.threshold)
        processed_df = file_processor.pre_process_dataframe(request.column_1, request.column_2)

        print("s1", processed_df['similarity'])
        if 'similarity' in processed_df.columns:
            processed_df['similarity'] = processed_df['similarity'].round(4)
        print("s2", processed_df['similarity'])

        data = processed_df.to_dict('records')
        columns = list(processed_df.columns)
        
        job = FuzzyJob(
            user_id=current_user.id,
            file_id=user_file.id,
            job_type="single_file_api",
            status="completed",
            file_1_column=request.column_1,
            file_2_column=request.column_2,
            threshold=request.threshold,
            matches_count=len(data),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        db.add(job)
        
        license_service.increment_operation_count(current_user, db)
        db.commit()
        
        return {
            "data": data,
            "columns": columns,
            "metadata": {
                "filename": request.filename,
                "column_1": request.column_1,
                "column_2": request.column_2,
                "threshold": request.threshold,
                "matches_found": len(data),
                "total_rows_processed": len(df),
                "job_id": job.id
            }
        }
        
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.post("/find_duplicates")
async def find_duplicates_in_column(
    file: UploadFile = File(...),
    column_name: str = Form(...),
    threshold: float = Form(0.8),
    output_type: str = Form("csv"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    license_service: LicenseService = Depends(get_license_service),
    file_service: FileService = Depends(get_file_service),
):
    license_service.check_file_upload_permissions(current_user, db, file.size or 0)
    license_service.check_operation_permissions(current_user, db)

    user_file = await file_service.save_uploaded_file(file, current_user, db)
    df = OutputDataframe(user_file.file_path).convert_to_dataframe()

    if column_name not in df.columns:
        raise HTTPException(status_code=400, detail=f"Column '{column_name}' not found")

    df_clean = df.dropna(subset=[column_name]).copy()
    df_clean[column_name] = df_clean[column_name].astype(str).str.strip()
    df_clean = df_clean[df_clean[column_name] != ''].reset_index(drop=True)

    if len(df_clean) == 0:
        raise HTTPException(status_code=400, detail="No valid data found in column")

    grouped_df = group_similar_strings(df_clean[column_name], min_similarity=threshold)
    
    group_rep_col = f"group_rep_{column_name}"
    result_df = pd.concat([df_clean, grouped_df[[group_rep_col, "group_rep_index"]]], axis=1)
    result_df = result_df.rename(columns={group_rep_col: 'group_rep', "group_rep_index": 'group_id'})

    result_df['similarity'] = result_df.apply(
        lambda x: Levenshtein.ratio(str(x[column_name]), str(x['group_rep'])), axis=1
    )

    group_counts = result_df.groupby('group_id').size()
    duplicate_groups = group_counts[group_counts > 1].index
    duplicates = result_df[result_df['group_id'].isin(duplicate_groups)]

    if len(duplicates) == 0:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_filename = f"no_duplicates_{timestamp}.{output_type}"
        output_path = f"data/downloads/{output_filename}"
        os.makedirs("data/downloads", exist_ok=True)

        empty_df = pd.DataFrame(columns=['rank'] + list(df.columns) + ['similarity'])
        if output_type == 'xlsx':
            empty_df.to_excel(output_path, index=False)
        else:
            empty_df.to_csv(output_path, index=False)
    else:
        duplicates = duplicates.sort_values(['group_id', 'similarity'], ascending=[True, False])
        duplicates['rank'] = duplicates.groupby('group_id').ngroup() + 1

        output_cols = ['rank'] + [col for col in df.columns if col in duplicates.columns] + ['similarity']
        final_df = duplicates[output_cols]

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_filename = f"duplicates_{column_name}_{timestamp}.{output_type}"
        output_path = f"data/downloads/{output_filename}"
        os.makedirs("data/downloads", exist_ok=True)

        if output_type == 'xlsx':
            final_df.to_excel(output_path, index=False)
        else:
            final_df.to_csv(output_path, index=False)

    license_service.increment_operation_count(current_user, db)
    return FileResponse(path=output_path, media_type='application/octet-stream', filename=output_filename)
