# models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON 
from .database import Base
import enum
from datetime import datetime

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DELIVERED = "delivered"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"

class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    HELD = "held"
    COMPLETED = "completed"
    DISPUTED = "disputed"
    REFUNDED = "refunded"

class UserRole(str, enum.Enum):
    BUYER = "buyer"
    SELLER = "seller"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    inn = Column(String(12), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_seller = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True)
    verification_token_expires = Column(DateTime, nullable=True)
    sms_code = Column(String(255), nullable=True)
    sms_code_created_at = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    last_failed_login = Column(DateTime, nullable=True)
    refresh_token = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    items = relationship("Item", back_populates="owner")
    services = relationship("Service", back_populates="provider")
    orders = relationship("Order", back_populates="buyer", foreign_keys="Order.buyer_id")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user")

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(255), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="password_reset_tokens")

class Item(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(String(500))
    price = Column(Integer, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    characteristics = Column(JSON)  # Для гибких характеристик
    location = Column(String)  # Геокоординаты "lat,lon"
    category_id = Column(Integer, ForeignKey('product_categories.id'))
    category = relationship("ProductCategory")
    owner = relationship("User", back_populates="items")

class Service(Base):
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(String(500))
    price = Column(Integer, nullable=False)
    provider_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    schedule = Column(JSON)  # Расписание в формате {"days": [...]}
    location = Column(String)  # Геокоординаты "lat,lon"
    category_id = Column(Integer, ForeignKey('service_categories.id'))
    category = relationship("ServiceCategory")
    provider = relationship("User", back_populates="services")
    available_slots = relationship("TimeSlot", back_populates="service")

class ProductCategory(Base):
    __tablename__ = "product_categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    parent_id = Column(Integer, ForeignKey('product_categories.id'))
    children = relationship("ProductCategory")

class ServiceCategory(Base):
    __tablename__ = "service_categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    parent_id = Column(Integer, ForeignKey('service_categories.id'))
    children = relationship("ServiceCategory")


class TimeSlot(Base):
    __tablename__ = "time_slots"
    
    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_booked = Column(Boolean, default=False)
    service_id = Column(Integer, ForeignKey("services.id"))
    
    service = relationship("Service", back_populates="available_slots")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"))
    seller_id = Column(Integer, ForeignKey("users.id"))
    item_id = Column(Integer, ForeignKey("items.id"), nullable=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    buyer = relationship("User", back_populates="orders", foreign_keys=[buyer_id])
    seller = relationship("User", foreign_keys=[seller_id])
    item = relationship("Item")
    service = relationship("Service")
    transaction = relationship("Transaction", uselist=False, back_populates="order")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    amount = Column(Float, nullable=False)
    platform_fee = Column(Float, default=0.05)  # 5% комиссии
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING)
    payment_id = Column(String(100))  # ID платежа в ЮKassa
    payment_method = Column(String(50), nullable=True)
    payment_metadata = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    order = relationship("Order", back_populates="transaction")