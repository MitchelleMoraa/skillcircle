
from getpass import getpass
from auth import register_user, login_user

print("=== SkillCircle Authentication Test ===")

username = input("Enter a test username: ")
password = getpass("Create a password (minimum 8 characters): ")

# Test registration
result = register_user(username, password)
print("\nRegistration:", result["message"])

if result["success"]:
    # Test login
    login_result = login_user(username, password)
    print("Login:", login_result["message"])

    # Test incorrect password
    wrong_login = login_user(username, "wrongpassword123")
    print("Incorrect password test:", wrong_login["message"])

else:
    print("Registration was unsuccessful. Try another username if it already exists.")