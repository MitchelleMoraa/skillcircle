import socket
import threading
import json
import sys
from datetime import datetime


# ==========================================
# SERVER CONFIGURATION
# ==========================================

HOST = "0.0.0.0"

SERVER_1_CLIENT_PORT = 9001
SERVER_2_CLIENT_PORT = 9002

SERVER_1_PEER_PORT = 9101

PEER_HOST = "127.0.0.1"


# ==========================================
# SERVER CLASS
# ==========================================

class ChatServer:

    def __init__(self, server_number):

        self.server_number = server_number

        self.clients = []

        self.clients_lock = threading.Lock()

        self.peer_socket = None

        self.peer_lock = threading.Lock()

        if server_number == 1:

            self.client_port = SERVER_1_CLIENT_PORT

        elif server_number == 2:

            self.client_port = SERVER_2_CLIENT_PORT

        else:

            raise ValueError("Server number must be 1 or 2")

        print(f"SERVER {server_number} INITIALIZED")


    # ======================================
    # START SERVER
    # ======================================

    def start(self):

        print(f"\nStarting Server {self.server_number}...")

        # Start client connection listener

        client_thread = threading.Thread(
            target=self.accept_clients,
            daemon=True
        )

        client_thread.start()


        # Server 1 listens for Server 2

        if self.server_number == 1:

            peer_thread = threading.Thread(
                target=self.accept_peer,
                daemon=True
            )

            peer_thread.start()


        # Server 2 connects to Server 1

        elif self.server_number == 2:

            peer_thread = threading.Thread(
                target=self.connect_to_peer,
                daemon=True
            )

            peer_thread.start()


        print(f"Server {self.server_number} is running!")

        print(f"Client Port: {self.client_port}")

        while True:

            threading.Event().wait(1)


    # ======================================
    # ACCEPT CLIENT CONNECTIONS
    # ======================================

    def accept_clients(self):

        server = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        server.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

        server.bind((HOST, self.client_port))

        server.listen()

        print(
            f"Server {self.server_number} "
            f"is waiting for clients..."
        )


        while True:

            client_socket, address = server.accept()

            print(f"New client connected: {address}")

            with self.clients_lock:

                self.clients.append(client_socket)


            threading.Thread(
                target=self.handle_client,
                args=(client_socket,),
                daemon=True
            ).start()


    # ======================================
    # HANDLE CLIENT MESSAGES
    # ======================================

    def handle_client(self, client_socket):

        buffer = b""

        try:

            while True:

                data = client_socket.recv(4096)

                if not data:

                    break

                buffer += data

                while b"\n" in buffer:

                    line, buffer = buffer.split(b"\n", 1)

                    if not line.strip():

                        continue

                    message = json.loads(line.decode("utf-8"))

                    if message.get("type") == "chat":

                        message["server"] = self.server_number

                        message["timestamp"] = datetime.now().strftime(
                            "%H:%M:%S"
                        )

                        print(
                            f"Message received: "
                            f"{message['username']}: "
                            f"{message['message']}"
                        )

                        # Broadcast locally

                        self.broadcast_local(message)

                        # Relay to the other server

                        self.send_to_peer(message)


        except (ConnectionError, OSError, json.JSONDecodeError):

            pass


        finally:

            with self.clients_lock:

                if client_socket in self.clients:

                    self.clients.remove(client_socket)

            client_socket.close()

            print("A client disconnected.")


    # ======================================
    # BROADCAST TO LOCAL CLIENTS
    # ======================================

    def broadcast_local(self, message):

        encoded_message = (
            json.dumps(message) + "\n"
        ).encode("utf-8")


        with self.clients_lock:

            current_clients = list(self.clients)


        for client in current_clients:

            try:

                client.sendall(encoded_message)

            except OSError:

                with self.clients_lock:

                    if client in self.clients:

                        self.clients.remove(client)

                client.close()


    # ======================================
    # ACCEPT CONNECTION FROM SERVER 2
    # ======================================

    def accept_peer(self):

        peer_server = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        peer_server.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

        peer_server.bind(
            (HOST, SERVER_1_PEER_PORT)
        )

        peer_server.listen()

        print("Waiting for Server 2 connection...")


        while True:

            peer_socket, address = peer_server.accept()

            print("Server 2 connected:", address)

            with self.peer_lock:

                self.peer_socket = peer_socket


            threading.Thread(
                target=self.handle_peer,
                args=(peer_socket,),
                daemon=True
            ).start()


    # ======================================
    # CONNECT SERVER 2 TO SERVER 1
    # ======================================

    def connect_to_peer(self):

        while True:

            with self.peer_lock:

                connected = self.peer_socket is not None


            if connected:

                threading.Event().wait(2)

                continue


            peer_socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )

            try:

                peer_socket.connect(
                    (PEER_HOST, SERVER_1_PEER_PORT)
                )

                with self.peer_lock:

                    self.peer_socket = peer_socket


                print("Successfully connected to Server 1!")

                threading.Thread(
                    target=self.handle_peer,
                    args=(peer_socket,),
                    daemon=True
                ).start()


            except OSError:

                peer_socket.close()

                print("Waiting to connect to Server 1...")

                threading.Event().wait(3)


    # ======================================
    # RECEIVE MESSAGES FROM OTHER SERVER
    # ======================================

    def handle_peer(self, peer_socket):

        buffer = b""

        try:

            while True:

                data = peer_socket.recv(4096)

                if not data:

                    break

                buffer += data

                while b"\n" in buffer:

                    line, buffer = buffer.split(b"\n", 1)

                    if not line.strip():

                        continue

                    message = json.loads(line.decode("utf-8"))

                    print(
                        "Message received from another server:",
                        message["message"]
                    )

                    # Deliver to local clients only

                    self.broadcast_local(message)


        except (ConnectionError, OSError, json.JSONDecodeError):

            pass


        finally:

            with self.peer_lock:

                if self.peer_socket is peer_socket:

                    self.peer_socket = None

            peer_socket.close()

            print("Connection to the other server lost.")


    # ======================================
    # SEND MESSAGE TO OTHER SERVER
    # ======================================

    def send_to_peer(self, message):

        encoded_message = (
            json.dumps(message) + "\n"
        ).encode("utf-8")


        with self.peer_lock:

            peer = self.peer_socket

            if peer is None:

                print("Other server is not connected.")

                return

            try:

                peer.sendall(encoded_message)

            except OSError:

                self.peer_socket = None

                peer.close()

                print("Failed to send message to other server.")


# ==========================================
# RUN SERVER
# ==========================================

if __name__ == "__main__":

    if len(sys.argv) != 2:

        print("Usage: python server_node.py <1 or 2>")

        sys.exit(1)


    server_number = int(sys.argv[1])

    chat_server = ChatServer(server_number)

    chat_server.start()