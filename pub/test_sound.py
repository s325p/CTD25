import unittest
from unittest.mock import Mock, patch, MagicMock
import pygame
import time
import os
from KFC_Py.sounds import Sounds

class TestSounds(unittest.TestCase):
    """Tests for the Sounds class"""
    
    def setUp(self):
        """Setup for each test"""
        print(f"\n🎵 Starting test: {self._testMethodName}")
        self.sounds = Sounds()
    
    def tearDown(self):
        """Cleanup after each test"""
        try:
            self.sounds.stop()
            pygame.mixer.quit()
        except:
            pass
        print(f"✅ Test completed: {self._testMethodName}")
    
    def test_initialization(self):
        """Test: Check correct initialization"""
        print("🧪 Testing class initialization...")
        
        # Check that the class was created
        self.assertIsNotNone(self.sounds)
        
        # Check that _sound variable is initialized to None
        self.assertIsNone(self.sounds._sound)
        
        # Check that pygame.mixer is working
        self.assertTrue(pygame.mixer.get_init())
        
        print("✅ Initialization successful!")
    
    @patch('pygame.mixer.Sound')
    def test_play_success(self, mock_sound):
        """Test: Successfully playing a sound file"""
        print("🧪 Testing sound file playback...")
        
        # Setup mock
        mock_sound_instance = MagicMock()
        mock_sound.return_value = mock_sound_instance
        
        # Call the function
        self.sounds.play("test_sound.wav")
        
        # Checks
        mock_sound.assert_called_once_with("test_sound.wav")
        mock_sound_instance.play.assert_called_once()
        self.assertEqual(self.sounds._sound, mock_sound_instance)
        
        print("✅ Sound file playback works!")
    
    @patch('pygame.mixer.Sound')
    @patch('builtins.print')
    def test_play_file_not_found(self, mock_print, mock_sound):
        """Test: Sound file not found"""
        print("🧪 Testing handling of non-existent file...")
        
        # Setup error
        mock_sound.side_effect = pygame.error("File not found")
        
        # Call the function
        self.sounds.play("non_existent.wav")
        
        # Check that error message was printed
        mock_print.assert_called_once()
        args = mock_print.call_args[0][0]
        self.assertIn("faild", args)
        
        print("✅ Error handling works!")
    
    def test_stop_without_sound(self):
        """Test: Stopping when no sound file is playing"""
        print("🧪 Testing stop without sound file...")
        
        # Call stop when no file is playing
        try:
            self.sounds.stop()
            print("✅ Stop without sound file works!")
        except Exception as e:
            self.fail(f"Stop without sound file caused error: {e}")
    
    @patch('pygame.mixer.Sound')
    def test_stop_with_sound(self, mock_sound):
        """Test: Stopping a sound file"""
        print("🧪 Testing sound file stopping...")
        
        # Setup mock
        mock_sound_instance = MagicMock()
        mock_sound.return_value = mock_sound_instance
        
        # Play and stop
        self.sounds.play("test.wav")
        self.sounds.stop()
        
        # Check that stop was called
        mock_sound_instance.stop.assert_called_once()
        
        print("✅ Sound file stopping works!")
    
    @patch('pygame.mixer.Sound')
    def test_multiple_plays(self, mock_sound):
        """Test: Playing multiple files in sequence"""
        print("🧪 Testing multiple file playback...")
        
        mock_sound_instance = MagicMock()
        mock_sound.return_value = mock_sound_instance
        
        # Play multiple files
        files = ["sound1.wav", "sound2.wav", "sound3.wav"]
        for file in files:
            self.sounds.play(file)
        
        # Check that all files were played
        self.assertEqual(mock_sound.call_count, 3)
        self.assertEqual(mock_sound_instance.play.call_count, 3)
        
        print("✅ Multiple file playback works!")
    
    def test_play_and_stop_sequence(self):
        """Test: Play and stop sequence"""
        print("🧪 Testing play and stop sequence...")
        
        with patch('pygame.mixer.Sound') as mock_sound:
            mock_sound_instance = MagicMock()
            mock_sound.return_value = mock_sound_instance
            
            # Sequence of operations
            self.sounds.play("test.wav")
            self.assertIsNotNone(self.sounds._sound)
            
            self.sounds.stop()
            mock_sound_instance.stop.assert_called_once()
            
            # Additional playback
            self.sounds.play("test2.wav")
            self.assertEqual(mock_sound.call_count, 2)
        
        print("✅ Play and stop sequence works!")

class TestSoundsIntegration(unittest.TestCase):
    """Integration tests with real sound files"""
    
    def setUp(self):
        self.sounds = Sounds()
        # Path to the sounds folder relative to the parent directory
        self.sounds_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sounds")
        self.test_sound_file = os.path.join(self.sounds_dir, "applause.wav")
    
    def tearDown(self):
        self.sounds.stop()
    
    def test_sounds_directory_exists(self):
        """Test: Check if sounds directory exists"""
        print("🧪 Testing sounds directory existence...")
        
        self.assertTrue(os.path.exists(self.sounds_dir), 
                       f"Sounds directory not found at: {self.sounds_dir}")
        
        print(f"✅ Sounds directory found at: {self.sounds_dir}")
    
    def test_applause_file_exists(self):
        """Test: Check if applause.wav file exists"""
        print("🧪 Testing applause.wav file existence...")
        
        self.assertTrue(os.path.exists(self.test_sound_file), 
                       f"applause.wav not found at: {self.test_sound_file}")
        
        print(f"✅ applause.wav found at: {self.test_sound_file}")
    
    def test_real_sound_playback(self):
        """Test with real sound file"""
        print("🧪 Testing with real sound file...")
        
        if not os.path.exists(self.test_sound_file):
            self.skipTest(f"Test file not found: {self.test_sound_file}")
        
        # Playback
        try:
            self.sounds.play(self.test_sound_file)
            self.assertIsNotNone(self.sounds._sound)
            
            # Short wait
            time.sleep(0.1)
            
            # Stop
            self.sounds.stop()
            
            print("✅ Real file playback and stop works!")
            
        except Exception as e:
            self.fail(f"Error playing real file: {e}")
    
    def test_invalid_file_path(self):
        """Test: Invalid file path handling"""
        print("🧪 Testing invalid file path...")
        
        invalid_path = os.path.join(self.sounds_dir, "non_existent.wav")
        
        # Should not raise exception, but should print error
        with patch('builtins.print') as mock_print:
            self.sounds.play(invalid_path)
            mock_print.assert_called_once()
        
        print("✅ Invalid file path handled correctly!")

def run_manual_test():
    """Manual test for real audio playback"""
    print("\n" + "🎵" * 50)
    print("🎵 Manual Test for Audio Playback")
    print("🎵" * 50)
    
    sounds = Sounds()
    
    # Get the sounds directory path
    current_dir = os.path.dirname(__file__)
    sounds_dir = os.path.join(os.path.dirname(current_dir), "sounds")
    applause_file = os.path.join(sounds_dir, "applause.wav")
    
    print(f"🔍 Looking for sound file at: {applause_file}")
    
    if os.path.exists(applause_file):
        print(f"🔊 Playing: applause.wav")
        sounds.play(applause_file)
        
        input("⏸️ Press Enter to stop and continue...")
        sounds.stop()
        print("⏹️ Stopped")
        
        # Test multiple plays
        print("\n🔁 Testing rapid play/stop sequence...")
        for i in range(3):
            print(f"  🔊 Play #{i+1}")
            sounds.play(applause_file)
            time.sleep(0.5)
            sounds.stop()
            time.sleep(0.2)
        
        print("✅ Manual test completed successfully!")
        
    else:
        print("❌ applause.wav not found!")
        print(f"💡 Expected path: {applause_file}")
        print("💡 Please ensure the file exists in the sounds directory")
        
        # List what's actually in the sounds directory
        if os.path.exists(sounds_dir):
            print(f"\n📁 Contents of {sounds_dir}:")
            for item in os.listdir(sounds_dir):
                print(f"  - {item}")
        else:
            print(f"❌ Sounds directory doesn't exist: {sounds_dir}")

def run_file_discovery():
    """Discover available sound files"""
    print("\n" + "🔍" * 50)
    print("🔍 Sound File Discovery")
    print("🔍" * 50)
    
    current_dir = os.path.dirname(__file__)
    sounds_dir = os.path.join(os.path.dirname(current_dir), "sounds")
    
    print(f"📂 Current script location: {current_dir}")
    print(f"📂 Expected sounds directory: {sounds_dir}")
    
    if os.path.exists(sounds_dir):
        print(f"\n✅ Sounds directory found!")
        print(f"📁 Contents:")
        
        sound_files = []
        for item in os.listdir(sounds_dir):
            item_path = os.path.join(sounds_dir, item)
            if os.path.isfile(item_path):
                file_size = os.path.getsize(item_path)
                print(f"  📄 {item} ({file_size} bytes)")
                if item.lower().endswith(('.wav', '.mp3', '.ogg')):
                    sound_files.append(item)
        
        if sound_files:
            print(f"\n🎵 Found {len(sound_files)} audio files:")
            for sound_file in sound_files:
                print(f"  🔊 {sound_file}")
        else:
            print("\n❌ No audio files found!")
    else:
        print(f"\n❌ Sounds directory not found!")
        print(f"📂 Create directory: {sounds_dir}")

if __name__ == "__main__":
    print("🎯" * 50)
    print("🎯 Tests for Sounds Class")
    print("🎯" * 50)
    
    # File discovery first
    run_file_discovery()
    
    # Automated tests
    print("\n🤖 Running automated tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Manual test
    choice = input("\n🎵 Run manual test with real audio? (y/n): ")
    if choice.lower() == 'y':
        run_manual_test()
    
    print("\n🎊 All tests completed!")