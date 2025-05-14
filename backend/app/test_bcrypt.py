from passlib.hash import bcrypt

password = "testpassword"
hashed = bcrypt.hash(password)
print(f"Hashed password: {hashed}")