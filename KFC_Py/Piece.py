from __future__ import annotations

from Board import Board
from Command import Command
from typing import Callable, Dict, List, Tuple


class Piece:
    def __init__(self, piece_id: str, init_state):
        self.id = piece_id
        self.state = init_state

    def on_command(self, cmd: Command, cell2piece: Dict[Tuple[int, int], List[Piece]]):
        """Process a command and potentially transition to a new state."""
        my_color = self.id[1]
        self.state, flag = self.state.on_command(cmd, cell2piece, my_color)
        return flag

    def reset(self, start_ms: int):
        cell = self.current_cell()
        flag = self.state.reset(Command(start_ms, self.id, "idle", [cell]))
        return flag

    def update(self, now_ms: int):
        self.state, flag = self.state.update(now_ms)
        return flag

    def is_movement_blocker(self) -> bool:
        return self.state.physics.is_movement_blocker()

    def draw_on_board(self, board, now_ms: int):
        x, y = self.state.physics.get_pos_pix()
        sprite = self.state.graphics.get_img()
        
        # Center the piece in the cell
        # Calculate the center offset to position the sprite in the middle of the cell
        center_offset_x = (board.cell_W_pix - sprite.img.shape[1]) // 2
        center_offset_y = (board.cell_H_pix - sprite.img.shape[0]) // 2
        
        # Apply the centering offset
        centered_x = x + center_offset_x
        centered_y = y + center_offset_y
        
        sprite.draw_on(board.img, centered_x, centered_y)  # <-- paste the piece centered

    # ────────────────────────────────────────────────────────────────────
    # Abstraction helper – SINGLE public accessor so other modules don't have
    # to reach deep into `state → physics` implementation details.
    # Does **not** mutate internal state, so thread-safe without extra locks.
    def current_cell(self) -> tuple[int, int]:
        """Return the piece's board cell as (row, col)."""
        return self.state.physics.get_curr_cell()
