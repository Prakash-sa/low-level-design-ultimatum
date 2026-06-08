# Text Editor with Undo & Redo — Complete Design Guide

> Command-based text editing with unlimited undo/redo, incremental history management, caret tracking, and memory-efficient operation storage.

**Scale**: Single-user desktop to collaborative multi-user editing, 100K+ operations per session  
**Duration**: 75-minute interview guide  
**Focus**: Command pattern for undo/redo, Memento for snapshots, thread-safe history management, efficient buffer operations

---

## Table of Contents

1. [Quick Start (5 min)](#quick-start)
2. [Step 01: The Setup — Clarify Requirements](#step-01-the-setup--clarify-requirements)
3. [Step 02: Structure — Define Entities](#step-02-structure--define-entities)
4. [Step 03: Interface — APIs & Entry Points](#step-03-interface--apis--entry-points)
5. [Step 04: Architecture — Relationships & Diagram](#step-04-architecture--relationships--diagram)
6. [Step 05: Optimization — Design Patterns](#step-05-optimization--design-patterns)
7. [Step 06: Implementation — Code & Concurrency](#step-06-implementation--code--concurrency)
8. [Demo Scenarios](#demo-scenarios)
9. [Interview Q&A](#interview-qa)
10. [Scaling Q&A](#scaling-qa)
11. [Success Checklist](#success-checklist)

---

## Quick Start

**5-Minute Overview for Last-Minute Prep**

### What Problem Are We Solving?
A user types text → each operation becomes a Command object → command is executed and pushed to the undo stack → redo stack is cleared → on undo, the command reverses itself → on redo, the command re-executes. Core concerns: reversibility of every operation, memory-efficient history, and correct caret management.

### Core Flow
```
Type / Delete / Replace
        ↓
  Command.execute()
        ↓
  Push to UndoStack  →  clear RedoStack
        ↓
  Undo: pop UndoStack → Command.undo() → push to RedoStack
        ↓
  Redo: pop RedoStack → Command.execute() → push to UndoStack
```

---

## Step 01: The Setup — Clarify Requirements

> **Interview Tip**: Never code immediately. Ask clarifying questions first. Define scope, actors, and constraints.

### Questions to Ask (30 seconds each)

1. **Single user or collaborative?** → "Single user for the core; mention collaborative as a scaling concern"
2. **What operations need undo/redo?** → "Insert, delete, replace — selection management is a bonus"
3. **Is undo depth bounded?** → "Unlimited for the core design; discuss bounding as optimization"
4. **Do we need persistent undo across file save?** → "No — in-memory history for this interview"
5. **Thread safety needed?** → "Single-threaded UI thread, but background autosave needs consideration"

### Actors (Who uses the system?)

| Actor | Role | Example Actions |
|-------|------|-----------------|
| **User** | Authors and edits document | Type text, delete characters, select range, undo, redo |
| **Editor UI** | Translates UI events to commands | Keypress → InsertCommand, Backspace → DeleteCommand |
| **System** | Autosave, crash recovery | Snapshot buffer periodically, restore last state |

### Functional Requirements (What does the system do?)

✅ **Text Insertion**
  - Insert arbitrary text at any valid position
  - Move caret to end of inserted text

✅ **Text Deletion**
  - Delete a range of characters by position and length
  - Move caret to deletion start position

✅ **Text Replacement**
  - Replace a range with new text (delete + insert atomically)
  - Captured as a single undoable operation

✅ **Undo (Unlimited Depth)**
  - Reverse the most recent command
  - Restore caret to pre-command position
  - Move reversed command to redo stack

✅ **Redo**
  - Re-execute the most recently undone command
  - Redo stack cleared when a new command is executed

✅ **Caret Management**
  - Track cursor position at all times
  - Restore position accurately on undo/redo

✅ **Memory Efficiency**
  - Store operation deltas (position + text) not full document copies
  - Optional: cap history depth to 1000 commands

### Non-Functional Requirements (How does it perform?)

✅ **Correctness**: Every undo must restore exact prior state  
✅ **Performance**: O(1) push/pop on history stacks; O(k) for insert/delete where k = text length  
✅ **Memory**: Delta storage; full snapshot only on explicit save  
✅ **Responsiveness**: Operations complete in <1ms for typical edits  
✅ **History Integrity**: New command always clears redo stack  

### Constraints & Clarifications

| Constraint | Decision |
|-----------|----------|
| **Max undo depth** | Unlimited (cap at 1000 in production) |
| **Collaborative editing** | Out of scope (mention OT/CRDT as scaling path) |
| **Persistent undo** | No — in-memory only |
| **Redo after new edit** | Redo stack cleared |
| **Replace as atomic?** | YES — single Command, single undo step |
| **Caret restored on undo?** | YES — stored in each Command |
| **Thread safety** | Single UI thread; background save uses snapshot |

---

## Step 02: Structure — Define Entities

> **Interview Tip**: Extract core objects from requirements. Look for **nouns**. Write them on the whiteboard immediately.

### Step 2.1: List Core Entities (Extract Nouns)

```
Document, TextBuffer, Command, InsertCommand, DeleteCommand, ReplaceCommand,
CommandHistory, Caret, EditorMemento, Editor, ...
```

### Step 2.2: Define Core Classes

#### **TextBuffer** — The raw document content
```
Properties:
  - content: str  (the full text as a mutable string)
  - caret: Caret  (current cursor position)

Behaviors:
  - insert(position, text): Insert text at position, advance caret
  - delete(position, length): Remove length chars from position
  - get_text(): Return full content
  - get_length(): Number of characters
  - save_memento(): Snapshot current state
  - restore_memento(memento): Restore from snapshot
```

#### **Command** — Abstract text operation (insert/delete/replace)
```
Properties:
  - buffer: TextBuffer  (the document to operate on)
  - caret_before: int   (caret position before execute)
  - caret_after: int    (caret position after execute)

Behaviors:
  - execute(): Apply operation to buffer
  - undo(): Reverse operation on buffer
```

#### **InsertCommand** — Insert text at a position
```
Properties:
  - position: int   (insertion point)
  - text: str       (text to insert)

Behaviors:
  - execute(): buffer.insert(position, text); move caret to position + len(text)
  - undo(): buffer.delete(position, len(text)); restore caret_before
```

#### **DeleteCommand** — Delete a range of characters
```
Properties:
  - position: int   (start of deleted range)
  - length: int     (number of chars to remove)
  - deleted_text: str  (captured on execute for undo)

Behaviors:
  - execute(): capture buffer[position:position+length], then buffer.delete(...)
  - undo(): buffer.insert(position, deleted_text); restore caret_before
```

#### **ReplaceCommand** — Replace a range with new text (atomic)
```
Properties:
  - position: int
  - length: int       (range to replace)
  - new_text: str     (replacement)
  - old_text: str     (captured on execute)

Behaviors:
  - execute(): capture old_text, delete range, insert new_text
  - undo(): delete new_text, insert old_text, restore caret_before
```

#### **CommandHistory** — Dual-stack undo/redo manager
```
Properties:
  - undo_stack: List[Command]
  - redo_stack: List[Command]
  - max_size: int  (optional cap, default 1000)

Behaviors:
  - push(command): Add to undo stack, clear redo stack
  - undo(): Pop from undo stack, call command.undo(), push to redo stack
  - redo(): Pop from redo stack, call command.execute(), push to undo stack
  - can_undo() / can_redo(): Check stack emptiness
  - clear(): Reset both stacks
```

#### **Caret** — Cursor position tracker
```
Properties:
  - position: int  (0-based character index)

Behaviors:
  - move_to(position): Set caret to absolute position
  - clamp(max_pos): Ensure position does not exceed buffer length
```

#### **Editor** — Orchestrator (Singleton)
```
Properties:
  - buffer: TextBuffer
  - history: CommandHistory
  - observers: List[Observer]

Behaviors:
  - insert(position, text): Create InsertCommand, execute, push to history
  - delete(position, length): Create DeleteCommand, execute, push to history
  - replace(position, length, new_text): Create ReplaceCommand, execute, push
  - undo(): Delegate to history.undo()
  - redo(): Delegate to history.redo()
  - get_content(): Return buffer.get_text()
  - add_observer(observer): Register UI listener
```

### Step 2.3: Define Enumerations (State & Type)

```python
class OperationType(Enum):
    INSERT  = "insert"   # Text added at position
    DELETE  = "delete"   # Text removed from range
    REPLACE = "replace"  # Range replaced with new text

class EditorEvent(Enum):
    TEXT_CHANGED = "text_changed"   # Buffer content modified
    UNDO_PERFORMED = "undo"         # Undo executed
    REDO_PERFORMED = "redo"         # Redo executed
    HISTORY_CLEARED = "history_cleared"
```

### Step 2.4: Why These Entities?

| Entity | Why | Cost of Missing |
|--------|-----|-----------------|
| **TextBuffer** | Central content store; separation from editor logic | No place to store/modify document |
| **Command (Insert/Delete/Replace)** | Encapsulate reversible operations | Can't undo — no record of what changed |
| **CommandHistory** | Dual-stack undo/redo management | Redo becomes impossible after undo |
| **Caret** | Cursor position survives undo/redo | Cursor jumps randomly after undo |
| **Editor** | Single orchestrator; prevents inconsistent state | Commands and history managed separately, leading to bugs |

---

## Step 03: Interface — APIs & Entry Points

> **Interview Tip**: Define the contract (inputs, outputs, exceptions) BEFORE implementation. Focus on "what" not "how".

### Step 3.1: Public API Contracts

#### **1. Insert Text** ⭐ CRITICAL
```python
def insert(self, position: int, text: str) -> None:
    """
    Insert text at position in the document.

    Precondition: 0 <= position <= len(buffer)
    Postcondition: buffer contains text starting at position; caret at position + len(text)

    Side Effects:
      - Creates and executes InsertCommand
      - Pushes command to undo stack
      - Clears redo stack
      - Notifies observers with TEXT_CHANGED event

    Raises:
      - IndexError: position out of range
      - ValueError: text is None

    Concurrency: NOT thread-safe (single UI thread assumed)
    Time: O(n) where n = len(buffer) — string concatenation
    """
    pass
```

#### **2. Delete Text** ⭐ CRITICAL
```python
def delete(self, position: int, length: int) -> None:
    """
    Delete `length` characters starting at position.

    Precondition: 0 <= position, position + length <= len(buffer)
    Postcondition: buffer shrinks by length chars; caret at position

    Side Effects:
      - Captures deleted text for undo
      - Creates and executes DeleteCommand
      - Pushes command to undo stack
      - Clears redo stack

    Raises:
      - IndexError: range out of bounds
      - ValueError: length <= 0

    Time: O(n) — string slicing
    """
    pass
```

#### **3. Replace Text**
```python
def replace(self, position: int, length: int, new_text: str) -> None:
    """
    Replace `length` chars at position with new_text.

    Atomic: single undo step for what is logically one edit.

    Precondition: 0 <= position, position + length <= len(buffer)
    Postcondition: buffer has old range replaced; caret at position + len(new_text)

    Time: O(n)
    """
    pass
```

#### **4. Undo** ⭐ CRITICAL
```python
def undo(self) -> bool:
    """
    Reverse the most recent command.

    Precondition: history.can_undo() == True
    Postcondition:
      - Top command removed from undo stack
      - command.undo() applied to buffer
      - Command pushed to redo stack
      - Caret restored to pre-command position

    Returns: True if undo succeeded, False if nothing to undo.
    Notifies: UNDO_PERFORMED event
    """
    pass
```

#### **5. Redo**
```python
def redo(self) -> bool:
    """
    Re-execute the most recently undone command.

    Precondition: history.can_redo() == True
    Postcondition:
      - Top command removed from redo stack
      - command.execute() applied to buffer
      - Command pushed back to undo stack

    Returns: True if redo succeeded, False if nothing to redo.
    Notifies: REDO_PERFORMED event
    """
    pass
```

#### **6. Register Observer** (For UI Updates)
```python
def add_observer(self, observer: 'EditorObserver') -> None:
    """
    Register a callback for editor events.
    Observer called: observer.on_event(event, editor)
    Example: Add UIRenderer to refresh display on every change.
    """
    pass
```

### Step 3.2: Exception / Failure Model

```python
class EditorException(Exception):
    """Base exception for all editor errors"""
    pass

class InvalidPositionError(EditorException):
    """Position is negative or beyond buffer length"""
    pass

class InvalidRangeError(EditorException):
    """Range (position + length) exceeds buffer length"""
    pass

class NothingToUndoError(EditorException):
    """Undo stack is empty"""
    pass

class NothingToRedoError(EditorException):
    """Redo stack is empty"""
    pass
```

### Step 3.3: API Usage Example

```python
editor = Editor.get_instance()

# 1. Type text
editor.insert(0, "Hello")
editor.insert(5, " World")
print(editor.get_content())   # "Hello World"

# 2. Replace a word
editor.replace(6, 5, "Python")
print(editor.get_content())   # "Hello Python"

# 3. Undo replace
editor.undo()
print(editor.get_content())   # "Hello World"

# 4. Undo second insert
editor.undo()
print(editor.get_content())   # "Hello"

# 5. Redo
editor.redo()
print(editor.get_content())   # "Hello World"

# 6. New edit clears redo
editor.insert(11, "!")
print(editor.get_content())   # "Hello World!"
print(editor.history.can_redo())  # False — redo stack cleared
```

---

## Step 04: Architecture — Relationships & Diagram

> **Interview Tip**: Use composition, aggregation, and association. Prefer composition over inheritance. Check cardinality (1:1, 1:N).

### Step 4.1: Relationship Types

```
Editor HAS-A TextBuffer (1:1 Composition)
  └─ Editor owns and manages the buffer lifecycle

Editor HAS-A CommandHistory (1:1 Composition)
  └─ Editor owns history; history tracks all commands

TextBuffer HAS-A Caret (1:1 Composition)
  └─ Buffer owns its cursor position

Command IS-A abstract interface
  └─ InsertCommand, DeleteCommand, ReplaceCommand IMPLEMENT Command

CommandHistory HAS-A List[Command] undo_stack (1:N Composition)
CommandHistory HAS-A List[Command] redo_stack (1:N Composition)

Editor NOTIFIES EditorObserver (1:N Association)
  └─ Multiple UI observers listen for changes

Command REFERENCES TextBuffer (1:1 Association)
  └─ Command operates on buffer (no ownership)
```

### Step 4.2: Complete UML Class Diagram

```
┌──────────────────────────────────────────┐
│         Editor (Singleton)               │
├──────────────────────────────────────────┤
│ - _instance: Editor                      │
│ - buffer: TextBuffer                     │
│ - history: CommandHistory                │
│ - observers: List[EditorObserver]        │
│ - _lock: threading.RLock                 │
├──────────────────────────────────────────┤
│ + get_instance(): Editor                 │
│ + insert(pos, text): void                │
│ + delete(pos, length): void              │
│ + replace(pos, length, text): void       │
│ + undo(): bool                           │
│ + redo(): bool                           │
│ + get_content(): str                     │
│ + add_observer(observer): void           │
└───────────────┬──────────────────────────┘
                │ owns 1:1
     ┌──────────┴──────────┐
     ▼                     ▼
┌────────────────┐   ┌──────────────────────────┐
│  TextBuffer    │   │    CommandHistory         │
├────────────────┤   ├──────────────────────────┤
│ - content: str │   │ - undo_stack: List[Cmd]  │
│ - caret: Caret │   │ - redo_stack: List[Cmd]  │
├────────────────┤   │ - max_size: int          │
│ + insert(...)  │   ├──────────────────────────┤
│ + delete(...)  │   │ + push(command): void    │
│ + get_text()   │   │ + undo(): bool           │
│ + save_memento │   │ + redo(): bool           │
│ + restore(...) │   │ + can_undo(): bool       │
└───────┬────────┘   │ + can_redo(): bool       │
        │            └──────────┬───────────────┘
        ▼                       │ stores 1:N
  ┌───────────┐                 ▼
  │   Caret   │    ┌─────────────────────────────┐
  ├───────────┤    │   Command (Abstract)         │
  │ - pos: int│    ├─────────────────────────────┤
  ├───────────┤    │ - buffer: TextBuffer (ref)  │
  │ + move_to │    │ - caret_before: int         │
  │ + clamp   │    │ - caret_after: int          │
  └───────────┘    ├─────────────────────────────┤
                   │ + execute(): void (abstract) │
                   │ + undo(): void   (abstract)  │
                   └──────┬──────────────────────┘
                          │ implemented by
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
 ┌──────────────┐ ┌──────────────┐ ┌────────────────┐
 │InsertCommand │ │DeleteCommand │ │ReplaceCommand  │
 ├──────────────┤ ├──────────────┤ ├────────────────┤
 │ position     │ │ position     │ │ position       │
 │ text         │ │ length       │ │ length         │
 │              │ │ deleted_text │ │ new_text       │
 │              │ │              │ │ old_text       │
 └──────────────┘ └──────────────┘ └────────────────┘

OBSERVER PATTERN (UI Notifications):
┌────────────────────────────────────┐
│  EditorObserver (Abstract)         │
├────────────────────────────────────┤
│ + on_event(event, editor)          │
└──┬─────────────────────────────────┘
   │ implemented by
   ├─→ ConsoleObserver (logging/debug)
   └─→ UIRenderer (redraws the editor view)

MEMENTO PATTERN (Snapshot):
TextBuffer ──save_memento()──→ EditorMemento
TextBuffer ←─restore_memento()── EditorMemento
```

### Step 4.3: Cardinality Summary

| Relationship | Cardinality | Type | Reason |
|-------------|------------|------|--------|
| Editor → TextBuffer | 1:1 | Composition | One document per editor |
| Editor → CommandHistory | 1:1 | Composition | Editor owns its history |
| TextBuffer → Caret | 1:1 | Composition | Buffer owns its cursor |
| CommandHistory → Commands | 1:N | Composition | History owns command objects |
| Command → TextBuffer | 1:1 | Association | Command references (not owns) buffer |
| Editor → EditorObserver | 1:N | Association | Many UI listeners |

---

## Step 05: Optimization — Design Patterns

> **Interview Tip**: Don't force patterns. Only solve specific problems.

### Pattern 1: **Command** (For Undo/Redo) ⭐ CORE

**Problem**: Text operations (insert, delete, replace) must be reversible without storing full document copies.

**Solution**: Encapsulate each operation as an object with `execute()` and `undo()` methods. Store these objects in a stack.

```python
from abc import ABC, abstractmethod

class Command(ABC):
    def __init__(self, buffer):
        self.buffer = buffer
        self.caret_before = buffer.caret.position
        self.caret_after = self.caret_before

    @abstractmethod
    def execute(self) -> None:
        pass

    @abstractmethod
    def undo(self) -> None:
        pass

class InsertCommand(Command):
    def __init__(self, buffer, position: int, text: str):
        super().__init__(buffer)
        self.position = position
        self.text = text

    def execute(self) -> None:
        self.buffer.insert(self.position, self.text)
        self.caret_after = self.position + len(self.text)
        self.buffer.caret.move_to(self.caret_after)

    def undo(self) -> None:
        self.buffer.delete(self.position, len(self.text))
        self.buffer.caret.move_to(self.caret_before)
```

**Benefit**: ✅ O(1) undo/redo (just pop and call), ✅ Delta storage not full copies, ✅ Easy to add new operation types  
**Trade-off**: ⚠️ Each command must perfectly capture state needed for reversal

---

### Pattern 2: **Memento** (For Snapshots)

**Problem**: Sometimes you want a full checkpoint (autosave, crash recovery) rather than per-command deltas.

**Solution**: `TextBuffer.save_memento()` captures `(content, caret_position)` into an opaque `EditorMemento`. Restoration is a single call.

```python
class EditorMemento:
    """Opaque snapshot of buffer state"""
    def __init__(self, content: str, caret_position: int):
        self._content = content
        self._caret_position = caret_position

    def get_content(self) -> str:
        return self._content

    def get_caret(self) -> int:
        return self._caret_position

class TextBuffer:
    def save_memento(self) -> EditorMemento:
        return EditorMemento(self.content, self.caret.position)

    def restore_memento(self, memento: EditorMemento) -> None:
        self.content = memento.get_content()
        self.caret.move_to(memento.get_caret())
```

**Benefit**: ✅ Crash recovery, ✅ "Save point" undo levels, ✅ Encapsulates state (no public fields)  
**Trade-off**: ⚠️ Full copy cost — use sparingly (on save, not every keystroke)

---

### Pattern 3: **Singleton** (For Editor)

**Problem**: Multiple UI components must share one consistent editor state.

**Solution**: One global `Editor` instance with thread-safe initialization.

```python
import threading

class Editor:
    _instance = None
    _class_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._class_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.buffer = TextBuffer()
        self.history = CommandHistory()
        self.observers = []
        self._lock = threading.RLock()
```

**Benefit**: ✅ Single source of truth, ✅ Thread-safe double-checked locking  
**Trade-off**: ⚠️ Global state (harder to unit test); ⚠️ Reset needed between tests

---

### Pattern 4: **Observer** (For UI Notifications)

**Problem**: The editor core must not directly depend on the UI renderer.

**Solution**: Observer pattern decouples editor from consumers.

```python
from abc import ABC, abstractmethod

class EditorObserver(ABC):
    @abstractmethod
    def on_event(self, event: str, editor: 'Editor') -> None:
        pass

class ConsoleObserver(EditorObserver):
    def on_event(self, event: str, editor: 'Editor') -> None:
        print(f"  [EVENT: {event}] content='{editor.get_content()}' "
              f"caret={editor.buffer.caret.position}")

# Usage
editor.add_observer(ConsoleObserver())
# Fires automatically on insert/delete/undo/redo
```

**Benefit**: ✅ Add new UI renderers without changing core, ✅ Easy to test (mock observer)  
**Trade-off**: ⚠️ Observer must be careful not to re-trigger edits (infinite loop risk)

---

### Pattern 5: **Strategy** (For History Bounding)

**Problem**: Unlimited undo history can exhaust memory on long editing sessions.

**Solution**: Pluggable `HistoryStrategy` determines what to do when the stack is full.

```python
class HistoryStrategy(ABC):
    @abstractmethod
    def on_overflow(self, stack: list, max_size: int) -> None:
        pass

class DropOldestStrategy(HistoryStrategy):
    def on_overflow(self, stack: list, max_size: int) -> None:
        while len(stack) >= max_size:
            stack.pop(0)   # Remove oldest command

class CompressStrategy(HistoryStrategy):
    def on_overflow(self, stack: list, max_size: int) -> None:
        # Collapse oldest N commands into a single snapshot command
        pass  # Advanced: merge into a RestoreSnapshotCommand
```

**Benefit**: ✅ Memory bounded, ✅ Swap strategy without touching CommandHistory core  
**Trade-off**: ⚠️ Oldest commands lost; user can't undo infinitely far back

---

### Design Patterns Summary Table

| Pattern | Problem Solved | Benefit |
|---------|---|---|
| **Command** | Reversible text operations without full copies | O(1) undo/redo, delta storage |
| **Memento** | Full-document snapshot for save/recovery | Crash recovery, save points |
| **Singleton** | One consistent editor state across components | Single source of truth |
| **Observer** | Decouple editor from UI renderer | Add displays without touching core |
| **Strategy** | Pluggable history-bounding behavior | Memory-safe, swappable policy |

---

## Step 06: Implementation — Code & Concurrency

> **Interview Tip**: Write thread-safe, defensive code. Mention "Thread Safety" even if not asked.

### Complete Thread-Safe Implementation

```python
"""
Text Editor with Undo & Redo - Interview Implementation

Demonstrates:
1. Insert text -> builds "Hello World"
2. Replace word -> "Hello Python"
3. Undo replace -> back to "Hello World"
4. Undo second insert -> back to "Hello"
5. Redo -> "Hello World"
6. Delete characters -> "Hello"
7. New edit clears redo stack
8. Full undo sequence back to empty document
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional
import threading


# ============================================================================
# ENUMERATIONS
# ============================================================================

class OperationType(Enum):
    INSERT  = "insert"
    DELETE  = "delete"
    REPLACE = "replace"

class EditorEvent(Enum):
    TEXT_CHANGED    = "text_changed"
    UNDO_PERFORMED  = "undo"
    REDO_PERFORMED  = "redo"
    HISTORY_CLEARED = "history_cleared"


# ============================================================================
# CARET
# ============================================================================

class Caret:
    """Tracks the cursor position inside a TextBuffer."""

    def __init__(self, position: int = 0):
        self.position = position

    def move_to(self, position: int) -> None:
        self.position = position

    def clamp(self, max_pos: int) -> None:
        self.position = max(0, min(self.position, max_pos))

    def __repr__(self) -> str:
        return f"Caret({self.position})"


# ============================================================================
# MEMENTO
# ============================================================================

class EditorMemento:
    """Opaque snapshot of buffer state (content + caret)."""

    def __init__(self, content: str, caret_position: int):
        self._content = content
        self._caret_position = caret_position

    def get_content(self) -> str:
        return self._content

    def get_caret(self) -> int:
        return self._caret_position


# ============================================================================
# TEXT BUFFER
# ============================================================================

class TextBuffer:
    """Core document store. Owns the text content and the caret."""

    def __init__(self):
        self.content: str = ""
        self.caret: Caret = Caret(0)

    def insert(self, position: int, text: str) -> None:
        if position < 0 or position > len(self.content):
            raise IndexError(
                f"Insert position {position} out of range [0, {len(self.content)}]"
            )
        self.content = self.content[:position] + text + self.content[position:]

    def delete(self, position: int, length: int) -> str:
        if position < 0 or position + length > len(self.content):
            raise IndexError(
                f"Delete range [{position}, {position + length}) out of bounds"
            )
        deleted = self.content[position: position + length]
        self.content = self.content[:position] + self.content[position + length:]
        return deleted

    def get_text(self) -> str:
        return self.content

    def get_length(self) -> int:
        return len(self.content)

    def save_memento(self) -> EditorMemento:
        return EditorMemento(self.content, self.caret.position)

    def restore_memento(self, memento: EditorMemento) -> None:
        self.content = memento.get_content()
        self.caret.move_to(memento.get_caret())

    def __repr__(self) -> str:
        return f"TextBuffer('{self.content}', caret={self.caret.position})"


# ============================================================================
# COMMANDS
# ============================================================================

class Command(ABC):
    """Abstract base for all reversible text operations."""

    def __init__(self, buffer: TextBuffer):
        self.buffer = buffer
        self.caret_before: int = buffer.caret.position
        self.caret_after: int = buffer.caret.position

    @abstractmethod
    def execute(self) -> None:
        pass

    @abstractmethod
    def undo(self) -> None:
        pass

    @abstractmethod
    def description(self) -> str:
        pass


class InsertCommand(Command):
    """Insert text at a given position."""

    def __init__(self, buffer: TextBuffer, position: int, text: str):
        super().__init__(buffer)
        self.position = position
        self.text = text

    def execute(self) -> None:
        self.buffer.insert(self.position, self.text)
        self.caret_after = self.position + len(self.text)
        self.buffer.caret.move_to(self.caret_after)

    def undo(self) -> None:
        self.buffer.delete(self.position, len(self.text))
        self.buffer.caret.move_to(self.caret_before)

    def description(self) -> str:
        return f"Insert(pos={self.position}, text='{self.text}')"


class DeleteCommand(Command):
    """Delete a range of characters. Captures deleted text for undo."""

    def __init__(self, buffer: TextBuffer, position: int, length: int):
        super().__init__(buffer)
        self.position = position
        self.length = length
        self.deleted_text: str = ""

    def execute(self) -> None:
        self.deleted_text = self.buffer.delete(self.position, self.length)
        self.caret_after = self.position
        self.buffer.caret.move_to(self.caret_after)

    def undo(self) -> None:
        self.buffer.insert(self.position, self.deleted_text)
        self.buffer.caret.move_to(self.caret_before)

    def description(self) -> str:
        return f"Delete(pos={self.position}, len={self.length}, text='{self.deleted_text}')"


class ReplaceCommand(Command):
    """Atomically replace a range with new text (single undo step)."""

    def __init__(self, buffer: TextBuffer, position: int, length: int, new_text: str):
        super().__init__(buffer)
        self.position = position
        self.length = length
        self.new_text = new_text
        self.old_text: str = ""

    def execute(self) -> None:
        self.old_text = self.buffer.delete(self.position, self.length)
        self.buffer.insert(self.position, self.new_text)
        self.caret_after = self.position + len(self.new_text)
        self.buffer.caret.move_to(self.caret_after)

    def undo(self) -> None:
        self.buffer.delete(self.position, len(self.new_text))
        self.buffer.insert(self.position, self.old_text)
        self.buffer.caret.move_to(self.caret_before)

    def description(self) -> str:
        return (f"Replace(pos={self.position}, len={self.length}, "
                f"old='{self.old_text}', new='{self.new_text}')")


# ============================================================================
# COMMAND HISTORY
# ============================================================================

class CommandHistory:
    """Dual-stack manager for undo/redo."""

    def __init__(self, max_size: int = 1000):
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []
        self.max_size = max_size

    def push(self, command: Command) -> None:
        """Record an executed command; clears redo stack."""
        if len(self.undo_stack) >= self.max_size:
            self.undo_stack.pop(0)   # Drop oldest (DropOldest strategy)
        self.undo_stack.append(command)
        self.redo_stack.clear()      # New edit invalidates redo history

    def undo(self) -> Optional[Command]:
        """Pop from undo stack, push to redo stack. Returns command or None."""
        if not self.undo_stack:
            return None
        command = self.undo_stack.pop()
        command.undo()
        self.redo_stack.append(command)
        return command

    def redo(self) -> Optional[Command]:
        """Pop from redo stack, re-execute, push to undo stack. Returns command or None."""
        if not self.redo_stack:
            return None
        command = self.redo_stack.pop()
        command.execute()
        self.undo_stack.append(command)
        return command

    def can_undo(self) -> bool:
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        return len(self.redo_stack) > 0

    def clear(self) -> None:
        self.undo_stack.clear()
        self.redo_stack.clear()

    def undo_depth(self) -> int:
        return len(self.undo_stack)

    def redo_depth(self) -> int:
        return len(self.redo_stack)


# ============================================================================
# OBSERVER
# ============================================================================

class EditorObserver(ABC):
    @abstractmethod
    def on_event(self, event: str, editor: 'Editor') -> None:
        pass


class ConsoleObserver(EditorObserver):
    def on_event(self, event: str, editor: 'Editor') -> None:
        content = editor.get_content()
        caret   = editor.buffer.caret.position
        undo_d  = editor.history.undo_depth()
        redo_d  = editor.history.redo_depth()
        print(f"  [{event:<16}] content='{content}'"
              f"  caret={caret}  undo={undo_d}  redo={redo_d}")


# ============================================================================
# EDITOR (SINGLETON)
# ============================================================================

class Editor:
    """
    Singleton orchestrator.
    Coordinates TextBuffer, CommandHistory, and Observers.
    Thread-safe via RLock (re-entrant to allow nested calls).
    """

    _instance: Optional['Editor'] = None
    _class_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        # Fix: accept *args/**kwargs so super().__new__(cls) never sees extra args
        if cls._instance is None:
            with cls._class_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.buffer  = TextBuffer()
        self.history = CommandHistory(max_size=1000)
        self.observers: List[EditorObserver] = []
        # RLock: re-entrant so undo/redo can safely call _notify inside the lock
        self._lock = threading.RLock()

    @classmethod
    def get_instance(cls) -> 'Editor':
        return cls()

    @classmethod
    def reset(cls) -> None:
        """Test helper: destroy the singleton so tests start fresh."""
        with cls._class_lock:
            cls._instance = None

    # ------------------------------------------------------------------ edits

    def insert(self, position: int, text: str) -> None:
        with self._lock:
            cmd = InsertCommand(self.buffer, position, text)
            cmd.execute()
            self.history.push(cmd)
        self._notify(EditorEvent.TEXT_CHANGED.value)

    def delete(self, position: int, length: int) -> None:
        with self._lock:
            cmd = DeleteCommand(self.buffer, position, length)
            cmd.execute()
            self.history.push(cmd)
        self._notify(EditorEvent.TEXT_CHANGED.value)

    def replace(self, position: int, length: int, new_text: str) -> None:
        with self._lock:
            cmd = ReplaceCommand(self.buffer, position, length, new_text)
            cmd.execute()
            self.history.push(cmd)
        self._notify(EditorEvent.TEXT_CHANGED.value)

    # ----------------------------------------------------------------- undo/redo

    def undo(self) -> bool:
        with self._lock:
            cmd = self.history.undo()
        if cmd is None:
            return False
        self._notify(EditorEvent.UNDO_PERFORMED.value)
        return True

    def redo(self) -> bool:
        with self._lock:
            cmd = self.history.redo()
        if cmd is None:
            return False
        self._notify(EditorEvent.REDO_PERFORMED.value)
        return True

    # ----------------------------------------------------------------- queries

    def get_content(self) -> str:
        with self._lock:
            return self.buffer.get_text()

    def get_caret(self) -> int:
        with self._lock:
            return self.buffer.caret.position

    def can_undo(self) -> bool:
        with self._lock:
            return self.history.can_undo()

    def can_redo(self) -> bool:
        with self._lock:
            return self.history.can_redo()

    # ---------------------------------------------------------------- observers

    def add_observer(self, observer: EditorObserver) -> None:
        with self._lock:
            self.observers.append(observer)

    def _notify(self, event: str) -> None:
        with self._lock:
            obs_copy = list(self.observers)
        for obs in obs_copy:
            obs.on_event(event, self)

    # ---------------------------------------------------------------- snapshot

    def save_snapshot(self) -> EditorMemento:
        with self._lock:
            return self.buffer.save_memento()

    def restore_snapshot(self, memento: EditorMemento) -> None:
        with self._lock:
            self.buffer.restore_memento(memento)
            self.history.clear()
        self._notify(EditorEvent.HISTORY_CLEARED.value)


# ============================================================================
# DEMO
# ============================================================================

if __name__ == "__main__":
    print("=" * 65)
    print("TEXT EDITOR WITH UNDO & REDO — DEMO")
    print("=" * 65)

    # Reset singleton so demo always starts clean
    Editor.reset()
    editor = Editor.get_instance()
    editor.add_observer(ConsoleObserver())

    print("\n--- Step 1: Insert 'Hello' at position 0 ---")
    editor.insert(0, "Hello")

    print("\n--- Step 2: Insert ' World' at position 5 ---")
    editor.insert(5, " World")

    print("\n--- Step 3: Replace 'World' (pos=6, len=5) with 'Python' ---")
    editor.replace(6, 5, "Python")

    print("\n--- Step 4: Undo replace -> back to 'Hello World' ---")
    editor.undo()

    print("\n--- Step 5: Undo ' World' insert -> back to 'Hello' ---")
    editor.undo()

    print("\n--- Step 6: Redo -> 'Hello World' ---")
    editor.redo()

    print("\n--- Step 7: Delete 6 chars from pos 5 (' World') -> 'Hello' ---")
    editor.delete(5, 6)

    print("\n--- Step 8: New insert clears redo stack ---")
    editor.insert(5, "!")
    print(f"  can_redo after new edit: {editor.can_redo()}")   # False

    print("\n--- Step 9: Undo '!' -> 'Hello' ---")
    editor.undo()

    print("\n--- Step 10: Undo delete -> 'Hello World' ---")
    editor.undo()

    print("\n--- Step 11: Undo insert 'Hello' twice -> empty ---")
    editor.undo()
    editor.undo()

    print(f"\nFinal content : '{editor.get_content()}'")
    print(f"Undo stack    : {editor.history.undo_depth()}")
    print(f"Redo stack    : {editor.history.redo_depth()}")
    assert editor.get_content() == "", "Expected empty buffer"
    print("\nAll assertions passed.")
    print("=" * 65)
```

### Thread-Safety Analysis

| Operation | Lock Strategy | Guarantees |
|-----------|---|---|
| **insert / delete / replace** | RLock on editor | Command created + executed + pushed atomically |
| **undo** | RLock on editor | Pop + reverse + push to redo stack are atomic |
| **redo** | RLock on editor | Pop + re-execute + push to undo stack are atomic |
| **_notify** | Snapshot observers under lock; call outside | No deadlock from observer re-entering editor |
| **Singleton init** | Class-level Lock (double-checked) | Only one Editor instance created |

**Concurrency Principles**:
1. ✅ `threading.RLock` allows undo/redo to call `_notify` without deadlock
2. ✅ `__new__(cls, *args, **kwargs)` accepts extra arguments — fixes common Singleton bug
3. ✅ Observer list copied before iterating — observers added during notification do not affect current pass
4. ✅ Notifications fire outside the critical section to minimize lock hold time

---

## Demo Scenarios

### Scenario 1: Type, Replace, Undo/Redo

```
[text_changed    ] content='Hello'           caret=5  undo=1  redo=0
[text_changed    ] content='Hello World'     caret=11 undo=2  redo=0
[text_changed    ] content='Hello Python'    caret=12 undo=3  redo=0
[undo            ] content='Hello World'     caret=11 undo=2  redo=1
[undo            ] content='Hello'           caret=5  undo=1  redo=2
[redo            ] content='Hello World'     caret=11 undo=2  redo=1
```

### Scenario 2: Delete Characters

```
editor.delete(5, 6)   # Remove ' World'
[text_changed    ] content='Hello'  caret=5  undo=3  redo=0
```

### Scenario 3: New Edit Clears Redo Stack

```
editor.undo()         # undo delete
[undo            ] content='Hello World'  redo=1
editor.insert(5, "!") # new edit
[text_changed    ] content='Hello World!'  redo=0   ← redo stack cleared
```

### Scenario 4: Full Undo Sequence

```
Undo repeatedly until undo stack is empty:
  content='Hello World'  → 'Hello'  → ''
  undo stack depth = 0, buffer empty
```

---

## Interview Q&A

### Basic Questions

**Q1: How does the undo stack work?**

A: Every operation creates a Command object with `execute()` and `undo()`. After `execute()`, the command is pushed onto the undo stack. On undo, we `pop()` the top command, call `undo()`, and push it to the redo stack:

```python
def undo(self):
    cmd = self.undo_stack.pop()
    cmd.undo()                   # Reverses buffer changes
    self.redo_stack.append(cmd)  # Enables redo
```

**Q2: What's the difference between Command and Memento here?**

A: Command stores the *delta* (position + text) needed to reverse one operation — O(delta) memory. Memento stores the *full document snapshot* — O(n) memory. Use Command for every keystroke; Memento for infrequent save-point checkpoints.

**Q3: Why does a new edit clear the redo stack?**

A: The redo stack represents a linear future that is no longer valid once you branch off with a new edit. Preserving it would require a tree-structured history (common in advanced editors but out of scope for interviews).

**Q4: How does caret position survive undo/redo?**

A: Each Command stores `caret_before` (captured at construction) and `caret_after` (set during execute). `undo()` restores `caret_before`; `execute()` / `redo()` restores `caret_after`. The buffer caret is updated directly.

**Q5: Why use RLock instead of Lock?**

A: `_notify` calls observer methods while holding the lock. If an observer calls back into the editor (e.g., to read content), a plain `Lock` would deadlock. An `RLock` allows the same thread to re-enter the lock safely.

---

### Intermediate Questions

**Q6: How is Replace implemented as a single undo step?**

A: `ReplaceCommand.execute()` deletes the old range first (capturing `old_text`), then inserts `new_text`. `undo()` does the reverse — delete `new_text`, re-insert `old_text`. One command, one undo step.

**Q7: What happens if insert position is out of bounds?**

A: `TextBuffer.insert()` raises `IndexError` immediately. The command is never pushed to the history stack, so the undo stack remains consistent.

**Q8: How would you bound memory usage on the undo stack?**

A: Cap the stack at N commands (e.g., 1000). When full, drop the oldest (bottom) entry. Optionally, collapse the bottom K commands into a single `RestoreSnapshotCommand` to preserve more logical undo depth at the cost of one full copy.

**Q9: How do you handle compound operations (e.g., Find & Replace All)?**

A: Wrap multiple commands in a `MacroCommand` that implements `execute()` / `undo()` by iterating its inner list. This appears as a single undo step to the user.

**Q10: How would you add persistent undo (survive file save)?**

A: Serialize each `Command` (position, type, text delta) to a log file. On reload, deserialize and replay to restore the undo stack.

---

### Advanced Questions

**Q11: How would you support collaborative editing with undo?**

A: Operational Transformation (OT) adjusts the `position` field of each pending command when a remote edit arrives, so local undo still applies to the correct offset. CRDTs (Conflict-free Replicated Data Types) are an alternative that avoids explicit position adjustment.

**Q12: Why is a string inefficient for large documents, and what replaces it?**

A: Python `str` is immutable; every insert/delete creates a new string (O(n) copy). A **Rope** data structure — a binary tree of string chunks — performs insert/delete in O(log n) time and is used in production editors like VS Code.

---

## Scaling Q&A

### Q1: Undo depth limit — how do you prevent memory exhaustion?

**Solution**: Cap stack at 1000 commands (configurable). When exceeded, drop oldest. Optionally compress oldest 100 commands into a single `RestoreSnapshotCommand` (one full copy, 100 commands gone). Trade-off: undo depth vs memory.

### Q2: Collaborative editing — multiple users editing simultaneously?

**Solution**: Operational Transformation (OT) — each operation carries a vector clock. On receiving a remote op, adjust position offsets before applying locally. undo becomes "undo in context of current server state" requiring server-side undo. CRDTs (like YATA used by Yjs) handle this without a central server.

### Q3: Network sync — how to propagate each operation to other clients?

**Solution**: Publish each Command's serialized form (type, position, text, vector clock) to a message broker (Kafka, Pub/Sub). Each client subscribes, receives ops, applies OT transformation, then executes locally. This is how Google Docs-style editing works at scale.

### Q4: Large files (100 MB) — how does buffer performance degrade?

**Solution**: Replace `str` with a **Piece Table** or **Rope**. A piece table tracks the original buffer and an append buffer; insert/delete are O(log n). Most modern editors (VS Code, Vim, Emacs) use piece tables or gap buffers.

### Q5: How would you implement autosave without blocking the UI thread?

**Solution**: Periodically (every 30s) call `save_snapshot()` on a background thread. The snapshot is a cheap deep copy of the current string. Write it to disk asynchronously. On crash, restore from the last snapshot; replay the command log since then.

### Q6: What if undo history needs to persist across sessions?

**Solution**: Serialize each Command to a structured log (JSON/protobuf) at runtime. On open, load the log and reconstruct the undo stack. Pair with a base snapshot so replay is bounded — replaying from the snapshot forward, not from the beginning of time.

---

## Success Checklist

- [ ] Explain all 6 steps: Setup → Structure → Interface → Architecture → Optimization → Implementation
- [ ] Draw UML class diagram showing Editor, TextBuffer, Caret, Command hierarchy, CommandHistory, Observer
- [ ] Explain Command pattern: execute() + undo() + delta storage vs full copy
- [ ] Explain how Memento differs from Command (snapshot vs delta; when to use each)
- [ ] Demonstrate undo stack push on execute, pop on undo, transfer to redo stack
- [ ] Explain why new edit clears redo stack
- [ ] Explain caret_before / caret_after capture and restoration
- [ ] Run the complete implementation without errors (assert passes)
- [ ] Explain RLock vs Lock and why RLock is needed here
- [ ] Fix Singleton __new__ to accept *args/**kwargs
- [ ] Answer 5+ Interview Q&A questions
- [ ] Answer 3+ Scaling Q&A questions (OT/CRDT, Rope/Piece Table, autosave)
- [ ] Discuss trade-offs: delta vs snapshot, bounded vs unlimited history

---

**Ready for interview? Type, undo, and redo your way to the offer! ✏️**
