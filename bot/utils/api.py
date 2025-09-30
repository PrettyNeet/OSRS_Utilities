import aiohttp
import asyncio
# Import HEADERS and CACHE_TTL from settings
from config.settings import HEADERS, CACHE_TTL

# Simple in-memory TTL cache
_CACHE = {
    'latest': {'ts': 0, 'data': None},
    '1h': {'ts': 0, 'data': None}
}
_CACHE_TTL = CACHE_TTL


# Asynchronous fetchers using aiohttp. Accept an optional session for reuse.
async def fetch_latest_prices(session: aiohttp.ClientSession | None = None):
    # Check cache
    now = asyncio.get_event_loop().time()
    if _CACHE['latest']['data'] is not None and (now - _CACHE['latest']['ts']) < _CACHE_TTL:
        return _CACHE['latest']['data']
    url = "https://prices.runescape.wiki/api/v1/osrs/latest"
    close_session = False
    if session is None:
        session = aiohttp.ClientSession(headers=HEADERS)
        close_session = True

    try:
        async with session.get(url) as resp:
            data = await resp.json()
    except asyncio.CancelledError:
        raise
    finally:
        if close_session:
            await session.close()

    if "data" not in data:
        raise ValueError("Error fetching data from API")
    _CACHE['latest']['ts'] = asyncio.get_event_loop().time()
    _CACHE['latest']['data'] = data["data"]
    return data["data"]


async def fetch_1h_prices(session: aiohttp.ClientSession | None = None):
    # Check cache
    now = asyncio.get_event_loop().time()
    if _CACHE['1h']['data'] is not None and (now - _CACHE['1h']['ts']) < _CACHE_TTL:
        return _CACHE['1h']['data']
    url = "https://prices.runescape.wiki/api/v1/osrs/1h"
    close_session = False
    if session is None:
        session = aiohttp.ClientSession(headers=HEADERS)
        close_session = True

    try:
        async with session.get(url) as resp:
            data = await resp.json()
    except asyncio.CancelledError:
        raise
    finally:
        if close_session:
            await session.close()

    if "data" not in data:
        raise ValueError("Error fetching data from API")
    _CACHE['1h']['ts'] = asyncio.get_event_loop().time()
    _CACHE['1h']['data'] = data["data"]
    return data["data"]