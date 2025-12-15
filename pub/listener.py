#בס"ד
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List
if TYPE_CHECKING:
    from publisher import Publisher

class Listener(ABC):
    def __init__(self, id: str, channel: str, publisher: "Publisher"):
        publisher.new_listener(id, channel, self)


    @abstractmethod
    def listening(self, message):
        pass

