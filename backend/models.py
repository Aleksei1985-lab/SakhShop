from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Enum
from sqlalchemy.orm import relationship
from database import Base
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

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    inn = Column(String(12), unique=True, nullable=False)
    is_seller = Column(Boolean, default=False)
    items = relationship("Item", back_populates="owner")
    services = relationship("Service", back_populates="provider")
    orders = relationship("Order", back_populates="buyer", foreign_keys="Order.buyer_id")

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(String(500))
    price = Column(Integer, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="items")

class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(String(500))
    price = Column(Integer, nullable=False)
    provider_id = Column(Integer, ForeignKey("users.id"))
    provider = relationship("User", back_populates="services")
    available_slots = relationship("TimeSlot", back_populates="service")

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
    created_at = Column(DateTime, default=datetime.utcnow)
    order = relationship("Order", back_populates="transaction")