import jwt
import bcrypt
import mysql.connector
from datetime import datetime, timedelta

# Configuration
SECRET_KEY = "ef40068e182adf23fdbd8d03e538d6afd946b92806ddae7a3ea7d8587cc2062b"
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "sihredact"
}

# Connect to the database
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# Login function
def login_user(email, password):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    conn.close()

    if user and bcrypt.checkpw(password.encode(), user["password"].encode()):
        # Generate JWT
        payload = {
            "user_id": user["id"],
            "email": user["email"],
            "exp": datetime.utcnow() + timedelta(days=7)  # Token valid for 7 days
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return {"status": "success", "token": token}

    return {"status": "error", "message": "Invalid email or password"}

# Register function
def register_user(email, password):
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, hashed_password))
        conn.commit()
        return {"status": "success", "message": "User registered successfully"}
    except mysql.connector.Error as err:
        return {"status": "error", "message": str(err)}
    finally:
        conn.close()

# Decode JWT
def decode_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return {"status": "error", "message": "Token expired"}
    except jwt.InvalidTokenError:
        return {"status": "error", "message": "Invalid token"}
