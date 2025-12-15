import socket
import json
import threading
import time
from GameFactory import create_game
from GraphicsFactory import ImgFactory

class ChessClient:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.color = None
        self.game_ready = False
        
    def start(self):
        print("Connecting to server...")
        self.socket.connect(('localhost', 8888))
        print("Connected!")
        
        # Start message handler
        threading.Thread(target=self.handle_messages, daemon=True).start()
        
        # Wait for game
        while not self.game_ready:
            time.sleep(0.1)
        
        # Start game
        print(f"Starting chess game as {self.color}")

        import pathlib
        import os
        
        # Find pieces directory
        possible_paths = [
            "../pieces",
            "pieces", 
            "../CTD25_Solutions_SC/pieces",
            "../../pieces"
        ]
        
        pieces_path = None
        for path in possible_paths:
            if os.path.exists(path) and os.path.exists(os.path.join(path, "board.csv")):
                pieces_path = path
                break
        
        if not pieces_path:
            print("Error: Could not find pieces directory")
            return
            
        game = create_game(pieces_path, ImgFactory())
        # Set the player color for single cursor display
        game.my_player_color = self.color
        # Store game instance for receiving moves
        self.game_instance = game
        
        # Override process input to send moves to server
        original_process = game._process_input
        def network_process(cmd):
            if (cmd.piece_id and len(cmd.piece_id) > 1 and 
                cmd.piece_id[1] == ('W' if self.color == 'white' else 'B') and
                cmd.type in ["move", "jump"]):
                # Send to server
                message = {
                    'type': cmd.type,
                    'piece_id': cmd.piece_id,
                    'src_cell': list(cmd.params[0]),
                    'dst_cell': list(cmd.params[1])
                }
                self.socket.send(json.dumps(message).encode())
            # Always process locally too
            original_process(cmd)
        
        game._process_input = network_process
        game.run()
    
    def handle_messages(self):
        while True:
            try:
                data = self.socket.recv(1024)
                if not data:
                    break
                
                msg = json.loads(data.decode())
                
                if msg['type'] == 'color':
                    self.color = msg['color']
                    print(f"You are {self.color}")

                    
                elif msg['type'] == 'start':

                    print("Game starting!")
                    self.game_ready = True
                    
                elif msg['type'] in ['move', 'jump']:
                    # Received move/jump from other player
                    if hasattr(self, 'game_instance') and self.game_instance:
                        from Command import Command
                        cmd = Command(
                            self.game_instance.game_time_ms(),
                            msg['piece_id'],
                            msg['type'],
                            [tuple(msg['src_cell']), tuple(msg['dst_cell'])]
                        )
                        self.game_instance._process_input(cmd)
                        print(f"Applied {msg['type']} from other player: {msg['piece_id']}")
                    
            except:
                break

if __name__ == "__main__":
    try:
        client = ChessClient()
        client.start()
    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit")