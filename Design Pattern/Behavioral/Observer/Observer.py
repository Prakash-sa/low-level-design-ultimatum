"""Observer Pattern (Python)
- Subjects notify observers about state changes
"""
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
