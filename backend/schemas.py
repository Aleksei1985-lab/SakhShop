from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DELIVERED = "delivered"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"

class TransactionStatus(str, Enum):
    PENDING = "pending"
    HELD = "held"
    COMPLETED = "completed"
    DISPUTED = "disputed"
    REFUNDED = "refunded"

class UserCreate(BaseModel):
    inn: str
    is_seller: bool = False

class UserResponse(BaseModel):
    id: int
    inn: str
    is_seller: bool
    class Config:
        from_attributes = True

class ItemCreate(BaseModel):
    title: str
    description: Optional[str]
    price: int

class ItemResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    price: int
    owner_id: int
    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    item_id: Optional[int] = None
    service_id: Optional[int] = None

class OrderResponse(BaseModel):
    id: int
    buyer_id: int
    seller_id: int
    item_id: Optional[int]
    service_id: Optional[int]
    status: OrderStatus
    created_at: datetime
    class Config:
        from_attributes = True

class TransactionCreate(BaseModel):
    order_id: int
    amount: float

class TransactionResponse(BaseModel):
    id: int
    order_id: int
    amount: float
    platform_fee: float
    status: TransactionStatus
    payment_id: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True