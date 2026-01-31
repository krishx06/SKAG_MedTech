"""
AdaptiveCare Backend Runner
"""

import uvicorn
from backend.core.config import Config


def main():
    """Run the AdaptiveCare backend server."""
    uvicorn.run(
        "backend.api.main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG,
        log_level="info"
    )


if __name__ == "__main__":
    main()
