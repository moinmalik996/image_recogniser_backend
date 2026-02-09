from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings



class Settings(BaseSettings):
    # CORS origins (comma-separated string)
    CORS_ORIGINS: Optional[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    PROJECT_NAME: Optional[str]  = "My FastAPI Project"
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_HOST: Optional[str] = "localhost"
    DB_PORT: Optional[int] = 5432
    DB_NAME: Optional[str] = None
    DBCONNECTIONSTRING: Optional[str] = None

    SECRET_KEY: Optional[str]
    JWT_ALGORITHM: Optional[str]
    ACCESS_TOKEN_EXPIRE_MINUTES: Optional[int]

    # S3 Settings
    AWS_ACCESS_KEY_ID: Optional[str]
    AWS_SECRET_ACCESS_KEY: Optional[str]
    AWS_REGION: Optional[str]
    AWS_S3_BUCKET_NAME: Optional[str]

    # Environment mode
    ENV: str = ".env"

    @property
    def DATABASE_URL(self) -> str:
        # Use DBCONNECTIONSTRING as-is if provided and not empty
        if self.DBCONNECTIONSTRING and self.DBCONNECTIONSTRING.strip():
            return self.DBCONNECTIONSTRING.strip()
        # Otherwise, build from parameters
        if not all([self.DB_USER, self.DB_PASSWORD, self.DB_NAME]):
            raise ValueError("Database credentials are not properly set")
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    class Config:
        env_file = ".env"
        
@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()