# Text Editor with Undo & Redo — 75-Minute Interview Guide

## Quick Start

### 5-Minute Overview
A collaborative text editor supporting unlimited undo/redo, text operations (insert, delete, replace), selection management, and command-based architecture. Core flow: **Type → Command → Execute → Add to UndoStack → Redo available**.

### Key Entities
| Entity | Purpose |
|--------|---------|
| **TextBuffer** | Core document content |
| **Command** | Text operation (insert, delete, replace) |
| **Memento** | Document snapshot for undo |
| **Editor** | Orchestrator managing buffer, stacks |

### 4 Design Patterns
1. **Command**: Execute, undo, redo operations
2. **Memento**: Save/restore document states
3. **Singleton**: Central editor instance
4. **Observer**: Notify UI of changes

### Critical Points
✅ Unlimited undo/redo → Command + stack pattern  
✅ Efficient storage → Memento snapshots  
✅ Text operations → Insert O(1), Delete O(n), Replace O(n)  
✅ Memory optimization → Store deltas not full copies  

---

## System Overview

### Problem
Users need unlimited undo/redo for text editors. Naive approach (full document copy per action) = memory overhead.

### Solution
Command pattern for operations + Memento for snapshots + incremental storage.

---

## Requirements

✅ Insert text at position  
✅ Delete text range  
✅ Replace text  
✅ Undo (infinite depth)  
✅ Redo (while not executing new command)  
✅ Save position (selection)  
✅ Efficient memory usage  

---

## Architecture & Patterns

### 1. Command Pattern
```python
class Command(ABC):
    @abstractmethod
    def execute(self):
        pass
    @abstractmethod
    def undo(self):
        pass

class InsertCommand(Command):
    def __init__(self, buffer, position, text):
        self.buffer = buffer
        self.position = position
        self.text = text
    
    def execute(self):
        self.buffer.insert(self.position, self.text)
    
    def undo(self):
        self.buffer.delete(self.position, len(self.text))
```

### 2. Memento Pattern
```python
class EditorMemento:
    def __init__(self, content, position):
        self.content = content
        self.position = position

class TextBuffer:
    def save_memento(self):
        return EditorMemento(self.content, self.cursor)
    
    def restore_memento(self, memento):
        self.content = memento.content
        self.cursor = memento.position
```

### 3. Singleton Editor
```python
class Editor:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.buffer = TextBuffer()
            cls._instance.undo_stack = []
            cls._instance.redo_stack = []
        return cls._instance
```

---

## Interview Q&A

### Q1: Undo stack implementation?
**A**: Stack of Command objects. On undo: pop, call command.undo(). On redo: pop from redo stack, execute.

### Q2: Memory optimization?
**A**: Store deltas (operation details) not full document copies. Rebuild state from operation history.

### Q3: Concurrent edits?
**A**: Operational Transformation (OT) for concurrent text editing. Each operation includes position adjustment.

### Q4: Large document performance?
**A**: Lazy undo - only compute full state when needed. Use rope data structure for efficient insert/delete.

### Q5: Selection persistence?
**A**: Store (start, end) positions in Memento. Restore selection on undo/redo.

---

## Scaling Q&A

### Q1: Collaborative editing (multiple users)?
**A**: Operational Transformation (OT) or CRDTs (Conflict-free Replicated Data Types) to merge edits.

### Q2: Undo depth limit?
**A**: Cap at 1000 commands max. Delete oldest when exceeded. Or compress old commands into snapshots.

### Q3: Network sync?
**A**: Publish each operation to Kafka. Other clients subscribe and apply operations locally.

---

## Demo
```python
editor = Editor()
editor.insert(0, "Hello")
editor.insert(5, " World")
print(editor.content)  # "Hello World"

editor.undo()  # "Hello"
editor.undo()  # ""
editor.redo()  # "Hello"
editor.redo()  # "Hello World"
```

---

**Ready for editing! ✏️**
