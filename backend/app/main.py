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
from .schemas import UserCreate, UserResponse
from .utils import get_password_hash, create_access_token, create_refresh_token, send_verification_email
from fastapi.staticfiles import StaticFiles
import shutil
from yookassa import Configuration, Payment
from yookassa.domain.request import PaymentRequest
import uuid
from redis.asyncio import Redis
import logging
from logging.config import dictConfig
from .config import LogConfig, settings
from geopy.distance import geodesic

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

# Эндпоинты аутентификации
@app.post("/api/auth/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        if len(user.inn) not in (10, 12):
            raise HTTPException(status_code=400, detail="ИНН должен содержать 10 или 12 цифр")
        if db.query(User).filter(User.inn == user.inn).first():
            raise HTTPException(status_code=400, detail="Пользователь с таким ИНН уже существует")
        if db.query(User).filter(User.email == user.email).first():
            raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

        hashed_password = get_password_hash(user.password)
        verification_token = secrets.token_urlsafe(32)
        db_user = User(
            inn=user.inn,
            email=user.email,
            phone=user.phone,
            name=user.name,
            hashed_password=hashed_password,
            is_seller=user.is_seller,
            verification_token=verification_token,
            verification_token_expires=datetime.utcnow() + timedelta(hours=24)
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # Отправка email (не прерывает регистрацию при ошибке)
        verification_code = "123456"  # В реальном проекте генерируй случайный код
        if not send_verification_email(db_user.email, verification_code):
            print("Предупреждение: Не удалось отправить email верификации")

        access_token = create_access_token(
            data={"sub": db_user.inn},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        return db_user
    except Exception as e:
        print(f"Ошибка при регистрации пользователя: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при регистрации пользователя")
    
@auth_router.post("/verify-email")
async def verify_email(request: VerifyEmailRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.verification_token == request.token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Неверный или устаревший токен")
    
    if user.verification_token_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Токен истек")

    user.email_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.commit()
    
    return {"message": "Email успешно подтвержден"}

async def create_payment(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
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
    
    order.payment_id = payment.id
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
    radius: int = 10,
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