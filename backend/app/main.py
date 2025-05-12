# main.py
from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRouter
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis
from phonenumbers import parse, is_valid_number
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Annotated, Optional
import os
import secrets
import smtplib
from email.mime.text import MIMEText
import requests
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from .models import User, Service, Item, Order 
from .database import Base, SessionLocal, engine
from fastapi.staticfiles import StaticFiles
import shutil
from yookassa import Configuration, Payment
from yookassa.domain.request import PaymentRequest
import uuid
from redis.asyncio import Redis
import logging
from logging.config import dictConfig
from .config import LogConfig


# Настройка логгирования
dictConfig(LogConfig().dict())
logger = logging.getLogger("sakhshop")

SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 дней

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройка ЮKassa
Configuration.account_id = os.getenv("YOOKASSA_SHOP_ID")
Configuration.secret_key = os.getenv("YOOKASSA_SECRET_KEY")

app = FastAPI()

Base.metadata.create_all(bind=engine)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

redis_connection = Redis(host="localhost", port=6379, decode_responses=True)
# Настройка rate limiting
@app.on_event("startup")
async def startup():
    await FastAPILimiter.init(redis_connection)

# Создание директории для загрузок
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Роутеры
auth_router = APIRouter(prefix="/api/auth", tags=["auth"])
users_router = APIRouter(prefix="/api/users", tags=["users"])
payments_router = APIRouter(prefix="/api/payments", tags=["payments"])
files_router = APIRouter(prefix="/api/files", tags=["files"])
# Добавьте в main.py
mobile_router = APIRouter(prefix="/api/mobile", tags=["mobile"])

@mobile_router.get("/products")
async def get_products(db: Session = Depends(get_db)):
    return db.query(Item).all()

@mobile_router.get("/services")
async def get_services(db: Session = Depends(get_db)):
    return db.query(Service).all()


# Модели для аутентификации
class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str

class TokenData(BaseModel):
    inn: Optional[str] = None

class UserRegister(BaseModel):
    inn: str = Field(..., min_length=10, max_length=12)
    email: EmailStr
    phone: str
    name: str
    is_seller: bool
    password: str = Field(..., min_length=8)

class VerifyEmailRequest(BaseModel):
    token: str

class UserLogin(BaseModel):
    inn: str
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class ResetPasswordConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)



def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict, expires_delta: timedelta = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

def verify_phone_number(phone: str) -> bool:
    try:
        parsed = parse(phone, "RU")
        return is_valid_number(parsed)
    except:
        return False

def send_verification_email(email: str, token: str):
    verification_url = f"https://sakhshop.ru/verify-email?token={token}"
    message = MIMEText(
        f"Для подтверждения email перейдите по ссылке: {verification_url}"
    )
    message["Subject"] = "Подтверждение email в SakhShop"
    message["From"] = os.getenv("SMTP_USER", "noreply@sakhshop.ru")
    message["To"] = email
    
    try:
        with smtplib.SMTP_SSL(
            os.getenv("SMTP_SERVER", "smtp.yandex.ru"),
            int(os.getenv("SMTP_PORT", 465))
        ) as server:
            server.login(
                os.getenv("SMTP_USER"),
                os.getenv("SMTP_PASSWORD")
            )
            server.sendmail(os.getenv("SMTP_USER"), [email], message.as_string())
    except Exception as e:
        logger.error(f"Ошибка отправки email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка отправки email"
        )

# Эндпоинты аутентификации
@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserRegister, db: Session = Depends(get_db)):
    # Проверка ИНН
    if user.is_seller and len(user.inn) != 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ИНН юрлица должен содержать 10 цифр"
        )
    elif not user.is_seller and len(user.inn) != 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ИНН физлица должен содержать 12 цифр"
        )
    
    # Проверка телефона
    if not verify_phone_number(user.phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный формат номера телефона"
        )
    
    # Проверка существования пользователя
    if db.query(User).filter(User.inn == user.inn).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким ИНН уже зарегистрирован"
        )
    
    # Хеширование пароля
    hashed_password = pwd_context.hash(user.password)
    verify_token = secrets.token_urlsafe(32)
    
    # Создание пользователя
    db_user = User(
        inn=user.inn,
        email=user.email,
        phone=user.phone,
        name=user.name,
        is_seller=user.is_seller,
        hashed_password=hashed_password,
        email_verified=False,
        verification_token=verify_token
    )
    
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Отправка email с подтверждением
        send_verification_email(user.email, verify_token)
        
        return {"message": "На ваш email отправлено письмо с подтверждением"}
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при регистрации пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при регистрации пользователя"
        )
    
@payments_router.post("/create-payment")
async def create_payment(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    
    payment = Payment.create({
        "amount": {
            "value": order.amount,
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://sakhshop.ru/payment/return"
        },
        "capture": True,
        "description": f"Заказ №{order.id}"
    }, uuid.uuid4())
    
    db.payment_id = payment.id
    db.commit()
    
    return {"confirmation_url": payment.confirmation.confirmation_url}

@auth_router.post("/login", response_model=Token)
async def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.inn == user.inn).first()
    
    if not db_user or not pwd_context.verify(user.password, db_user.hashed_password):
        logger.warning(f"Неудачная попытка входа для ИНН: {user.inn}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учетные данные",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not db_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email не подтвержден"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.inn},
        expires_delta=access_token_expires
    )
    
    refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    refresh_token = create_refresh_token(
        data={"sub": db_user.inn},
        expires_delta=refresh_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token
    }

@mobile_router.get("/search/nearby")
async def search_nearby(
    lat: float, 
    lon: float, 
    radius: int = 10,  # радиус в км
    db: Session = Depends(get_db)
):
    products = db.query(Item).all()
    services = db.query(Service).all()
    
    nearby_results = []
    
    for item in [*products, *services]:
        item_lat, item_lon = map(float, item.location.split(','))
        if geodesic((lat, lon), (item_lat, item_lon)).km <= radius:
            nearby_results.append(item)
    
    return nearby_results

@auth_router.post("/refresh", response_model=Token)
async def refresh_token(token: RefreshTokenRequest):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Невалидный refresh токен",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token.refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        inn: str = payload.get("sub")
        if inn is None:
            raise credentials_exception
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": inn},
            expires_delta=access_token_expires
        )
        
        refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
        refresh_token = create_refresh_token(
            data={"sub": inn},
            expires_delta=refresh_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token
        }
    except JWTError:
        raise credentials_exception

# Подключение роутеров
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(payments_router)
app.include_router(files_router)
app.include_router(mobile_router)