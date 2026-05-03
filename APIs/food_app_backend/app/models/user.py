from sqlalchemy import Column, String, Float, Date, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base


class GenderEnum(str, enum.Enum):
    male   = "male"
    female = "female"
    other  = "other"


class DiseaseEnum(str, enum.Enum):
    none           = "none"
    diabetes       = "diabetes"
    hypertension   = "hypertension"
    obesity        = "obesity"
    heart_disease  = "heart_disease"
    kidney_disease = "kidney_disease"
    celiac         = "celiac"


class User(Base):
    """
    This class defines the 'users' table in PostgreSQL.
    Each attribute = one column in the table.
    SQLAlchemy reads this and creates the table automatically.
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    name          = Column(String(100), nullable=False)
    email         = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Stored as a proper Date — e.g. 1999-05-22
    # age is NOT stored — computed dynamically via @property below
    date_of_birth = Column(Date, nullable=False)

    gender  = Column(Enum(GenderEnum),  nullable=False)
    disease = Column(Enum(DiseaseEnum), nullable=False, default=DiseaseEnum.none)

    height_cm = Column(Float, nullable=False)
    weight_kg = Column(Float, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # ── Relationships to other tables ─────────────────────────────────────────
    # uselist=False on goals → one-to-one (user has exactly one goals row)
    goals          = relationship("UserGoals",    back_populates="user", uselist=False, cascade="all, delete")
    meal_logs      = relationship("MealLog",      back_populates="user", cascade="all, delete")
    analysis_tasks = relationship("AnalysisTask", back_populates="user", cascade="all, delete")

    @property
    def age(self) -> int:
        """
        Computes age from date_of_birth dynamically — never stored in DB.
        Always accurate, auto-updates on birthdays.
        """
        from datetime import date
        today = date.today()
        dob   = self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
