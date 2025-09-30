import types
import sys
from unittest.mock import MagicMock, AsyncMock
import pytest


# Inject top-level fake modules used by the application so tests can import command modules
def _inject_fake_modules():
    # Fake config.settings
    fake_settings = types.ModuleType('config.settings')
    fake_settings.HEADERS = {"User-Agent": "test-agent"}
    fake_settings.CACHE_TTL = 30
    sys.modules['config.settings'] = fake_settings

    # yaml (used by logger)
    sys.modules['yaml'] = types.ModuleType('yaml')

    # Minimal fake discord module and subpackages
    discord_mod = types.ModuleType('discord')
    discord_ext = types.ModuleType('discord.ext')
    discord_ext_commands = types.ModuleType('discord.ext.commands')
    discord_app = types.ModuleType('discord.app_commands')
    discord_ui = types.ModuleType('discord.ui')

    # Provide minimal classes/attributes used by the code under test
    class FakeView:
        pass

    class FakeEmbed:
        def __init__(self, title=None, color=None):
            self.title = title
            self.color = color
            self.fields = []
        def add_field(self, name, value, inline=False):
            self.fields.append((name, value, inline))
        def set_author(self, name=None, icon_url=None):
            self.author = (name, icon_url)

    class FakeColor:
        @staticmethod
        def green():
            return 0

    discord_ui.View = FakeView
    discord_mod.Embed = FakeEmbed
    discord_mod.Color = FakeColor

    # Minimal SelectOption and select decorator used in the command class definition
    class SelectOption:
        def __init__(self, label=None, value=None):
            self.label = label
            self.value = value

    def select_decorator(*d_args, **d_kwargs):
        def _decorator(func):
            return func
        return _decorator

    discord_ui.SelectOption = SelectOption
    discord_ui.select = select_decorator
    # Expose SelectOption at top-level discord module as well
    discord_mod.SelectOption = SelectOption
    # Minimal Interaction class used as type hint/reference in command definitions
    class Interaction:
        pass
    discord_mod.Interaction = Interaction

    # minimal nested modules
    discord_mod.ext = discord_ext
    discord_ext.commands = discord_ext_commands
    discord_mod.app_commands = discord_app

    # Minimal commands.Cog base class
    class Cog:
        def __init__(self, *args, **kwargs):
            pass
    discord_ext_commands.Cog = Cog

    # Minimal app_commands decorators and Choice class
    def _passthrough_decorator(*d_args, **d_kwargs):
        # Support both @decorator and @decorator(...)
        if len(d_args) == 1 and callable(d_args[0]) and not d_kwargs:
            return d_args[0]
        def _inner(func):
            return func
        return _inner

    discord_app.command = _passthrough_decorator
    discord_app.describe = _passthrough_decorator
    discord_app.choices = lambda **k: _passthrough_decorator

    class AppChoice:
        def __init__(self, name=None, value=None):
            self.name = name
            self.value = value
        @classmethod
        def __class_getitem__(cls, item):
            return cls

    discord_app.Choice = AppChoice

    # expose ui submodule on discord_mod
    discord_mod.ui = discord_ui

    sys.modules['discord'] = discord_mod
    sys.modules['discord.ext'] = discord_ext
    sys.modules['discord.ext.commands'] = discord_ext_commands
    sys.modules['discord.app_commands'] = discord_app
    sys.modules['discord.ui'] = discord_ui

    # Fake aiohttp and aiosqlite modules to avoid import errors
    aiohttp_mod = types.ModuleType('aiohttp')
    class FakeClientSession:
        def __init__(self, *a, **k):
            pass
        async def get(self, *a, **k):
            class Resp:
                async def json(self):
                    return {}
                async def __aenter__(self):
                    return self
                async def __aexit__(self, exc_type, exc, tb):
                    return False
            return Resp()
        async def close(self):
            return
    aiohttp_mod.ClientSession = FakeClientSession
    sys.modules['aiohttp'] = aiohttp_mod
    sys.modules['aiosqlite'] = types.ModuleType('aiosqlite')


_inject_fake_modules()



@pytest.fixture
def sample_prices():
    return {
        "100": {"high": 10, "avgHighPrice": 9},
        "101": {"high": 100, "avgHighPrice": 95}
    }


@pytest.fixture
def sample_herbs(monkeypatch):
    # Provide a minimal herbs mapping and monkeypatch data.items.herbs if needed
    herbs = {"Guam": {"seed_id": 100, "herb_id": 101, "lowCTS": 100}}
    monkeypatch.setitem(sys.modules, 'data.items', types.ModuleType('data.items'))
    sys.modules['data.items'].herbs = herbs
    return herbs


@pytest.fixture
def fake_user():
    user = MagicMock()
    user.id = 12345
    user.mention = '@tester'
    user.display_name = 'Tester'
    # Simple object to mimic display_avatar with url attribute
    avatar = types.SimpleNamespace(url='http://avatar.url')
    user.display_avatar = avatar
    return user


@pytest.fixture
def fake_interaction(fake_user):
    inter = MagicMock()
    inter.user = fake_user
    # response.send_message and followup.send are coroutines in real discord.
    # Use AsyncMock so tests can await them and still use assert_called()/assert_awaited()
    inter.response = MagicMock()
    inter.response.send_message = AsyncMock()
    inter.response.defer = AsyncMock()
    inter.followup = MagicMock()
    inter.followup.send = AsyncMock()
    # allow setting .data for select callback tests
    inter.data = {}
    return inter


@pytest.fixture
def async_fetch_latest_prices(monkeypatch, sample_prices):
    async def _fake(session=None):
        return sample_prices
    monkeypatch.setattr('bot.commands.herb_profit.fetch_latest_prices', _fake)
    monkeypatch.setattr('bot.commands.herb_profit.fetch_1h_prices', _fake)
    return _fake


@pytest.fixture
def stub_calculate_custom_profit(monkeypatch):
    def _stub(prices, herbs, *args, **kwargs):
        return [{"Herb": "Guam", "Seed Price": 10, "Grimy Herb Price": 100, "Profit per Run": 90}]
    monkeypatch.setattr('bot.commands.herb_profit.calculate_custom_profit', _stub)
    return _stub

# Expose test data fixtures from tests.test_duel_fixtures for tests that
# request them as pytest fixtures.
from tests.test_duel_fixtures import test_weapons as _weapons_helper, test_items as _items_helper, test_user_stats as _stats_helper


@pytest.fixture(scope="module")
def test_weapons():
    return _weapons_helper()


@pytest.fixture(scope="module")
def test_items():
    return _items_helper()


@pytest.fixture(scope="module")
def test_user_stats():
    return _stats_helper()
