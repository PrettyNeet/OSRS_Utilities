import pytest
from unittest.mock import AsyncMock
import asyncio
from bot.utils.combat_views import DuelRequestView, CombatActionView, EquipmentView
from tests.test_duel_fixtures import (
    mock_interaction, mock_member, mock_db,
    setup_mock_db, test_weapons, test_items
)

@pytest.mark.asyncio
async def test_duel_request_view():
    """Test duel request view creation and interaction"""
    # Setup
    interaction = mock_interaction()
    challenger = mock_member()
    opponent = mock_member()
    
    # Create duel request view
    view = DuelRequestView(
        challenger=challenger,
        opponent=opponent,
        timeout=60
    )
    
    # Test view properties
    assert view.challenger == challenger
    assert view.opponent == opponent
    assert not view.accepted
    assert not view.declined
    
    # Test accept button click
    accept_button = next(b for b in view.children if b.custom_id == "accept")
    await accept_button.callback(interaction)
    
    assert view.accepted
    assert not view.declined
    assert view.is_finished()

    # Verify interaction response
    interaction.response.edit_message.assert_called_once()

@pytest.mark.asyncio
async def test_combat_action_view():
    """Test combat action view functionality"""
    # Setup
    interaction = mock_interaction()
    attacker = mock_member()
    defender = mock_member()
    mock_db_conn = setup_mock_db(mock_db())
    
    # Create combat view
    view = CombatActionView(
        attacker=attacker,
        defender=defender,
        db=mock_db_conn,
        timeout=60
    )
    
    # Test view initialization
    assert view.attacker == attacker
    assert view.defender == defender
    assert not view.action_selected
    
    # Test attack button
    attack_button = next(b for b in view.children if b.custom_id == "attack")
    await attack_button.callback(interaction)
    
    assert view.action_selected
    assert view.selected_action == "attack"
    
    # Verify combat calculations were requested
    interaction.response.edit_message.assert_called_once()

@pytest.mark.asyncio
async def test_equipment_view():
    """Test equipment management view"""
    # Setup
    interaction = mock_interaction()
    user = mock_member()
    mock_db_conn = setup_mock_db(mock_db())
    
    # Create equipment view
    view = EquipmentView(
        user=user,
        db=mock_db_conn,
        timeout=60
    )
    
    # Test equipment slots are properly initialized
    assert len(view.children) > 0
    assert any(b.custom_id == "weapon" for b in view.children)
    assert any(b.custom_id == "armor" for b in view.children)
    
    # Test weapon selection
    weapon_select = next(c for c in view.children if c.custom_id == "weapon")
    
    # Verify weapon options from test data
    weapons = test_weapons()
    assert len(weapon_select.options) == len(weapons)
    assert any(o.label == "Dragon Scimitar" for o in weapon_select.options)
    
    # Test equipment change
    await weapon_select.callback(interaction)
    
    # Verify database was queried
    assert any("UPDATE user_equipment" in q for q in mock_db_conn.executed_queries)

@pytest.mark.asyncio
async def test_view_timeouts():
    """Test view timeout handling"""
    # Setup
    challenger = mock_member()
    opponent = mock_member()
    
    # Create view with short timeout
    view = DuelRequestView(
        challenger=challenger,
        opponent=opponent,
        timeout=0.1
    )
    
    # Wait for timeout
    await asyncio.sleep(0.2)
    
    # Verify view is inactive after timeout
    assert view.is_finished()
    assert not view.accepted
    assert not view.declined

@pytest.mark.asyncio
async def test_view_error_handling():
    """Test error handling in views"""
    # Setup with bad database connection
    interaction = mock_interaction()
    user = mock_member()
    mock_db_conn = mock_db()
    mock_db_conn.execute = AsyncMock(side_effect=Exception("Database error"))
    
    # Create equipment view
    view = EquipmentView(
        user=user,
        db=mock_db_conn,
        timeout=60
    )
    
    # Test error handling during equipment change
    weapon_select = next(c for c in view.children if c.custom_id == "weapon")
    await weapon_select.callback(interaction)
    
    # Verify error response sent
    interaction.response.send_message.assert_called_once_with(
        "An error occurred while updating equipment.",
        ephemeral=True
    )