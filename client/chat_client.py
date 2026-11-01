import socket
import threading
import json


class ChatClient:

    def __init__(self, username, host, port,
                 on_message, on_disconnect):

        self.username = username
        self.host = host
        self.port = port

        self.on_message = on_message
        self.on_disconnect = on_disconnect

        self.client_socket = None

        self.connected = False

        self.stop_event = threading.Event()

        self.send_lock = threading.Lock()


    # =====================================
    # CONNECT TO SERVER
    # =====================================

    def connect(self):

        self.client_socket = socket.create_connection(
            (self.host, self.port),
            timeout=5
        )

        self.client_socket.settimeout(None)

        self.connected = True

        print(f"{self.username} connected successfully.")


        # Start receiving messages in another thread

        receive_thread = threading.Thread(
            target=self.receive_messages,
            daemon=True
        )

        receive_thread.start()


    # =====================================
    # SEND MESSAGE
    # =====================================

    def send_message(self, message):

        if not self.connected:

            raise ConnectionError("Not connected to server.")


        data = {

            "type": "chat",

            "username": self.username,

            "message": message

        }


        encoded_message = (
            json.dumps(data) + "\n"
        ).encode("utf-8")


        with self.send_lock:

            self.client_socket.sendall(encoded_message)


    # =====================================
    # RECEIVE MESSAGES
    # =====================================

    def receive_messages(self):

        buffer = b""

        try:

            while not self.stop_event.is_set():

                data = self.client_socket.recv(4096)

                if not data:

                    break


                buffer += data


                while b"\n" in buffer:

                    line, buffer = buffer.split(b"\n", 1)

                    if not line.strip():

                        continue


                    message = json.loads(
                        line.decode("utf-8")
                    )


                    self.on_message(message)


        except (ConnectionError, OSError, json.JSONDecodeError):

            pass


        finally:

            was_connected = self.connected

            self.connected = False

            self.stop_event.set()

            if self.client_socket:

                self.client_socket.close()


            if was_connected:

                self.on_disconnect(
                    "Connection to the server was lost."
                )


    # =====================================
    # DISCONNECT
    # =====================================

    def disconnect(self):

        self.stop_event.set()

        self.connected = False

        if self.client_socket:

            try:

                self.client_socket.shutdown(
                    socket.SHUT_RDWR
                )

            except OSError:

                pass


            try:

                self.client_socket.close()

            except OSError:

                pass


        print(f"{self.username} disconnected.")