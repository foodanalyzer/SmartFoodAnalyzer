from pydantic import BaseModel, EmailStr, field_validator
from datetime import date
from typing import Optional
from uuid import UUID
from enum import Enum


class GenderEnum(str, Enum):
    male = "male"
    female = "female"
    other = "other"


class DiseaseEnum(str, Enum):
    none = "none"
    diabetes = "diabetes"
    hypertension = "hypertension"
    obesity = "obesity"
    heart_disease = "heart_disease"
    kidney_disease = "kidney_disease"
    celiac = "celiac"


# ── Register ────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    """
    Pydantic validates incoming JSON against these fields automatically.
    If the user sends wrong types or missing fields, FastAPI returns a 422 error.
    """
    name: str
    email: EmailStr                   # validates email format automatically
    password: str
    date_of_birth: date               # expects "YYYY-MM-DD" string, parses to date
    gender: GenderEnum
    height_cm: float
    weight_kg: float
    disease: DiseaseEnum = DiseaseEnum.none

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def not_future_date(cls, v):
        if v >= date.today():
            raise ValueError("Date of birth cannot be today or in the future")
        return v

    @field_validator("height_cm")
    @classmethod
    def valid_height(cls, v):
        if not (50 <= v <= 250):
            raise ValueError("Height must be between 50 and 250 cm")
        return v

    @field_validator("weight_kg")
    @classmethod
    def valid_weight(cls, v):
        if not (20 <= v <= 300):
            raise ValueError("Weight must be between 20 and 300 kg")
        return v


class RegisterResponse(BaseModel):
    """What we send back after successful registration."""
    user_id: UUID
    name: str
    email: str
    age: int
    token: str                        # JWT token — user is logged in immediately

    model_config = {"from_attributes": True}


# ── Login ────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    token: str
    user_id: UUID
    name: str
    email: str

    model_config = {"from_attributes": True}


# ── Get current user (me) ─────────────────────────────────────────────────────

class UserProfileResponse(BaseModel):
    """Returned by GET /auth/me"""
    user_id: UUID
    name: str
    email: str
    age: int
    gender: str
    height_cm: float
    weight_kg: float
    disease: str
    date_of_birth: date

    model_config = {"from_attributes": True}