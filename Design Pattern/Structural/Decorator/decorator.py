"""Decorator Pattern (Python)
- Add behavior to objects dynamically
"""
from typing import Protocol

class Notifier(Protocol):
    def send(self, msg: str) -> None: ...

class EmailNotifier:
    def send(self, msg: str) -> None:
        print(f"EMAIL: {msg}")

class SMSDecorator:
    def __init__(self, wrap: Notifier):
        self._wrap = wrap
    def send(self, msg: str) -> None:
        self._wrap.send(msg)
        print(f"SMS: {msg}")

class SlackDecorator:
    def __init__(self, wrap: Notifier):
        self._wrap = wrap
    def send(self, msg: str) -> None:
        self._wrap.send(msg)
        print(f"SLACK: {msg}")

if __name__ == "__main__":
    n: Notifier = EmailNotifier()
    n = SMSDecorator(n)
    n = SlackDecorator(n)
    n.send("Build completed successfully")
