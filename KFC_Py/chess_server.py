import socket
import threading
import json

class ChessServer:
    def __init__(self):
        self.white_client = None
        self.black_client = None
        self.lock = threading.Lock()
        
    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('localhost', 8888))
        server.listen(2)
        print("Chess server started on localhost:8888")
        
        while True:
            client, addr = server.accept()
            print(f"New client: {addr}")
            threading.Thread(target=self.handle_client, args=(client,)).start()
    
    def handle_client(self, client):
        with self.lock:
            if self.white_client is None:
                self.white_client = client
                color = 'white'
            elif self.black_client is None:
                self.black_client = client
                color = 'black'
            else:
                client.close()
                return
        
        print(f"Assigned {color}")
        client.send(json.dumps({'type': 'color', 'color': color}).encode())
        
        # Start game if both connected
        with self.lock:
            if self.white_client and self.black_client:
                print("Both players connected - starting game")
                msg = json.dumps({'type': 'start'}).encode()
                try:
                    self.white_client.send(msg)
                    self.black_client.send(msg)
                except:
                    pass
        
        # Handle messages
        try:
            while True:
                data = client.recv(1024)
                if not data:
                    break
                
                try:
                    message = json.loads(data.decode())                    
                    # Forward move/jump to other player
                    if message.get('type') in ['move', 'jump']:
                        with self.lock:
                            other_client = self.black_client if color == 'white' else self.white_client
                            if other_client:
                                try:
                                    other_client.send(json.dumps(message).encode())
                                except:
                                    pass
                except:
                    pass
        except:
            pass
        finally:
            with self.lock:
                if client == self.white_client:
                    self.white_client = None
                    print("White disconnected")
                elif client == self.black_client:
                    self.black_client = None
                    print("Black disconnected")
            client.close()

if __name__ == "__main__":
    ChessServer().start()