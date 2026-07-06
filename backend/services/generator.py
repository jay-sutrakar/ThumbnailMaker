import asyncio
import logging

from sqlmodel import Session, select
from database import engine

from models import Job, Thumbnail
from services.google_image_service import generate_thumbnail
from services.imagekit_service import upload_file

logger=logging.getLogger(__name__)

STYLES_PROMPTS = {
    "bold_dramatic": (
        "Create a bold dramatic Youtube thumbnain with high contrast",
        "cinematic lighting, dark background, neon highlights, dynamic composition, 16x9 aspect ratio, ultra-detailed, 4k"
    ),
    "clean_minimal":(
       "Create a clean minimal professional thumbnail using this image, place the person in the center, use soft lighting, negative space, and simple typography." 
    ),
    "vibrant_energetic":(
     "Create a vibrant energetic and eye-catching thumbnail, use bright colors, high energy, and dynamic composition."   
    )
}

STYLE_ORDER = ['bold_dramatic', 'clean_minimal', 'vibrant_energetic']

async def generate_single_thumbnail(thumbnail_id: str, prompt: str, headshot_url: str):
    with Session(engine) as session:
        thumbnail = session.get(Thumbnail, thumbnail_id)
        if not thumbnail:
            logger.warning(f"Thumbnail not found: {thumbnail_id}")
            return
        thumbnail.status = "generating"
        style_name = thumbnail.style_name
        session.add(thumbnail)
        session.commit()

    style_prompt = STYLES_PROMPTS[style_name]

    try:
        image_bytes = await generate_thumbnail(prompt, style_prompt, headshot_url)
        with Session(engine) as session:
            thumbnail = session.get(Thumbnail, thumbnail_id)
            if not thumbnail:
                logger.warning(f"Thumbnail not found: {thumbnail_id}")
                return
            job_id = thumbnail.job_id
            cdn_url = upload_file(
                image_bytes,
                file_name=f"{thumbnail_id}.png",
                folder=f"thumbnails/{job_id}"
            )

            with Session(engine) as session:
                thumbnail = session.get(Thumbnail, thumbnail_id)
                if not thumbnail:
                    logger.warning(f"Thumbnail not found: {thumbnail_id}")
                    return
                thumbnail.status = "uploaded"
                thumbnail.imagekit_url = cdn_url
                session.add(thumbnail)
                session.commit()
            logger.info(f"Thumbnail {thumbnail_id} uploaded successfully: {cdn_url}")
    except Exception as e:
        logger.error(f"Error generating thumbnail: {e}")
        with Session(engine) as session:
            thumbnail = session.get(Thumbnail, thumbnail_id)
            if not thumbnail:
                logger.warning(f"Thumbnail not found: {thumbnail_id}")
                return
            thumbnail.status = "failed"
            thumbnail.error_message = str(e)
            session.add(thumbnail)
            session.commit()
        return

async def process_job(job_id: str):
    with Session(engine) as session:
        job = session.get(Job, job_id)
        if not job:
            logger.warning(f"Job not found: {job_id}")
            return
        job.status = "processing"
        session.add(job)
        session.commit()
        logger.info(f"Processing job: {job_id}")

        tasks = []
        for thumbnail in job.thumbnails:
            task = asyncio.create_task(
                generate_single_thumbnail(
                    thumbnail.id,
                    job.prompt,
                    job.headshot_url
                )
            )
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

        job.status = "completed"
        session.add(job)
        session.commit()
        logger.info(f"Job {job_id} completed successfully")
    

    