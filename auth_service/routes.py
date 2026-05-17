from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
from models import User, RoleEnum
from schemas import UserCreate, UserResponse, Token
from auth_utils import hash_password, verify_password, create_access_token, get_current_user
from dotenv import load_dotenv
import os

load_dotenv()

# Secret key jo sirf admin registration ke waqt chahiye
# Yeh .env mein set karo — koi bhi isko jaane bina admin nahi ban sakta
ADMIN_REGISTRATION_KEY = os.getenv("ADMIN_REGISTRATION_KEY", "indiquant-admin-secret-2026")

router = APIRouter(tags=["Authentication"])


# ═══════════════════════════════════════════════════════════
#   PARTICIPANT PORTAL
#   /api/participant/register  — participant register
#   /api/participant/login     — participant login
# ═══════════════════════════════════════════════════════════

participant_router = APIRouter(prefix="/api/participant", tags=["Participant Portal"])


@participant_router.post("/register", response_model=UserResponse, status_code=201)
def participant_register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Participant registration — koi bhi register kar sakta hai.
    Role hamesha 'participant' hoga — admin nahi ban sakta yahan se.
    """
    existing = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username ya email pehle se exist karta hai.")

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role=RoleEnum.participant,  # Force — participant hi banega, admin nahi
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@participant_router.post("/login", response_model=Token)
def participant_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Participant login — sirf participant account se login hoga.
    Admin yahan se login karne ki koshish kare toh 403.
    """
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Galat username ya password.",
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account inactive hai — admin se contact karo.")

    # Admin yahan se login nahi kar sakta
    if user.role != RoleEnum.participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Yeh participant login hai. Admin /api/admin/login use karo.",
        )

    token = create_access_token({
        "sub": user.username,
        "role": user.role.value,
        "user_id": user.id,
    })
    return {"access_token": token, "token_type": "bearer"}


@participant_router.get("/me", response_model=UserResponse)
def participant_me(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Apna profile dekho."""
    if current_user["role"] != "participant":
        raise HTTPException(status_code=403, detail="Yeh participant endpoint hai.")
    user = db.query(User).filter(User.username == current_user["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


# ═══════════════════════════════════════════════════════════
#   ADMIN PORTAL
#   /api/admin/register  — admin register (secret key chahiye)
#   /api/admin/login     — admin login
#   /api/admin/users     — sabke users dekho
#   /api/admin/users/{id}/delete  — user delete karo
#   /api/admin/users/{id}/deactivate — user block karo
# ═══════════════════════════════════════════════════════════

admin_router = APIRouter(prefix="/api/admin", tags=["Admin Portal"])


@admin_router.post("/register", response_model=UserResponse, status_code=201)
def admin_register(
    user_data: UserCreate,
    admin_key: str,  # Query parameter — ?admin_key=xxxx
    db: Session = Depends(get_db),
):
    """
    Admin registration — secret key ke bina koi admin nahi ban sakta.
    URL: POST /api/admin/register?admin_key=indiquant-admin-secret-2026
    Yeh key sirf boss/authorized log jaante hain.
    """
    # Secret key check
    if admin_key != ADMIN_REGISTRATION_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Galat admin key. Unauthorized.",
        )

    existing = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username ya email pehle se exist karta hai.")

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role=RoleEnum.admin,  # Force — hamesha admin banega
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@admin_router.post("/login", response_model=Token)
def admin_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Admin login — sirf admin account se login hoga.
    Participant yahan se login karne ki koshish kare toh 403.
    """
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Galat username ya password.",
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account inactive hai.")

    # Participant yahan se login nahi kar sakta
    if user.role != RoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Yeh admin login hai. Participant /api/participant/login use karo.",
        )

    token = create_access_token({
        "sub": user.username,
        "role": user.role.value,
        "user_id": user.id,
    })
    return {"access_token": token, "token_type": "bearer"}


@admin_router.get("/me", response_model=UserResponse)
def admin_me(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Admin apna profile dekhe."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Yeh admin endpoint hai.")
    user = db.query(User).filter(User.username == current_user["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


@admin_router.get("/users", response_model=list[UserResponse])
def list_all_users(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """ADMIN ONLY — platform ke sabhi users ki list."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only.")
    return db.query(User).order_by(User.id).all()


@admin_router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """ADMIN ONLY — kisi bhi user ko permanently delete karo."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only.")
    if current_user["user_id"] == user_id:
        raise HTTPException(status_code=400, detail="Khud ko delete nahi kar sakte.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.role == RoleEnum.admin:
        raise HTTPException(status_code=400, detail="Doosre admin ko delete nahi kar sakte.")
    db.delete(user)
    db.commit()


@admin_router.patch("/users/{user_id}/deactivate", status_code=200)
def deactivate_user(
    user_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """ADMIN ONLY — user ko block karo (delete nahi, sirf band karo)."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only.")
    if current_user["user_id"] == user_id:
        raise HTTPException(status_code=400, detail="Khud ko deactivate nahi kar sakte.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.is_active = False
    db.commit()
    return {"message": f"User '{user.username}' block ho gaya."}


@admin_router.patch("/users/{user_id}/activate", status_code=200)
def activate_user(
    user_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """ADMIN ONLY — blocked user ko wapas activate karo."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.is_active = True
    db.commit()
    return {"message": f"User '{user.username}' activate ho gaya."}


# ═══════════════════════════════════════════════════════════
#   INTERNAL ENDPOINT — backend_service use karta hai
# ═══════════════════════════════════════════════════════════

internal_router = APIRouter(prefix="/api/auth", tags=["Internal"])


@internal_router.get("/verify")
def verify_token(current_user=Depends(get_current_user)):
    """Backend_service is endpoint se token verify karta hai."""
    return {
        "valid": True,
        "username": current_user["username"],
        "role": current_user["role"],
        "user_id": current_user["user_id"],
    }