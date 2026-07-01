from fastapi import FastAPI
from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from database import get_db
from models import User
from schemas import UserCreate, UserResponse, UserUpdate
from pwdlib import PasswordHash
from fastapi import HTTPException

password_hasher = PasswordHash.recommended()

# podman container start expense-db
# podman exec -it expense-db psql -U bism -d expense_tracker

# uvicorn main:app --reload

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World!"}


@app.get("/users", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    result = db.execute(select(User))
    users = result.scalars().all()
    return users


@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = User(
        username = user.username,
        email = user.email,
        password_hash = password_hasher.hash(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.get("/users/{id}", response_model=UserResponse)
def get_single_user(id: int, db: Session = Depends(get_db)):
    result = db.execute(select(User).where(User.id == id))
    user = result.scalars().one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not Found.")

    return(user)


@app.put("/users/{id}", response_model=UserResponse)
def update_user(id: int, update_info: UserUpdate, db: Session = Depends(get_db)):
    result = db.execute(select(User).where(User.id == id))
    current_user = result.scalars().one_or_none()

    if current_user is None:
        raise HTTPException(status_code=404, detail="User not Found")

    if update_info.username is not None:
        current_user.username = update_info.username
    
    if update_info.email is not None:
        current_user.email = update_info.email

    if update_info.password is not None:
        current_user.password_hash = password_hasher.hash(update_info.password)

    db.commit()
    db.refresh(current_user)
    return current_user