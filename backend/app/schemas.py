# schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
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

class UserRole(str, Enum):
    BUYER = "buyer"
    SELLER = "seller"
    ADMIN = "admin"

class UserBase(BaseModel):
    inn: str = Field(..., min_length=10, max_length=12)
    email: EmailStr
    phone: str
    name: str

class UserCreate(BaseModel):
    inn: str = Field(..., min_length=10, max_length=12)
    email: EmailStr
    phone: str | None = None
    name: str | None = None
    password: str = Field(..., min_length=8)
    is_seller: bool = False

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    name: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    inn: str
    email: EmailStr
    phone: str | None
    name: str | None
    is_seller: bool
    email_verified: bool

    class Config:
        from_attributes = True

class UserWithTokenResponse(UserResponse):
    access_token: str
    refresh_token: str
    token_type: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class ResetPasswordConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

class VerifyEmailRequest(BaseModel):
    token: str

class VerifySMSRequest(BaseModel):
    code: str = Field(..., min_length=4, max_length=6)

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ItemBase(BaseModel):
    title: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: int = Field(..., gt=0)

class ItemCreate(ItemBase):
    pass

class ItemResponse(ItemBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ServiceBase(BaseModel):
    title: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: int = Field(..., gt=0)

class ServiceCreate(ServiceBase):
    pass

class ServiceResponse(ServiceBase):
    id: int
    provider_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TimeSlotBase(BaseModel):
    start_time: datetime
    end_time: datetime

class TimeSlotCreate(TimeSlotBase):
    pass

class TimeSlotResponse(TimeSlotBase):
    id: int
    service_id: int
    is_booked: bool
    
    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    item_id: Optional[int] = None
    service_id: Optional[int] = None

class OrderCreate(OrderBase):
    pass

class OrderResponse(BaseModel):
    id: int
    buyer_id: int
    seller_id: int
    item_id: Optional[int]
    service_id: Optional[int]
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TransactionBase(BaseModel):
    order_id: int
    amount: float = Field(..., gt=0)
    payment_method: Optional[str] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(BaseModel):
    id: int
    order_id: int
    amount: float
    platform_fee: float
    status: TransactionStatus
    payment_id: Optional[str]
    payment_method: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True