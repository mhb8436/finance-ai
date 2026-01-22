#!/usr/bin/env python3
"""Run the FastAPI backend server only."""

import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main():
    """Start the backend server."""
    # Load environment
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")

    import uvicorn

    port = int(os.getenv("BACKEND_PORT", "8001"))

    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )


if __name__ == "__main__":
    main()
