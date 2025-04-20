# Import necessary modules and classes
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from prisma import Prisma
from auth import hash_password, verify_password, create_access_token, decode_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime

# Initialize FastAPI app
app = FastAPI()

# Initialize Prisma client
db = Prisma()

# Set up OAuth2 for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Allow CORS (Cross-Origin Resource Sharing) for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from any origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to the database when the app starts
@app.on_event("startup")
async def startup():
    await db.connect()

# Disconnect from the database when the app shuts down
@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()

# Dependency to get the current user by decoding the token
async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await db.user.find_unique(where={"id": payload.get("user_id")})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Route to get the logged-in user's info
@app.get("/users/me")
async def read_users_me(current_user = Depends(get_current_user)):
    """Returns the current user's information."""
    return current_user

# Route to register a new user
@app.post("/register")
async def register(data: Request):
    body = await data.json()
    username = body.get("username")
    email = body.get("email")
    phone = body.get("phone_number")
    password = hash_password(body.get("password"))

    # Check if username already exists
    existing_username = await db.user.find_unique(where={"username": username})
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Check if email already exists
    existing_email = await db.user.find_unique(where={"email": email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Create new user
    user = await db.user.create(data={
        "username": username,
        "email": email,
        "phoneNumber": phone,
        "password": password
    })

    return {"message": "User registered", "user_id": user.id}

# Route to login and receive an access token
@app.post("/login")
async def login(data: Request):
    body = await data.json()
    username = body.get("username")
    password = body.get("password")

    # Validate input
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password are required.")

    # Find user by username and verify password
    user = await db.user.find_unique(where={"username": username})
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create and return access token
    token = create_access_token({"user_id": user.id})
    return {"access_token": token, "token_type": "bearer"}

# Route to add a new expense
@app.post("/add_expense")
async def add_expense(data: Request, current_user = Depends(get_current_user)):
    body = await data.json()
    category = body.get("category")
    amount = body.get("amount")
    note = body.get("note")
    recurring = body.get("recurring")

    user_id = current_user.id  # Get user ID from decoded token

    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found in token.")

    try:
        # Create new expense entry
        expense = await db.expense.create(data={
            "userId": user_id,
            "category": category,
            "amount": amount,
            "note": note,
            "recurring": recurring
        })
        return {"message": "Expense added successfully", "expense_id": expense.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Route to add a new savings jar
@app.post("/add_savings_jar")
async def add_savings_jar(data: Request, current_user = Depends(get_current_user)):
    body = await data.json()
    name = body.get("name")
    goal = body.get("goal")
    description = body.get("description")
    progress = body.get("progress")

    try:
        # Create new savings jar
        savings_jar = await db.savingsjar.create(data={
            "userId": current_user.id,
            "name": name,
            "goal": goal,
            "description": description,
            "progress": progress
        })
        return {"message": "Savings jar added successfully", "savings_jar_id": savings_jar.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Route to add a new reminder
@app.post("/add_reminder")
async def add_reminder(data: Request, current_user = Depends(get_current_user)):
    body = await data.json()
    name = body.get("name")
    amount = body.get("amount")
    due_date_str = body.get("due_date")

    # Parse the due date string into a datetime object
    try:
        due_date = datetime.fromisoformat(due_date_str + "T00:00:00")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    try:
        # Create new reminder entry
        reminder = await db.reminder.create(data={
            "userId": current_user.id,
            "name": name,
            "amount": amount,
            "dueDate": due_date,
        })
        return {"message": "Reminder added successfully", "reminder_id": reminder.id, "due_date": due_date.isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Route to get all reminders for the current user
@app.get("/get_reminders")
async def get_reminders(current_user = Depends(get_current_user)):
    try:
        reminders = await db.reminder.find_many(where={"userId": current_user.id})
        return reminders
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Route to get all expenses for the current user
@app.get("/get_expenses")
async def get_expenses(current_user = Depends(get_current_user)):
    try:
        expenses = await db.expense.find_many(where={"userId": current_user.id})
        return expenses
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Route to get all savings jars for the current user
@app.get("/get_savings_jars")
async def get_savings_jars(current_user = Depends(get_current_user)):
    try:
        savings_jars = await db.savingsjar.find_many(where={"userId": current_user.id})
        return savings_jars
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
