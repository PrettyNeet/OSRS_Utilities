import types
import sys
import asyncio
import pytest

from unittest.mock import patch, MagicMock


# Top-level fake modules so imports of bot.utils succeed during pytest collection
def _inject_fake_modules():
    # Fake config.settings with HEADERS
    fake_settings = types.ModuleType('config.settings')
    fake_settings.HEADERS = {"User-Agent": "test-agent"}
    fake_settings.CACHE_TTL = 30
    sys.modules['config.settings'] = fake_settings

    # Fake yaml module used by logger (safe to be empty)
    sys.modules['yaml'] = types.ModuleType('yaml')

    # Fake discord and discord.ui to avoid requiring the real library in tests
    discord_mod = types.ModuleType('discord')
    discord_ui = types.ModuleType('discord.ui')

    class FakeView:
        def __init__(self, timeout=None):
            self.timeout = timeout
            self.children = []
        def add_item(self, item):
            self.children.append(item)

    class FakeButton:
        def __init__(self, style=None, label=None, custom_id=None):
            self.style = style
            self.label = label
            self.custom_id = custom_id

    class FakeButtonStyle:
        green = 1

    class FakeEmbed:
        def __init__(self, title=None, description=None, color=None):
            self.title = title
            self.description = description
            self.color = color
            self.fields = []
            self.timestamp = None
        def add_field(self, name, value, inline=True):
            self.fields.append((name, value, inline))
        def set_footer(self, text=None):
            self.footer = text

    class FakeColor:
        @staticmethod
        def green():
            return 0x00ff00
        @staticmethod
        def red():
            return 0xff0000

    discord_ui.View = FakeView
    discord_ui.Button = FakeButton
    discord_mod.ui = discord_ui
    discord_mod.ButtonStyle = FakeButtonStyle
    discord_mod.Embed = FakeEmbed
    discord_mod.Color = FakeColor
    sys.modules['discord'] = discord_mod
    sys.modules['discord.ui'] = discord_ui

    # Fake aiohttp for environments where aiohttp isn't installed (tests will patch ClientSession)
    aiohttp_mod = types.ModuleType('aiohttp')
    class FakeClientSession:
        def __init__(self, headers=None):
            self.headers = headers
        async def get(self, url):
            # Tests patch ClientSession.get, so this won't be called directly
            raise RuntimeError("FakeClientSession.get should be patched in tests")
        async def close(self):
            return
    aiohttp_mod.ClientSession = FakeClientSession
    sys.modules['aiohttp'] = aiohttp_mod

    # Fake aiosqlite for environments where aiosqlite isn't installed
    aiosqlite_mod = types.ModuleType('aiosqlite')
    class FakeAioConnection:
        async def execute(self, *args, **kwargs):
            return None
        async def commit(self):
            return None
        async def close(self):
            return None
        async def execute_fetchone(self, *args, **kwargs):
            return None
    aiosqlite_mod.connect = lambda path: FakeAioConnection()
    aiosqlite_mod.Connection = FakeAioConnection
    sys.modules['aiosqlite'] = aiosqlite_mod


_inject_fake_modules()


# Fixtures to inject fake modules used by the code under test (kept for completeness)
@pytest.fixture(autouse=True)
def fake_env_modules(monkeypatch):
    # Nothing to do here because modules are injected at import time
    yield


# Import modules under test after the fake modules are installed
from bot.utils import api as api_mod
from bot.utils import helpers as helpers_mod
from bot.utils import calculations as calc_mod
from bot.utils import formatting as fmt_mod
from bot.utils import DButil as dbmod
from bot.utils import logger as logmod
from bot.utils import views as views_mod


@pytest.fixture(autouse=True)
def clear_api_cache():
    # ensure the simple in-memory cache is cleared between tests
    try:
        api_mod._CACHE['latest']['data'] = None
        api_mod._CACHE['1h']['data'] = None
    except Exception:
        pass
    yield


def test_fetch_latest_prices_success(monkeypatch):
    # Mock async context manager behavior
    mock_get = MagicMock()
    mock_resp = MagicMock()

    async def mock_json():
        return {"data": {"1": {"high": 100}}}

    mock_resp.json = mock_json
    mock_get.__aenter__.return_value = mock_resp

    mock_session = MagicMock()
    mock_session.get.return_value = mock_get

    monkeypatch.setattr(api_mod.aiohttp, 'ClientSession', lambda *a, **k: mock_session)

    data = asyncio.get_event_loop().run_until_complete(api_mod.fetch_latest_prices(session=mock_session))
    assert '1' in data
    assert data['1']['high'] == 100


def test_fetch_latest_prices_failure(monkeypatch):
    mock_get = MagicMock()
    mock_resp = MagicMock()

    async def mock_json():
        return {"error": "no data"}

    mock_resp.json = mock_json
    mock_get.__aenter__.return_value = mock_resp

    mock_session = MagicMock()
    mock_session.get.return_value = mock_get

    monkeypatch.setattr(api_mod.aiohttp, 'ClientSession', lambda *a, **k: mock_session)

    with pytest.raises(ValueError):
        asyncio.get_event_loop().run_until_complete(api_mod.fetch_latest_prices(session=mock_session))


def test_fetch_1h_prices_success(monkeypatch):
    mock_get = MagicMock()
    mock_resp = MagicMock()

    async def mock_json():
        return {"data": {"2": {"avgHighPrice": 42}}}

    mock_resp.json = mock_json
    mock_get.__aenter__.return_value = mock_resp

    mock_session = MagicMock()
    mock_session.get.return_value = mock_get

    monkeypatch.setattr(api_mod.aiohttp, 'ClientSession', lambda *a, **k: mock_session)

    data = asyncio.get_event_loop().run_until_complete(api_mod.fetch_1h_prices(session=mock_session))
    assert '2' in data
    assert data['2']['avgHighPrice'] == 42


def test_skill_interp_bounds():
    v = helpers_mod.skill_interp(100, 200, 1)
    assert 0 <= v <= 1
    v2 = helpers_mod.skill_interp(100, 200, 99)
    assert 0 <= v2 <= 1


def test_generate_estimated_yield_error_case():
    res = helpers_mod.generate_estimated_yield(99, 0, 0, 3, 0, 0, 0)
    assert isinstance(res, (str, int, float))


def test_generate_estimated_yield_numeric():
    res = helpers_mod.generate_estimated_yield(50, 100, 200, 4, 0.1, 2, 0.05)
    assert isinstance(res, float)
    assert res > 0


def test_calculate_custom_profit_basic():
    prices = {
        "100": {"high": 10, "avgHighPrice": 9},
        "101": {"high": 100, "avgHighPrice": 95}
    }
    herbs = {
        "Guam": {"seed_id": 100, "herb_id": 101, "lowCTS": 100}
    }
    results = calc_mod.calculate_custom_profit(prices, herbs, farming_level=50, patches=1,
                                               weiss=False, trollheim=False, hosidius=False, fortis=False,
                                               compost='None', kandarin_diary='None', kourend=False,
                                               magic_secateurs=False, farming_cape=False, bottomless_bucket=False,
                                               attas=False, price_key='high')
    assert isinstance(results, list)


def test_format_profit_table_empty():
    table = helpers_mod.format_profit_table([])
    assert 'Herb | Seed Price | Grimy Herb Price' in table


def test_format_profit_table_rows():
    rows = [{"Herb": "Guam", "Seed Price": 10, "Grimy Herb Price": 100, "Potential Yield": 2, "Profit per Seed": 45, "Profit per Run": 90}]
    table = helpers_mod.format_profit_table(rows)
    assert 'Guam' in table
    assert '90' in table


@patch('bot.utils.DButil.sqlite3.connect')
@patch('bot.utils.DButil.os.makedirs')
def test_get_db_connection_and_initialize(mock_makedirs, mock_connect):
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    conn = dbmod.get_db_connection()
    assert conn is mock_conn

    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    dbmod.initialize_db()
    mock_conn.commit.assert_called()
    mock_conn.close.assert_called()


@patch('bot.utils.DButil.sqlite3.connect')
def test_add_predefined_weapons(mock_connect):
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    with patch('bot.utils.DButil.os.makedirs'):
        dbmod.add_predefined_weapons()
    mock_conn.commit.assert_called()
    mock_conn.close.assert_called()


@patch('bot.utils.logger.RotatingFileHandler')
@patch('bot.utils.logger.os.makedirs')
def test_setup_logging_creates_logger(mock_makedirs, mock_rotating):
    logger = logmod.setup_logging()
    assert logger is not None
    assert hasattr(logger, 'info')


def test_profit_view_initialization():
    async def dummy_cb():
        return {}

    view = views_mod.ProfitView(dummy_cb)
    assert view is not None
    assert len(view.children) >= 1
    # end of file - pytest will collect the tests above
