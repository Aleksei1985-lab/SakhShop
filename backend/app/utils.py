# utils.py
import smtplib
from email.mime.text import MIMEText
import requests
from datetime import datetime, timedelta
from passlib.context import CryptContext
import os
import secrets
from jose import jwt
from typing import Optional
from fastapi import HTTPException, status
import logging
from .config import settings

logger = logging.getLogger("sakhshop")

# Настройки
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.yandex.ru")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMS_API_KEY = os.getenv("SMS_API_KEY")
SMS_SENDER = "SakhShop"
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = settings.ALGORITHM

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def send_verification_email(email: str, token: str):
    verification_url = f"https://sakhshop.ru/verify-email?token={token}"
    message = MIMEText(
        f"Для подтверждения email перейдите по ссылке: {verification_url}"
    )
    message["Subject"] = "Подтверждение email в SakhShop"
    message["From"] = settings.SMTP_USER
    message["To"] = email
    
    try:
        with smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USER, [email], message.as_string())
        logger.info(f"Email успешно отправлен на {email}")
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки email: {e}")
        return False

def send_sms_secure(phone: str, message: str) -> bool:
    if not SMS_API_KEY:
        logger.error("SMS_API_KEY не настроен")
        return False
    try:
        response = requests.post(
            "https://sms.ru/sms/send",
            data={
                "api_id": SMS_API_KEY,
                "to": phone,
                "msg": message,
                "json": 1,
                "from": SMS_SENDER
            },
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Ошибка отправки SMS: {e}")
        return False

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict, expires_delta: timedelta = timedelta(days=7)) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)