from fastapi import FastAPI
from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from database import get_db
from models import User
from schemas import UserCreate, UserResponse

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
        password_hash = user.password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user