import pytest

from bot.utils import calculations


def sample_prices():
    return {
        "100": {"high": 10, "avgHighPrice": 9},
        "101": {"high": 100, "avgHighPrice": 95}
    }


def sample_herbs():
    return {
        "Guam": {"seed_id": 100, "herb_id": 101, "lowCTS": 100}
    }


def test_calculate_custom_profit_basic():
    prices = sample_prices()
    herbs = sample_herbs()
    results = calculations.calculate_custom_profit(prices, herbs, farming_level=50, patches=1,
                                                   weiss=False, trollheim=False, hosidius=False, fortis=False,
                                                   compost='None', kandarin_diary='None', kourend=False,
                                                   magic_secateurs=False, farming_cape=False, bottomless_bucket=False,
                                                   attas=False, price_key='high')
    assert isinstance(results, list)
    assert len(results) == 1
    row = results[0]
    assert row['Herb'] == 'Guam'
    assert 'Profit per Run' in row


def test_calculate_custom_profit_missing_prices():
    prices = {"100": {"high": 10, "avgHighPrice": 9}}  # missing herb id 101
    herbs = sample_herbs()
    results = calculations.calculate_custom_profit(prices, herbs, farming_level=50, patches=1,
                                                   weiss=False, trollheim=False, hosidius=False, fortis=False,
                                                   compost='None', kandarin_diary='None', kourend=False,
                                                   magic_secateurs=False, farming_cape=False, bottomless_bucket=False,
                                                   attas=False, price_key='high')
    # Should skip herbs with missing price entries
    assert results == []

