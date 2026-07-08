from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import select
from database import get_db
from models import User, Expense
from schemas import UserCreate, UserResponse, UserUpdate, ExpenseCreate, ExpenseUpdate, ExpenseResponse, LoginRequest
from pwdlib import PasswordHash
from fastapi import HTTPException
from jose import jwt, JWTError
from datetime import datetime, timedelta, UTC

password_hasher = PasswordHash.recommended()

SECRET_KEY = "replace-this-with-a-long-random-string"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# podman container start expense-db
# podman exec -it expense-db psql -U bism -d expense_tracker

# cd ~/Documents/The\ Vault\ -\ Linux/VS\ code\ Programing/Expense-Tracker-API/
# uvicorn main:app --reload

app = FastAPI()


def create_access_token(user_id: int):
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),
        "exp": expire
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Invalid authentication credentials"
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = db.execute(
        select(User).where(User.id == int(user_id))
    ).scalars().one_or_none()

    if user is None:
        raise credentials_exception

    return user


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
def create_expense(expense: ExpenseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    new_expense = Expense(
        user_id = current_user.id,
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
def get_expenses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = db.execute(select(Expense).where(Expense.user_id == current_user.id))
    expenses = result.scalars().all()
    return expenses


@app.get("/expenses/{id}", response_model=ExpenseResponse)
def get_single_expense(id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    expense = db.execute(
        select(Expense).where(Expense.id == id, Expense.user_id == current_user.id)).scalars().one_or_none()

    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found.")

    return expense


@app.put("/expenses/{id}", response_model=ExpenseResponse)
def update_expense(id: int, update_info: ExpenseUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_expense = db.execute(
        select(Expense).where(Expense.id == id, Expense.user_id == current_user.id)).scalars().one_or_none()

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
def delete_expense(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    expense = db.execute(
        select(Expense).where(Expense.id == id, Expense.user_id == current_user.id)).scalars().one_or_none()

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
    
    return {"access_token": create_access_token(user.id),
            "token_type": "bearer"}
