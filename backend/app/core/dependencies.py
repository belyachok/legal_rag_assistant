"""
Dependency injection for FastAPI.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from .database import get_db


def get_current_user(db: Session = Depends(get_db)):
    """
    Get current user (placeholder for future authentication).
    Currently returns None.
    """
    # TODO: Implement authentication when needed
    return None


def require_auth(current_user=Depends(get_current_user)):
    """
    Dependency that requires authentication.
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user