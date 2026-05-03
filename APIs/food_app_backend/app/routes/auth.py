from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date

from app.database import get_db
from app.models.user import User
from app.models.user_goals import UserGoals
from app.schemas.auth import (
    RegisterRequest, RegisterResponse,
    LoginRequest, LoginResponse,
    UserProfileResponse
)
from app.utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def calculate_age(dob: date) -> int:
    """Calculate age from date of birth."""
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


# ── ENDPOINT 1: Register ──────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account"
)
def register(request: RegisterRequest, db: Session = Depends(get_db)):

    # 1. Check duplicate email
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists"
        )

    # 2. Hash password
    hashed_pw = hash_password(request.password)

    # 3. Create User row
    new_user = User(
        name          = request.name,
        email         = request.email,
        password_hash = hashed_pw,
        date_of_birth = request.date_of_birth,
        gender        = request.gender,
        height_cm     = request.height_cm,
        weight_kg     = request.weight_kg,
        disease       = request.disease
    )
    db.add(new_user)
    db.flush()  # assigns UUID before commit

    # 4. Auto-create default goals row
    default_goals = UserGoals(
        user_id            = new_user.id,
        daily_calorie_goal = 2000,
        protein_goal_g     = 50,
        carbs_goal_g       = 250,
        fat_goal_g         = 65,
        fiber_goal_g       = 25
    )
    db.add(default_goals)

    # 5. Commit both rows
    db.commit()
    db.refresh(new_user)

    # 6. Generate token
    token = create_access_token(str(new_user.id))

    # 7. Return response — calculate age directly, no @property needed
    return RegisterResponse(
        user_id = new_user.id,
        name    = new_user.name,
        email   = new_user.email,
        age     = calculate_age(new_user.date_of_birth),
        token   = token
    )


# ── ENDPOINT 2: Login ─────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login and get JWT token"
)
def login(request: LoginRequest, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == request.email).first()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    token = create_access_token(str(user.id))

    return LoginResponse(
        token   = token,
        user_id = user.id,
        name    = user.name,
        email   = user.email
    )


# ── ENDPOINT 3: Get current user ──────────────────────────────────────────────

@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get logged-in user profile"
)
def get_me(current_user: User = Depends(get_current_user)):

    return UserProfileResponse(
        user_id       = current_user.id,
        name          = current_user.name,
        email         = current_user.email,
        age           = calculate_age(current_user.date_of_birth),
        gender        = current_user.gender.value,
        height_cm     = current_user.height_cm,
        weight_kg     = current_user.weight_kg,
        disease       = current_user.disease.value,
        date_of_birth = current_user.date_of_birth
    )