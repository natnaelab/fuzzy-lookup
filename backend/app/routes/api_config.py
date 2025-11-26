from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models import User, APIConfiguration, UserFile
from ..dependencies import get_current_user
from ..services.fuzzy import OutputDataframe
from string_grouper import match_strings
import pandas as pd

router = APIRouter()


# Pydantic models for request/response
class APIConfigCreate(BaseModel):
    name: str
    description: Optional[str] = None
    file_id: int
    column_name: str
    threshold: float = 0.8


class APIConfigUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    column_name: Optional[str] = None
    threshold: Optional[float] = None
    is_active: Optional[bool] = None


class APIConfigResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    file_id: int
    filename: str
    column_name: str
    threshold: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QueryRequest(BaseModel):
    search_term: str
    threshold: Optional[float] = None  # Override default threshold if provided


class QueryResponse(BaseModel):
    config_id: int
    config_name: str
    search_term: str
    threshold: float
    matches_found: int
    results: List[dict]


@router.post("/", response_model=APIConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_api_configuration(
    config: APIConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new API configuration for fuzzy matching"""
    
    # Verify user owns the file
    user_file = db.query(UserFile).filter(
        UserFile.id == config.file_id,
        UserFile.user_id == current_user.id
    ).first()
    
    if not user_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or access denied"
        )
    
    # Verify column exists in file
    try:
        output_df = OutputDataframe(user_file.file_path)
        df = output_df.convert_to_dataframe()
        
        if config.column_name not in df.columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Column '{config.column_name}' not found in file. Available columns: {list(df.columns)}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read file: {str(e)}"
        )
    
    # Create configuration
    api_config = APIConfiguration(
        user_id=current_user.id,
        name=config.name,
        description=config.description,
        file_id=config.file_id,
        column_name=config.column_name,
        threshold=config.threshold
    )
    
    db.add(api_config)
    db.commit()
    db.refresh(api_config)
    
    return APIConfigResponse(
        id=api_config.id,
        name=api_config.name,
        description=api_config.description,
        file_id=api_config.file_id,
        filename=user_file.original_filename,
        column_name=api_config.column_name,
        threshold=api_config.threshold,
        is_active=api_config.is_active,
        created_at=api_config.created_at,
        updated_at=api_config.updated_at
    )


@router.get("/", response_model=List[APIConfigResponse])
async def list_api_configurations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    include_inactive: bool = False
):
    """List all API configurations for the current user"""
    
    query = db.query(APIConfiguration).filter(
        APIConfiguration.user_id == current_user.id
    )
    
    if not include_inactive:
        query = query.filter(APIConfiguration.is_active == True)
    
    configs = query.order_by(APIConfiguration.created_at.desc()).all()
    
    response = []
    for config in configs:
        file = db.query(UserFile).filter(UserFile.id == config.file_id).first()
        response.append(APIConfigResponse(
            id=config.id,
            name=config.name,
            description=config.description,
            file_id=config.file_id,
            filename=file.original_filename if file else "File not found",
            column_name=config.column_name,
            threshold=config.threshold,
            is_active=config.is_active,
            created_at=config.created_at,
            updated_at=config.updated_at
        ))
    
    return response


@router.get("/{config_id}", response_model=APIConfigResponse)
async def get_api_configuration(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific API configuration"""
    
    config = db.query(APIConfiguration).filter(
        APIConfiguration.id == config_id,
        APIConfiguration.user_id == current_user.id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )
    
    file = db.query(UserFile).filter(UserFile.id == config.file_id).first()
    
    return APIConfigResponse(
        id=config.id,
        name=config.name,
        description=config.description,
        file_id=config.file_id,
        filename=file.original_filename if file else "File not found",
        column_name=config.column_name,
        threshold=config.threshold,
        is_active=config.is_active,
        created_at=config.created_at,
        updated_at=config.updated_at
    )


@router.put("/{config_id}", response_model=APIConfigResponse)
async def update_api_configuration(
    config_id: int,
    update_data: APIConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an API configuration"""
    
    config = db.query(APIConfiguration).filter(
        APIConfiguration.id == config_id,
        APIConfiguration.user_id == current_user.id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )
    
    # Update fields if provided
    if update_data.name is not None:
        config.name = update_data.name
    if update_data.description is not None:
        config.description = update_data.description
    if update_data.column_name is not None:
        # Verify column exists
        file = db.query(UserFile).filter(UserFile.id == config.file_id).first()
        try:
            output_df = OutputDataframe(file.file_path)
            df = output_df.convert_to_dataframe()
            if update_data.column_name not in df.columns:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Column '{update_data.column_name}' not found"
                )
            config.column_name = update_data.column_name
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to validate column: {str(e)}"
            )
    if update_data.threshold is not None:
        config.threshold = update_data.threshold
    if update_data.is_active is not None:
        config.is_active = update_data.is_active
    
    db.commit()
    db.refresh(config)
    
    file = db.query(UserFile).filter(UserFile.id == config.file_id).first()
    
    return APIConfigResponse(
        id=config.id,
        name=config.name,
        description=config.description,
        file_id=config.file_id,
        filename=file.original_filename if file else "File not found",
        column_name=config.column_name,
        threshold=config.threshold,
        is_active=config.is_active,
        created_at=config.created_at,
        updated_at=config.updated_at
    )


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_configuration(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete (soft delete) an API configuration"""
    
    config = db.query(APIConfiguration).filter(
        APIConfiguration.id == config_id,
        APIConfiguration.user_id == current_user.id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )
    
    # Soft delete
    config.is_active = False
    db.commit()
    
    return None


@router.post("/{config_id}/query", response_model=QueryResponse)
async def query_api_configuration(
    config_id: int,
    query_data: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Query a saved API configuration with fuzzy matching"""
    
    # Get configuration
    config = db.query(APIConfiguration).filter(
        APIConfiguration.id == config_id,
        APIConfiguration.user_id == current_user.id,
        APIConfiguration.is_active == True
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found or inactive"
        )
    
    # Get file
    file = db.query(UserFile).filter(UserFile.id == config.file_id).first()
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reference file not found"
        )
    
    # Use provided threshold or default from config
    threshold = query_data.threshold if query_data.threshold is not None else config.threshold
    
    try:
        # Load dataset
        output_df = OutputDataframe(file.file_path)
        df = output_df.convert_to_dataframe()
        
        if config.column_name not in df.columns:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Column '{config.column_name}' no longer exists in file"
            )
        
        # Perform fuzzy matching
        matches = match_strings(
            pd.Series([query_data.search_term]),
            df[config.column_name].astype(str).dropna(),
            ignore_index=True,
            min_similarity=threshold
        )
        
        results = []
        if len(matches) > 0:
            matched_indices = matches[f'right_{config.column_name}'].values
            matched_rows = df[df[config.column_name].isin(matched_indices)].copy()
            similarity_map = dict(zip(matches[f'right_{config.column_name}'], matches['similarity']))
            matched_rows['similarity_score'] = matched_rows[config.column_name].map(similarity_map)
            matched_rows = matched_rows.sort_values('similarity_score', ascending=False)
            results = matched_rows.to_dict('records')
        
        return QueryResponse(
            config_id=config.id,
            config_name=config.name,
            search_term=query_data.search_term,
            threshold=threshold,
            matches_found=len(results),
            results=results
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )


@router.get("/{config_id}/docs")
async def get_api_documentation(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get API usage documentation for a specific configuration"""
    
    config = db.query(APIConfiguration).filter(
        APIConfiguration.id == config_id,
        APIConfiguration.user_id == current_user.id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )
    
    # Base URL for API
    base_url = "https://api.fuzzylookupmatch.com"
    
    documentation = {
        "config_id": config.id,
        "config_name": config.name,
        "description": config.description,
        "column": config.column_name,
        "default_threshold": config.threshold,
        "authentication": {
            "type": "JWT Bearer Token",
            "login_endpoint": f"{base_url}/auth/login",
            "example": {
                "request": {
                    "method": "POST",
                    "url": f"{base_url}/auth/login",
                    "body": {
                        "username": "your-email@example.com",
                        "password": "your-password"
                    }
                },
                "response": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer"
                }
            }
        },
        "query_endpoint": {
            "url": f"{base_url}/api/configurations/{config.id}/query",
            "method": "POST",
            "headers": {
                "Authorization": "Bearer <your-access-token>",
                "Content-Type": "application/json"
            },
            "body": {
                "search_term": "string",
                "threshold": "float (optional, override default)"
            },
            "example_request": {
                "search_term": "Microsoft Corporation",
                "threshold": 0.85
            },
            "example_response": {
                "config_id": config.id,
                "config_name": config.name,
                "search_term": "Microsoft Corporation",
                "threshold": 0.85,
                "matches_found": 5,
                "results": [
                    {"similarity_score": 0.95, config.column_name: "Microsoft Corp", "...": "other columns"}
                ]
            }
        },
        "curl_example": f"""
curl -X POST "{base_url}/api/configurations/{config.id}/query" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{{"search_term": "Microsoft Corporation", "threshold": 0.85}}'
        """.strip()
    }
    
    return documentation
