"""Command Pattern (Python)
- Encapsulate a request as an object
- Support undo/redo
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List

# Receiver
class TextDocument:
    def __init__(self):
        self.text = ""
    def insert(self, s: str):
        self.text += s
    def delete_last(self, n: int):
        self.text = self.text[:-n] if n <= len(self.text) else ""

# Command interface
class Command:
    def execute(self):
        raise NotImplementedError
    def undo(self):
        raise NotImplementedError

@dataclass
class InsertCommand(Command):
    doc: TextDocument
    s: str
    def execute(self):
        self.doc.insert(self.s)
    def undo(self):
        self.doc.delete_last(len(self.s))

# Invoker with history
class Editor:
    def __init__(self):
        self._undo: List[Command] = []
        self._redo: List[Command] = []
    def run(self, cmd: Command):
        cmd.execute()
        self._undo.append(cmd)
        self._redo.clear()
    def undo(self):
        if not self._undo:
            return
        cmd = self._undo.pop()
        cmd.undo()
        self._redo.append(cmd)
    def redo(self):
        if not self._redo:
            return
        cmd = self._redo.pop()
        cmd.execute()
        self._undo.append(cmd)

if __name__ == "__main__":
    doc = TextDocument()
    ed = Editor()
    ed.run(InsertCommand(doc, "Hello "))
    ed.run(InsertCommand(doc, "World"))
    print("After inserts:", doc.text)
    ed.undo()
    print("After undo:", doc.text)
    ed.redo()
    print("After redo:", doc.text)
