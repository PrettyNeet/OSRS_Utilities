import pytest
import asyncio
from datetime import datetime, timedelta
from bot.commands.duel import Duel
from bot.utils.combat_mechanics import calculate_hit_chance, calculate_damage
from tests.test_duel_fixtures import (
    mock_interaction, mock_member, mock_db,
    setup_mock_db, test_weapons, test_items, test_user_stats
)

@pytest.mark.asyncio
async def test_full_duel_flow():
    """Test a complete duel from start to finish"""
    # Setup
    interaction = mock_interaction()
    challenger = mock_member()
    opponent = mock_member()
    mock_db_conn = setup_mock_db(mock_db())
    
    # Initialize duel command
    duel_cog = Duel(bot=interaction.client)
    
    # Start duel
    await duel_cog.duel(interaction, opponent)
    
    # Verify duel request sent
    interaction.response.send_message.assert_called_once()
    assert "has challenged" in interaction.response.send_message.call_args[0][0]
    
    # Simulate opponent accepting
    view = interaction.response.send_message.call_args[0][1]
    accept_button = next(b for b in view.children if b.custom_id == "accept")
    await accept_button.callback(interaction)
    
    # Verify combat started
    assert any("Battle begins" in call.args[0][0] 
              for call in interaction.followup.send_message.call_args_list)
    
    # Simulate some turns of combat
    for _ in range(3):
        combat_view = next(call.args[0][1] 
                         for call in interaction.followup.send_message.call_args_list 
                         if hasattr(call.args[0][1], "selected_action"))
        
        # Execute attack
        attack_button = next(b for b in combat_view.children if b.custom_id == "attack")
        await attack_button.callback(interaction)
        
        # Verify combat updates
        assert any("attacks" in call.args[0][0] 
                  for call in interaction.followup.send_message.call_args_list)

@pytest.mark.asyncio
async def test_duel_special_attacks():
    """Test special attack mechanics in duel"""
    # Setup
    interaction = mock_interaction()
    challenger = mock_member()
    opponent = mock_member()
    mock_db_conn = setup_mock_db(mock_db())
    
    # Set up users with granite maul for special testing
    mock_db_conn.set_results(
        "SELECT * FROM user_equipment",
        [{
            "user_id": challenger.id,
            "weapon_id": test_weapons()["granite_maul"]["id"]
        }]
    )
    
    # Initialize duel
    duel_cog = Duel(bot=interaction.client)
    await duel_cog.duel_challenge(interaction, opponent)
    
    # Skip to combat phase
    view = interaction.response.send_message.call_args[0][1]
    accept_button = next(b for b in view.children if b.custom_id == "accept")
    await accept_button.callback(interaction)
    
    # Use special attack
    combat_view = next(call.args[0][1] 
                      for call in interaction.followup.send_message.call_args_list 
                      if hasattr(call.args[0][1], "selected_action"))
    
    special_button = next(b for b in combat_view.children if b.custom_id == "special")
    await special_button.callback(interaction)
    
    # Verify special attack execution
    assert any("special attack" in call.args[0][0].lower() 
              for call in interaction.followup.send_message.call_args_list)

@pytest.mark.asyncio
async def test_duel_item_usage():
    """Test item usage during duel"""
    # Setup
    interaction = mock_interaction()
    challenger = mock_member()
    opponent = mock_member()
    mock_db_conn = setup_mock_db(mock_db())
    
    # Give challenger some items
    mock_db_conn.set_results(
        "SELECT * FROM user_inventory",
        [{
            "user_id": challenger.id,
            "item_id": test_items()["shark"]["id"],
            "quantity": 3
        }]
    )
    
    # Start duel
    duel_cog = Duel(bot=interaction.client)
    await duel_cog.duel_challenge(interaction, opponent)
    
    # Skip to combat
    view = interaction.response.send_message.call_args[0][1]
    accept_button = next(b for b in view.children if b.custom_id == "accept")
    await accept_button.callback(interaction)
    
    # Use item
    combat_view = next(call.args[0][1] 
                      for call in interaction.followup.send_message.call_args_list 
                      if hasattr(call.args[0][1], "selected_action"))
    
    item_button = next(b for b in combat_view.children if b.custom_id == "use_item")
    await item_button.callback(interaction)
    
    # Verify item usage
    assert any("used" in call.args[0][0] and "Shark" in call.args[0][0]
              for call in interaction.followup.send_message.call_args_list)
    
    # Verify inventory update
    assert any("UPDATE user_inventory" in q for q in mock_db_conn.executed_queries)

@pytest.mark.asyncio
async def test_duel_timeout():
    """Test duel timeout handling"""
    # Setup
    interaction = mock_interaction()
    challenger = mock_member()
    opponent = mock_member()
    mock_db_conn = setup_mock_db(mock_db())
    
    # Start duel with short timeout
    duel_cog = Duel(bot=interaction.client)
    duel_cog.DUEL_TIMEOUT = 0.1
    
    await duel_cog.duel(interaction, opponent)
    
    # Wait for timeout
    await asyncio.sleep(0.2)
    
    # Verify timeout handling
    assert any("timed out" in call.args[0][0].lower()
              for call in interaction.followup.send_message.call_args_list)

@pytest.mark.asyncio
async def test_duel_stats_update():
    """Test stats are properly updated after duel"""
    # Setup
    interaction = mock_interaction()
    challenger = mock_member()
    opponent = mock_member()
    mock_db_conn = setup_mock_db(mock_db())
    
    # Start and finish duel
    duel_cog = Duel(bot=interaction.client)
    await duel_cog.duel_challenge(interaction, opponent)
    
    # Force duel completion
    duel_cog._active_duels[challenger.id].winner = challenger
    await duel_cog._handle_duel_completion(challenger.id)
    
    # Verify stats update
    assert any("UPDATE users" in q and "total_wins" in q 
              for q in mock_db_conn.executed_queries)
    assert any("INSERT INTO duel_history" in q 
              for q in mock_db_conn.executed_queries)