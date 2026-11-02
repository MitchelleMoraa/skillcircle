import os
import psycopg2
import bcrypt


# Connect to PostgreSQL
def get_connection():
    from urllib.parse import urlparse, unquote

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise Exception("DATABASE_URL is not configured.")

    parsed = urlparse(database_url)

    return psycopg2.connect(
        dbname=parsed.path.lstrip("/"),
        user=unquote(parsed.username),
        password=unquote(parsed.password),
        host=parsed.hostname,
        port=parsed.port or 5432,
        sslmode="require"
    )


# Register a new user
def register_user(username, password):

    username = username.strip()

    # Validate username
    if not username:
        return {
            "success": False,
            "message": "Username cannot be empty."
        }

    if len(username) > 50:
        return {
            "success": False,
            "message": "Username must not exceed 50 characters."
        }

    # Validate password
    if not password:
        return {
            "success": False,
            "message": "Password cannot be empty."
        }

    if len(password) < 8:
        return {
            "success": False,
            "message": "Password must be at least 8 characters."
        }

    # Hash the password before storing it
    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    INSERT INTO users (username, password_hash)
                    VALUES (%s, %s)
                    RETURNING user_id, username;
                    """,
                    (username, password_hash)
                )

                user = cursor.fetchone()

        return {
            "success": True,
            "message": "Account created successfully.",
            "user_id": user[0],
            "username": user[1]
        }

    except psycopg2.errors.UniqueViolation:
        return {
            "success": False,
            "message": "Username is already taken."
        }

    except Exception:
        return {
            "success": False,
            "message": "Registration failed. Please try again."
        }


# Login an existing user
def login_user(username, password):

    username = username.strip()

    if not username or not password:
        return {
            "success": False,
            "message": "Please enter your username and password."
        }

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT user_id, username, password_hash
                    FROM users
                    WHERE username = %s;
                    """,
                    (username,)
                )

                user = cursor.fetchone()

        # Check whether the username exists
        if user is None:
            return {
                "success": False,
                "message": "Invalid username or password."
            }

        user_id, stored_username, password_hash = user

        # Verify the password
        password_matches = bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8")
        )

        if password_matches:
            return {
                "success": True,
                "message": "Login successful.",
                "user_id": user_id,
                "username": stored_username
            }

        return {
            "success": False,
            "message": "Invalid username or password."
        }

    except Exception:
        return {
            "success": False,
            "message": "Login failed. Please try again."
        }