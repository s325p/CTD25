import cmd
import queue, threading, time, math, logging, pathlib
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
import numpy as np
import cv2

from Board import Board
from Command import Command
from Piece import Piece
from sounds import Sound
from KeyboardInput import KeyboardProcessor, KeyboardProducer

# Import existing classes
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pub.publisher import Publisher
from pub.score import Score
from pub.game_log import GameLog

# set up a module-level logger
logger = logging.getLogger(__name__)

class InvalidBoard(Exception): ...

class Game:
    def __init__(self, pieces: List[Piece], board: Board):
        if not self._validate(pieces):
            raise InvalidBoard("missing kings")
        self.pieces = pieces
        self.board = board
        self.START_NS = time.monotonic_ns()
        self._time_factor = 1  # for tests
        self.user_input_queue = queue.Queue()  # thread-safe

        # lookup tables ---------------------------------------------------
        self.pos: Dict[Tuple[int, int], List[Piece]] = defaultdict(list)
        self.piece_by_id: Dict[str, Piece] = {p.id: p for p in pieces}

        self.selected_id_1: Optional[str] = None
        self.selected_id_2: Optional[str] = None
        self.last_cursor2: Tuple[int, int] | None = None
        self.last_cursor1: Tuple[int, int] | None = None

        # keyboard helpers ---------------------------------------------------
        self.keyboard_processor: Optional[KeyboardProcessor] = None
        self.keyboard_producer: Optional[KeyboardProducer] = None

        # Using existing classes
        self.publisher = Publisher()
        self.score_white = Score("white", self.publisher)
        self.score_black = Score("black", self.publisher)
        self.game_log_white = GameLog("white", self.publisher)
        self.game_log_black = GameLog("black", self.publisher)
        self.white = 0
        self.black = 0
        
        # List of captured pieces
        self.captured_pieces = []
        
        # Initialize sound system
        self.sound = Sound()
        
        # Extended board dimensions - expanding the side areas
        self.board_size_px = 480  # Board size: 8 cells * 60 pixels per cell
        self.side_panel_width = 150  # Reduced width for side areas
        self.expanded_width = self.board_size_px + (2 * self.side_panel_width)

    def game_time_ms(self) -> int:
        return self._time_factor * (time.monotonic_ns() - self.START_NS) // 1_000_000

    def clone_board(self) -> Board:
        return self.board.clone()

    def start_user_input_thread(self):
        # Determine which player this client is
        if hasattr(self, 'my_player_color'):
            if self.my_player_color == 'white':
                # White player uses arrow keys
                keymap = {
                    "up": "up", "down": "down", "left": "left", "right": "right",
                    "enter": "select", "+": "jump"
                }
                self.kp1 = KeyboardProcessor(self.board.H_cells, self.board.W_cells, keymap=keymap)
                self.kb_prod_1 = KeyboardProducer(self, self.user_input_queue, self.kp1, player=1)
                self.kb_prod_1.start()
                self.kp2 = None
                self.kb_prod_2 = None
            else:
                # Black player uses WASD
                keymap = {
                    "w": "up", "s": "down", "a": "left", "d": "right",
                    "space": "select", "g": "jump"
                }
                self.kp2 = KeyboardProcessor(self.board.H_cells, self.board.W_cells, keymap=keymap)
                self.kb_prod_2 = KeyboardProducer(self, self.user_input_queue, self.kp2, player=2)
                self.kb_prod_2.start()
                self.kp1 = None
                self.kb_prod_1 = None

    def _update_cell2piece_map(self):
        self.pos.clear()
        for p in self.pieces:
            self.pos[p.current_cell()].append(p)

    def _run_game_loop(self, num_iterations=None, is_with_graphics=True):
        it_counter = 0
        while not self._is_win():
            now = self.game_time_ms()

            for p in self.pieces:
                p.update(now)

            self._update_cell2piece_map()

            while not self.user_input_queue.empty():
                cmd: Command = self.user_input_queue.get()
                self._process_input(cmd)

            if is_with_graphics:
                self._draw()
                self._show()

            if not self._is_show():           # returns False if user closed window
                break
            self._resolve_collisions()

            # for testing
            if num_iterations is not None:
                it_counter += 1
                if num_iterations <= it_counter:
                    return

    def run(self, num_iterations=None, is_with_graphics=True):
        # Show countdown before game starts
        if is_with_graphics:
            self._show_countdown()
            
        self.start_user_input_thread()
        start_ms = self.START_NS
        for p in self.pieces:
            p.reset(start_ms)

        self._run_game_loop(num_iterations, is_with_graphics)

        self._announce_win()
        if hasattr(self, 'kb_prod_1') and self.kb_prod_1:
            self.kb_prod_1.stop()
        if hasattr(self, 'kb_prod_2') and self.kb_prod_2:
            self.kb_prod_2.stop()

    def _create_expanded_board(self):
        """Create expanded board with side areas"""
        # Create expanded image - board height matches board size in pixels
        expanded_img = np.zeros((self.board_size_px, self.expanded_width, 3), dtype=np.uint8)
        
        # Paint white player area (left) - green
        expanded_img[:, 0:self.side_panel_width] = (50, 150, 50)
        
        # Paint black player area (right) - blue
        expanded_img[:, self.side_panel_width + self.board_size_px:] = (150, 50, 50)
        
        # Convert current board to RGB if it's RGBA
        current_board = self.curr_board.img.img
        if len(current_board.shape) == 3 and current_board.shape[2] == 4:
            current_board = cv2.cvtColor(current_board, cv2.COLOR_BGRA2BGR)

        # Resize current board to match new board size in pixels
        current_board_resized = cv2.resize(current_board, (self.board_size_px, self.board_size_px))
        
        # Add chess board in the middle
        expanded_img[:, self.side_panel_width:self.side_panel_width + self.board_size_px] = current_board_resized
        
        return expanded_img

    def _add_side_labels(self, expanded_img):
        """Add side labels for players"""
        # White player area (left)
        # WHITE title at the top - smaller font and positions
        cv2.putText(expanded_img, "WHITE PLAYER", (10, 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Draw separator line
        cv2.line(expanded_img, (5, 30), (self.side_panel_width - 5, 30), (255, 255, 255), 1)
        
        # SCORE section
        cv2.putText(expanded_img, "SCORE:", (10, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
        
        # Score number - smaller
        score_text = str(self.score_white.get_score())
        cv2.putText(expanded_img, score_text, (80, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # MOVEMENTS section
        cv2.putText(expanded_img, "MOVEMENTS:", (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
        
        # Draw box for movements - smaller size
        cv2.rectangle(expanded_img, (5, 80), (self.side_panel_width - 5, self.board_size_px - 5), (100, 100, 100), 1)
        
        # Movement list with better spacing
        y_offset = 90
        line_height = 12
        max_moves = int((self.board_size_px - 90) / line_height) - 1  # Adjust to smaller frame
        
        moves = self.game_log_white.get_log()
        for i, move in enumerate(moves[-max_moves:]):  
            if y_offset + i * line_height > self.board_size_px - 10:  
                break
            cv2.putText(expanded_img, move, 
                       (10, y_offset + i * line_height), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
            
        # Black player area (right)
        right_x = self.side_panel_width + self.board_size_px
        
        # BLACK title at the top
        cv2.putText(expanded_img, "BLACK PLAYER", (right_x + 10, 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Draw separator line
        cv2.line(expanded_img, (right_x + 5, 30), (right_x + self.side_panel_width - 5, 30), (255, 255, 255), 1)
        
        # SCORE section
        cv2.putText(expanded_img, "SCORE:", (right_x + 10, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
        
        # Score number - smaller
        score_text = str(self.score_black.get_score())
        cv2.putText(expanded_img, score_text, (right_x + 80, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # MOVEMENTS section
        cv2.putText(expanded_img, "MOVEMENTS:", (right_x + 10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
        
        # Draw box for movements 
        cv2.rectangle(expanded_img, (right_x + 5, 80), (right_x + self.side_panel_width - 5, self.board_size_px - 5), (100, 100, 100), 1)

        # Movement list with better spacing
        y_offset = 90
        moves = self.game_log_black.get_log()
        for i, move in enumerate(moves[-max_moves:]):  
            if y_offset + i * line_height > self.board_size_px - 10:  
                break
            cv2.putText(expanded_img, move, 
                       (right_x + 10, y_offset + i * line_height), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)

    def _draw(self):
        self.curr_board = self.clone_board()
        for p in self.pieces:
            p.draw_on_board(self.curr_board, now_ms=self.game_time_ms())

        # Create expanded board with side areas first
        self.expanded_board_img = self._create_expanded_board()
        self._add_side_labels(self.expanded_board_img)

        # Draw valid moves for selected pieces
        self._draw_valid_moves()

        # Show only my player's cursor
        if hasattr(self, 'my_player_color'):
            if self.my_player_color == 'white' and self.kp1:
                kp = self.kp1
                color = (0, 255, 0)  # Green for white player
                last_attr = 'last_cursor1'
            elif self.my_player_color == 'black' and self.kp2:
                kp = self.kp2
                color = (255, 0, 0)  # Red for black player  
                last_attr = 'last_cursor2'
            else:
                return
                
            r, c = kp.get_cursor()
            cell_H_pix = self.board_size_px // self.board.H_cells
            cell_W_pix = self.board_size_px // self.board.W_cells

            y1 = r * cell_H_pix
            x1 = c * cell_W_pix + self.side_panel_width
            y2 = y1 + cell_H_pix - 1
            x2 = x1 + cell_W_pix - 1
            
            cv2.rectangle(self.expanded_board_img, (x1, y1), (x2, y2), color, 2)

            prev = getattr(self, last_attr, None)
            if prev != (r, c):
                logger.debug("My cursor moved to (%s, %s)", r, c)
                setattr(self, last_attr, (r, c))

    def _draw_valid_moves(self):
        """Draw highlights for valid moves of selected pieces."""
        cell_H_pix = self.board_size_px // self.board.H_cells
        cell_W_pix = self.board_size_px // self.board.W_cells

        # Show valid moves only for my player
        selected_id = None
        if hasattr(self, 'my_player_color'):
            if self.my_player_color == 'white' and hasattr(self, 'kb_prod_1') and self.kb_prod_1:
                selected_id = self.kb_prod_1.selected_id if self.kb_prod_1 else None
                highlight_color = (0, 255, 255)  # Yellow for white player
            elif self.my_player_color == 'black' and hasattr(self, 'kb_prod_2') and self.kb_prod_2:
                selected_id = self.kb_prod_2.selected_id if self.kb_prod_2 else None
                highlight_color = (255, 255, 0)  # Cyan for black player
        
        if selected_id:
            valid_moves = self.get_valid_moves(selected_id)
            for row, col in valid_moves:
                y1 = row * cell_H_pix
                x1 = col * cell_W_pix + self.side_panel_width
                y2 = y1 + cell_H_pix - 1
                x2 = x1 + cell_W_pix - 1
                # Draw highlight for valid moves
                cv2.rectangle(self.expanded_board_img, (x1, y1), (x2, y2), highlight_color, 2)
                # Add a small circle in the center
                center_x = x1 + cell_W_pix // 2
                center_y = y1 + cell_H_pix // 2
                cv2.circle(self.expanded_board_img, (center_x, center_y), 5, highlight_color, -1)

    def _show(self):
        # Display the expanded board
        cv2.imshow("Chess Game", self.expanded_board_img)
        cv2.waitKey(1)

    def _side_of(self, piece_id: str) -> str:
        return piece_id[1]

    def get_valid_moves(self, piece_id: str) -> List[Tuple[int, int]]:
        """Get all valid moves for a given piece."""
        piece = self.piece_by_id.get(piece_id)
        if not piece:
            return []
        
        src_cell = piece.current_cell()
        my_color = piece.id[1]
        
        # Get the piece's moves from its current state
        if not hasattr(piece.state, 'moves') or piece.state.moves is None:
            return []
        
        moves = piece.state.moves
        valid_moves = []
        
        # Check each possible move
        for dr, dc in moves.moves.keys():
            dst_cell = (src_cell[0] + dr, src_cell[1] + dc)
            
            # Check if move is valid
            if moves.is_valid(src_cell, dst_cell, self.pos, 
                            piece.state.physics.is_need_clear_path(), my_color):
                valid_moves.append(dst_cell)
        
        return valid_moves

    def _process_input(self, cmd: Command):
        mover = self.piece_by_id.get(cmd.piece_id)
        if not mover:
            logger.debug("Unknown piece id %s", cmd.piece_id)
            return

        # Fix position sync issue - ensure the command source matches piece location
        if cmd.type == "move" and len(cmd.params) >= 2:
            piece_current_cell = mover.current_cell()
            command_src_cell = cmd.params[0]
            
            if piece_current_cell != command_src_cell:
                logger.warning(f"Position mismatch for {cmd.piece_id}: piece at {piece_current_cell}, command from {command_src_cell}")
                # Update the command to use the actual piece location
                cmd.params[0] = piece_current_cell

        flag = mover.on_command(cmd, self.pos)
        # Send to appropriate log only for MOVE commands
        if flag == True:
            if cmd.type == "move":
                if cmd.piece_id[1] == 'W':
                    self.publisher.publish("moves", "white", cmd)
                else:
                    self.publisher.publish("moves", "black", cmd)

    def _resolve_collisions(self):
        self._update_cell2piece_map()
        occupied = self.pos

        # Check for pawn promotion first
        self._check_pawn_promotion()

        for cell, plist in occupied.items():
            if len(plist) < 2:
                continue

            # Special handling for Knight moves - only allow collision at destination
            knights_moving = []
            other_pieces = []
            
            for p in plist:
                # Check if this is a knight currently moving
                if (p.id.startswith(('NW', 'NB')) and 
                    hasattr(p.state, 'name') and p.state.name == "move"):
                    knights_moving.append(p)
                else:
                    other_pieces.append(p)
            
            # If there are moving knights, only allow collision if knight reached destination
            if knights_moving:
                knight = knights_moving[0]  # Should only be one knight per cell
                
                # Check if knight has reached its destination
                if hasattr(knight.state.physics, '_end_cell'):
                    destination = knight.state.physics._end_cell
                    current_cell = knight.current_cell()
                    
                    # Only resolve collision if knight is at its final destination
                    if current_cell != destination:
                        continue  # Skip collision resolution for intermediate positions
                
                # Knight at destination wins over stationary pieces
                winner = knight
            else:
                # Regular collision resolution for non-knight pieces
                moving_pieces = []
                stationary_pieces = []
                
                for p in plist:
                    # Check if piece is currently moving (not idle)
                    if hasattr(p.state, 'name') and p.state.name != "idle":
                        moving_pieces.append(p)
                    else:
                        stationary_pieces.append(p)
                
                # If there are moving pieces, they take priority
                if moving_pieces:
                    # Among moving pieces, choose the one that entered most recently
                    winner = max(moving_pieces, key=lambda p: p.state.physics.get_start_ms())
                else:
                    # If all pieces are stationary, choose the one that entered most recently
                    winner = max(plist, key=lambda p: p.state.physics.get_start_ms())

            # Determine if captures allowed: default allow
            if not winner.state.can_capture():
                # Allow capture even for idle pieces to satisfy game rules
                pass

            # Remove every other piece that *can be captured*
            captured_pieces = []
            for p in plist:
                if p is winner:
                    continue
                if p.state.can_be_captured():
                    self.pieces.remove(p)
                    captured_pieces.append(p)
                    
                    points = {
                        "P": 100,
                        "N": 300,
                        "B": 500,
                        "R": 500,
                        "Q": 1000,
                        "K": 1000000,
                    }

                    currPoint = points[p.id[0]]
                    if p.id[1] == 'B':
                        self.publisher.publish("score", "white", currPoint)
                    else:
                        self.publisher.publish("score", "black", currPoint)
                    
                    # Play capture sound
                    self.sound.play("sounds/Boom_sound.wav")

            # Check if a king was captured
            for captured in captured_pieces:
                if captured.id.startswith(('KW', 'KB')):
                    # Play victory sound
                    self.sound.play("sounds/applause.wav")
                    time.sleep(2)
                    
                    # Determine winner and show appropriate image based on player
                    if captured.id.startswith('KW'):
                        # White king captured, black wins
                        if hasattr(self, 'my_player_color'):
                            if self.my_player_color == 'black':
                                # Show black win image
                                img_paths = ["../pic/black_win.png", "pic/black_win.png", "../CTD25_Solutions_SC/pic/black_win.png", "../../pic/black_win.png"]
                                winner_text = "YOU WIN!"
                            else:
                                # Show white loser image
                                img_paths = ["../pic/white_loser.png", "pic/white_loser.png", "../CTD25_Solutions_SC/pic/white_loser.png", "../../pic/white_loser.png"]
                                winner_text = "YOU LOSE!"
                        else:
                            img_paths = ["../pic/black_win.png", "pic/black_win.png", "../CTD25_Solutions_SC/pic/black_win.png", "../../pic/black_win.png"]
                            winner_text = "BLACK WINS!"
                    else:
                        # Black king captured, white wins
                        if hasattr(self, 'my_player_color'):
                            if self.my_player_color == 'white':
                                # Show white win image
                                img_paths = ["../pic/white_win.png", "pic/white_win.png", "../CTD25_Solutions_SC/pic/white_win.png", "../../pic/white_win.png"]
                                winner_text = "YOU WIN!"
                            else:
                                # Show black loser image
                                img_paths = ["../pic/black_loser.png", "pic/black_loser.png", "../CTD25_Solutions_SC/pic/black_loser.png", "../../pic/black_loser.png"]
                                winner_text = "YOU LOSE!"
                        else:
                            img_paths = ["../pic/white_win.png", "pic/white_win.png", "../CTD25_Solutions_SC/pic/white_win.png", "../../pic/white_win.png"]
                            winner_text = "WHITE WINS!"
                    
                    # Try to find and display victory/defeat image
                    result_img = None
                    for img_path in img_paths:
                        try:
                            result_img = cv2.imread(img_path)
                            if result_img is not None:
                                break
                        except:
                            continue
                    
                    if result_img is not None:
                        # Display result image
                        result_img = cv2.resize(result_img, (self.board_size_px, self.board_size_px))
                        expanded_img_for_result = np.zeros((self.board_size_px, self.expanded_width, 3), dtype=np.uint8)
                        expanded_img_for_result[:, self.side_panel_width:self.side_panel_width + self.board_size_px] = result_img
                        cv2.imshow("Chess Game", expanded_img_for_result)
                        cv2.waitKey(5000)
                    else:
                        # Show text result message if no image
                        expanded_img_for_result = np.zeros((self.board_size_px, self.expanded_width, 3), dtype=np.uint8)
                        text_color = (0, 255, 0) if "WIN" in winner_text else (0, 0, 255)
                        cv2.putText(expanded_img_for_result, winner_text, (self.expanded_width//4, self.board_size_px//2), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 2, text_color, 3)
                        cv2.imshow("Chess Game", expanded_img_for_result)
                        cv2.waitKey(5000)
                    
                    return

    def _check_pawn_promotion(self):
        """Check if any pawns have reached the opposite end and promote them to queens."""
        promoted_pawns = []
        
        for piece in self.pieces:
            # Check if this is a pawn
            if piece.id.startswith(('PW', 'PB')):
                row, col = piece.current_cell()
                
                # Check if pawn reached the opposite end
                if ((piece.id[1] == 'W' and row == 0) or  # White pawn reached top
                    (piece.id[1] == 'B' and row == (self.board.H_cells - 1))):   # Black pawn reached bottom 
                    promoted_pawns.append(piece)
        
        # Promote pawns to queens
        for pawn in promoted_pawns:
            # Create new queen ID
            color = pawn.id[1]  # W or B
            new_queen_id = f"Q{color}_{pawn.id[2:]}"  # Replace P with Q, keep rest of ID
            
            # Get the queen piece factory to create a new queen
            from PieceFactory import PieceFactory
            from GraphicsFactory import GraphicsFactory, ImgFactory
            import os
            
            # Find pieces directory
            pieces_paths = ["../pieces", "pieces", "../CTD25_Solutions_SC/pieces"]
            pieces_root = None
            for path in pieces_paths:
                if os.path.exists(path):
                    pieces_root = pathlib.Path(path)
                    break
            
            if not pieces_root:
                continue  # Skip promotion if no pieces directory
                
            gfx_factory = GraphicsFactory(ImgFactory())
            pf = PieceFactory(self.board, pieces_root, graphics_factory=gfx_factory)
            
            try:
                new_queen = pf.create_piece(f"Q{color}", pawn.current_cell())
                new_queen.id = new_queen_id  # Set the specific ID
                
                # Remove pawn and add queen
                self.pieces.remove(pawn)
                self.pieces.append(new_queen)
                
                # Update piece lookup
                del self.piece_by_id[pawn.id]
                self.piece_by_id[new_queen_id] = new_queen
                
                # Silently skip promotion if queen files missing
                pass
                
            except Exception as e:
                # Silently skip promotion if queen files missing
                pass

    def _validate(self, pieces):
        """Ensure both kings present and no two pieces share a cell."""
        has_white_king = has_black_king = False
        seen_cells: dict[tuple[int, int], str] = {}
        for p in pieces:
            cell = p.current_cell()
            if cell in seen_cells:
                if seen_cells[cell] == p.id[1]:
                    return False
            else:
                seen_cells[cell] = p.id[1]
            if p.id.startswith("KW"):
                has_white_king = True
            elif p.id.startswith("KB"):
                has_black_king = True
        return has_white_king and has_black_king

    def _is_win(self) -> bool:
        kings = [p for p in self.pieces if p.id.startswith(('KW', 'KB'))]
        return len(kings) < 2

    def _announce_win(self):
        self.sound = Sound()
        self.sound.play("sounds/applause.wav")
        text = 'Black wins!' if any(p.id.startswith('KB') for p in self.pieces) else 'White wins!'
        logger.info(text)

    
    def _show_countdown(self):
        """Show countdown before game starts"""
        # Create base board for countdown
        self.curr_board = self.clone_board()
        expanded_img = self._create_expanded_board()
        
        # Show GAME START
        countdown_img = expanded_img.copy()
        cv2.putText(countdown_img, "GAME START", 
                   (self.expanded_width//2 - 100, self.board_size_px//2 - 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
        cv2.imshow("Chess Game", countdown_img)
        cv2.waitKey(1000)
        
        # Countdown 3, 2, 1
        for i in [3, 2, 1]:
            countdown_img = expanded_img.copy()
            cv2.putText(countdown_img, str(i), 
                       (self.expanded_width//2 - 30, self.board_size_px//2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 0, 255), 5)
            cv2.imshow("Chess Game", countdown_img)
            cv2.waitKey(1000)
    
    def _is_show(self) -> bool:
        """ESC closes window"""
        key = cv2.waitKey(50)
        return key != 27