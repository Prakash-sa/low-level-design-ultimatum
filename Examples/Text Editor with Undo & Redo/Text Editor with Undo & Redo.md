# Text Editor with Undo & Redo — 75-Minute Interview Guide

Single-user editor that supports insert/delete/replace with robust undo/redo stacks, pluggable formatting strategy, and event notifications. Scope: in-memory text, single thread, doc < 1MB.

## Timeline (75 minutes)
| Time | Phase | Output |
|------|-------|--------|
| 0–5 | Requirements | Ops, constraints, assumptions agreed |
| 5–15 | Architecture | Command interface, stacks, events |
| 15–35 | Core Entities | Document, Session, Commands, Strategies |
| 35–55 | Logic | execute/undo/redo invariants, events |
| 55–70 | Integration | Demos, formatting strategy, snapshot |
| 70–75 | Q&A | Trade-offs, scaling story |

## Requirements & Assumptions
- Ops: insert, delete, replace; unlimited undo/redo (memory-bounded).
- Redo invalidated on any new command.
- Events emitted for execute/undo/redo/formatting/snapshot.
- Strategy hook for formatting/persistence; snapshot optional (Memento style).
- Single-threaded; persistence/collab out of scope.

## Design Patterns
- **Command**: Reversible edits (`execute/undo`).
- **Singleton**: `EditorSession` as single controller.
- **Observer**: Event listeners for UI/analytics.
- **Strategy**: Formatting strategy swap (e.g., trim whitespace).
- **State**: Track editing lifecycle (IDLE/EDITING/UNDOING/REDOING).
- **Memento (optional)**: Snapshots for restore.

## Architecture Sketch
```
Client/UI
  └─→ EditorSession (Singleton)
         ├─ Document (text, version)
         ├─ undo_stack / redo_stack (Command instances)
         ├─ FormattingStrategy (Strategy)
         └─ listeners[] (Observer callbacks)

Flow:
execute(cmd) → cmd.execute(doc) → push undo → clear redo → emit event
undo()       → pop undo → cmd.undo(doc) → push redo → emit event
redo()       → pop redo → cmd.execute(doc) → push undo → emit event
apply_formatting() → strategy.apply(text) → push FormattingCommand
```

## UML Class Diagram (text)
```
┌─────────────────────┐
│    EditorSession    │ (Singleton)
├─────────────────────┤
│+ document: Document │
│+ undo_stack: [Cmd]  │
│+ redo_stack: [Cmd]  │
│+ state: EditorState │
│+ formatting_strategy│
│+ listeners: [fn]    │
├─────────────────────┤
│+ execute_command()  │
│+ undo() / redo()    │
│+ apply_formatting() │
│+ take/restore_snap()│
└───────────┬─────────┘
            │uses
            ▼
      ┌────────────┐
      │  Document  │
      └────────────┘

┌─────────────┐    implements    ┌─────────────────────────┐
│  Command    │<---------------- │ InsertText/Delete/Replace│
├─────────────┤                  └─────────────────────────┘
│+ execute()  │
│+ undo()     │
└─────────────┘

┌───────────────────┐   implements   ┌────────────────────────────┐
│ FormattingStrategy│<--------------│ TrimTrailingSpacesStrategy │
└───────────────────┘               └────────────────────────────┘

Observers: listeners[] consume events (command_executed, command_undone, ...)
Enums: EditorState (IDLE/EDITING/UNDOING/REDOING)
Memento: Snapshot(text, version, timestamp) optionally stored/restored
```

## Core Model
| Entity | Responsibility |
|--------|----------------|
| `Document` | Holds `text`, `version` |
| `EditorSession` | Executes commands, manages stacks/state, emits events |
| `Command` | Reversible edit (`execute/undo`) |
| `FormattingStrategy` | Transform text (e.g., trim whitespace) |
| `Snapshot` | Frozen state for restore |

## Undo/Redo Invariants
1) New command clears redo stack.  
2) Undo pushes command to redo only after a successful undo.  
3) Redo re-executes command then pushes it back to undo.  
4) Version bumps on execute/undo/redo for traceability.

## Demo Scenarios
1) Setup + inserts.  
2) Insert/Delete with undo/redo chain.  
3) Full redo chain after clears.  
4) Strategy swap (trim) and apply.  
5) Snapshot, mutate, restore.

Run demos: `python3 "Text Editor with Undo & Redo.md"` (or copy code to a `.py` file).

## Scaling & Trade-offs (Q&A)
- **Large documents?** Use rope/gap buffer and operate on slices; keep command payloads as spans, not full text copies.  
- **Persistence?** Append-only command log or periodic snapshots + redo log; versioned storage for recovery.  
- **Concurrency/collab?** Add OT/CRDT layer; command bus per user; conflict resolution (out of scope here).  
- **Performance of undo/redo?** Keep operations O(1) push/pop; avoid heavy copies; use diff-based commands for large spans.  
- **Memory growth?** Cap history length; drop oldest commands or snapshot then truncate history.  
- **Events overhead?** Batch or debounce; use async queue if UI/analytics are slow.

## Compact Code
```python
"""Compact implementation: Text Editor with Undo & Redo patterns"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import List, Callable, Optional, Dict, Any
import time

# ---------------------- Document ----------------------
@dataclass
class Document:
    text: str = ""
    version: int = 0

    def __str__(self) -> str:
        return f"(v{self.version}) '{self.text}'"

# ---------------------- Editor State ----------------------
class EditorState(Enum):
    IDLE = "IDLE"
    EDITING = "EDITING"
    UNDOING = "UNDOING"
    REDOING = "REDOING"

# ---------------------- Command Base ----------------------
class Command:
    def execute(self, doc: Document) -> None:
        raise NotImplementedError
    def undo(self, doc: Document) -> None:
        raise NotImplementedError
    def describe(self) -> str:
        return self.__class__.__name__

# ---------------------- Concrete Commands ----------------------
class InsertTextCommand(Command):
    def __init__(self, position: int, text: str) -> None:
        self.position = position
        self.text = text
    def execute(self, doc: Document) -> None:
        if not 0 <= self.position <= len(doc.text):
            raise ValueError("Insert position out of bounds")
        doc.text = doc.text[:self.position] + self.text + doc.text[self.position:]
    def undo(self, doc: Document) -> None:
        doc.text = doc.text[:self.position] + doc.text[self.position + len(self.text):]
    def describe(self) -> str:
        return f"Insert '{self.text}' at {self.position}"

class DeleteRangeCommand(Command):
    def __init__(self, start: int, length: int) -> None:
        self.start = start
        self.length = length
        self.removed: Optional[str] = None
    def execute(self, doc: Document) -> None:
        if not 0 <= self.start < len(doc.text):
            raise ValueError("Delete start out of bounds")
        end = self.start + self.length
        if end > len(doc.text):
            raise ValueError("Delete range exceeds length")
        self.removed = doc.text[self.start:end]
        doc.text = doc.text[:self.start] + doc.text[end:]
    def undo(self, doc: Document) -> None:
        if self.removed is None:
            raise RuntimeError("Nothing to undo; command not executed")
        doc.text = doc.text[:self.start] + self.removed + doc.text[self.start:]
    def describe(self) -> str:
        return f"Delete {self.length} chars at {self.start}"

class ReplaceRangeCommand(Command):
    def __init__(self, start: int, length: int, new_text: str) -> None:
        self.start = start
        self.length = length
        self.new_text = new_text
        self.old_text: Optional[str] = None
    def execute(self, doc: Document) -> None:
        if not 0 <= self.start < len(doc.text):
            raise ValueError("Replace start out of bounds")
        end = self.start + self.length
        if end > len(doc.text):
            raise ValueError("Replace range exceeds length")
        self.old_text = doc.text[self.start:end]
        doc.text = doc.text[:self.start] + self.new_text + doc.text[end:]
    def undo(self, doc: Document) -> None:
        if self.old_text is None:
            raise RuntimeError("Nothing to undo; command not executed")
        end = self.start + len(self.new_text)
        doc.text = doc.text[:self.start] + self.old_text + doc.text[end:]
    def describe(self) -> str:
        return f"Replace {self.length} chars at {self.start} with '{self.new_text}'"

class FormattingCommand(Command):
    def __init__(self, strategy_name: str, before: str, after: str) -> None:
        self.strategy_name = strategy_name
        self.before = before
        self.after = after
    def execute(self, doc: Document) -> None:
        doc.text = self.after
    def undo(self, doc: Document) -> None:
        doc.text = self.before
    def describe(self) -> str:
        return f"Formatting applied: {self.strategy_name}"

class RestoreSnapshotCommand(Command):
    def __init__(self, before: str, after: str) -> None:
        self.before = before
        self.after = after
    def execute(self, doc: Document) -> None:
        doc.text = self.after
    def undo(self, doc: Document) -> None:
        doc.text = self.before
    def describe(self) -> str:
        return "Restore Snapshot"

# ---------------------- Strategies ----------------------
class FormattingStrategy:
    def name(self) -> str:
        return self.__class__.__name__
    def apply(self, text: str) -> str:
        raise NotImplementedError

class TrimTrailingSpacesStrategy(FormattingStrategy):
    def apply(self, text: str) -> str:
        lines = [ln.rstrip() for ln in text.split("\n")]
        return "\n".join(lines)

class IdentityFormattingStrategy(FormattingStrategy):
    def apply(self, text: str) -> str:
        return text

# ---------------------- Snapshot ----------------------
@dataclass
class Snapshot:
    text: str
    version: int
    timestamp: float

# ---------------------- Editor Session (Singleton) ----------------------
class EditorSession:
    _instance: Optional["EditorSession"] = None
    def __init__(self) -> None:
        self.document = Document()
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []
        self.state = EditorState.IDLE
        self.listeners: List[Callable[[str, Dict[str, Any]], None]] = []
        self.formatting_strategy: FormattingStrategy = IdentityFormattingStrategy()
    @classmethod
    def instance(cls) -> "EditorSession":
        if cls._instance is None:
            cls._instance = EditorSession()
        return cls._instance
    def register(self, listener: Callable[[str, Dict[str, Any]], None]) -> None:
        self.listeners.append(listener)
    def _emit(self, event: str, payload: Dict[str, Any]) -> None:
        for listener_fn in self.listeners:
            listener_fn(event, payload)
    def execute_command(self, cmd: Command) -> None:
        self.state = EditorState.EDITING
        cmd.execute(self.document)
        self.undo_stack.append(cmd)
        self.redo_stack.clear()
        self.document.version += 1
        self._emit("command_executed", {"cmd": cmd.describe(), "doc": str(self.document)})
        self.state = EditorState.IDLE
    def undo(self) -> None:
        if not self.undo_stack:
            return
        self.state = EditorState.UNDOING
        cmd = self.undo_stack.pop()
        cmd.undo(self.document)
        self.redo_stack.append(cmd)
        self.document.version += 1
        self._emit("command_undone", {"cmd": cmd.describe(), "doc": str(self.document)})
        self.state = EditorState.IDLE
    def redo(self) -> None:
        if not self.redo_stack:
            return
        self.state = EditorState.REDOING
        cmd = self.redo_stack.pop()
        cmd.execute(self.document)
        self.undo_stack.append(cmd)
        self.document.version += 1
        self._emit("command_redone", {"cmd": cmd.describe(), "doc": str(self.document)})
        self.state = EditorState.IDLE
    def apply_formatting(self) -> None:
        before = self.document.text
        after = self.formatting_strategy.apply(before)
        if before == after:
            return
        self.execute_command(FormattingCommand(self.formatting_strategy.name(), before, after))
        self._emit("formatting_applied", {"strategy": self.formatting_strategy.name()})
    def set_formatting_strategy(self, strategy: FormattingStrategy) -> None:
        old = self.formatting_strategy.name()
        self.formatting_strategy = strategy
        self._emit("strategy_swapped", {"old": old, "new": strategy.name()})
    def take_snapshot(self) -> Snapshot:
        snap = Snapshot(text=self.document.text, version=self.document.version, timestamp=time.time())
        self._emit("snapshot_taken", {"version": snap.version})
        return snap
    def restore_snapshot(self, snap: Snapshot) -> None:
        before = self.document.text
        after = snap.text
        if before == after:
            return
        self.execute_command(RestoreSnapshotCommand(before, after))
        self._emit("snapshot_restored", {"to_version": snap.version})

# ---------------------- Demo Helpers ----------------------
def print_header(title: str) -> None:
    print("\n=== " + title + " ===")

def listener(event: str, payload: Dict[str, Any]) -> None:
    print(f"[EVENT] {event} -> {payload}")

# ---------------------- Demo Scenarios ----------------------
def demo_1_setup() -> None:
    print_header("Demo 1: Setup & Initial Insert")
    sess = EditorSession.instance()
    sess.register(listener)
    sess.execute_command(InsertTextCommand(0, "Hello"))
    sess.execute_command(InsertTextCommand(len(sess.document.text), ", world!  "))
    print("Current:", sess.document)

def demo_2_edits_and_undo_redo() -> None:
    print_header("Demo 2: Edits + Undo/Redo")
    sess = EditorSession.instance()
    sess.execute_command(DeleteRangeCommand(5, 1))  # remove comma
    sess.execute_command(InsertTextCommand(5, " -"))
    print("After edits:", sess.document)
    sess.undo()
    sess.undo()
    print("After two undos:", sess.document)
    sess.redo()
    print("After one redo:", sess.document)

def demo_3_multi_redo_chain() -> None:
    print_header("Demo 3: Redo Chain")
    sess = EditorSession.instance()
    while sess.undo_stack:
        sess.undo()
    print("After clearing via undo:", sess.document)
    while sess.redo_stack:
        sess.redo()
    print("After full redo chain:", sess.document)

def demo_4_formatting_strategy() -> None:
    print_header("Demo 4: Formatting Strategy Swap")
    sess = EditorSession.instance()
    sess.set_formatting_strategy(TrimTrailingSpacesStrategy())
    sess.apply_formatting()
    print("After formatting:", sess.document)

def demo_5_snapshot_restore() -> None:
    print_header("Demo 5: Snapshot & Restore")
    sess = EditorSession.instance()
    snap = sess.take_snapshot()
    sess.execute_command(InsertTextCommand(len(sess.document.text), " EXTRA"))
    sess.execute_command(ReplaceRangeCommand(0, 5, "Hi"))
    print("Mutated doc:", sess.document)
    sess.restore_snapshot(snap)
    print("Restored doc:", sess.document)

# ---------------------- Main ----------------------
if __name__ == "__main__":
    demo_1_setup()
    demo_2_edits_and_undo_redo()
    demo_3_multi_redo_chain()
    demo_4_formatting_strategy()
    demo_5_snapshot_restore()
    print("\n✅ All demos completed")
```

## Key Takeaways
- Command pattern keeps undo/redo symmetrical; clear redo on any new execution.
- Use events to decouple UI/analytics; strategies to tweak formatting without touching commands.
- For scale, swap storage (rope/gap buffer) and add command log + snapshots; for collab, layer OT/CRDT on top.***
