r"""Convenience script to start the HYMIND FastAPI server with uvicorn.

Usage:
    C:\Users\nest\.conda\envs\hymind\python.exe scripts/run_api.py

Or directly with uvicorn:
    uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload

Then expose to n8n via ngrok (fixed domain):
    ngrok http --domain=take-jury-plot.ngrok-free.dev 8000
"""

import subprocess
import sys

if __name__ == "__main__":
    subprocess.run(
        [
            sys.executable, "-m", "uvicorn",
            "src.api.server:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
        ],
        check=True,
    )
