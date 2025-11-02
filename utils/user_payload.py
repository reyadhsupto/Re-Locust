# utils/user_payload.py

# Generates new user payload for PetStore API
# You can extend this to generate random users
def new_user_payload():
    return {
        "username": "reyadhassan",
        "firstName": "Reyad",
        "lastName": "Hassan",
        "email": "reyad@pathao.com",
        "password": "123456",
        "phone": "01843547674",
        "userStatus": 1
    }
