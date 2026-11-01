import asyncio
import json
import sys
import os
import websockets

# Allow Python to find the existing client folder
PROJECT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_PATH)

from client.chat_client import ChatClient


# Existing Python server client ports
SERVERS = {
    "A": 9001,
    "B": 9002
}


async def handle_connection(websocket):

    loop = asyncio.get_running_loop()

    chat_client = None

    # Send data from Python's receiving thread to React
    def on_message(message):

        asyncio.run_coroutine_threadsafe(
            websocket.send(json.dumps(message)),
            loop
        )

    # Handle Python server disconnection
    def on_disconnect(reason):

        asyncio.run_coroutine_threadsafe(
            websocket.send(json.dumps({
                "type": "disconnect",
                "message": reason
            })),
            loop
        )

    try:

        async for raw_message in websocket:

            data = json.loads(raw_message)

            # USER CONNECTS
            if data["type"] == "connect":

                username = data["username"]
                selected_server = data["server"]

                if selected_server not in SERVERS:
                    raise ValueError("Invalid server selected.")

                if chat_client is not None:
                    raise ValueError("Already connected.")

                port = SERVERS[selected_server]

                chat_client = ChatClient(
                    username=username,
                    host="127.0.0.1",
                    port=port,
                    on_message=on_message,
                    on_disconnect=on_disconnect
                )

                chat_client.connect()

                await websocket.send(json.dumps({
                    "type": "connected",
                    "username": username,
                    "server": selected_server,
                    "message": "Successfully connected!"
                }))

                print(
                    f"{username} connected through Server "
                    f"{selected_server}"
                )

            # USER SENDS A CHAT MESSAGE
            elif data["type"] == "message":

                if chat_client is None:
                    raise ValueError("Connect before sending messages.")

                chat_client.send_message(data["message"])

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

        if chat_client is not None:
            chat_client.disconnect()

        print("User disconnected.")


async def main():
    port = int(os.environ.get("PORT", "8765"))

    print("SkillCircle WebSocket Bridge is running...")
    print(f"Listening on port: {port}")

    async with websockets.serve(
        handle_connection,
        "0.0.0.0",
        port
    ):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())