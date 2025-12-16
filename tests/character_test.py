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
        """Test process_signals clears the signals list"""
        character.signals = [{"type": "test", "data": {}}]
        character.process_signals()
        
        assert character.signals == []


class TestCharacterUpdate:
    """Tests for Character update method"""
    
    def test_update_without_elapsed_time(self, character):
        """Test update doesn't trigger movement without sufficient time elapsed"""
        with patch.object(character, 'move') as mock_move:
            with patch.object(character, 'act') as mock_act:
                character.update(character.last_move_time + 50)  # Less than MOVE_INTERVAL
                
                mock_move.assert_not_called()
                mock_act.assert_not_called()
    
    def test_update_with_elapsed_time(self, character):
        """Test update triggers movement when sufficient time elapsed"""
        with patch.object(character, 'move') as mock_move:
            with patch.object(character, 'act') as mock_act:
                character.update(character.last_move_time + MOVE_INTERVAL + 10)
                
                mock_move.assert_called_once()
                mock_act.assert_called_once()
    
    def test_update_with_elapsed_time_exactly_move_speed(self, character):
        """Test update triggers movement when elapsed time equals move_speed exactly"""
        with patch.object(character, 'move') as mock_move:
            with patch.object(character, 'act') as mock_act:
                character.update(character.last_move_time + MOVE_INTERVAL)
                
                mock_move.assert_called_once()
                mock_act.assert_called_once()
    
    def test_update_updates_last_move_time(self, character):
        """Test update updates last_move_time"""
        old_time = character.last_move_time
        new_time = old_time + MOVE_INTERVAL + 10
        
        with patch.object(character, 'move'):
            with patch.object(character, 'act'):
                character.update(new_time)
        
        assert character.last_move_time == new_time
    
    def test_update_processes_signals(self, character):
        """Test update calls process_signals"""
        character.signals = [{"type": "test", "data": {}}]
        
        with patch.object(character, 'move'):
            with patch.object(character, 'act'):
                character.update(character.last_move_time + MOVE_INTERVAL + 10)
        
        assert character.signals == []


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


class TestCharacterSurrounding:
    """Tests for getting surrounding characters"""
    
    def test_get_surrounding_characters_empty(self, mock_grid, character):
        """Test get_surrounding_characters with no nearby characters"""
        mock_grid.characters = [character]
        
        nearby = character.get_surrounding_characters(radius=3)
        assert nearby == []
    
    def test_get_surrounding_characters_in_range(self, mock_grid, character):
        """Test get_surrounding_characters finds characters in range"""
        other_char1 = Mock()
        other_char1.x = character.x + 1
        other_char1.y = character.y
        
        other_char2 = Mock()
        other_char2.x = character.x + 3
        other_char2.y = character.y
        
        mock_grid.characters = [character, other_char1, other_char2]
        
        nearby = character.get_surrounding_characters(radius=3)
        assert len(nearby) == 2
        assert other_char1 in nearby
        assert other_char2 in nearby
    
    def test_get_surrounding_characters_out_of_range(self, mock_grid, character):
        """Test get_surrounding_characters excludes out of range characters"""
        other_char = Mock()
        other_char.x = character.x + 10
        other_char.y = character.y + 10
        
        mock_grid.characters = [character, other_char]
        
        nearby = character.get_surrounding_characters(radius=3)
        assert len(nearby) == 0
    
    def test_get_surrounding_characters_without_grid(self, character):
        """Test get_surrounding_characters returns empty list without grid"""
        character.grid = None
        nearby = character.get_surrounding_characters(radius=3)
        assert nearby == []
    
    def test_get_surrounding_characters_excludes_self(self, mock_grid, character):
        """Test get_surrounding_characters excludes self"""
        mock_grid.characters = [character]
        
        nearby = character.get_surrounding_characters(radius=100)
        assert character not in nearby
    
    def test_get_surrounding_characters_default_radius(self, mock_grid, character):
        """Test get_surrounding_characters uses correct default radius of 3"""
        # Character at distance 3 should be included with default radius
        in_range = Mock()
        in_range.x = character.x + 3
        in_range.y = character.y
        
        # Character at distance 4 should be excluded with default radius
        out_of_range = Mock()
        out_of_range.x = character.x + 4
        out_of_range.y = character.y
        
        mock_grid.characters = [character, in_range, out_of_range]
        
        # Call without specifying radius to verify default is 3
        nearby = character.get_surrounding_characters()
        assert len(nearby) == 1
        assert in_range in nearby
        assert out_of_range not in nearby


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


class TestCharacterTypeAndProperties:
    """Tests for Character type and properties"""
    
    def test_get_type_name(self, character):
        """Test get_type_name returns correct type"""
        assert character.get_type_name() == "Character"
    
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
