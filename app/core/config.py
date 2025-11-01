
from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    OPENAI_API_KEY: str
    PINECONE_API_KEY: str
    PINECONE_TEXT_INDEX: str = "rag-testing"  # Default value
    PINECONE_IMAGE_INDEX: str = "rag-testing"  # Default value
    
    class Config:
        env_file = ".env"
        extra = "allow"  # Allow extra fields from .env
settings=Settings()
