import subprocess
import sys
import time
import os

# Get the main project directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

processes = []


def start_process(command):
    process = subprocess.Popen(
        command,
        cwd=BASE_DIR
    )

    processes.append(process)

    return process


try:
    print("Starting SkillCircle distributed chat system...")

    # Start Server A
    print("Starting Server A...")

    server_a = start_process([
        sys.executable,
        os.path.join(BASE_DIR, "server", "server_node.py"),
        "1"
    ])

    time.sleep(2)

    # Start Server B
    print("Starting Server B...")

    server_b = start_process([
        sys.executable,
        os.path.join(BASE_DIR, "server", "server_node.py"),
        "2"
    ])

    time.sleep(3)

    # Start WebSocket Bridge
    print("Starting WebSocket Bridge...")

    bridge = start_process([
        sys.executable,
        os.path.join(BASE_DIR, "bridge", "websocket_bridge.py")
    ])

    # Keep the main process alive
    while True:

        for process in processes:

            if process.poll() is not None:
                raise RuntimeError(
                    "A SkillCircle service stopped unexpectedly."
                )

        time.sleep(2)


except KeyboardInterrupt:
    print("Stopping SkillCircle...")

except Exception as error:
    print("Deployment error:", error)

finally:

    for process in processes:

        if process.poll() is None:
            process.terminate()

    for process in processes:

        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()