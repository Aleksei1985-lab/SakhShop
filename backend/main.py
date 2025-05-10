from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Annotated
import os
import secrets
import smtplib
from email.mime.text import MIMEText
import requests
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import models, schemas
from database import SessionLocal, engine
from fastapi.staticfiles import StaticFiles
import shutil
from yookassa import Configuration, Payment
from yookassa.domain.request import PaymentRequest
import uuid

SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройка ЮKassa
Configuration.account_id = os.getenv("YOOKASSA_SHOP_ID")
Configuration.secret_key = os.getenv("YOOKASSA_SECRET_KEY")

app = FastAPI()

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Модели для аутентификации
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    inn: str | None = None

class UserInDB(BaseModel):
    inn: str
    email: str
    phone: str
    name: str
    is_seller: bool
    hashed_password: str
    email_verified: bool


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt




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

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.inn == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect inn or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.inn}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

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

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        inn: str = payload.get("sub")
        if inn is None:
            raise credentials_exception
        token_data = TokenData(inn=inn)
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.inn == token_data.inn).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: Annotated[models.User, Depends(get_current_user)]
):
    if not current_user.email_verified:
        raise HTTPException(status_code=400, detail="Email not verified")
    return current_user

@app.get("/users/me/", response_model=schemas.UserResponse)
async def read_users_me(
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    return current_user

def get_password_hash(password: str):
    return pwd_context.hash(password)

@app.post("/users/", response_model=schemas.UserResponse)
def create_user(
    user: schemas.UserCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # Только администратор может создавать пользователей
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admin can create users")
    
    db_user = db.query(models.User).filter(models.User.inn == user.inn).first()
    if db_user:
        raise HTTPException(status_code=400, detail="User already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        inn=user.inn,
        email=user.email,
        hashed_password=hashed_password,
        is_seller=user.is_seller
    )
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
    
def send_sms_secure(phone: str, message: str):
    try:
        # В продакшене используйте HTTPS
        response = requests.post(
            "https://sms.ru/sms/send",
            data={
                "api_id": os.getenv("SMS_API_KEY"),
                "to": phone,
                "msg": message,
                "json": 1,
                "from": "SakhShop"
            },
            timeout=5  # Таймаут для безопасности
        )
        return response.status_code == 200
    except Exception as e:
        print(f"SMS sending error: {e}")
        return False

@app.post("/api/auth/send-verification-sms")
async def send_verification_sms(
    phone: str,
    current_user: models.User = Depends(get_current_active_user)
):
    code = secrets.randbelow(9000) + 1000
    if send_sms_secure(phone, f"Ваш код подтверждения: {code}"):
        # Сохраняем код в БД (без возврата клиенту)
        current_user.sms_code = str(code)
        db.commit()
        return {"message": "SMS отправлено"}
    raise HTTPException(status_code=500, detail="Ошибка отправки SMS")