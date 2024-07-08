# utils/authentication.py
# Define users and passwords (for demonstration purposes, use a more secure method in production)
users = {
    "admin": "magnus_user",
    "user": "test_password"
}

# Function to check user credentials
def check_credentials(username, password):
    return users.get(username) == password