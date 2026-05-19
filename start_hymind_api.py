# scripts/start_hymind_api.py

import subprocess
import time
import requests
import webbrowser

# Start FastAPI
subprocess.Popen(
    [
        "uvicorn",
        "src.hymind.api.server:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
    ]
)

print("Starting FastAPI server...")
time.sleep(5)

# Start ngrok
subprocess.Popen(["ngrok", "http", "8000"])

print("Starting ngrok...")
time.sleep(5)

# Read ngrok public URL
response = requests.get("http://127.0.0.1:4040/api/tunnels")
data = response.json()

public_url = data["tunnels"][0]["public_url"]
endpoint = f"{public_url}/run-hymind"

print("\nHYMIND Public Endpoint:")
print(endpoint)

print("\nSwagger Docs:")
print(f"{public_url}/docs")

# Optional
webbrowser.open(f"{public_url}/docs")