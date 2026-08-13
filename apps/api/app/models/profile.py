import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

class DietType(str, Enum):
    OMNIVORE = "omnivore"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    EGGETARIAN = "eggetarian"
    PESCATARIAN = "pescatarian"
    HALAL = "halal"
    OTHER = "other"

class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str | None] = mapped_column(String(320), unique=True, index=True, nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state_or_region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    food_profile: Mapped["FoodProfile | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    cuisine_preferences: Mapped[list["UserCuisinePreference"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    comfort_foods: Mapped[list["UserComfortFood"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    allergies: Mapped[list["UserAllergy"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    recommendation_interactions: Mapped[list["RecommendationInteraction"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class FoodProfile(Base):
    __tablename__ = "food_profiles"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    diet_type: Mapped[DietType] = mapped_column(SqlEnum(DietType, name="diet_type"), default=DietType.OMNIVORE)
    spice_tolerance: Mapped[int] = mapped_column(Integer)
    adventurousness: Mapped[int] = mapped_column(Integer)
    usual_budget_min: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    usual_budget_max: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    usual_travel_radius_miles: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    prefers_delivery: Mapped[bool] = mapped_column(Boolean, default=False)
    prefers_pickup: Mapped[bool] = mapped_column(Boolean, default=False)
    prefers_dine_in: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    user: Mapped[User] = relationship(back_populates="food_profile")

class Cuisine(Base):
    __tablename__ = "cuisines"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    preferences: Mapped[list["UserCuisinePreference"]] = relationship(back_populates="cuisine")

class UserCuisinePreference(Base):
    __tablename__ = "user_cuisine_preferences"
    __table_args__ = (UniqueConstraint("user_id", "cuisine_id", name="user_cuisine"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    cuisine_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cuisines.id", ondelete="RESTRICT"), index=True)
    preference_level: Mapped[int] = mapped_column(Integer)
    user: Mapped[User] = relationship(back_populates="cuisine_preferences")
    cuisine: Mapped[Cuisine] = relationship(back_populates="preferences")

class ComfortFood(Base):
    __tablename__ = "comfort_foods"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)

class UserComfortFood(Base):
    __tablename__ = "user_comfort_foods"
    __table_args__ = (UniqueConstraint("user_id", "comfort_food_id", name="user_comfort_food"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    comfort_food_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("comfort_foods.id", ondelete="RESTRICT"), index=True)
    user: Mapped[User] = relationship(back_populates="comfort_foods")
    comfort_food: Mapped[ComfortFood] = relationship()

class Allergy(Base):
    __tablename__ = "allergies"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)

class UserAllergy(Base):
    __tablename__ = "user_allergies"
    __table_args__ = (UniqueConstraint("user_id", "allergy_id", name="user_allergy"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    allergy_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("allergies.id", ondelete="RESTRICT"), index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    user: Mapped[User] = relationship(back_populates="allergies")
    allergy: Mapped[Allergy] = relationship()

class RecommendationInteraction(Base):
    __tablename__ = "recommendation_interactions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    restaurant_external_id: Mapped[str] = mapped_column(String(255))
    restaurant_name: Mapped[str] = mapped_column(String(255))
    cuisine: Mapped[str | None] = mapped_column(String(100), nullable=True)
    recommended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    selected: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    liked: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    feedback_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    user: Mapped[User] = relationship(back_populates="recommendation_interactions")