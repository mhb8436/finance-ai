#!/usr/bin/env python3
"""Start FinanceAI backend and frontend servers."""

import os
import subprocess
import sys
import signal
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent


def load_env():
    """Load environment variables from .env file."""
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)


def start_backend():
    """Start the FastAPI backend server."""
    backend_port = os.getenv("BACKEND_PORT", "8001")

    return subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "src.api.main:app",
            "--host", "0.0.0.0",
            "--port", backend_port,
            "--reload",
        ],
        cwd=PROJECT_ROOT,
    )


def start_frontend():
    """Start the Next.js frontend server."""
    frontend_port = os.getenv("FRONTEND_PORT", "3000")
    web_dir = PROJECT_ROOT / "web"

    # Check if node_modules exists
    if not (web_dir / "node_modules").exists():
        print("Installing frontend dependencies...")
        subprocess.run(["npm", "install"], cwd=web_dir, check=True)

    return subprocess.Popen(
        ["npm", "run", "dev", "--", "-p", frontend_port],
        cwd=web_dir,
    )


def main():
    """Main entry point."""
    load_env()

    processes = []

    def cleanup(signum=None, frame=None):
        """Clean up processes on exit."""
        print("\nShutting down...")
        for proc in processes:
            if proc.poll() is None:
                proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    print("Starting FinanceAI...")
    print(f"Backend: http://localhost:{os.getenv('BACKEND_PORT', '8001')}")
    print(f"Frontend: http://localhost:{os.getenv('FRONTEND_PORT', '3000')}")
    print("Press Ctrl+C to stop\n")

    # Start servers
    backend = start_backend()
    processes.append(backend)

    frontend = start_frontend()
    processes.append(frontend)

    # Wait for processes
    try:
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
