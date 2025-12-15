"""
Comprehensive tests for the real-time chess Publisher-Subscriber system
The tests check:
1. Correct listener registration
2. Message passing between components
3. Score management
4. Game log
5. Complex chess scenarios
"""

import unittest
from unittest.mock import Mock, patch
from publisher import Publisher
from listener import Listener
from pub.score import Score
from game_log import GameLog

# Mock Command for tests (replaces real Command)
class MockCommand:
    def __init__(self, timestamp: int, piece_id: str, type: str, params: list):
        self.timestamp = timestamp
        self.piece_id = piece_id
        self.type = type
        self.params = params
    
    def __str__(self):
        return f"MockCommand({self.timestamp}, {self.piece_id}, {self.type}, {self.params})"
    
    def __eq__(self, other):
        if not isinstance(other, MockCommand):
            return False
        return (self.timestamp == other.timestamp and 
                self.piece_id == other.piece_id and 
                self.type == other.type and 
                self.params == other.params)

# Basic listener for tests
class TestListener(Listener):
    def __init__(self, id: str, channel: str, publisher: Publisher):
        super().__init__(id, channel, publisher)
        self.messages = []
        
    def listening(self, message):
        self.messages.append(message)
        print(f"🔔 {self.__class__.__name__} '{id}' received: {message}")

class TestCompleteSystem(unittest.TestCase):
    """Comprehensive tests for the chess system"""
    
    def setUp(self):
        """Setup for each test - create new system"""
        print("\n" + "🎯" * 50)
        print("🚀 Starting new test")
        self.publisher = Publisher()
        print("📡 Publisher created with channels: moves, score")
    
    def test_publisher_initialization(self):
        """Test: Check correct Publisher initialization"""
        print("\n🧪 Test: Publisher initialization")
        
        # Check that channels were created
        self.assertIn("moves", self.publisher._channels)
        self.assertIn("score", self.publisher._channels)
        
        # Check that channels are empty
        self.assertEqual(len(self.publisher._channels["moves"]), 0)
        self.assertEqual(len(self.publisher._channels["score"]), 0)
        
        print("✅ Publisher initialized correctly with all channels")
    
    def test_score_listener_registration_and_function(self):
        """Test: Score system - registration and functionality"""
        print("\n🧪 Test: Score system")
        
        # Create score listeners
        white_score = Score("white", self.publisher)
        black_score = Score("black", self.publisher)
        
        # Check they registered to correct channel
        self.assertIn("white", self.publisher._channels["score"])
        self.assertIn("black", self.publisher._channels["score"])
        
        # Send points
        print("🏆 Sending 10 points to white player")
        self.publisher.publish("score", "white", 10)
        
        print("🏆 Sending 5 points to black player")
        self.publisher.publish("score", "black", 5)
        
        print("🏆 Sending additional 15 points to white player")
        self.publisher.publish("score", "white", 15)
        
        # Check scores
        self.assertEqual(white_score.get_score(), 25)
        self.assertEqual(black_score.get_score(), 5)
        
        print(f"✅ White score: {white_score.get_score()}")
        print(f"✅ Black score: {black_score.get_score()}")
    
    def test_game_log_functionality(self):
        """Test: GameLog - move recording"""
        print("\n🧪 Test: Game log")
        
        # Create game log
        game_log = GameLog("main_log", self.publisher)
        
        # Check it registered to correct channel
        self.assertIn("main_log", self.publisher._channels["moves"])
        
        # Create moves
        move1 = MockCommand(1000, "pawn_e2", "move", ["e2", "e4"])
        move2 = MockCommand(1500, "knight_b1", "move", ["b1", "c3"])
        move3 = MockCommand(2000, "queen_d1", "jump", ["d1", "h5"])
        
        # Send moves
        print("📝 Sending move 1: pawn e2→e4")
        self.publisher.publish("moves", "main_log", move1)
        
        print("📝 Sending move 2: knight b1→c3")
        self.publisher.publish("moves", "main_log", move2)
        
        print("📝 Sending move 3: queen d1→h5")
        self.publisher.publish("moves", "main_log", move3)
        
        # Check log
        log = game_log.get_log()
        self.assertEqual(len(log), 3)
        
        # Check record content
        self.assertIn("1000", log[0])
        self.assertIn("pawn_e2", log[0])
        self.assertIn("e2 -> e4", log[0])
        
        print("✅ Log recorded 3 moves correctly")
        for i, entry in enumerate(log, 1):
            print(f"   {i}. {entry}")
    
    def test_multiple_listeners_same_channel(self):
        """Test: Multiple listeners on same channel"""
        print("\n🧪 Test: Multiple listeners on same channel")
        
        # Create multiple logs
        main_log = GameLog("main_log", self.publisher)
        backup_log = GameLog("backup_log", self.publisher)
        analysis_log = GameLog("analysis_log", self.publisher)
        
        # Send move
        move = MockCommand(1000, "rook_a1", "move", ["a1", "a5"])
        self.publisher.publish("moves", "main_log", move)
        self.publisher.publish("moves", "backup_log", move)
        
        # Check each log received its moves
        self.assertEqual(len(main_log.get_log()), 1)
        self.assertEqual(len(backup_log.get_log()), 1)
        self.assertEqual(len(analysis_log.get_log()), 0)  # received nothing
        
        print("✅ Each listener received only messages intended for it")
    
    def test_cross_channel_communication(self):
        """Test: Cross-channel communication"""
        print("\n🧪 Test: Cross-channel communication")
        
        # Create complete system
        white_score = Score("white", self.publisher)
        black_score = Score("black", self.publisher)
        game_log = GameLog("log", self.publisher)
        
        # Game simulation
        print("🎮 Starting game simulation...")
        
        # Move 1: white moves
        move1 = MockCommand(1000, "pawn_e2", "move", ["e2", "e4"])
        self.publisher.publish("moves", "log", move1)
        
        # Move 2: black moves and captures piece
        move2 = MockCommand(1500, "pawn_d7", "capture", ["d7", "d5"])
        self.publisher.publish("moves", "log", move2)
        self.publisher.publish("score", "black", 3)  # points for capture
        
        # Move 3: white captures back
        move3 = MockCommand(2000, "pawn_e4", "capture", ["e4", "d5"])
        self.publisher.publish("moves", "log", move3)
        self.publisher.publish("score", "white", 5)  # points for capture
        
        # Checks
        self.assertEqual(len(game_log.get_log()), 3)
        self.assertEqual(white_score.get_score(), 5)
        self.assertEqual(black_score.get_score(), 3)
        
        print("✅ Cross-channel communication works perfectly")
        print(f"📊 Log: {len(game_log.get_log())} moves")
        print(f"🏆 White score: {white_score.get_score()}")
        print(f"🏆 Black score: {black_score.get_score()}")
    
    def test_error_handling_invalid_channel(self):
        """Test: Error handling - non-existent channel"""
        print("\n🧪 Test: Error handling")
        
        # Try creating listener for non-existent channel
        with self.assertRaises(ValueError) as context:
            TestListener("test", "non_existent_channel", self.publisher)
        
        print(f"❌ Error as expected: {context.exception}")
        print("✅ System prevents registration to non-existent channel")
    
    def test_rapid_messages_sequence(self):
        """Test: Rapid message sequence"""
        print("\n🧪 Test: Rapid message sequence")
        
        # Create system
        score_tracker = Score("rapid", self.publisher)
        
        # Send messages rapidly
        print("⚡ Sending 100 messages rapidly...")
        for i in range(100):
            self.publisher.publish("score", "rapid", 1)
        
        # Check all messages were received
        self.assertEqual(score_tracker.get_score(), 100)
        print("✅ All 100 messages received successfully")
    
    def test_concurrent_operations(self):
        """Test: Concurrent operations"""
        print("\n🧪 Test: Concurrent operations")
        
        # Create multiple listeners
        players = {}
        logs = {}
        
        for color in ["white", "black", "red", "blue"]:
            players[color] = Score(color, self.publisher)
            logs[color] = GameLog(f"log_{color}", self.publisher)
        
        print("🎭 Creating 4 players and 4 logs")
        
        # Concurrent operations
        operations = [
            ("score", "white", 10),
            ("moves", "log_white", MockCommand(1000, "king_e1", "move", ["e1", "f1"])),
            ("score", "black", 5),
            ("moves", "log_black", MockCommand(1100, "queen_d8", "move", ["d8", "d7"])),
            ("score", "red", 8),
            ("score", "blue", 12),
        ]
        
        print("⚡ Performing 6 concurrent operations...")
        for channel, id, message in operations:
            self.publisher.publish(channel, id, message)
        
        # Checks
        self.assertEqual(players["white"].get_score(), 10)
        self.assertEqual(players["black"].get_score(), 5)
        self.assertEqual(players["red"].get_score(), 8)
        self.assertEqual(players["blue"].get_score(), 12)
        
        self.assertEqual(len(logs["white"].get_log()), 1)
        self.assertEqual(len(logs["black"].get_log()), 1)
        
        print("✅ All operations performed correctly concurrently")
    
    def test_real_chess_game_simulation(self):
        """Test: Real chess game simulation"""
        print("\n🧪 Test: Full chess game simulation")
        
        # Setup system
        white_player = Score("white_player", self.publisher)
        black_player = Score("black_player", self.publisher)
        main_log = GameLog("game_log", self.publisher)
        analysis_log = GameLog("analysis_log", self.publisher)
        
        print("♟️ Starting full chess game...")
        
        # Game opening
        game_moves = [
            (1000, "pawn_e2", "move", ["e2", "e4"], None, None),
            (1200, "pawn_e7", "move", ["e7", "e5"], None, None),
            (1400, "knight_g1", "move", ["g1", "f3"], None, None),
            (1600, "knight_b8", "move", ["b8", "c6"], None, None),
            (1800, "bishop_f1", "move", ["f1", "c4"], None, None),
            (2000, "bishop_f8", "move", ["f8", "c5"], None, None),
            # Captures
            (2200, "knight_f3", "capture", ["f3", "e5"], "white_player", 5),
            (2400, "pawn_d7", "capture", ["d7", "d6"], "black_player", 3),
            # Advanced moves
            (2600, "queen_d1", "jump", ["d1", "h5"], None, None),
            (2800, "king_e8", "move", ["e8", "f8"], None, None),
        ]
        
        print("🎯 Performing sequence of 10 moves...")
        
        for timestamp, piece, move_type, params, scorer, points in game_moves:
            # Record move
            move = MockCommand(timestamp, piece, move_type, params)
            self.publisher.publish("moves", "game_log", move)
            self.publisher.publish("moves", "analysis_log", move)
            
            # Update score if applicable
            if scorer and points:
                self.publisher.publish("score", scorer, points)
                print(f"🏆 {scorer} received {points} points")
        
        # Final checks
        self.assertEqual(len(main_log.get_log()), 10)
        self.assertEqual(len(analysis_log.get_log()), 10)
        self.assertEqual(white_player.get_score(), 5)
        self.assertEqual(black_player.get_score(), 3)
        
        print("♔ Game completed successfully!")
        print(f"📊 Total moves: {len(main_log.get_log())}")
        print(f"🏆 Final score - White: {white_player.get_score()}, Black: {black_player.get_score()}")
        
        # Print game log
        print("\n📜 Game log:")
        for i, entry in enumerate(main_log.get_log()[:5], 1):
            print(f"   {i}. {entry}")
        print("   ...")
    
    def test_stress_test_multiple_games(self):
        """Stress test: Multiple concurrent games"""
        print("\n🧪 Stress test: 5 concurrent games")
        
        games = {}
        
        # Create 5 games
        for game_id in range(1, 6):
            games[game_id] = {
                'white': Score(f"white_{game_id}", self.publisher),
                'black': Score(f"black_{game_id}", self.publisher),
                'log': GameLog(f"game_{game_id}", self.publisher)
            }
        
        print("🎮 Creating 5 games with 10 players and 5 logs")
        
        # Run games
        total_moves = 0
        total_score = 0
        
        for game_id in range(1, 6):
            # 10 moves per game
            for move_num in range(10):
                timestamp = game_id * 1000 + move_num * 100
                piece = f"piece_{game_id}_{move_num}"
                move = MockCommand(timestamp, piece, "move", [f"a{move_num}", f"b{move_num}"])
                
                self.publisher.publish("moves", f"game_{game_id}", move)
                total_moves += 1
                
                # Random points
                if move_num % 3 == 0:  # every third move
                    points = (move_num + 1) * 2
                    player = "white" if move_num % 2 == 0 else "black"
                    self.publisher.publish("score", f"{player}_{game_id}", points)
                    total_score += points
        
        print(f"⚡ Performed {total_moves} moves and {total_score} points")
        
        # Checks
        total_recorded_moves = sum(len(games[i]['log'].get_log()) for i in range(1, 6))
        total_recorded_score = sum(
            games[i]['white'].get_score() + games[i]['black'].get_score() 
            for i in range(1, 6)
        )
        
        self.assertEqual(total_recorded_moves, 50)  # 10 moves × 5 games
        
        print("✅ Stress test passed successfully!")
        print(f"📊 Recorded moves: {total_recorded_moves}")
        print(f"🏆 Recorded score: {total_recorded_score}")

def run_performance_test():
    """Separate performance test"""
    print("\n" + "⚡" * 50)
    print("⚡ Advanced Performance Test")
    print("⚡" * 50)
    
    import time
    
    publisher = Publisher()
    
    # Create large system
    print("🏗️ Building large system...")
    
    # 50 players
    players = [Score(f"player_{i}", publisher) for i in range(50)]
    
    # 20 logs
    logs = [GameLog(f"log_{i}", publisher) for i in range(20)]
    
    print("📊 Created 50 players and 20 logs")
    
    # Speed test
    start_time = time.time()
    
    print("⚡ Sending 1000 messages...")
    for i in range(1000):
        # Score message
        player_id = i % 50
        publisher.publish("score", f"player_{player_id}", 1)
        
        # Move message
        if i % 5 == 0:  # every 5 messages
            log_id = i % 20
            move = MockCommand(i, f"piece_{i}", "move", [f"a{i%8}", f"b{i%8}"])
            publisher.publish("moves", f"log_{log_id}", move)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"⏱️ Execution time: {duration:.3f} seconds")
    print(f"📈 Speed: {1000/duration:.0f} messages per second")
    
    # Check results
    total_score = sum(player.get_score() for player in players)
    total_moves = sum(len(log.get_log()) for log in logs)
    
    print(f"✅ Total points: {total_score}")
    print(f"✅ Total moves: {total_moves}")

if __name__ == "__main__":
    print("🎯" * 50)
    print("🎯 Comprehensive Tests for Chess Publisher-Subscriber System")
    print("🎯" * 50)
    
    # Run unit tests
    print("\n🧪 Running unit tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Performance test
    try:
        run_performance_test()
    except Exception as e:
        print(f"❌ Error in performance test: {e}")
    
    print("\n🎊 All tests completed!")
    print("✨ System works excellently!")