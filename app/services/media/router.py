# backend/app/services/media/router.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import boto3
from botocore.config import Config

from app.core.config import settings
from app.api.dependencies import get_current_user

router = APIRouter()

# Initialize the S3 client pointing to Cloudflare R2
s3_client = boto3.client(
    "s3",
    endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=settings.R2_ACCESS_KEY_ID,
    aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
    config=Config(signature_version="s3v4"),
    region_name="auto"
)

class PresignedUrlRequest(BaseModel):
    filename: str
    content_type: str
    folder: str = "publications" # e.g., 'cv', 'profile', 'publications'

@router.post("/presigned-url")
async def generate_presigned_url(
    payload: PresignedUrlRequest,
    current_user: dict = Depends(get_current_user)
):
    tenant_id = current_user["tenant_id"]
    
    # 1. Enforce the strict Multi-Tenant Bucket Structure from your blueprint
    # Structure: /tenant_id/folder/filename
    safe_filename = payload.filename.replace(" ", "_")
    object_key = f"{tenant_id}/{payload.folder}/{safe_filename}"

    try:
        # 2. Generate the temporary upload ticket (Valid for 15 minutes)
        presigned_url = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": settings.R2_BUCKET_NAME,
                "Key": object_key,
                "ContentType": payload.content_type
            },
            ExpiresIn=900 
        )

        # 3. Return the URL and the Key (The frontend saves the Key to PostgreSQL later)
        return {
            "upload_url": presigned_url,
            "file_key": object_key
        }
        
    except Exception as e:
        print(f"R2 Error: {e}")
        raise HTTPException(status_code=500, detail="Could not generate upload URL")
    


# backend/app/services/media/router.py (Add to bottom)

@router.get("/download-url")
async def get_download_url(file_key: str):
    """
    Generates a temporary read-only URL for students to download PDFs.
    Valid for 60 minutes.
    """
    try:
        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.R2_BUCKET_NAME,
                "Key": file_key
            },
            ExpiresIn=3600 # 1 hour expiration
        )
        return {"download_url": presigned_url}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not generate download link")