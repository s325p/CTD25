import sys
import os
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from KFC_Py.Command import Command
from .listener import Listener
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from publisher import Publisher

class GameLog(Listener):
    def __init__(self, color: str, publisher: "Publisher"):
        super().__init__(color, "moves", publisher) 
        self._log = []

    def listening(self, cmd: Command):
        self._log.append(self._processing_message(cmd))

    def _processing_message(self, cmd: Command):
        return f"{self.format_millis(cmd.timestamp)}, {cmd.piece_id[:2]}{cmd.piece_id[7]}, {chr(cmd.params[0][0] + ord('a'))}{ cmd.params[0][1]} -> {chr(cmd.params[1][0] + ord('a'))}{ cmd.params[1][1]}"

    def format_millis(self, millis: int) -> str:
        seconds, ms = divmod(millis, 1000)
        minutes, sec = divmod(seconds, 60)
        hours, min_ = divmod(minutes, 60)
        #return f"{hours:02}:{min_:02}:{sec:02}.{ms:03}"
        return f"{hours:02}:{min_:02}:{sec:02}"

    def get_log(self):
        return self._log