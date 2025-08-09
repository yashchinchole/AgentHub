import asyncio
import sys
import os

import uvicorn
from dotenv import load_dotenv

from core import settings

load_dotenv()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    port = int(os.environ.get("PORT", settings.PORT))

    uvicorn.run(
        "service:app",
        host="0.0.0.0",
        port=port,
        reload=settings.is_dev()
    )
