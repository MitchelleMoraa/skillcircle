import os
import psycopg2


# Connect to PostgreSQL
def get_connection():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise Exception("DATABASE_URL is not configured.")

    return psycopg2.connect(database_url)


# Save a chat message
def save_message(sender_id, sender_username, message, server):

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO messages (
                    sender_id,
                    sender_username,
                    message,
                    server
                )
                VALUES (%s, %s, %s, %s)
                RETURNING message_id, timestamp;
                """,
                (sender_id, sender_username, message, server)
            )

            saved_message = cursor.fetchone()

        connection.commit()

        return {
            "success": True,
            "message_id": saved_message[0],
            "timestamp": saved_message[1].isoformat()
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# Retrieve previous chat messages
def get_recent_messages(limit=50):

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    message_id,
                    sender_id,
                    sender_username,
                    message,
                    server,
                    timestamp
                FROM messages
                ORDER BY timestamp DESC, message_id DESC
                LIMIT %s;
                """,
                (limit,)
            )

            messages = cursor.fetchall()

        # Reverse them so the oldest appears first
        messages.reverse()

        return [
            {
                "message_id": row[0],
                "sender_id": row[1],
                "username": row[2],
                "message": row[3],
                "server": row[4],
                "timestamp": row[5].isoformat()
            }
            for row in messages
        ]

    finally:
        connection.close()