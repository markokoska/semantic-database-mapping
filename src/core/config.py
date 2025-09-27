
import os
from typing import List, Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    DATABASE_URL: str = "sqlite:///./semantic_mapping.db"
    
    TRANSFORMERS_CACHE: str = "./cache/transformers"
    SPACY_MODEL: str = "en_core_web_sm"
    SENTENCE_TRANSFORMER_MODEL: str = "all-MiniLM-L6-v2"
    
    DEFAULT_NAMESPACE: str = "http://example.org/semantic-mapping/"
    DBPEDIA_ENDPOINT: str = "http://dbpedia.org/sparql"
    SCHEMA_ORG_URL: str = "https://schema.org/"
    
    DBPEDIA_LOOKUP_URL: str = "https://lookup.dbpedia.org/api/search"
    SCHEMA_ORG_API_URL: str = "https://schema.org/version/latest/schemaorg-current-https.jsonld"
    
    MAX_WORKERS: int = 4
    BATCH_SIZE: int = 100
    CONFIDENCE_THRESHOLD: float = 0.7
    
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    MAX_FILE_SIZE: int = 50 * 1024 * 1024
    ALLOWED_FILE_EXTENSIONS: List[str] = [".csv", ".json", ".sql", ".xlsx"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
