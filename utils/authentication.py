# utils/authentication.py
# Define users and passwords (for demonstration purposes, use a more secure method in production)
users = {
    "admin": "password123",
    "user": "123",
    "u": "p"
}

# Function to check user credentials
def check_credentials(username, password):
    return users.get(username) == password