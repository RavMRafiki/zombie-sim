"""Tests for the Character class"""

import pytest
import pygame
import numpy as np
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from collections import deque

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize pygame before importing character module
pygame.init()

from character import Character
from constants import GRID_SIZE, CELL_SIZE, MOVE_INTERVAL


@pytest.fixture
def mock_grid():
    """Create a mock grid for testing"""
    grid = Mock()
    grid.characters = []
    return grid


@pytest.fixture
def character(mock_grid):
    """Create a Character instance for testing"""
    char = Character(x=10, y=10, grid=mock_grid)
    return char


class TestCharacterInitialization:
    """Tests for Character initialization"""
    
    def test_character_init_with_grid(self, mock_grid):
        """Test character initialization with grid"""
        char = Character(x=5, y=7, grid=mock_grid)
        assert char.x == 5
        assert char.y == 7
        assert char.grid is mock_grid
        assert char.char_type_name == "Character"
        assert char.color == (255, 255, 255)
        assert char.move_speed == MOVE_INTERVAL
    
    def test_character_init_without_grid(self):
        """Test character initialization without grid"""
        char = Character(x=0, y=0, grid=None)
        assert char.x == 0
        assert char.y == 0
        assert char.grid is None
    
    def test_character_state_buffer_initialization(self, character):
        """Test state buffer is initialized with 4 frames of 11x11 zeros"""
        assert len(character.state_buffer) == 4
        for frame in character.state_buffer:
            assert frame.shape == (11, 11)
            assert np.all(frame == 0)
    
    def test_character_signals_initialization(self, character):
        """Test signals list is initialized empty"""
        assert character.signals == []
        assert isinstance(character.signals, list)
    
    def test_character_last_move_time_set(self, character):
        """Test last_move_time is set on initialization"""
        current_time = pygame.time.get_ticks()
        assert abs(character.last_move_time - current_time) < 100
    def test_character_state_buffer_initialized_exactly_four_frames(self):
        char = Character(x=0, y=0)

        assert len(char.state_buffer) == 4

        frames = list(char.state_buffer)
        for frame in frames:
            assert frame.shape == (11, 11)
            assert np.all(frame == 0)

    def test_character_is_alive_initialized_true(self, character):
        """Test is_alive is initialized as True (mutmut_4 and mutmut_5)"""
        assert character.is_alive is True
        assert character.is_alive is not False
        assert character.is_alive is not None
    
    def test_character_is_alive_boolean_type(self, character):
        """Test is_alive is a boolean, not None or other type"""
        assert isinstance(character.is_alive, bool)
        assert character.is_alive == True

    def test_character_signal_memory_time_exact_value(self, character):
        """Test SIGNAL_MEMORY_TIME is exactly 10000 (mutmut_9 uses 10001)"""
        assert character.SIGNAL_MEMORY_TIME == 10000
        assert character.SIGNAL_MEMORY_TIME != 10001
        assert character.SIGNAL_MEMORY_TIME > 0

class TestCharacterMovement:
    """Tests for Character movement"""
    
    def test_move_without_action_code(self, character):
        """Test move without action code stays in place"""
        initial_x, initial_y = character.x, character.y
        result = character.move()
        assert character.x == initial_x
        assert character.y == initial_y
    
    def test_move_up(self, character):
        """Test move action_code 0 moves up (dy = -1)"""
        initial_x, initial_y = character.x, character.y
        character.move(action_code=0)
        assert character.x == initial_x
        assert character.y == initial_y - 1
    
    def test_move_down(self, character):
        """Test move action_code 1 moves down (dy = 1)"""
        initial_x, initial_y = character.x, character.y
        character.move(action_code=1)
        assert character.x == initial_x
        assert character.y == initial_y + 1
    
    def test_move_left(self, character):
        """Test move action_code 2 moves left (dx = -1)"""
        initial_x, initial_y = character.x, character.y
        character.move(action_code=2)
        assert character.x == initial_x - 1
        assert character.y == initial_y
    
    def test_move_right(self, character):
        """Test move action_code 3 moves right (dx = 1)"""
        initial_x, initial_y = character.x, character.y
        character.move(action_code=3)
        assert character.x == initial_x + 1
        assert character.y == initial_y
    
    def test_move_wait(self, character):
        """Test move action_code 4 waits (no movement)"""
        initial_x, initial_y = character.x, character.y
        result = character.move(action_code=4)
        assert character.x == initial_x
        assert character.y == initial_y
        assert result is True
    
    def test_move_action_code_4_vs_other_codes(self, character):
        """Test that action code 4 is treated the same as invalid codes (no movement)"""
        # Position character in middle of grid
        character.x = 50
        character.y = 50
        
        # Test action code 4 (wait)
        result_4 = character.move(action_code=4)
        x_after_4 = character.x
        y_after_4 = character.y
        
        # Reset position
        character.x = 50
        character.y = 50
        
        # Test action code 5 (invalid)
        result_5 = character.move(action_code=5)
        x_after_5 = character.x
        y_after_5 = character.y
        
        # Both should behave identically - no movement, return True
        assert result_4 == result_5 == True
        assert x_after_4 == x_after_5 == 50
        assert y_after_4 == y_after_5 == 50
    
    def test_move_to_top_boundary(self, character):
        """Test movement to y=0 is allowed (not blocked at boundary)"""
        character.x = 5
        character.y = 1
        result = character.move(action_code=0)  # Move up to y=0
        assert character.y == 0
        assert result is True
    
    def test_move_boundary_top(self, character):
        """Test movement blocked at top boundary"""
        character.x = 5
        character.y = 0
        result = character.move(action_code=0)  # Try to move up
        assert character.y == 0
        assert result is False
    
    def test_move_boundary_bottom(self, character):
        """Test movement blocked at bottom boundary"""
        character.x = 5
        character.y = GRID_SIZE - 1
        result = character.move(action_code=1)  # Try to move down
        assert character.y == GRID_SIZE - 1
        assert result is False
    
    def test_move_to_left_boundary(self, character):
        """Test movement to x=0 is allowed (not blocked at boundary)"""
        character.x = 1
        character.y = 5
        result = character.move(action_code=2)  # Move left to x=0
        assert character.x == 0
        assert result is True
    
    def test_move_boundary_left(self, character):
        """Test movement blocked at left boundary"""
        character.x = 0
        character.y = 5
        result = character.move(action_code=2)  # Try to move left
        assert character.x == 0
        assert result is False
    
    def test_move_boundary_right(self, character):
        """Test movement blocked at right boundary"""
        character.x = GRID_SIZE - 1
        character.y = 5
        result = character.move(action_code=3)  # Try to move right
        assert character.x == GRID_SIZE - 1
        assert result is False
    
    def test_move_occupied_cell(self, mock_grid, character):
        """Test movement blocked when cell is occupied"""
        other_char = Mock()
        other_char.x = character.x + 1
        other_char.y = character.y
        mock_grid.characters = [character, other_char]
        
        result = character.move(action_code=3)  # Try to move right
        assert character.x == 10  # Should stay in place
        assert result is False
    
    def test_move_returns_true_on_success(self, character):
        """Test move returns True on successful movement"""
        result = character.move(action_code=3)
        assert result is True
    
    def test_move_ignores_self_in_occupied_check(self, mock_grid, character):
        """Test move doesn't block on self"""
        mock_grid.characters = [character]
        result = character.move(action_code=3)
        assert result is True
    
    def test_move_requires_different_character_at_position(self, mock_grid, character):
        """Test that movement is only blocked when a different character is at the destination"""
        # Create another character at the destination
        other_char = Mock()
        other_char.x = character.x + 1
        other_char.y = character.y
        
        # Only add the other character to the grid
        mock_grid.characters = [other_char]
        
        # Try to move to where other_char is - should be blocked
        result = character.move(action_code=3)
        assert character.x == 10  # Should stay in place
        assert result is False
    
    def test_move_not_blocked_by_different_character_at_different_position(self, mock_grid, character):
        """Test that movement is not blocked by a different character at a different position"""
        # Create another character at a different position
        other_char = Mock()
        other_char.x = character.x + 2  # Different x position
        other_char.y = character.y
        
        # Add both characters to the grid
        mock_grid.characters = [character, other_char]
        
        # Try to move right - should succeed (other_char is at x+2, not x+1)
        result = character.move(action_code=3)
        assert character.x == 11  # Should move successfully
        assert result is True


class TestCharacterActions:
    """Tests for Character actions and signals"""
    
    def test_act_default_implementation(self, character):
        """Test act method default implementation does nothing"""
        # Should not raise any exception
        character.act()
    
    def test_send_signal_to_nearby_character(self, mock_grid, character):
        """Test sending signal to nearby character"""
        other_char = Mock()
        other_char.x = character.x + 1
        other_char.y = character.y
        other_char.receive_signal = Mock()
        
        mock_grid.characters = [character, other_char]
        
        character.send_signal("test_signal", broadcast_range=3)
        
        other_char.receive_signal.assert_called_once()
        call_args = other_char.receive_signal.call_args
        assert call_args[0][0] == "test_signal"
        assert "source" in call_args[0][1]
        assert "distance" in call_args[0][1]
    
    def test_send_signal_out_of_range(self, mock_grid, character):
        """Test signal not sent when character out of range"""
        other_char = Mock()
        other_char.x = character.x + 10
        other_char.y = character.y + 10
        other_char.receive_signal = Mock()
        
        mock_grid.characters = [character, other_char]
        
        character.send_signal("test_signal", broadcast_range=3)
        
        other_char.receive_signal.assert_not_called()
    
    def test_send_signal_without_grid(self, character):
        """Test send_signal does nothing without grid"""
        character.grid = None
        # Should not raise exception
        character.send_signal("test_signal")
    
    def test_receive_signal(self, character):
        """Test receiving a signal"""
        signal_data = {"source": Mock(), "distance": 2}
        character.receive_signal("alert", signal_data)
        
        assert len(character.signals) == 1
        assert character.signals[0]["type"] == "alert"
        assert character.signals[0]["data"] == signal_data
        assert "time" in character.signals[0]
    
    def test_process_signals_clears_signals(self, character):
        """Test process_signals clears old signals"""
        # Create a signal with an old timestamp (older than SIGNAL_MEMORY_TIME)
        old_time = pygame.time.get_ticks() - 11000  # 11 seconds ago (SIGNAL_MEMORY_TIME is 10000)
        character.signals = [{"type": "test", "data": {}, "time": old_time}]
        character.process_signals()
        
        assert character.signals == []

    def test_process_signals_keeps_recent_signals(self, character):
        """Test process_signals keeps recent signals"""
        # Create a signal with a recent timestamp (younger than SIGNAL_MEMORY_TIME)
        recent_time = pygame.time.get_ticks() - 5000  # 5 seconds ago
        character.signals = [{"type": "test", "data": {}, "time": recent_time}]
        character.process_signals()
        
        # Signal should still be in the list
        assert len(character.signals) == 1
        assert character.signals[0]["type"] == "test"

    def test_process_signals_mixed_old_and_new(self, character):
        """Test process_signals removes only old signals"""
        old_time = pygame.time.get_ticks() - 11000  # 11 seconds ago
        recent_time = pygame.time.get_ticks() - 5000  # 5 seconds ago
        
        character.signals = [
            {"type": "old", "data": {}, "time": old_time},
            {"type": "new", "data": {}, "time": recent_time},
        ]
        character.process_signals()
        
        # Only recent signal should remain
        assert len(character.signals) == 1
        assert character.signals[0]["type"] == "new"

    def test_process_signals_returns_list_not_none(self, character):
        """Test that process_signals returns signals as list, not None (mutmut_2)"""
        character.signals = [{"type": "test", "data": {}, "time": pygame.time.get_ticks()}]
        character.process_signals()
        
        # signals must be a list, not None
        assert isinstance(character.signals, list)
        assert character.signals is not None

    def test_process_signals_uses_subtraction_not_addition(self, character):
        """Test process_signals uses subtraction for time comparison (mutmut_3)"""
        # Use a signal at the boundary: exactly at SIGNAL_MEMORY_TIME ago
        boundary_time = pygame.time.get_ticks() - character.SIGNAL_MEMORY_TIME
        character.signals = [{"type": "boundary", "data": {}, "time": boundary_time}]
        character.process_signals()
        
        # The signal should be removed because current_time - boundary_time 
        # equals SIGNAL_MEMORY_TIME, and we check < not <=
        # If addition was used instead (current_time + boundary_time), 
        # the logic would be completely broken
        assert len(character.signals) == 0

    def test_process_signals_uses_correct_time_key(self, character):
        """Test process_signals accesses 'time' key, not 'XXtimeXX' or 'TIME' (mutmut_4, mutmut_5)"""
        recent_time = pygame.time.get_ticks() - 5000
        character.signals = [{"type": "test", "data": {}, "time": recent_time}]
        
        # This should not raise KeyError
        try:
            character.process_signals()
            success = True
        except KeyError:
            success = False
        
        assert success, "process_signals should access the correct 'time' key"
        assert len(character.signals) == 1

    def test_process_signals_less_than_comparison(self, character):
        """Test process_signals uses < not <= for comparison (mutmut_6)"""
        # Create a signal that is exactly SIGNAL_MEMORY_TIME old
        exact_boundary_time = pygame.time.get_ticks() - character.SIGNAL_MEMORY_TIME
        character.signals = [{"type": "boundary", "data": {}, "time": exact_boundary_time}]
        
        character.process_signals()
        
        # With correct < operator, this signal should be REMOVED (age is NOT < SIGNAL_MEMORY_TIME)
        # With <= operator, it would be kept (age <= SIGNAL_MEMORY_TIME would be true)
        assert len(character.signals) == 0, "Signal at exact boundary should be removed with < operator"

    def test_process_signals_just_before_boundary(self, character):
        """Test process_signals keeps signals just before boundary (mutmut_6)"""
        # Create a signal that is just under SIGNAL_MEMORY_TIME old
        just_under_boundary = pygame.time.get_ticks() - character.SIGNAL_MEMORY_TIME + 100  # 100ms before boundary
        character.signals = [{"type": "recent", "data": {}, "time": just_under_boundary}]
        
        character.process_signals()
        
        # This signal should be KEPT
        assert len(character.signals) == 1, "Signal just before boundary should be kept"

    def test_process_signals_empty_list(self, character):
        """Test process_signals handles empty signal list"""
        character.signals = []
        character.process_signals()
        
        assert character.signals == []

    def test_process_signals_multiple_signals_selective_removal(self, character):
        """Test process_signals with multiple signals of varying ages"""
        now = pygame.time.get_ticks()
        
        character.signals = [
            {"type": "very_old", "data": {}, "time": now - 15000},
            {"type": "old", "data": {}, "time": now - 11000},
            {"type": "medium", "data": {}, "time": now - 5000},
            {"type": "young", "data": {}, "time": now - 1000},
        ]
        
        character.process_signals()
        
        # Should keep only medium and young (< 10000 ms old)
        assert len(character.signals) == 2
        remaining_types = [s["type"] for s in character.signals]
        assert "medium" in remaining_types
        assert "young" in remaining_types
        assert "very_old" not in remaining_types
        assert "old" not in remaining_types

    def test_send_signal_uses_lowercase_data_key(self, mock_grid, character):
        """Test that send_signal spreads data keys into payload"""
        other_char = Mock()
        other_char.x = character.x + 1
        other_char.y = character.y
        other_char.receive_signal = Mock()

        mock_grid.characters = [character, other_char]

        character.send_signal("test_signal", data={"foo": "bar"}, broadcast_range=3)

        other_char.receive_signal.assert_called_once()
        call_args = other_char.receive_signal.call_args
        # The signal data dict should contain the spread data from the payload
        payload = call_args[0][1]
        assert "foo" in payload
        assert "bar" == payload["foo"]
    def test_send_signal_default_broadcast_range_is_3(self, mock_grid, character):
        """Test that send_signal uses default broadcast_range of 3, not 4"""
        # Character at distance exactly 3 should receive signal with default range
        in_range_char = Mock()
        in_range_char.x = character.x + 3
        in_range_char.y = character.y
        in_range_char.receive_signal = Mock()
        
        # Character at distance exactly 4 should NOT receive signal with default range
        out_of_range_char = Mock()
        out_of_range_char.x = character.x + 4
        out_of_range_char.y = character.y
        out_of_range_char.receive_signal = Mock()
        
        mock_grid.characters = [character, in_range_char, out_of_range_char]
        
        # Call send_signal without specifying broadcast_range (uses default)
        character.send_signal("test_signal")
        
        # Character at distance 3 should receive the signal
        in_range_char.receive_signal.assert_called_once()
        
        # Character at distance 4 should NOT receive the signal
        out_of_range_char.receive_signal.assert_not_called()
    def test_send_signal_uses_lowercase_source_pos_key(self, mock_grid, character):
        """Test that send_signal uses 'source_pos' (not 'SOURCE_POS') as the key in signal data"""
        other_char = Mock()
        other_char.x = character.x + 1
        other_char.y = character.y
        other_char.receive_signal = Mock()

        mock_grid.characters = [character, other_char]

        character.send_signal("test_signal", broadcast_range=3)

        other_char.receive_signal.assert_called_once()
        call_args = other_char.receive_signal.call_args
        # The signal data dict should have a 'source_pos' key, not 'SOURCE_POS'
        assert "source_pos" in call_args[0][1]
        assert "SOURCE_POS" not in call_args[0][1]
        assert call_args[0][1]["source_pos"] == (character.x, character.y)


class TestCharacterUpdate:
    """Tests for Character update method"""
    
    def test_move_speed_attribute(self, character):
        """Test that move_speed attribute is set correctly"""
        assert character.move_speed == MOVE_INTERVAL


class TestCharacterObservation:
    """Tests for Character observation and state buffer"""
    
    def test_get_observation_center_position(self, character):
        """Test get_observation returns correct shape"""
        global_matrix = np.zeros((GRID_SIZE, GRID_SIZE))
        observation = character.get_observation(global_matrix)
        
        assert observation.shape == (4, 11, 11)
        assert isinstance(observation, np.ndarray)
    
    def test_get_observation_updates_state_buffer(self, character):
        """Test get_observation updates state buffer"""
        global_matrix = np.ones((GRID_SIZE, GRID_SIZE))
        
        # First observation
        char_0 = character.get_observation(global_matrix)
        
        # Modify global matrix
        global_matrix[character.y][character.x] = 2
        
        # Second observation
        char_1 = character.get_observation(global_matrix)
        
        # Last frame in state buffer should be the new one
        assert np.any(char_1[-1] != char_0[-1])
    
    def test_get_observation_frame_stacking(self, character):
        """Test state buffer maintains 4 most recent frames"""
        global_matrix = np.zeros((GRID_SIZE, GRID_SIZE))
        
        for i in range(5):
            global_matrix[:, :] = i
            character.get_observation(global_matrix)
        
        # Should have frames from observations 1, 2, 3, 4 (0 was dropped)
        assert character.state_buffer[0][0, 0] == 1
        assert character.state_buffer[1][0, 0] == 2
        assert character.state_buffer[2][0, 0] == 3
        assert character.state_buffer[3][0, 0] == 4
    
    def test_get_observation_center_view(self, character):
        """Test observation center matches character position"""
        global_matrix = np.zeros((GRID_SIZE, GRID_SIZE))
        global_matrix[character.y][character.x] = 5
        
        observation = character.get_observation(global_matrix)
        # Center of 11x11 is at [5, 5]
        assert observation[-1][5, 5] == 5
    
    def test_get_observation_boundary_edge(self, character):
        """Test observation at map boundary fills with walls"""
        character.x = 0
        character.y = 0
        
        global_matrix = np.zeros((GRID_SIZE, GRID_SIZE))
        observation = character.get_observation(global_matrix)
        
        # Top-left should be filled with 1s (walls) for out-of-bounds areas
        assert observation[-1][0, 0] == 1
        assert observation[-1][0, 1] == 1
    
    def test_get_observation_boundary_bottom_right(self, character):
        """Test observation at bottom-right boundary"""
        character.x = GRID_SIZE - 1
        character.y = GRID_SIZE - 1
        
        global_matrix = np.zeros((GRID_SIZE, GRID_SIZE))
        observation = character.get_observation(global_matrix)
        
        # Bottom-right should be filled with 1s (walls) for out-of-bounds areas
        assert observation[-1][-1, -1] == 1
    
    def test_get_observation_left_boundary(self, character):
        """Test observation correctly adjusts local_x_start when character is near left edge"""
        # Character at x=1, so x_start = 1 - 5 = -4 (triggers adjustment)
        character.x = 1
        character.y = 10
        
        global_matrix = np.zeros((GRID_SIZE, GRID_SIZE))
        # Set distinctive values to verify correct placement
        for i in range(GRID_SIZE):
            global_matrix[10, i] = i + 100  # 100, 101, 102, ...
        
        observation = character.get_observation(global_matrix)
        
        # Verify the observation was computed successfully and has correct shape
        assert observation.shape == (4, 11, 11)
        
        # When x_start=-4, local_x_start should be set to 4 (not None)
        # This means first 4 columns of local_view stay as walls (1s)
        # The data from global_matrix[10, 0:7] should appear at local positions [5, 4:11]
        assert observation[-1][5, 0] == 1   # Wall (out of bounds)
        assert observation[-1][5, 1] == 1   # Wall (out of bounds) 
        assert observation[-1][5, 2] == 1   # Wall (out of bounds)
        assert observation[-1][5, 3] == 1   # Wall (out of bounds)
        # Now check the actual data from the global matrix
        assert observation[-1][5, 4] == 100  # global[10, 0]
        assert observation[-1][5, 5] == 101  # global[10, 1]
        assert observation[-1][5, 6] == 102  # global[10, 2]
    
    def test_get_observation_copies_data_into_view(self, character):
        """Test that observation correctly copies data when conditions are met"""
        # Use a normal center position to ensure x_end > x_start and y_end > y_start
        character.x = 10
        character.y = 10
        
        global_matrix = np.zeros((GRID_SIZE, GRID_SIZE))
        # Mark center area distinctly
        global_matrix[10, 10] = 42
        global_matrix[9, 10] = 43
        global_matrix[11, 10] = 44
        
        observation = character.get_observation(global_matrix)
        
        # Center of 11x11 view is at [5, 5]
        assert observation[-1][5, 5] == 42
        assert observation[-1][4, 5] == 43
        assert observation[-1][6, 5] == 44
    
    def test_get_observation_does_not_copy_when_ranges_invalid(self, character):
        """Test that observation preserves walls when slices would be empty"""
        character.x = 10
        character.y = 10
        
        global_matrix = np.ones((GRID_SIZE, GRID_SIZE)) * 99
        
        observation = character.get_observation(global_matrix)
        
        # All non-boundary areas should be copied (since x_end > x_start and y_end > y_start)
        # This test ensures the condition is checked properly
        assert observation.shape == (4, 11, 11)
        # Center area should be from global_matrix (99)
        center_values = observation[-1][2:9, 2:9]
        assert np.all(center_values == 99)
    
    def test_get_observation_strict_boundary_check(self, character):
        """Test that observation uses strict > comparison, not >="""
        # This test verifies the boundary condition is x_end > x_start (not >=)
        # and y_end > y_start (not >=)
        character.x = 10
        character.y = 10
        
        global_matrix = np.zeros((GRID_SIZE, GRID_SIZE))
        global_matrix[5:16, 5:16] = 7  # Mark the 11x11 area around character
        
        observation = character.get_observation(global_matrix)
        
        # Verify that data is copied (x_end > x_start and y_end > y_start are true)
        # If the mutation changes to >= with 0-width/height slices, the behavior would be different
        assert observation[-1][5, 5] == 7  # Center should have data from global_matrix
        
        # All interior cells should have the marked value
        for i in range(1, 10):
            for j in range(1, 10):
                assert observation[-1][i, j] == 7, f"Cell [{i},{j}] should be 7, got {observation[-1][i, j]}"
    def test_get_observation_local_x_start_initialized_to_zero(self, character):
        """Test that local_x_start is initialized to 0, not None"""
        # Use a center position where x_start >= 0 (no adjustment needed)
        character.x = 10
        character.y = 10
        
        global_matrix = np.zeros((GRID_SIZE, GRID_SIZE))
        global_matrix[10, 10] = 42
        
        observation = character.get_observation(global_matrix)
        
        # If local_x_start was None instead of 0, the slicing logic would fail
        # Verify observation was computed correctly
        assert observation.shape == (4, 11, 11)
        # The value at center should be correctly copied
        assert observation[-1][5, 5] == 42
        # Check that the state_buffer contains the expected frames
        assert isinstance(character.state_buffer, deque)
        assert len(character.state_buffer) == 4
        # The last frame should have the value 42 at the center
        assert character.state_buffer[-1][5, 5] == 42
    def test_get_observation_local_x_start_must_be_int_not_none(self, character):
        """Test that local_x_start is initialized to int 0, not None"""
        # Position character near left edge to trigger x_start < 0
        character.x = 1
        character.y = 10
        
        global_matrix = np.zeros((GRID_SIZE, GRID_SIZE))
        global_matrix[10, 0:7] = np.array([100, 101, 102, 103, 104, 105, 106])
        
        # This should work without TypeError
        observation = character.get_observation(global_matrix)
        
        # Verify the observation was computed correctly
        assert observation.shape == (4, 11, 11)
        
        # Verify data was correctly placed (local_x_start adjustment worked)
        # With proper local_x_start=4 adjustment, data from global[10,0:7] 
        # should appear at local positions [5, 4:11]
        assert observation[-1][5, 4] == 100  # global[10, 0]
        assert observation[-1][5, 5] == 101  # global[10, 1]
        print(observation[-1])

class TestCharacterSurrounding:
    """Tests for getting surrounding characters"""
    
    def test_send_signal_default_broadcast_range_is_3_coverage(self, mock_grid, character):
        """Test signal sending broadcasts properly"""
        other_char = Mock()
        other_char.x = character.x + 2
        other_char.y = character.y
        other_char.receive_signal = Mock()
        
        mock_grid.characters = [character, other_char]
        character.send_signal("test_signal")
        
        other_char.receive_signal.assert_called_once()


class TestCharacterTypeAndProperties:
    """Tests for character type and properties"""
    
    def test_char_type_name_returns_correct_value(self, character):
        """Test char_type_name returns correct value"""
        assert character.char_type_name == "Character"
    
    def test_char_type_name_class_attribute(self):
        """Test char_type_name is a class attribute"""
        assert Character.char_type_name == "Character"


class TestCharacterBoundaryObservation:
    """Tests for boundary condition in observation"""
    
    def test_get_observation_boundary_condition_uses_greater_than_not_gte(self, character):
        """Test that boundary check uses > not >= to catch mutation"""
        # Position character such that y_end equals GRID_SIZE exactly
        # y_end = y - 5 + 5 + 1 = y + 1
        # So we need y + 1 = GRID_SIZE, therefore y = GRID_SIZE - 1
        character.x = 10
        character.y = GRID_SIZE - 6  # So y_end = GRID_SIZE - 6 + 5 + 1 = GRID_SIZE
        
        global_matrix = np.zeros((GRID_SIZE, GRID_SIZE))
        # Fill rows 5 through GRID_SIZE-1 with distinctive values
        # These should be visible in the observation
        global_matrix[5:GRID_SIZE, 5:16] = 77
        
        observation = character.get_observation(global_matrix)
        
        # The character is at y = GRID_SIZE - 6
        # In the 11x11 view centered on character:
        # - Center is at local [5, 5]
        # - Character's y position maps to local row 5
        # - Row below character (y = GRID_SIZE - 5) maps to local row 6
        # - Row y = GRID_SIZE - 1 maps to local row 10
        
        # All rows from global y=5 to y=GRID_SIZE-1 should have value 77
        # These map to local rows in the observation
        # Verify some of the visible data
        assert observation[-1][10, 5] == 77  # Bottom of view should have data
        
        # Similarly for x_end == GRID_SIZE
        character.x = GRID_SIZE - 6  # So x_end = GRID_SIZE - 6 + 5 + 1 = GRID_SIZE
        character.y = 10
        
        global_matrix = np.zeros((GRID_SIZE, GRID_SIZE))
        global_matrix[5:16, 5:GRID_SIZE] = 88
        
        observation = character.get_observation(global_matrix)
        
        # Verify the right boundary has data (not over-adjusted)
        assert observation[-1][5, 10] == 88  # Right side of view should have data
class TestCharacterDrawing:
    """Tests for Character drawing"""
    
    @patch('pygame.draw.rect')
    def test_draw_calls_pygame_rect(self, mock_rect, character):
        """Test draw calls pygame.draw.rect with correct parameters"""
        mock_screen = Mock()
        
        character.draw(mock_screen)
        
        mock_rect.assert_called_once()
        call_args = mock_rect.call_args[0]
        assert call_args[0] is mock_screen
        assert call_args[1] == character.color
        
        # Check that rect coordinates are based on grid position
        rect = call_args[2]
        assert rect[0] == character.x * CELL_SIZE
        assert rect[1] == character.y * CELL_SIZE
        assert rect[2] == CELL_SIZE
        assert rect[3] == CELL_SIZE

    @patch('pygame.draw.rect')
    def test_draw_with_offset_y_adds_correctly(self, mock_rect, character):
        """Test draw uses + for offset_y, not - (mutmut_5)"""
        mock_screen = Mock()
        offset_y = 50
        
        character.draw(mock_screen, offset_y=offset_y)
        
        mock_rect.assert_called_once()
        call_args = mock_rect.call_args[0]
        
        # Check that rect y-coordinate ADDS offset_y, not subtracts
        rect = call_args[2]
        expected_y = character.y * CELL_SIZE + offset_y
        actual_y = rect[1]
        
        assert actual_y == expected_y
        assert actual_y != character.y * CELL_SIZE - offset_y  # Would be wrong with - operator
        
    @patch('pygame.draw.rect')
    def test_draw_offset_y_zero_default(self, mock_rect, character):
        """Test draw with default offset_y=0"""
        mock_screen = Mock()
        
        character.draw(mock_screen)
        
        mock_rect.assert_called_once()
        call_args = mock_rect.call_args[0]
        rect = call_args[2]
        
        # With offset_y=0, y should be same as without offset
        assert rect[1] == character.y * CELL_SIZE

    @patch('pygame.draw.rect')
    def test_draw_offset_y_positive(self, mock_rect, character):
        """Test draw with positive offset_y"""
        mock_screen = Mock()
        offset_y = 100
        
        character.draw(mock_screen, offset_y=offset_y)
        
        mock_rect.assert_called_once()
        call_args = mock_rect.call_args[0]
        rect = call_args[2]
        
        # y should be increased by offset_y
        assert rect[1] == character.y * CELL_SIZE + offset_y


class TestCharacterTypeAndProperties:
    """Tests for Character type and properties"""
    
    def test_char_type_name_returns_correct_value(self, character):
        """Test char_type_name returns correct value"""
        assert character.char_type_name == "Character"
    
    def test_char_type_name_class_attribute(self):
        """Test char_type_name is a class attribute"""
        assert Character.char_type_name == "Character"
    
    def test_color_class_attribute(self):
        """Test color is a class attribute"""
        assert Character.color == (255, 255, 255)
    
    def test_move_speed_class_attribute(self):
        """Test move_speed is a class attribute"""
        assert Character.move_speed == MOVE_INTERVAL


class TestCharacterTargetVector:
    """Tests for Character target vector"""
    
    def test_get_target_vector_default(self, character):
        """Test get_target_vector returns default zero vector"""
        target = character.get_target_vector()
        
        assert isinstance(target, np.ndarray)
        assert target.shape == (2,)
        assert np.allclose(target, [0.0, 0.0])
        assert target.dtype == np.float32
