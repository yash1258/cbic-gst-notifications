"""
Robust API wrapper providing rate limiting, retries, and SSL bypass.
Specifically customized for the CBIC Tax Information Portal.
"""

import asyncio
import ssl
import logging
from datetime import datetime
from typing import Dict, Any, Optional

import aiohttp
from . import config

# Setup standard logger
logger = logging.getLogger(__name__)

class CbicApiClient:
    def __init__(self, concurrent_limit: int = config.MAX_CONCURRENT_REQUESTS):
        # The CBIC server uses a self-signed certificate, requiring bypass
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

        self.semaphore = asyncio.Semaphore(concurrent_limit)
        self.connector = aiohttp.TCPConnector(
            limit=concurrent_limit, 
            ssl=self.ssl_context
        )
        self.headers = {
            "User-Agent": "CBIC-Research-Scraper/2.0 (Legal Data Extraction; Modular Structure)",
            "Accept": "application/json",
        }
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(connector=self.connector, headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch_json(self, endpoint: str) -> Dict[str, Any]:
        """Fetch JSON data from API with exponential backoff retries."""
        url = f"{config.BASE_URL}{endpoint}"
        
        async with self.semaphore:
            for attempt in range(config.MAX_RETRIES):
                try:
                    async with self.session.get(
                        url, 
                        timeout=aiohttp.ClientTimeout(total=config.DEFAULT_REQUEST_TIMEOUT)
                    ) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 404:
                            return {"error": "not_found", "status": 404}
                        elif response.status in (429, 503, 500):
                            # Server overloaded or general error. Backoff and retry.
                            if attempt == config.MAX_RETRIES - 1:
                                return {"error": "max_retries", "status": response.status}
                            await asyncio.sleep(config.RETRY_BACKOFF_FACTOR ** (attempt + 1))
                            continue
                        else:
                            return {"error": f"http_{response.status}", "status": response.status}
                
                except asyncio.TimeoutError:
                    if attempt == config.MAX_RETRIES - 1:
                        return {"error": "timeout", "status": None}
                    await asyncio.sleep(config.RETRY_BACKOFF_FACTOR ** (attempt + 1))
                except Exception as e:
                    if attempt == config.MAX_RETRIES - 1:
                        return {"error": str(e)[:200], "status": None}
                    await asyncio.sleep(config.RETRY_BACKOFF_FACTOR ** (attempt + 1))
        
        return {"error": "unknown_failure", "status": None}

    def format_error_log(self, item_id: int, error_msg: str, status_code: Optional[int] = None) -> Dict[str, Any]:
        """Standardized parsing of error output."""
        return {
            "id": item_id,
            "status": status_code,
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }
