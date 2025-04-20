import requests  # For making HTTP requests to the FastAPI backend
import asyncio  # For async programming (concurrent tasks)
from openai import OpenAI  # OpenAI Python client to interact with GPT models
from dotenv import load_dotenv  # To load environment variables from a .env file
import os  # For interacting with the operating system/environment variables

# Load environment variables from a .env file
load_dotenv()

# Define constants
BASE_URL = "http://localhost:8000"  # Base URL for the local FastAPI server
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # OpenAI API key loaded securely from .env

def generate_response():
    """
    Returns a function that generates an AI response using user data from the API.
    It wraps the internal async functions to separate concerns: fetching data + generating AI response.
    """

    async def get_user_data(access_token: str):
        """
        Retrieves user-specific data (expenses, savings jars, reminders) from the FastAPI API.
        
        :param access_token: JWT token used for authenticating API requests.
        :return: A dictionary containing the user's data or None if any error occurs.
        """
        headers = {"Authorization": f"Bearer {access_token}"}  # Set up auth headers

        try:
            # Fetch expenses
            expenses_response = requests.get(f"{BASE_URL}/get_expenses", headers=headers)
            expenses_response.raise_for_status()  # Raise exception if response code is not 2xx
            expenses = expenses_response.json()  # Parse the JSON response

            # Fetch savings jars
            savings_jars_response = requests.get(f"{BASE_URL}/get_savings_jars", headers=headers)
            savings_jars_response.raise_for_status()
            savings_jars = savings_jars_response.json()

            # Fetch reminders
            reminders_response = requests.get(f"{BASE_URL}/get_reminders", headers=headers)
            reminders_response.raise_for_status()
            reminders = reminders_response.json()

            # Combine all fetched data into one dictionary
            user_data = {
                "expenses": expenses,
                "savings_jars": savings_jars,
                "reminders": reminders,
            }
            return user_data

        except requests.exceptions.RequestException as e:
            # Handle any HTTP-related errors (connection issues, bad responses, etc.)
            print(f"Error fetching user data: {e}")
            return None
        except Exception as e:
            # Handle any other unexpected errors
            print(f"An unexpected error occurred: {e}")
            return None

    async def generate_ai_response(user_prompt: str, access_token: str):
        """
        Generates an AI response using OpenAI, based on the user's data fetched from the API.
        
        :param user_prompt: The user's question or command.
        :param access_token: JWT token for fetching user-specific data.
        :return: AI-generated response string.
        """
        # Initialize OpenAI client with API key
        client = OpenAI(api_key=OPENAI_API_KEY)

        # Fetch the user's data
        user_data = await get_user_data(access_token)

        if not user_data:
            return "Sorry, I couldn't retrieve your data."

        # Build the context for the AI model from the fetched user data
        context = f"User Information: \n"
        context += f"Expenses: {user_data['expenses']}\n"
        context += f"Savings Jars: {user_data['savings_jars']}\n"
        context += f"Reminders: {user_data['reminders']}\n"
        context += "Please use this information to respond to the user's query.\n"

        # Combine the context with the user's actual prompt
        full_prompt = context + f"User Query: {user_prompt}"

        try:
            # Make a call to OpenAI's Chat Completions endpoint
            response = client.chat.completions.create(
                model="gpt-4o",  # Specify model (e.g., gpt-4o)
                messages=[
                    {"role": "system", "content": "You are a helpful personal finance assistant."},
                    {"role": "user", "content": full_prompt}
                ]
            )
            # Extract and return the AI's generated message
            return response.choices[0].message.content
        except Exception as e:
            # Catch any errors from OpenAI API calls
            return f"An error occurred: {e}"

    async def get_response(user_prompt: str, access_token: str) -> str:
        """
        Public function to be called externally to generate an AI response.

        :param user_prompt: The prompt/question from the user.
        :param access_token: JWT token for authenticating API requests.
        :return: The AI-generated response as a string.
        """
        return await generate_ai_response(user_prompt, access_token)

    return get_response  # Return the get_response function for external use
