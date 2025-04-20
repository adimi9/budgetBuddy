# 🎀 Budget Buddy 🎀: Personal Budgeting and Financial Management App

**BudgetBuddy** is a web-based financial management application that allows users to track their expenses, set savings goals, receive payment reminders, and chat with an AI assistant to stay on top of their budgeting. The application is built using **Streamlit** for the frontend and **FastAPI** for the backend, with a **PostgreSQL** database for data storage.

---

## Features

- **User Registration & Login**: Secure registration and login system using JWT tokens.
- **Expense Tracking**: Add, view, and manage your expenses by category (e.g., Food, Transport, etc.).
- **Savings Jars**: Create savings goals with progress tracking.
- **Reminders**: Add and manage payment reminders with due dates and amounts.
- **Weekly Summary**: View your weekly expenses summary.
- **Chat Assistant**: Interact with an AI-powered assistant for financial advice and budgeting tips.

---

## Tech Stack

### Frontend:
- **Streamlit**: A fast and interactive web framework for building data-driven applications.
- **Plotly**: Interactive charts and graphs for visualizing expenses and financial data.

### Backend:
- **FastAPI**: High-performance web framework for building APIs.
- **Prisma**: ORM for interacting with the PostgreSQL database.
- **PostgreSQL**: Database for storing user data, expenses, reminders, and savings jars.

### Additional Libraries:
- **OpenAI**: For integrating AI-powered chat assistant features.
- **JWT**: For secure token-based authentication.
- **AsyncIO**: For handling asynchronous tasks in the backend.
- **PassLib**: For securely hashing and verifying user passwords.

---

## 📦 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/adimi9/budgetBuddy
cd budget-buddy
```

### 2. Set Up Backend (FastAPI + Prisma + PostgreSQL)

#### Install Python dependencies:
```
pip install -r requirements.txt
```

#### Set up configurations 
Create a .env file in the root directory and add the following:

```
DATABASE_URL="postgresql://username:password@localhost:5432/database_name"
JWT_SECRET="your_jwt_secret_key"
JWT_ALGORITHM="HS256"
JWT_EXPIRE_MINUTES=60
OPENAI_API_KEY="your_openai_api_key"
```

#### Run Prisma Commands
```
prisma generate
prisma migrate dev --name init
```

#### Run FastAPI server:
```
uvicorn main:app --reload
```

The backend server will be running at:
http://localhost:8000

### 3. Set Up Frontend (Streamlit)

#### Run Streamlit app:
```
streamlit run budget_buddy.py
```

The app will open at:
http://localhost:8501

---

### 🔑 Authentication Flow

- User signs up and is stored in PostgreSQL with a hashed password.
- User logs in → Receives a JWT token.
- Streamlit frontend stores the token in session state.
- Token is sent with every protected API request.

### 📚 API Endpoints

| Method | Endpoint        | Description                            | Auth Required |
|--------|-----------------|----------------------------------------|---------------|
| POST   | /register       | Register a new user                   | ❌            |
| POST   | /login          | Login and get access token            | ❌            |
| GET    | /users/me       | Get current user's profile            | ✅            |
| POST   | /add_expense    | Add a new expense                      | ✅            |
| POST   | /add_savings_jar| Add a new savings jar                 | ✅            |
| POST   | /add_reminder   | Add a new payment reminder            | ✅            |
| GET    | /get_expenses   | Fetch user's expenses                 | ✅            |
| GET    | /get_savings_jars| Fetch user's savings jars            | ✅            |
| GET    | /get_reminders  | Fetch user's payment reminders        | ✅            |


### 🛡 Security

- Passwords are hashed using bcrypt before saving.
- Authentication handled via OAuth2 Bearer Tokens (JWT).
- CORS Middleware enabled to allow frontend-backend communication.

---

✨ Built with ❤️ to make managing money easier and fun!
