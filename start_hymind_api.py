import os
import subprocess
import time
import webbrowser

import requests
from dotenv import load_dotenv

load_dotenv()

NGROK_SKIP_HEADER = {"ngrok-skip-browser-warning": "true"}
API_KEY = os.getenv("HYMIND_API_KEY", "")

# ---------------------------------------------------------------------------
# Start FastAPI
# ---------------------------------------------------------------------------

subprocess.Popen(
    [
        "uvicorn",
        "src.api.server:app",
        "--host", "0.0.0.0",
        "--port", "8000",
    ]
)

print("Starting FastAPI server...")
time.sleep(5)

# ---------------------------------------------------------------------------
# Start ngrok with fixed domain
# ---------------------------------------------------------------------------

subprocess.Popen(["ngrok", "http", "--domain=take-jury-plot.ngrok-free.dev", "8000"])

print("Starting ngrok...")
time.sleep(5)

# ---------------------------------------------------------------------------
# Read ngrok tunnel URL
# ---------------------------------------------------------------------------

response = requests.get("http://127.0.0.1:4040/api/tunnels")
data = response.json()
public_url = data["tunnels"][0]["public_url"]
endpoint = f"{public_url}/run-hymind"
health_url = f"{public_url}/health"

# ---------------------------------------------------------------------------
# Health check — verifies ngrok forwards correctly, bypassing interstitial
# ---------------------------------------------------------------------------

print("\nVerifying tunnel...")
try:
    health = requests.get(health_url, headers=NGROK_SKIP_HEADER, timeout=10)
    if health.status_code == 200:
        print("Tunnel OK — FastAPI is reachable through ngrok.")
    else:
        print(f"Unexpected health status: {health.status_code}")
except Exception as exc:
    print(f"Health check failed: {exc}")

# ---------------------------------------------------------------------------
# Print n8n configuration
# ---------------------------------------------------------------------------

print("\n" + "=" * 60)
print("HYMIND API ready")
print("=" * 60)
print(f"\n  Endpoint : {endpoint}")
print(f"  Health   : {health_url}")
print(f"  Docs     : {public_url}/docs")
print("\n  Required headers for every n8n / HTTP request:")
print("    ngrok-skip-browser-warning : true")
if API_KEY:
    print("    x-api-key                  : <your HYMIND_API_KEY>")
else:
    print("    x-api-key                  : (not set — auth disabled)")
print("=" * 60 + "\n")

webbrowser.open(f"{public_url}/docs")
