from fastapi import FastAPI

from database import engine, Base
import models 
from app.routers.auth import router as auth_router
from app.routers.expenses import router as expenses_router
from app.routers.users import router as users_router

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth_router)
app.include_router(expenses_router)
app.include_router(users_router)


@app.get("/")
def read_root():
    return {"message": "Hello World!"}