from fastapi import Depends, FastAPI, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine
import models, schemas
from fastapi.staticfiles import StaticFiles
import os
import shutil
from database import SessionLocal, engine
import secrets
import smtplib
import requests
from yookassa import Configuration, Payment
from yookassa.domain.request import PaymentRequest
import uuid
# Добавьте в начало файла
from jose import JWTError, jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key"  # В продакшене используйте сложный ключ
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Настройка ЮKassa (замените на ваши данные)
Configuration.account_id = "your_shop_id"
Configuration.secret_key = "your_secret_key"

app = FastAPI()
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.yandex.ru")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMS_API_KEY = os.getenv("SMS_API_KEY")
SMS_SENDER = "SakhShop"

class UserRegister(BaseModel):
    inn: str
    email: EmailStr
    phone: str
    name: str
    is_seller: bool

class VerifyEmailRequest(BaseModel):
    token: str

class UserLogin(BaseModel):
    inn: str
    password: str

def send_verification_email(email: str, token: str):
    verification_url = f"https://sakhshop.ru/verify-email?token={token}"
    message = MIMEText(
        f"Для подтверждения email перейдите по ссылке: {verification_url}"
    )
    message["Subject"] = "Подтверждение email в SakhShop"
    message["From"] = SMTP_USER
    message["To"] = email
    
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, [email], message.as_string())
    except Exception as e:
        print(f"Ошибка отправки email: {e}")

def send_sms(phone: str, message: str):
    try:
        response = requests.post(
            "https://sms.ru/sms/send",
            data={
                "api_id": SMS_API_KEY,
                "to": phone,
                "msg": message,
                "json": 1,
                "from": SMS_SENDER
            }
        )
        return response.json()
    except Exception as e:
        print(f"Ошибка отправки SMS: {e}")
        return None

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Генерируем уникальное имя файла
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{secrets.token_hex(8)}{file_ext}"
        file_path = os.path.join("uploads", unique_filename)
        
        # Сохраняем файл
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {"filename": unique_filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/register")
async def register(user: UserRegister, db: Session = Depends(get_db)):
    # Проверка ИНН в зависимости от типа пользователя
    if user.is_seller and len(user.inn) != 10:
        raise HTTPException(status_code=400, detail="ИНН юрлица должен содержать 10 цифр")
    elif not user.is_seller and len(user.inn) != 12:
        raise HTTPException(status_code=400, detail="ИНН физлица должен содержать 12 цифр")
    
    # Проверка, что пользователь с таким ИНН не существует
    db_user = db.query(models.User).filter(models.User.inn == user.inn).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким ИНН уже зарегистрирован")
    
    # Генерация токена подтверждения
    verify_token = secrets.token_urlsafe(32)
    
    # Сохранение пользователя в БД (пример)
    db_user = models.User(
        inn=user.inn,
        email=user.email,
        phone=user.phone,
        name=user.name,
        is_seller=user.is_seller,
        email_verified=False,
        verification_token=verify_token
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Отправка email с подтверждением
    send_verification_email(user.email, verify_token)
    
    return {"message": "На ваш email отправлено письмо с подтверждением"}

def send_verification_email(email: str, token: str):
    verification_url = f"https://sakhshop.ru/verify-email?token={token}"
    message = MIMEText(
        f"Для подтверждения email перейдите по ссылке: {verification_url}"
    )
    message["Subject"] = "Подтверждение email в SakhShop"
    message["From"] = SMTP_USER
    message["To"] = email
    
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, [email], message.as_string())
    except Exception as e:
        print(f"Ошибка отправки email: {e}")

@app.post("/api/auth/verify-email")
async def verify_email(request: VerifyEmailRequest, db: Session = Depends(get_db)):
    # Находим пользователя по токену
    db_user = db.query(models.User).filter(
        models.User.verification_token == request.token
    ).first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="Неверный токен подтверждения")
    
    # Обновляем статус подтверждения
    db_user.email_verified = True
    db_user.verification_token = None
    db.commit()
    
    return {"message": "Email успешно подтверждён"}

@app.post("/api/auth/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    # Находим пользователя по ИНН
    db_user = db.query(models.User).filter(models.User.inn == user.inn).first()
    
    if not db_user or not db_user.email_verified:
        raise HTTPException(status_code=401, detail="Неверные учетные данные или email не подтвержден")
    
    # Здесь должна быть проверка пароля (пока пропущена для простоты)
    # Генерация JWT токена (упрощенный пример)
    token_data = {
        "sub": db_user.inn,
        "role": "seller" if db_user.is_seller else "buyer"
    }
    # В реальном приложении используйте библиотеку для JWT
    
    return {"token": "generated-jwt-token", "role": "seller" if db_user.is_seller else "buyer"}

@app.get("/api/users/me")
async def read_users_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # В реальном приложении здесь должна быть проверка JWT токена
    # Для примера просто возвращаем данные первого пользователя
    db_user = db.query(models.User).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "inn": db_user.inn,
        "email": db_user.email,
        "name": db_user.name,
        "is_seller": db_user.is_seller,
        "email_verified": db_user.email_verified
    }


@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.inn == user.inn).first()
    if db_user:
        raise HTTPException(status_code=400, detail="User already registered")
    db_user = models.User(inn=user.inn, is_seller=user.is_seller)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/users/{user_id}/items/", response_model=schemas.ItemResponse)
def create_item_for_user(user_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_item = models.Item(**item.model_dump(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.post("/orders/", response_model=schemas.OrderResponse)
def create_order(order: schemas.OrderCreate, buyer_id: int, db: Session = Depends(get_db)):
    if not (order.item_id or order.service_id):
        raise HTTPException(status_code=400, detail="Item or service must be specified")
    if order.item_id:
        db_item = db.query(models.Item).filter(models.Item.id == order.item_id).first()
        if not db_item:
            raise HTTPException(status_code=404, detail="Item not found")
        seller_id = db_item.owner_id
    else:
        db_service = db.query(models.Service).filter(models.Service.id == order.service_id).first()
        if not db_service:
            raise HTTPException(status_code=404, detail="Service not found")
        seller_id = db_service.provider_id
    db_order = models.Order(
        buyer_id=buyer_id,
        seller_id=seller_id,
        item_id=order.item_id,
        service_id=order.service_id
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

@app.post("/transactions/", response_model=schemas.TransactionResponse)
def create_transaction(transaction: schemas.TransactionCreate, db: Session = Depends(get_db)):
    db_order = db.query(models.Order).filter(models.Order.id == transaction.order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    idempotence_key = str(uuid.uuid4())
    payment_request = PaymentRequest({
        "amount": {"value": str(transaction.amount), "currency": "RUB"},
        "capture": False,  # Холдирование
        "confirmation": {"type": "redirect", "return_url": "https://sakhshop.local/return"},
        "description": f"Order #{transaction.order_id}",
        "metadata": {"transaction_id": str(transaction.order_id)}
    })
    payment = Payment.create(payment_request, idempotence_key)
    db_transaction = models.Transaction(
        order_id=transaction.order_id,
        amount=transaction.amount,
        status=models.TransactionStatus.HELD,
        payment_id=payment.id
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@app.post("/transactions/{transaction_id}/confirm")
def confirm_transaction(transaction_id: int, db: Session = Depends(get_db)):
    db_transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if db_transaction.status != models.TransactionStatus.HELD:
        raise HTTPException(status_code=400, detail="Transaction cannot be confirmed")
    payment = Payment.capture(db_transaction.payment_id, {"amount": {"value": str(db_transaction.amount), "currency": "RUB"}})
    db_transaction.status = models.TransactionStatus.COMPLETED
    db_order = db.query(models.Order).filter(models.Order.id == db_transaction.order_id).first()
    db_order.status = models.OrderStatus.DELIVERED
    db.commit()
    return {"status": "confirmed"}

import requests

SMS_API_KEY = os.getenv("SMS_API_KEY")
SMS_SENDER = "SakhShop"

def send_sms(phone: str, message: str):
    try:
        response = requests.post(
            "https://sms.ru/sms/send",
            data={
                "api_id": SMS_API_KEY,
                "to": phone,
                "msg": message,
                "json": 1,
                "from": SMS_SENDER
            }
        )
        return response.json()
    except Exception as e:
        print(f"Ошибка отправки SMS: {e}")
        return None

# Использование:
@app.post("/api/auth/send-verification-sms")
async def send_verification_sms(phone: str):
    code = secrets.randbelow(9000) + 1000  # 4-значный код
    send_sms(phone, f"Ваш код подтверждения: {code}")
    return {"message": "SMS отправлено", "code": str(code)}  # В продакшене не возвращайте код!