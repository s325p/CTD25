#בס"ד
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from KFC_Py.Command import Command
from .listener import Listener
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from publisher import Publisher

class Score(Listener):
    def __init__(self, color: str, publisher: "Publisher"):
        publisher.new_listener(color, "score", self)
        self._score =  0
  
    def listening(self, points: int):
        self._score += points 

    def get_score(self):
        return self._score
        
