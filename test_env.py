import os
from dotenv import load_dotenv
import dotenv

# Print the current directory
print(f"Current working directory: {os.getcwd()}")

# Check if .env file exists in different locations
current_dir_env = os.path.join(os.getcwd(), ".env")
parent_dir_env = os.path.join(os.getcwd(), "..", ".env")

print(f".env file in current dir exists: {os.path.exists(current_dir_env)}")
print(f".env file in parent dir exists: {os.path.exists(parent_dir_env)}")

# Try to load it explicitly
print("Attempting to load .env file...")
dotenv.load_dotenv(dotenv_path=current_dir_env, verbose=True)

# Check if variables are loaded
print(f"EBAY_APP_ID: {os.getenv('EBAY_APP_ID')}")
print(f"EBAY_CERT_ID: {os.getenv('EBAY_CERT_ID')}")

# Try to look at the contents of the .env file
if os.path.exists(current_dir_env):
    print("\nFirst 100 characters of .env file:")
    with open(current_dir_env, 'r') as f:
        print(f.read(100))