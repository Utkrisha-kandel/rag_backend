from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    #APP
    APP_NAME: str = "RAG Backend"
    DEBUG: bool = False

    #Groq 
    GROQ_API_KEY:str = ""                            
    GROQ_CHAT_MODEL: str = "llama-3.3-70b-versatile"

    #Embeddings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"   
    EMBEDDING_DIM: int = 384                    

    #Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "documents"
    QDRANT_API_KEY: str = ""                  


    #Redis
    REDIS_URL: str = "redis://localhost:6379"
    CHAT_HISTORY_TTL: int = 3600                 

    #PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/ragdb"

    #Chunking
    DEFAULT_CHUNK_STRATEGY: str = "fixed"        
    FIXED_CHUNK_SIZE: int = 512                  
    FIXED_CHUNK_OVERLAP: int = 64               
    SENTENCE_CHUNK_SIZE: int = 5                 

    #RAG
    TOP_K_RESULTS: int = 5                       

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()