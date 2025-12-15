#בס"ד
from typing import Dict, List
from .listener import Listener


class Publisher:  
    def __init__(self):
        self._channels: Dict[str, Dict[str, Listener]] = {}
        self._channels["moves"] = {}
        self._channels["score"] = {}
        # self._channels["sounds"] = {}

    def new_listener(self, id: str, channel: str, listener: Listener):
            if channel not in self._channels:
                raise ValueError(f"Channel {channel} does not exist.")
            self._channels[channel][id] = listener

    def publish(self, channel: str, id: str, message):
        self._channels[channel][id].listening(message)