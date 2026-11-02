import asyncio
import json
import sys
import os
import websockets

PROJECT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_PATH)

from client.chat_client import ChatClient
from auth import register_user, login_user, get_connection
from message_storage import save_message, get_recent_messages

SERVERS = {"A": 9001, "B": 9002}
active_clients = set()


def get_group_members():
    """Return every registered username from PostgreSQL."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT username FROM users ORDER BY username ASC")
        rows = cursor.fetchall()
        cursor.close()
        return [{"username": row[0]} for row in rows]
    finally:
        connection.close()


async def send_group_members(websocket):
    await websocket.send(json.dumps({
        "type": "group_members",
        "members": get_group_members()
    }))


async def broadcast_group_members():
    """Refresh the member list for everyone currently in the chat."""
    payload = json.dumps({
        "type": "group_members",
        "members": get_group_members()
    })
    disconnected = []
    for client in list(active_clients):
        try:
            await client.send(payload)
        except websockets.exceptions.ConnectionClosed:
            disconnected.append(client)
    for client in disconnected:
        active_clients.discard(client)


async def handle_connection(websocket):
    loop = asyncio.get_running_loop()
    chat_client = None
    user_id = None
    username = None
    selected_server = None

    def on_message(message):
        asyncio.run_coroutine_threadsafe(
            websocket.send(json.dumps(message)), loop
        )

    def on_disconnect(reason):
        asyncio.run_coroutine_threadsafe(
            websocket.send(json.dumps({
                "type": "disconnect",
                "message": reason
            })), loop
        )

    try:
        async for raw_message in websocket:
            data = json.loads(raw_message)
            message_type = data.get("type")

            # USER REGISTRATION
            if message_type == "register":
                result = register_user(
                    data.get("username", ""),
                    data.get("password", "")
                )
                await websocket.send(json.dumps({
                    "type": "register_result",
                    **result
                }))
                if result.get("success"):
                    await broadcast_group_members()

            # USER LOGIN
            elif message_type == "login":
                if chat_client is not None:
                    raise ValueError("Already connected.")

                result = login_user(
                    data.get("username", ""),
                    data.get("password", "")
                )
                if not result.get("success"):
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": result.get("message", "Login failed.")
                    }))
                    continue

                username = result["username"]
                user_id = result["user_id"]
                selected_server = data.get("server")
                if selected_server not in SERVERS:
                    raise ValueError("Invalid server selected.")

                chat_client = ChatClient(
                    username=username,
                    host="127.0.0.1",
                    port=SERVERS[selected_server],
                    on_message=on_message,
                    on_disconnect=on_disconnect
                )
                chat_client.connect()
                active_clients.add(websocket)

                await websocket.send(json.dumps({
                    "type": "history",
                    "messages": get_recent_messages(50)
                }))
                await send_group_members(websocket)
                await websocket.send(json.dumps({
                    "type": "connected",
                    "username": username,
                    "server": selected_server,
                    "message": "Successfully connected!"
                }))
                print(f"{username} logged in through Server {selected_server}")

            # USER SENDS A CHAT MESSAGE
            elif message_type == "message":
                if chat_client is None or user_id is None:
                    raise ValueError("Please log in first.")
                message_text = data.get("message", "").strip()
                if not message_text:
                    continue
                save_message(user_id, username, message_text, selected_server)
                chat_client.send_message(message_text)

    except websockets.exceptions.ConnectionClosed:
        print("Browser connection closed.")
    except Exception as error:
        try:
            await websocket.send(json.dumps({
                "type": "error",
                "message": str(error)
            }))
        except websockets.exceptions.ConnectionClosed:
            pass
        print("Bridge error:", error)
    finally:
        active_clients.discard(websocket)
        if chat_client is not None:
            chat_client.disconnect()
        print("User disconnected.")


async def main():
    port = int(os.environ.get("PORT", "8765"))
    print("SkillCircle WebSocket Bridge is running...")
    print(f"Listening on port: {port}")
    async with websockets.serve(handle_connection, "0.0.0.0", port):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
