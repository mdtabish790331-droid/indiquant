import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
import os

load_dotenv()

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{AUTH_SERVICE_URL}/api/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{AUTH_SERVICE_URL}/api/auth/verify",
                headers={"Authorization": f"Bearer {token}"},
            )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return resp.json()
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unavailable.",
        )


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Sirf admin access kar sakta hai."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied — sirf admin yeh kaam kar sakta hai.",
        )
    return current_user


async def require_participant(current_user: dict = Depends(get_current_user)) -> dict:
    """Sirf participant submit kar sakta hai."""
    if current_user.get("role") != "participant":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied — sirf participant prediction submit kar sakta hai.",
        )
    return current_user