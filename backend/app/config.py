# config.py
from pydantic_settings import BaseSettings
from typing import Dict, Any

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://sakhshop:sakhshop123@localhost:5432/sakhshop"
    REDIS_URL: str = "redis://localhost:6379"
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080
    SMTP_SERVER: str = "smtp.yandex.ru"
    SMTP_PORT: int = 465
    SMTP_USER: str = "aleksey.oberemok@yandex.ru"
    SMTP_PASSWORD: str = "bssggejzcfcuhrwt"
    YANDEX_S3_ACCESS_KEY: str = "your-access-key"
    YANDEX_S3_SECRET_KEY: str = "your-secret-key"
    YANDEX_S3_ENDPOINT: str = "https://storage.yandexcloud.net"
    YANDEX_S3_BUCKET: str = "sakhshop-bucket"
    GOSUSLUGI_CLIENT_ID: str = "your-client-id"
    GOSUSLUGI_CLIENT_SECRET: str = "your-client-secret"
    GOSUSLUGI_REDIRECT_URI: str = "http://localhost:8000/api/auth/gosuslugi/callback"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class LogConfig(BaseSettings):
    LOGGER_NAME: str = "sakhshop"
    LOG_FORMAT: str = "%(levelprefix)s | %(asctime)s | %(message)s"
    LOG_LEVEL: str = "INFO"

    version: int = 1
    disable_existing_loggers: bool = False
    formatters: Dict[str, Dict[str, str]] = {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    handlers: Dict[str, Dict[str, str]] = {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    }
    loggers: Dict[str, Dict[str, Any]] = {
        LOGGER_NAME: {"handlers": ["default"], "level": LOG_LEVEL},
    }

settings = Settings()