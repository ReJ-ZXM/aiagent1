"""行程 ORM 模型"""
import uuid
from datetime import datetime, date, time
from sqlalchemy import String, Integer, Float, Date, Time, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), default="未命名行程")
    destination: Mapped[str] = mapped_column(String(100), default="")
    start_date: Mapped[date] = mapped_column(Date, nullable=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=True)
    total_days: Mapped[int] = mapped_column(Integer, default=0)
    budget: Mapped[float] = mapped_column(Float, default=0)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    days: Mapped[list["TripDay"]] = relationship(back_populates="trip", order_by="TripDay.day_number")


class TripDay(Base):
    __tablename__ = "trip_days"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id: Mapped[str] = mapped_column(String(36), ForeignKey("trips.id"), nullable=False)
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=True)
    title: Mapped[str] = mapped_column(String(200), default="")
    weather: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    trip: Mapped["Trip"] = relationship(back_populates="days")
    items: Mapped[list["TripItem"]] = relationship(back_populates="trip_day", order_by="TripItem.sort_order")


class TripItem(Base):
    __tablename__ = "trip_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_day_id: Mapped[str] = mapped_column(String(36), ForeignKey("trip_days.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(200), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    location: Mapped[str] = mapped_column(String(300), default="")
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost: Mapped[float] = mapped_column(Float, default=0)
    booking_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    trip_day: Mapped["TripDay"] = relationship(back_populates="items")
