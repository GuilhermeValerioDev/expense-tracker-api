from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from schemas import UserCreate, UserResponse, UserUpdate
from models import User
from database import get_db
from app.routers.auth import password_hasher

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    result = db.execute(select(User))
    users = result.scalars().all()
    return users


@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = User(
        username=user.username,
        email=user.email,
        password_hash=password_hasher.hash(user.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/{id}", response_model=UserResponse)
def get_single_user(id: int, db: Session = Depends(get_db)):
    user = (
        db.execute(select(User).where(User.id == id))
        .scalars()
        .one_or_none()
    )

    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    return user


@router.put("/{id}", response_model=UserResponse)
def update_user(id: int, update_info: UserUpdate, db: Session = Depends(get_db)):
    current_user = (
        db.execute(select(User).where(User.id == id))
        .scalars()
        .one_or_none()
    )

    if current_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if update_info.username is not None:
        current_user.username = update_info.username

    if update_info.email is not None:
        current_user.email = update_info.email

    if update_info.password is not None:
        current_user.password_hash = password_hasher.hash(update_info.password)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/{id}")
def delete_user(id: int, db: Session = Depends(get_db)):
    user = ( db.execute(select(User).where(User.id == id)).scalars().one_or_none())

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"message": f"Deleted user {id}"}