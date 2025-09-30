import pytest
import asyncio

from bot.commands.herb_profit import HerbProfit, FormatSelectView


@pytest.mark.asyncio
async def test_herb_profit_builds_view_and_prompts(async_fetch_latest_prices, fake_interaction, sample_herbs):
    # Create a fake bot with an http_session attribute
    class FakeBot:
        http_session = None

    bot = FakeBot()
    cog = HerbProfit(bot)

    # Prepare choices and compost/price_type simulated args
    class FakeChoice:
        def __init__(self, value):
            self.value = value

    farming_level = 50
    patches = 1
    weiss = False
    trollheim = False
    hosidius = False
    fortis = False
    kandarin_diary = 'None'
    kourend = False
    magic_secateurs = False
    farming_cape = False
    bottomless_bucket = False
    attas = False
    compost = FakeChoice('None')
    price_type = FakeChoice('latest')

    # Call the command
    await cog.herb_profit(
        fake_interaction,
        farming_level,
        patches,
        weiss,
        trollheim,
        hosidius,
        fortis,
        kandarin_diary,
        kourend,
        magic_secateurs,
        farming_cape,
        bottomless_bucket,
        attas,
        compost,
        price_type
    )

    # The command should prompt with a view via interaction.response.send_message
    fake_interaction.response.send_message.assert_called()
    called_args, called_kwargs = fake_interaction.response.send_message.call_args
    assert 'view' in called_kwargs
    view = called_kwargs['view']
    assert isinstance(view, FormatSelectView)


@pytest.mark.asyncio
async def test_formatselectview_markdown_sends_table(stub_calculate_custom_profit, fake_interaction, sample_prices, sample_herbs):
    # Build the view with the fake interaction and sample data
    view = FormatSelectView(bot=None, interaction=fake_interaction, farming_level=50, patches=1,
                            weiss=False, trollheim=False, hosidius=False, fortis=False,
                            kandarin_diary='None', kourend=False, magic_secateurs=False,
                            farming_cape=False, bottomless_bucket=False, attas=False,
                            compost='None', prices=sample_prices, price_key='high', price_type='latest')

    # Simulate a user selecting markdown
    fake_interaction.data = {"values": ["markdown"]}

    # Call the select callback
    await view.select_callback(fake_interaction, select=None)

    # The followup send should be called with content containing the table header
    fake_interaction.followup.send.assert_called()
    args, kwargs = fake_interaction.followup.send.call_args
    # content is passed as a keyword argument by the implementation
    content = kwargs.get('content') if kwargs.get('content') is not None else (args[0] if args else '')
    # Ensure the message includes the mention and the table header
    assert fake_interaction.user.mention in content
    assert 'Herb' in content
