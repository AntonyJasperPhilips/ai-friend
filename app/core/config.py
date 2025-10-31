
from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    OPENAI_API_KEY:str
    PINECONE_API_KEY:str
    PINECONE_TEXT_INDEX:str
    PINECONE_IMAGE_INDEX:str
    class Config:env_file=".env"
settings=Settings()
