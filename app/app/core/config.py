
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    PINECONE_API_KEY: str
    PINECONE_ENV: str = "us-east-1"
    PINECONE_TEXT_INDEX: str = "edu-text-chunks"
    PINECONE_IMAGE_INDEX: str = "edu-image-chunks"

    OCR_ENABLED: bool = True
    TESSERACT_PATH: Optional[str] = None

    AWS_REGION: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET: str = ""

    ENABLE_IMAGE_CAPTIONS: bool = True

    class Config:
        env_file = ".env"
        extra = "allow"  # Allow extra fields from .env

settings = Settings()
