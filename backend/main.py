from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import create_db_and_tables
from routes import router
# Import models to ensure they are registered with SQLModel's metadata
import models

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database and create tables on startup
    create_db_and_tables()
    yield

app = FastAPI(
    title="Thumbnail Maker API",
    lifespan=lifespan
)

# Configure CORS so your frontend can call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Update this with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API routes under /api
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
