
from getpass import getpass
from auth import login_user
from message_storage import save_message, get_recent_messages

print("=== SkillCircle Message Storage Test ===")

username = input("Enter your registered username: ")
password = getpass("Enter your password: ")

# Verify the user
login_result = login_user(username, password)

if not login_result["success"]:
    print("Login failed:", login_result["message"])
else:
    user_id = login_result["user_id"]

    # Save a test message
    result = save_message(
        user_id,
        username,
        "Hello everyone! This is my first saved SkillCircle message.",
        "A"
    )

    print("\nMessage saved successfully!")
    print("Message ID:", result["message_id"])

    # Retrieve previous messages
    messages = get_recent_messages()

    print("\n=== Retrieved Messages ===")

    for message in messages:
        print(
            message["username"],
            ":",
            message["message"]
        )

