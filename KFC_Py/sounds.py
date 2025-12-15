import pygame

class Sound:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self._sound = None

    def play(self, sound_file: str):
        try:
            # Check multiple paths
            import os
            paths = [sound_file, f"../{sound_file}", f"../CTD25_Solutions_SC/{sound_file}"]
            
            for path in paths:
                if os.path.exists(path):
                    self._sound = pygame.mixer.Sound(path)
                    self._sound.play()
                    return
        except:
            pass  # Ignore sound errors

    def stop(self):
        if self._sound:
            self._sound.stop()