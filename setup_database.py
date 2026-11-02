
import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("Database URL not found.")
    exit()

try:
    connection = psycopg2.connect(DATABASE_URL)
    cursor = connection.cursor()

    # Table for registered users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Table for saved chat messages
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            message_id BIGSERIAL PRIMARY KEY,
            sender_id INTEGER REFERENCES users(user_id)
                ON DELETE SET NULL,
            sender_username VARCHAR(50) NOT NULL,
            message TEXT NOT NULL,
            server VARCHAR(10),
            timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
    """)

    connection.commit()

    print("Users table created successfully!")
    print("Messages table created successfully!")

    cursor.close()
    connection.close()

except Exception as error:
    print("Database setup failed:")
    print(error)
    