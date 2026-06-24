import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
from admin.app import app
from admin.config import AdminConfig

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

logging.getLogger("uvicorn").setLevel(logging.CRITICAL)
logging.getLogger("uvicorn.access").setLevel(logging.CRITICAL)
logging.getLogger("fastapi").setLevel(logging.CRITICAL)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=AdminConfig.HOST,
        port=AdminConfig.PORT,
        log_level="error",
    )
