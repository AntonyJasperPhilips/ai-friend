"""Configuration settings for the AI Friend application."""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    
    # Pinecone Configuration
    pinecone_api_key: str = Field(..., alias="PINECONE_API_KEY")
    pinecone_environment: str = Field(..., alias="PINECONE_ENVIRONMENT")
    pinecone_index_name: str = Field(default="textbook-embeddings", alias="PINECONE_INDEX_NAME")
    
    # Upload Configuration
    max_upload_size: int = Field(default=52428800, alias="MAX_UPLOAD_SIZE")  # 50MB
    upload_dir: str = Field(default="./uploads", alias="UPLOAD_DIR")
    
    # Processing Configuration
    chunk_size: int = Field(default=1000, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, alias="CHUNK_OVERLAP")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
