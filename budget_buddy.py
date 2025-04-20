# Import required libraries
import streamlit as st  # For creating the web app UI
import pandas as pd  # For handling dataframes
import plotly.express as px  # For plotting interactive charts
from datetime import datetime, timedelta, timezone  # For handling dates and times
from transformers import GPT2LMHeadModel, GPT2Tokenizer  # For loading and using GPT-2 model
import torch  # For PyTorch operations (ML backend)
import time  # For adding delays
import os  # For file and environment management
import random  # For generating random numbers if needed
import base64  # For encoding/decoding data
import requests  # For making HTTP requests
import json  # For parsing JSON data
import asyncio  # For asynchronous programming
from ai_assistant import generate_response  # Custom function to generate AI responses

# --- SESSION STATE INITIALIZATION ---

# Initialize device width to avoid errors on login
if "device_width" not in st.session_state:
    st.session_state["device_width"] = None

# --- DEVICE RESPONSIVENESS ---

def detect_device():
    """
    Injects JavaScript to detect user's device screen width 
    and passes it back into Streamlit.
    """
    detect_width = """
        <script>
        const width = window.innerWidth;
        const height = window.innerHeight;
        const streamlitInput = window.parent.document.querySelectorAll('input[data-testid="stTextInput"]')[0];
        streamlitInput.value = ${width};
        streamlitInput.dispatchEvent(new Event('input', { bubbles: true }));
        </script>
    """
    if st.session_state.device_width and str(st.session_state.device_width).isdigit():
        st.markdown(detect_width, unsafe_allow_html=True)
        device_width = st.text_input("Screen width", label_visibility="collapsed", key="device_width")
        return int(device_width) if device_width.isdigit() else None

# --- PAGE CONFIGURATION ---

# Set global settings for the page
st.set_page_config(page_title="🎀 BudgetBuddy", layout="wide")

# --- THEME CONFIGURATION (LIGHT & DARK MODE) ---

# Initialize dark mode setting
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# Light theme custom CSS
light_theme = """
    <style>
    body { background-color: #ffe4ec; color: #000000; }
    .stApp { background-color: #ffe4ec; }
    /* Set text and button colors */
    ...
    </style>
"""

# Dark theme custom CSS
dark_theme = """
    <style>
    body { background-color: #1c1f26; color: #f8bbd0; }
    .stApp { background-color: #1c1f26; }
    /* Set text and button colors */
    ...
    </style>
"""

# Sidebar styling CSS
sidebar_style = """
<style>
[data-testid="stSidebar"] { background-color: #1f1f29 !important; }
/* Style sidebar texts, labels, and radio buttons */
...
</style>
"""

# Apply sidebar styles
st.markdown(sidebar_style, unsafe_allow_html=True)

# Apply light or dark theme based on toggle
if st.session_state.dark_mode:
    st.markdown(dark_theme, unsafe_allow_html=True)
else:
    st.markdown(light_theme, unsafe_allow_html=True)

# --- DARK MODE TOGGLE ---

# More session state initialization
if "theme_toggled" not in st.session_state:
    st.session_state.theme_toggled = False

# Apply the theme again (defensive coding)
if st.session_state.dark_mode:
    st.markdown(dark_theme, unsafe_allow_html=True)
else:
    st.markdown(light_theme, unsafe_allow_html=True)

# Create a dark mode toggle in sidebar
toggle = st.sidebar.checkbox("🌙 Toggle Dark Mode", value=st.session_state.dark_mode)

# If user toggles, update session state and rerun
if toggle != st.session_state.dark_mode:
    st.session_state.dark_mode = toggle
    st.session_state.theme_toggled = True
    st.rerun()

# Reset the toggle after applying the change
if st.session_state.theme_toggled:
    st.session_state.theme_toggled = False

# --- GPT-2 MODEL LOADING ---

@st.cache_resource  # Cache the model to avoid reloading every time
def load_gpt2():
    """
    Loads and caches the GPT-2 tokenizer and model.
    """
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    model = GPT2LMHeadModel.from_pretrained("gpt2")
    model.eval()  # Set model to evaluation mode
    return tokenizer, model

# Load the model and tokenizer
tokenizer, model = load_gpt2()

def get_gpt_response(user_input):
    """
    Generates a short GPT-2 based text response to user input.
    
    :param user_input: The prompt or message from the user.
    :return: Generated text.
    """
    input_ids = tokenizer.encode(user_input, return_tensors="pt")
    with torch.no_grad():
        outputs = model.generate(
            input_ids, max_length=100, num_return_sequences=1, 
            pad_token_id=tokenizer.eos_token_id
        )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# --- HELPER FUNCTIONS FOR EXPENSES ---

def load_expenses():
    """
    Loads expense data from a CSV file into a DataFrame.
    
    :return: A pandas DataFrame containing the expenses.
    """
    try:
        df = pd.read_csv("expenses.csv", on_bad_lines='skip')  # Ignore bad lines
        df["date"] = pd.to_datetime(df["date"])  # Convert 'date' column to datetime
        return df
    except FileNotFoundError:
        st.error("The expenses.csv file was not found.")
        return pd.DataFrame()  # Return an empty DataFrame if not found

def predict_expenses(df, period_type, horizon=1):
    """
    Predicts future expenses based on historical data.
    
    :param df: The expenses DataFrame.
    :param period_type: 'week' or 'month'.
    :param horizon: How many periods into the future.
    :return: Predicted expense amount.
    """
    if period_type == 'week':
        return df['amount'].mean()  # Average weekly expense
    elif period_type == 'month':
        return df['amount'].sum()  # Total monthly expenses
    else:
        return 0

def add_expense(category, amount, note, recurring):
    """
    Adds a new expense entry to the CSV file.
    
    :param category: Expense category (e.g., Food, Transport).
    :param amount: Amount spent.
    :param note: Optional note.
    :param recurring: Whether the expense is recurring.
    """
    with st.spinner("Adding expense..."):
        time.sleep(1)  # Simulate processing time
        df = pd.DataFrame([{
            "date": datetime.now().strftime("%Y-%m-%d"),  # Current date
            "category": category,
            "amount": amount,
            "note": note,
            "recurring": recurring
        }])
        file_exists = os.path.isfile("expenses.csv")
        df.to_csv("expenses.csv", mode='a', header=not file_exists, index=False)  # Append new entry
        st.success("🎉 Expense added!")

# --- FAKE AUTHENTICATION SETUP ---

# Initialize user login state
if "is_logged_in" not in st.session_state:
    st.session_state.is_logged_in = False

# LOGIN PAGE
def login_page():
    # Page title and subtitle
    st.title("🎀 Track your every last cent... with BudgetBuddy!")
    st.markdown("<p style='font-size:18px;'>Login here 🐥</p>", unsafe_allow_html=True)

    # Input fields for username and password
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login = st.button("Login")

    # If login button is pressed
    if login:
        # Basic validation
        if not username or not password:
            st.error("Please enter both username and password.")
        else:
            try:
                # Make a POST request to login API
                response = requests.post("http://localhost:8000/login", json={
                    "username": username,
                    "password": password
                })

                # Handle successful login
                if response.status_code == 200:
                    data = response.json()
                    token = data.get("access_token")

                    # Save token and username into session
                    st.session_state.token = token
                    st.session_state.username = username

                    # Update login state
                    st.session_state.is_logged_in = True
                    st.session_state.just_logged_in = True
                    st.session_state.just_registered = False  # Reset registration state if re-login

                    # Detect device width for responsiveness
                    st.session_state.device_width = detect_device()

                    # Set default landing page after login
                    st.session_state.page = "Dashboard"

                    # Rerun to update app state
                    st.rerun()

                # Handle wrong credentials
                elif response.status_code == 401:
                    st.error("Invalid credentials. Please try again.")

                # Handle specific server error
                elif response.status_code == 400:
                    st.error(response.json().get("detail"))

                # Handle any other error
                else:
                    st.error(f"Login failed: {response.json().get('detail', 'Unknown error')}")

            except requests.exceptions.RequestException as e:
                # Handle network errors
                st.error(f"Login failed: {e}")

            except ValueError:
                # Handle invalid server response
                st.error("Login failed: Invalid response from server")


# REGISTER PAGE
def register_page():
    # Registration page layout
    st.title("📝 Register for BudgetBuddy")
    username = st.text_input("Username")
    email = st.text_input("Email")
    phone_number = st.text_input("Phone Number")
    profile_pic = st.file_uploader("Upload Profile Picture", type=["jpg", "png", "jpeg"])
    password = st.text_input("Password", type="password")

    # Register button
    if st.button("Register"):
        # Validation checks
        if not username:
            st.error("Username is required.")
        if not email:
            st.error("Email is required.")
        if not phone_number:
            st.error("Phone number is required.")
        if not password:
            st.error("Password is required.")

        # If all fields are filled
        if username and email and phone_number and password:
            try:
                # Debug print
                print(json.dumps({"username": username, email:email, phone_number: phone_number, password: password}))

                # Make a POST request to register API
                response = requests.post("http://localhost:8000/register", json={
                    "username": username,
                    "email": email,
                    "phone_number": phone_number,
                    "password": password
                })

                # Handle successful registration
                if response.status_code == 200:
                    st.success("Registration successful! You can now log in.")
                    st.balloons()

                # Handle registration error
                elif response.status_code == 400:
                    error_detail = response.json().get('detail', 'Unknown error')
                    st.error(f"Registration failed: {error_detail}")

                else:
                    response.raise_for_status()
                    st.error(f"Registration failed: {response.json().get('detail', 'Unknown error')}")

            except requests.exceptions.RequestException as e:
                # Handle network errors
                st.error(f"Registration failed: {e}")

            except ValueError:
                # Handle invalid server response
                st.error("Registration failed: Invalid response from server")


# DASHBOARD PAGE
def dashboard_page(): 
    # Retrieve token for API authentication
    token = st.session_state.get('token')
    title_color = "white" if st.session_state.dark_mode else "black"

    try:
        # Get expenses data from server
        expenses_response = requests.get(
            "http://localhost:8000/get_expenses",
            headers={"Authorization": f"Bearer {token}"}
        )
        expenses_response.raise_for_status()
        expenses_data = expenses_response.json()
        df = pd.DataFrame(expenses_data)

        # Layout: 2 columns
        col1, col2 = st.columns([2, 1])

        with col1:
            # If there are expenses, show spending summary
            if not df.empty:
                df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
                spending_by_category = df.groupby("category")["amount"].sum().reset_index()

                # Show total spending
                st.markdown(
                    f"""
                    <div style='background-color: {"#ffebf0" if not st.session_state.dark_mode else "#331c1c"}; padding: 20px; border-radius: 20px; margin-bottom: 20px; border: 2px dashed {"#ff4081" if not st.session_state.dark_mode else "#ff80ab"}; box-shadow: 0 4px 10px rgba(0,0,0,0.1);'>
                        <h3 style='text-align: center; color: {title_color}; margin: 0;'>Total Spending</h3>
                        <h2 style='text-align: center; color: {title_color}; margin-top: 10px;'>${df['amount'].sum():.2f}</h2>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # Create a donut chart for spending by category
                fig = px.pie(
                    spending_by_category, 
                    names="category", 
                    values="amount",
                    color_discrete_sequence=px.colors.sequential.RdBu,
                    hole=0.4
                )
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color=title_color, size=14),
                    legend=dict(font=dict(color=title_color)),
                    showlegend=True
                )

                st.markdown(f"<h3 style='text-align:center; color:{title_color};'>Spending by Category</h3>", unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True)

            else:
                st.info("No expenses yet. Add one under Add Expense")

        with col2:
            # Expense Forecasts section
            st.markdown(f"<h3 style='color:{title_color};'>📉 Expense Forecasts</h3>", unsafe_allow_html=True)

            # If enough data for predictions
            if not df.empty and len(df) >= 2:
                try:
                    weekly_prediction = predict_expenses(df, 'week', horizon=1)
                    monthly_prediction = predict_expenses(df, 'month', horizon=1)

                    st.markdown(
                        f"""
                        <div style='color:{title_color}; font-size: 20px;'>
                            <p><strong>Next Week Forecast:</strong> ${weekly_prediction:.2f}</p>
                            <p><strong>Next Month Forecast:</strong> ${monthly_prediction:.2f}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                except Exception:
                    st.info("Need more data for predictions")

            # Display tip to encourage adding more data
            tip_color = "white" if st.session_state.dark_mode else "black"
            tip_bg = "#222222" if st.session_state.dark_mode else "#f0f0f0"
            st.markdown(
                f"""
                <div style='background-color:{tip_bg}; padding:15px; border-radius:10px; color:{tip_color};'>
                💡 Predictions improve with more expense data!
                </div>
                """,
                unsafe_allow_html=True
            )

            if df.empty or len(df) < 2:
                st.info("Add at least 2 expenses to see predictions")

            # Add vertical spacing
            st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

            # Get upcoming reminders
            reminders_response = requests.get(
                "http://localhost:8000/get_reminders",
                headers={"Authorization": f"Bearer {token}"}
            )
            reminders_data = reminders_response.json()
            reminders_df = pd.DataFrame(reminders_data)

            # Show upcoming reminders if available
            if not reminders_df.empty:
                reminders_df["dueDate"] = pd.to_datetime(reminders_df["dueDate"])
                today_utc = pd.Timestamp.today(tz='UTC')
                upcoming_reminders = reminders_df[reminders_df["dueDate"] >= today_utc]

                if not upcoming_reminders.empty:
                    st.markdown(f"<h3 style='color:{title_color};'>🔔 Upcoming Payment Reminders</h3>", unsafe_allow_html=True)
                    for _, row in upcoming_reminders.iterrows():
                        st.markdown(
                            f"<div style='background-color:#ffe4ec; padding:10px; border-radius:10px; margin-bottom:10px; color:#880e4f;'>"
                            f"<strong>{row['name']}</strong> <br/>"
                            f"📅 Due on: {row['dueDate'].strftime('%B %d, %Y')}"
                            f"</div>", unsafe_allow_html=True
                        )
                else:
                    st.info("No upcoming reminders!")
            else:
                st.info("No reminders saved yet.")

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
    except ValueError:
        st.error("Invalid response from server.")



# Page to add an expense
def add_expense_page():
    # Select category from a dropdown
    category = st.selectbox("Category", ["Food", "Transport", "Shopping", "Rent", "Utilities", "Other"])
    # Input the amount spent
    amount = st.number_input("Amount", min_value=0.0, format="%.2f")
    # Add an optional note
    note = st.text_input("Note")
    # Checkbox for recurring expense
    recurring = st.checkbox("Recurring?")
    # Retrieve user's token from session
    token = st.session_state.get('token')

    # When the user clicks the "Add Expense" button
    if st.button("Add Expense"):
        if token:
            if not category:
                st.error("Please select a category.")
            elif amount <= 0:
                st.error("Amount must be greater than zero.")
            else:
                try:
                    # Send POST request to backend to add the expense
                    response = requests.post(
                        "http://localhost:8000/add_expense",
                        json={
                            "category": category,
                            "amount": amount,
                            "note": note,
                            "recurring": recurring,
                        },
                        headers={"Authorization": f"Bearer {token}"}
                    )

                    if response.status_code == 200:
                        st.success("Expense added successfully!")
                    else:
                        # Try to extract error message from server response
                        try:
                            error_message = response.json().get('detail', 'Unknown error')
                        except ValueError:
                            error_message = "Invalid response from server"
                        st.error(f"Failed to add expense: {error_message}")

                except requests.exceptions.RequestException as e:
                    st.error(f"Failed to add expense: {e}")
        else:
            st.error("User not logged in.")

# Page to manage savings jars
def savings_jar():
    # Initialize empty jars list if not already created
    if "jars" not in st.session_state:
        st.session_state.jars = []

    # Input fields for jar details
    jar_name = st.text_input("Jar Name")
    jar_goal = st.number_input("Financial Goal", min_value=0.0, format="%.2f")
    jar_description = st.text_input("What is this jar for?")
    jar_progress = st.slider("Progress", 0, 100, 0)
    token = st.session_state.get('token')

    # Animation when jar is successfully created
    def coin_drop_animation():
        coin = "🪙"
        st.markdown("<p style='font-size:24px; text-align:center;'>Saving ongoing!</p>", unsafe_allow_html=True)
        coin_placeholder = st.empty()
        for i in range(1, 11):
            coin_placeholder.markdown(f"<p style='font-size:48px; text-align:center; padding-top:{i * 5}px;'>{coin}</p>", unsafe_allow_html=True)
            time.sleep(0.1)

    # When the user clicks the "Add Jar" button
    if st.button("Add Jar"):
        if jar_name and jar_goal > 0 and jar_description:
            try:
                # Send POST request to backend to add a new savings jar
                response = requests.post(
                    "http://localhost:8000/add_savings_jar",
                    json={
                        "name": jar_name,
                        "goal": jar_goal,
                        "description": jar_description,
                        "progress": jar_progress,
                    },
                    headers={"Authorization": f"Bearer {token}"}
                )

                if response.status_code == 200:
                    st.success(f"Jar '{jar_name}' has been added successfully!")
                    coin_drop_animation()
                else:
                    st.error(f"Failed to add jar: {response.json().get('detail', 'Unknown error')}")
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to add jar: {e}")
            except ValueError:
                st.error("Failed to add jar: Invalid response from server")
        else:
            st.warning("Please fill in all fields to add a jar.")

    # Display jar image
    with open("image.png", "rb") as image_file:
        jar_image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

    st.markdown(
        f"""
        <div style='text-align: center; margin-top: -5px;'>
            <img src='data:image/png;base64,{jar_image_base64}' width='150'>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Display existing jar progress (if any)
    for jar in st.session_state.jars:
        st.markdown(f"<p style='font-size:16px; color:black; text-align:center;'>Progress: {jar['progress']}%</p>", unsafe_allow_html=True)

# Page to add reminders for upcoming payments
def reminders_page():
    token = st.session_state.get('token')

    st.subheader("Add a Reminder")

    # Input fields for reminder details
    name = st.text_input("Name of reminder", key="reminder_name")
    amount = st.number_input("Amount", min_value=0.0, format="%.2f", key="reminder_amount")
    due_date = st.date_input("Due date", key="reminder_due_date")

    # When the user clicks the "Add Reminder" button
    if st.button("Add Reminder", key="add_reminder_button"):
        try:
            # Send POST request to backend to add the reminder
            response = requests.post(
                "http://localhost:8000/add_reminder",
                json={
                    "name": name,
                    "amount": amount,
                    "due_date": str(due_date.isoformat()),
                },
                headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code == 200:
                st.success(f"Reminder '{name}' has been added successfully!")
            else:
                st.error(f"Failed to add reminder: {response.json().get('detail', 'Unknown error')}")
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to add reminder: {e}")
        except ValueError:
            st.error("Failed to add reminder: Invalid response from server")

# Page with AI chat assistant
async def chat_assistant_page():
    token = st.session_state.get('token')
    get_ai_response = generate_response()

    # Initialize chat history if not already there
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display previous chat messages
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input field for new user prompt
    if prompt := st.chat_input("Ask me anything about budgeting!"):
        # Add user's new message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display a placeholder while generating AI response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = await get_ai_response(prompt, token)
            message_placeholder.markdown(full_response)

        # Add assistant's response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": full_response})

# Page to view weekly expenses
def weekly_expenses_page():
    token = st.session_state.get('token')
    if not token:
        st.error("You're not logged in. Please log in to view expenses.")
        return

    # Set authorization header and fetch expenses
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("http://localhost:8000/get_expenses", headers=headers)

    if response.status_code != 200:
        st.error("Failed to fetch expenses.")
        return

    expenses = response.json()

    if not expenses:
        st.warning("No expenses recorded yet!")
        return

    # Convert expenses into a pandas DataFrame
    df = pd.DataFrame(expenses)

    if "createdAt" in df.columns:
        df["createdAt"] = pd.to_datetime(df["createdAt"])
        # Filter only expenses from the past 7 days
        past_week = datetime.now(timezone.utc) - timedelta(days=7)
        weekly_df = df[df["createdAt"] >= past_week]

        if not weekly_df.empty:
            # Clean up DataFrame and display
            weekly_df = weekly_df.drop(columns=["id", "userId", "user"], errors="ignore")
            weekly_df["createdAt"] = weekly_df["createdAt"].dt.date
            st.markdown("Here’s a quick glance at your expenses this past week:")
            st.dataframe(weekly_df)
        else:
            st.info("You haven’t added any expenses in the past week.")
    else:
        st.warning("Unexpected data format received from server.")





# Main asynchronous function to run the Streamlit app
async def main():
    """Main function to run the Streamlit app."""
    
    # Sidebar title
    st.sidebar.title("🎀 Budget Buddy 🎀")

    # Check if the user is logged in
    if not st.session_state.get('is_logged_in', False):
        # If not logged in, show options to login or register
        auth_choice = st.sidebar.radio("Choose an option", ["Login", "Register"])
        
        if auth_choice == "Login":
            login_page()  # Show login page
        else:
            register_page()  # Show registration page

    else:
        # If logged in, show navigation menu
        page = st.sidebar.radio(
            "Navigate", 
            ["Dashboard", "Add Expense", "Weekly Summary", "Savings Jars", "Reminders", "Chat Assistant"]
        )

        # Show a success message after login
        st.sidebar.success("✅ You're logged in!")

        # Provide a logout button
        if st.sidebar.button("Logout"):
            st.session_state.is_logged_in = False  # Reset login state
            st.rerun()  # Refresh the app to show login/register options again

        # Handle page navigation
        if page == "Dashboard":
            st.header("📊 Dashboard")
            dashboard_page()

        elif page == "Add Expense":
            st.header("➕ Add New Expense")
            add_expense_page()

        elif page == "Savings Jars":
            st.header("🏦 Savings Jars")
            savings_jar()

        elif page == "Reminders":
            st.header("🔔 Payment Reminders")
            reminders_page()

        elif page == "Chat Assistant":
            st.header("🧠 Chat with BudgetBuddy")
            await chat_assistant_page()  # Important: Await because it's an async function

        elif page == "Weekly Summary":
            st.header("📬 Weekly Summary of Expenses")
            weekly_expenses_page()

# Standard Python script entry point
if __name__ == "__main__":
    # Run the main async function using asyncio
    asyncio.run(main())
