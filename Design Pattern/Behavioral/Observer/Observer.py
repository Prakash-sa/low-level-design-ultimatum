"""Observer Pattern (Python)
- Subjects notify observers about state changes
"""
# It's common for different components of an app to respond to events or state changes, 
# but how can we communicate these events?
# The Observer pattern is a popular solution. We have a Subject (aka Publisher) which will be the source of events.
#  And we could have multiple Observers (aka Subscribers) which will recieve events from the Subject in realtime.

## pub/sub

class YoutubeChannel:
    def __init__(self,name):
        self.name=name
        self.subscribers=[]

    def subscribe(self,sub):
        self.subscribes.append(sub)
    
    def notify(self,event):
        for sub in self.subscribers:
            sub.sendNotification(self.name,event)

from abc import ABC,abstractmethod


class YoutubeSubscriber(ABC):
    @abstractmethod
    def sendNotification(self,event):
        pass

class YoutubeUser(YoutubeSubscriber):
    def __init__(self,name):
        self.name=name

    def sendNotification(self,channel,event):
        print(f"User {self.name} received notification from {channel}: {event}")

channel=YoutubeChannel("neetcode")

channel.subscribe(YoutubeUser("sub1"))
channel.subscribe(YoutubeUser("sub2"))
channel.subscribe(YoutubeUser("sub3"))

## Another example

from typing import Callable, List, Dict, Any

class Subject:
    def __init__(self):
        self._observers: List[Callable[[str, Dict[str, Any]], None]] = []
        self._state: Dict[str, Any] = {}
    def attach(self, fn: Callable[[str, Dict[str, Any]], None]):
        self._observers.append(fn)
    def detach(self, fn: Callable[[str, Dict[str, Any]], None]):
        self._observers = [o for o in self._observers if o != fn]
    def set(self, key: str, value: Any):
        self._state[key] = value
        self._emit("changed", {key: value})
    def _emit(self, name: str, payload: Dict[str, Any]):
        for o in self._observers:
            try:
                o(name, payload)
            except Exception:
                pass

if __name__ == "__main__":
    subject = Subject()
    subject.attach(lambda ev, p: print(f"[OBSERVER] {ev} -> {p}"))
    subject.set("temperature", 23)
    subject.set("status", "ok")
