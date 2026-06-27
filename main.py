from fastapi import FastAPI
from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from database import get_db
from models import User

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World!"}


@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    result = db.execute(select(User))
    users = result.scalars().all()
    return users

