import os
import logging
import asyncio

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse

from pydantic import BaseModel
from sqlmodel import Session, select

from database import get_session
from models import Job, Thumbnail
from services.generator import process_job
from services.imagekit_service import upload_file, get_variants
from typing import Optional
from services.generator import STYLE_ORDER

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

# Request Response Schema

class CreateJobRequest(BaseModel):
    prompt: str
    num_thumbnails: int = 3
    headshot_url: str

class CreateJobResponse(BaseModel):
    job_id: str

class ThumbnailResponse(BaseModel):
    id: str
    style_name: str
    status: str
    imagekit_url: str = None
    error_message: Optional[str] = None
    variants: Optional[dict[str, str]] = None

class JobResponse(BaseModel):
    id: str
    prompt: str
    num_thumbnails: int
    headshot_url: str
    status: str
    thumbnails: list[ThumbnailResponse]

# API Endpoints

@router.post('/upload-headshot')
async def upload_headshot(file: UploadFile = File(...)):
    try:
        content = await file.read()
        logger.info(f'Uploading headshot: {file.filename}')
        url = upload_file(content, file.filename, 'headshots', file.content_type)
        if not url:
            raise HTTPException(status_code=500, detail='Failed to upload headshot')
        return {'url': url}
    except Exception as e:
        logger.error(f'Error uploading headshot: {e}')
        raise HTTPException(status_code=500, detail='Failed to upload headshot')



@router.post('/jobs', response_model=CreateJobResponse)
async def create_job(request: CreateJobRequest, session: Session = Depends(get_session)):
    if request.num_thumbnails not in [1, 2, 3]:
        raise HTTPException(status_code=400, detail='Number of thumbnails must be between 1 and 3')
    
    job = Job(
        prompt=request.prompt,
        num_thumbnails=request.num_thumbnails,
        headshot_url=request.headshot_url,
        status='pending'
    )
    session.add(job)
    styles = STYLE_ORDER[:request.num_thumbnails]
    for style_name in styles:
        thumbnail = Thumbnail(
            job_id=job.id,
            style_name=style_name,
            status='pending'
        )
        session.add(thumbnail)
    session.commit()
    logger.info(f"Job created with ID: {job.id}")

    asyncio.create_task(process_job(job.id))
    
    return CreateJobResponse(job_id=job.id)



@router.get('/jobs/{job_id}', response_model=JobResponse)
async def get_job(job_id: str, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')
    thumbnail_response = []
    for thumbnail in job.thumbnails:
        variants = get_variants(thumbnail.imagekit_url) if thumbnail.imagekit_url else None
        thumbnail_response.append(ThumbnailResponse(
            id=thumbnail.id,
            style_name=thumbnail.style_name,
            status=thumbnail.status,
            imagekit_url=thumbnail.imagekit_url,
            error_message=thumbnail.error_message,
            variants=variants
        ))
    return JobResponse(
        id=job.id,
        prompt=job.prompt,
        num_thumbnails=job.num_thumbnails,
        headshot_url=job.headshot_url,
        status=job.status,
        thumbnails=thumbnail_response
    )    
    
