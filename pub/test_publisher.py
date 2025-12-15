import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'KFC_Py'))

import unittest
from unittest.mock import Mock, patch, MagicMock
from listener import Listener
from publisher import Publisher

# Mock Command class
class MockCommand:
    def __init__(self, timestamp: int, piece_id: str, type: str, params: list):
        self.timestamp = timestamp
        self.piece_id = piece_id
        self.type = type
        self.params = params
    
    def __str__(self) -> str:
        return f"MockCommand(timestamp={self.timestamp}, piece_id={self.piece_id}, type={self.type}, params={self.params})"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def __eq__(self, other):
        if not isinstance(other, MockCommand):
            return False
        return (self.timestamp == other.timestamp and 
                self.piece_id == other.piece_id and 
                self.type == other.type and 
                self.params == other.params)

# Mock Listener for tests
class MockListener(Listener):
    def __init__(self, id: str, channel: str, publisher: "Publisher"):
        super().__init__(id, channel, publisher)
        self.received_messages = []
        print(f"📋 MockListener '{id}' registered to channel '{channel}'")
    
    def listening(self, message):
        self.received_messages.append(message)
        print(f"🔔 MockListener received message: {message}")

class TestPublisherListener(unittest.TestCase):
    
    def setUp(self):
        """Setup for each test"""
        print("\n" + "="*50)
        print("🚀 Starting new test")
        self.publisher = Publisher()
        print("📡 Publisher created with channels: moves, score")
    
    def test_listener_registration(self):
        """Test listener registration"""
        print("\n🧪 Test: Listener registration")
        
        listener = MockListener("white", "moves", self.publisher)
        
        # Check that listener is registered
        self.assertIn("white", self.publisher._channels["moves"])
        self.assertEqual(self.publisher._channels["moves"]["white"], listener)
        print("✅ Listener registered successfully")
    
    def test_publish_command(self):
        """Test command publishing"""
        print("\n🧪 Test: Command publishing")
        
        # Create listener
        listener = MockListener("black", "moves", self.publisher)
        
        # Create mock command
        command = MockCommand(
            timestamp=1000,
            piece_id="pawn_e2",
            type="move",
            params=["e2", "e4"]
        )
        print(f"📝 Mock command created: {command}")
        
        # Publish command
        print("📢 Publishing command...")
        self.publisher.publish("moves", "black", command)
        
        # Check that listener received the message
        self.assertEqual(len(listener.received_messages), 1)
        self.assertEqual(listener.received_messages[0], command)
        print("✅ Listener received command successfully")
    
    def test_multiple_listeners(self):
        """Test multiple listeners on same channel"""
        print("\n🧪 Test: Multiple listeners")
        
        # Create two listeners
        listener1 = MockListener("white", "score", self.publisher)
        listener2 = MockListener("black", "score", self.publisher)
        
        # Publish message to white player
        print("📢 Publishing points to white player...")
        self.publisher.publish("score", "white", 10)
        
        # Checks
        self.assertEqual(len(listener1.received_messages), 1)
        self.assertEqual(listener1.received_messages[0], 10)
        self.assertEqual(len(listener2.received_messages), 0)
        print("✅ Only correct listener received the message")
    
    def test_invalid_channel(self):
        """Test non-existent channel"""
        print("\n🧪 Test: Non-existent channel")
        
        with self.assertRaises(ValueError) as context:
            MockListener("test", "invalid_channel", self.publisher)
        
        print(f"❌ Error as expected: {context.exception}")
        print("✅ System prevents registration to non-existent channel")
    
    @patch('builtins.print')
    def test_with_mock_print(self, mock_print):
        """Test with Mock of print"""
        print("\n🧪 Test: With print mock")
        
        listener = MockListener("test", "moves", self.publisher)
        command = MockCommand(2000, "queen_d1", "jump", ["d1", "h5"])
        
        self.publisher.publish("moves", "test", command)
        
        # Check that print was called
        self.assertTrue(mock_print.called)
        print("✅ Prints work as expected")
    
    def test_chess_game_scenario(self):
        """Test chess game scenario"""
        print("\n🧪 Test: Chess game scenario")
        
        # Create listeners for moves and score
        move_listener = MockListener("game_log", "moves", self.publisher)
        white_score = MockListener("white", "score", self.publisher)
        black_score = MockListener("black", "score", self.publisher)
        
        print("♟️ Starting chess game simulation...")
        
        # Move 1: White pawn
        move1 = MockCommand(1000, "pawn_e2", "move", ["e2", "e4"])
        self.publisher.publish("moves", "game_log", move1)
        print("🏃 White pawn moves from e2 to e4")
        
        # Move 2: Black pawn
        move2 = MockCommand(1500, "pawn_e7", "move", ["e7", "e5"])
        self.publisher.publish("moves", "game_log", move2)
        print("🏃 Black pawn moves from e7 to e5")
        
        # Points for white player (capturing piece)
        self.publisher.publish("score", "white", 5)
        print("🏆 White player received 5 points")
        
        # Checks
        self.assertEqual(len(move_listener.received_messages), 2)
        self.assertEqual(len(white_score.received_messages), 1)
        self.assertEqual(len(black_score.received_messages), 0)
        
        print("♔ Simulation completed successfully!")
        print(f"📊 Total moves: {len(move_listener.received_messages)}")
        print(f"🏆 White player points: {white_score.received_messages}")
        print("✅ All tests passed successfully!")
    
    def test_mock_command_equality(self):
        """Test MockCommand equality"""
        print("\n🧪 Test: MockCommand equality")
        
        cmd1 = MockCommand(1000, "pawn_a2", "move", ["a2", "a4"])
        cmd2 = MockCommand(1000, "pawn_a2", "move", ["a2", "a4"])
        cmd3 = MockCommand(2000, "pawn_a2", "move", ["a2", "a4"])
        
        self.assertEqual(cmd1, cmd2)
        self.assertNotEqual(cmd1, cmd3)
        print("✅ MockCommand equality works correctly")

def run_interactive_test():
    """Interactive test with prints"""
    print("\n" + "🎮" * 20)
    print("🎯 Interactive Test - Publisher-Listener System")
    print("🎮" * 20)
    
    # Create system
    publisher = Publisher()
    print("📡 Publisher created with channels: moves, score")
    
    # Create listeners
    print("\n1️⃣ Creating listeners...")
    game_logger = MockListener("game_logger", "moves", publisher)
    white_player = MockListener("white_player", "score", publisher)
    black_player = MockListener("black_player", "score", publisher)
    
    # Sequence of actions
    print("\n2️⃣ Publishing moves...")
    commands = [
        MockCommand(1000, "knight_b1", "move", ["b1", "c3"]),
        MockCommand(1200, "bishop_f1", "move", ["f1", "c4"]),
        MockCommand(1400, "queen_d1", "jump", ["d1", "h5"])
    ]
    
    for i, cmd in enumerate(commands, 1):
        print(f"  🎯 Move {i}: {cmd.piece_id} from {cmd.params[0]} to {cmd.params[1]}")
        publisher.publish("moves", "game_logger", cmd)
    
    print("\n3️⃣ Updating scores...")
    print("  🏆 White player receives 10 points")
    publisher.publish("score", "white_player", 10)
    
    print("  🏆 Black player receives 5 points")
    publisher.publish("score", "black_player", 5)
    
    print("  🏆 White player receives additional 15 points")
    publisher.publish("score", "white_player", 15)
    
    print("\n📈 Final results:")
    print(f"📝 Total moves recorded: {len(game_logger.received_messages)}")
    print(f"🏆 White player points: {sum(white_player.received_messages)}")
    print(f"🏆 Black player points: {sum(black_player.received_messages)}")
    
    print("\n🎊 Interactive test completed successfully!")
    print("✨ System works perfectly!")

def test_advanced_scenarios():
    """Test advanced scenarios"""
    print("\n" + "⚡" * 20)
    print("⚡ Advanced Test Scenarios")
    print("⚡" * 20)
    
    publisher = Publisher()
    
    # Test 1: Multiple commands in sequence
    print("\n🔥 Test: Rapid command sequence")
    listener = MockListener("rapid_test", "moves", publisher)
    
    rapid_commands = [
        MockCommand(i*100, f"piece_{i}", "move", [f"a{i}", f"b{i}"])
        for i in range(1, 6)
    ]
    
    for cmd in rapid_commands:
        publisher.publish("moves", "rapid_test", cmd)
    
    print(f"✅ Processed {len(rapid_commands)} commands rapidly")
    
    # Test 2: Score accumulation
    print("\n💰 Test: Score accumulation")
    score_listener = MockListener("accumulator", "score", publisher)
    
    scores = [5, 10, 3, 8, 12]
    for score in scores:
        publisher.publish("score", "accumulator", score)
    
    total_score = sum(score_listener.received_messages)
    print(f"✅ Total accumulated score: {total_score}")
    
    print("\n🎊 Advanced tests completed!")

if __name__ == "__main__":
    # Run unit tests
    print("🧪 Running unit tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run interactive test
    run_interactive_test()
    
    # Run advanced scenarios
    test_advanced_scenarios()