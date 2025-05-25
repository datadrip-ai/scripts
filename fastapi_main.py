import uvicorn
from fastapi import FastAPI
import logging
import os
from dotenv import load_dotenv
from colorama import init, Fore, Style
from typing import Union

# Initialize colorama for colored console output
init(autoreset=True)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        level = record.levelname
        msg = record.getMessage()
        if level == "ERROR":
            return f"{Fore.RED}{msg}{Style.RESET_ALL}"
        elif level == "WARNING":
            return f"{Fore.YELLOW}{msg}{Style.RESET_ALL}"
        elif level == "INFO":
            return f"{Fore.GREEN}{msg}{Style.RESET_ALL}"
        else:
            return f"{Fore.CYAN}{msg}{Style.RESET_ALL}"

# Update console handler with colored formatter
for handler in logger.handlers:
    if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
        handler.setFormatter(ColoredFormatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))

# Initialize FastAPI app
app = FastAPI(docs_url="/docs", redoc_url=None)  # Serve Swagger UI at /docs

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/api/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

if __name__ == "__main__":
    try:
        host = os.getenv("FASTAPI_HOST", "127.0.0.1")
        port = int(os.getenv("FASTAPI_PORT", 8000))
        logger.info(f"Starting FastAPI server on {host}:{port}")
        uvicorn.run(app, host=host, port=port)
    except Exception as e:
        logger.error(f"Failed to start FastAPI server: {str(e)}")
        raise