import bcrypt  # Library for hashing and verifying passwords securely
from jose import jwt  # Library for encoding and decoding JSON Web Tokens (JWT)
from datetime import datetime, timedelta  # Used for time calculations for token expiration
import os  # For interacting with environment variables
from dotenv import load_dotenv  # To load environment variables from a .env file

# Load environment variables from a .env file
load_dotenv()

# Retrieve necessary environment variables
JWT_SECRET = os.getenv("JWT_SECRET")  # Secret key used to sign and verify JWT tokens
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")  # Algorithm to be used for JWT encoding/decoding (e.g., "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES"))  # Token expiry duration in minutes

def hash_password(password: str) -> str:
    """
    Hashes a plain-text password using bcrypt and returns the hashed password as a string.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    """
    Verifies if a plain-text password matches its hashed version.
    
    :param plain: The plain-text password.
    :param hashed: The hashed password stored in the database.
    :return: True if they match, False otherwise.
    """
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

def create_access_token(data: dict) -> str:
    """
    Creates a JWT access token embedding the provided data.
    
    :param data: A dictionary of user-related data to encode into the token (e.g., user_id).
    :return: The generated JWT token as a string.
    """
    to_encode = data.copy()  # Copy the data to avoid mutating the original
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)  # Set token expiration time
    to_encode.update({"exp": expire})  # Add expiration information to the payload
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)  # Encode the payload with the secret and algorithm

def decode_token(token: str):
    """
    Decodes and verifies a JWT token.
    
    :param token: The JWT token string to decode.
    :return: The decoded payload if valid, or None if token is invalid/expired.
    """
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except:
        return None  # If decoding fails (invalid token, expired, wrong signature), return None
