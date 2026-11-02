
import os
import psycopg2

# Read the database URL securely from an environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("Database URL was not found.")
else:
    try:
        connection = psycopg2.connect(DATABASE_URL)

        print("Successfully connected to PostgreSQL!")

        cursor = connection.cursor()
        cursor.execute("SELECT version();")

        result = cursor.fetchone()
        print("PostgreSQL version:")
        print(result[0])

        cursor.close()
        connection.close()

        print("Database connection closed successfully.")

    except Exception as error:
        print("Database connection failed.")
        print(error)