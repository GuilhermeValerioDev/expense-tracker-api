from fastapi import FastAPI
from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from database import get_db
from models import User, Expense
from schemas import UserCreate, UserResponse, UserUpdate, ExpenseCreate, ExpenseUpdate, ExpenseResponse, LoginRequest
from pwdlib import PasswordHash
from fastapi import HTTPException

password_hasher = PasswordHash.recommended()

# podman container start expense-db
# podman exec -it expense-db psql -U bism -d expense_tracker

# cd ~/Documents/The\ Vault\ -\ Linux/VS\ code\ Programing/Expense-Tracker-API/
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
    user = db.execute(select(User).where(User.id == id)).scalars().one_or_none()
    
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    return(user)


@app.put("/users/{id}", response_model=UserResponse)
def update_user(id: int, update_info: UserUpdate, db: Session = Depends(get_db)):
    current_user = db.execute(select(User).where(User.id == id)).scalars().one_or_none()
    
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


@app.delete("/users/{id}")
def delete_user(id: int, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.id == id)).scalars().one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return {"message": f"Deleted user {id}"}


@app.post("/expenses", response_model=ExpenseResponse)
def create_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.id == expense.user_id)).scalars().one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_expense = Expense(
        user_id = expense.user_id,
        category = expense.category,
        expense_date = expense.expense_date,
        amount = expense.amount,
        name = expense.name
    )
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return new_expense


@app.get("/expenses", response_model=list[ExpenseResponse])
def get_expenses(db: Session = Depends(get_db)):
    result = db.execute(select(Expense))
    expenses = result.scalars().all()
    return expenses


@app.get("/expenses/{id}", response_model=ExpenseResponse)
def get_single_expense(id: int, db: Session = Depends(get_db)):
    expense = db.execute(select(Expense).where(Expense.id == id)).scalars().one_or_none()

    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found.")

    return expense


@app.put("/expenses/{id}", response_model=ExpenseResponse)
def update_expense(id: int, update_info: ExpenseUpdate, db: Session = Depends(get_db)):
    current_expense = db.execute(select(Expense).where(Expense.id == id)).scalars().one_or_none()

    if current_expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")

    if update_info.name is not None:
        current_expense.name = update_info.name

    if update_info.category is not None:
        current_expense.category = update_info.category

    if update_info.amount is not None:
        current_expense.amount = update_info.amount

    if update_info.expense_date is not None:
        current_expense.expense_date = update_info.expense_date

    db.commit()
    db.refresh(current_expense)
    return current_expense


@app.delete("/expenses/{id}")
def delete_expense(id: int, db: Session = Depends(get_db)):
    expense = db.execute(select(Expense).where(Expense.id == id)).scalars().one_or_none()

    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")

    db.delete(expense)
    db.commit()
    return {"message": f"Deleted expense {id}"}


@app.post("/login")
def login(login: LoginRequest, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == login.email)).scalars().one_or_none()

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not password_hasher.verify(login.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {"message": "Login successful!"}
