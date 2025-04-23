from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
import models, schemas
from database import SessionLocal, engine
from yookassa import Configuration, Payment
from yookassa.domain.request import PaymentRequest
import uuid

# Настройка ЮKassa (замените на ваши данные)
Configuration.account_id = "your_shop_id"
Configuration.secret_key = "your_secret_key"

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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