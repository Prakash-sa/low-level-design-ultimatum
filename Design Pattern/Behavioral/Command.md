# Command Pattern

> Encapsulate a request as an object, allowing parameterization of clients with different requests, queuing of requests, and logging of the requests.

---

## Problem

You need to support undo/redo operations, queue commands for later execution, or log commands without tightly coupling the sender and receiver.

## Solution

The Command pattern encapsulates requests as objects. This allows treating commands as first-class objects that can be stored, passed, and executed.

---

## Implementation

```python
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

# Concrete Commands
@dataclass
class InsertCommand(Command):
    doc: TextDocument
    s: str
    
    def execute(self):
        self.doc.insert(self.s)
    
    def undo(self):
        self.doc.delete_last(len(self.s))

@dataclass
class DeleteCommand(Command):
    doc: TextDocument
    n: int
    deleted_text: str = ""
    
    def execute(self):
        self.deleted_text = self.doc.text[-self.n:] if self.n <= len(self.doc.text) else self.doc.text
        self.doc.delete_last(self.n)
    
    def undo(self):
        self.doc.insert(self.deleted_text)

# Invoker with command history
class Editor:
    def __init__(self):
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []
    
    def execute(self, cmd: Command):
        cmd.execute()
        self._undo_stack.append(cmd)
        self._redo_stack.clear()
    
    def undo(self):
        if not self._undo_stack:
            print("Nothing to undo")
            return
        cmd = self._undo_stack.pop()
        cmd.undo()
        self._redo_stack.append(cmd)
    
    def redo(self):
        if not self._redo_stack:
            print("Nothing to redo")
            return
        cmd = self._redo_stack.pop()
        cmd.execute()
        self._undo_stack.append(cmd)
    
    def show_state(self):
        print(f"Document: '{self._undo_stack[-1].doc.text if self._undo_stack else 'empty'}'")

# Demo
if __name__ == "__main__":
    doc = TextDocument()
    editor = Editor()
    
    editor.execute(InsertCommand(doc, "Hello "))
    print(f"After insert 'Hello ': {doc.text}")
    
    editor.execute(InsertCommand(doc, "World"))
    print(f"After insert 'World': {doc.text}")
    
    editor.undo()
    print(f"After undo: {doc.text}")
    
    editor.undo()
    print(f"After undo: {doc.text}")
    
    editor.redo()
    print(f"After redo: {doc.text}")
```

---

## Key Concepts

- **Command Object**: Encapsulates a request with all necessary data
- **Receiver**: The object that performs the actual work (TextDocument)
- **Invoker**: Stores and executes commands (Editor)
- **Undo/Redo Stack**: Maintains history of executed commands

---

## When to Use

✅ Need to implement undo/redo functionality  
✅ Want to queue, log, or defer execution  
✅ Need to parameterize objects with operations  
✅ Building a macro or script system  

---

## Interview Q&A

**Q1: How do you implement undo/redo in Command pattern?**

A: Maintain two stacks:
- **Undo stack**: Stores executed commands. Pop from stack and call `undo()`
- **Redo stack**: Stores undone commands. Pop from stack and call `execute()`. Clear on new command.

```python
def undo(self):
    if self._undo_stack:
        cmd = self._undo_stack.pop()
        cmd.undo()
        self._redo_stack.append(cmd)
```

---

**Q2: What's the difference between Command and Strategy patterns?**

A:
- **Command**: Encapsulates requests as objects. Focuses on HOW to execute something (undo/redo, queuing).
- **Strategy**: Encapsulates algorithms. Focuses on WHAT algorithm to use (sorting, filtering).

Commands are typically stored and executed later. Strategies are usually selected upfront and swapped.

---

**Q3: How would you handle macro recording (sequence of commands)?**

A:
```python
class MacroCommand(Command):
    def __init__(self):
        self.commands: List[Command] = []
    
    def add(self, cmd: Command):
        self.commands.append(cmd)
    
    def execute(self):
        for cmd in self.commands:
            cmd.execute()
    
    def undo(self):
        for cmd in reversed(self.commands):
            cmd.undo()
```

---

**Q4: Can you thread-safely execute commands?**

A: Use a queue with a background worker:
```python
import threading
import queue

class CommandQueue:
    def __init__(self):
        self.q = queue.Queue()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()
    
    def _worker(self):
        while True:
            cmd = self.q.get()
            cmd.execute()
            self.q.task_done()
    
    def execute(self, cmd: Command):
        self.q.put(cmd)
```

---

**Q5: What happens if `undo()` modifies state that other commands depend on?**

A: This is a critical issue. Solutions:
1. **Memento Pattern**: Store full state snapshot instead of incremental undo
2. **Transaction Log**: Maintain immutable log of all changes
3. **Causal Ordering**: Ensure commands execute in correct dependency order
4. **Conflict Resolution**: If undo conflicts with subsequent command, flag error

---

## Trade-offs

✅ **Pros**: Decouples sender/receiver, enables undo/redo, supports queuing/logging  
❌ **Cons**: More objects to manage, potential memory overhead for large command histories

---

## Real-World Examples

- **Text editors** (Undo/Redo in VS Code, Word)
- **Transaction systems** (Database commits/rollbacks)
- **Game development** (Input handling, replay system)
- **Job scheduling** (Queued tasks, retry logic)
