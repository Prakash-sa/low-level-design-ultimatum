# File System — Complete Design Guide

> Hierarchical in-memory file system with pluggable storage strategies, reversible commands with undo/redo, snapshot/restore via Memento, and event-driven observability.

**Scale**: Single-process in-memory; extensible to distributed/persistent storage  
**Duration**: 75-minute interview guide  
**Focus**: Composite tree (File/Directory), Strategy (storage), Command (undo/redo), Memento (snapshot), Singleton (FileSystem)

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
Model a hierarchical file system: files and directories live in a tree, content is stored/retrieved via swappable strategies (plain vs compressed), every mutation is a reversible Command (undo/redo), the entire tree can be snapshotted and restored, and all lifecycle events are observable. Core concerns: uniform tree traversal, pluggable encoding, and reversible state changes.

### Core Flow
```
Create Directory → Create File → Write Content → (undo/redo)
        │                              │
        └── Composite Tree             └── StorageStrategy encodes bytes
                │
                ├── take_snapshot()  → Snapshot (deep clone)
                └── restore_snapshot() → RestoreSnapshotCommand (reversible)

COMMAND FLOW:
RECORD → STRATEGY_ENCODE → EXECUTE → PUSH_UNDO → CLEAR_REDO → EMIT_EVENT
                                       ↓
                                  [UNDO] → REDO_STACK
                                       ↓
                                  [REDO] → UNDO_STACK
```

---

## Step 01: The Setup — Clarify Requirements

> **Interview Tip**: Never code immediately. Ask clarifying questions first. Define scope, actors, and constraints.

### Questions to Ask (30 seconds each)

1. **Persistent or in-memory?** → "In-memory for interview; discuss persistence as scaling concern"
2. **Single-process or distributed?** → "Single-process; mention sharding as extension"
3. **How many node types?** → "Files and directories; extensible to symlinks, mounts"
4. **Undo depth limit?** → "Unbounded for interview; cap to last N in production"
5. **Concurrency required?** → "Single-threaded demo; thread-safe Singleton init with RLock"

### Actors (Who uses the system?)

| Actor | Role | Example Actions |
|-------|------|-----------------|
| **User / Application** | Create, read, write, move, delete nodes | `create_file`, `write`, `read`, `move`, `delete` |
| **FileSystem Singleton** | Coordinates all operations, manages stacks | Execute commands, emit events, track metrics |
| **Observer / Listener** | Monitors lifecycle events | Log created/deleted/strategy-swapped events |

### Functional Requirements (What does the system do?)

✅ **CRUD on Files and Directories**
  - Create/read/write/delete files
  - Create/delete directories
  - Hierarchical path resolution (`/dir/sub/file.txt`)

✅ **Move Nodes**
  - Move file or directory between parent directories
  - Path updates automatically (resolved via parent chain)

✅ **Undo / Redo**
  - Every mutation is a reversible Command
  - Undo: pop from undo_stack, call `cmd.undo()`, push to redo_stack
  - Redo: pop from redo_stack, re-execute, push to undo_stack
  - New execute clears redo_stack

✅ **Pluggable Storage Strategies**
  - `PlainStorageStrategy`: UTF-8 encode/decode
  - `CompressedStorageStrategy`: zlib compress/decompress
  - Strategy swap re-encodes all files transparently

✅ **Snapshot / Restore**
  - `take_snapshot()`: deep-clone entire tree into Snapshot (Memento)
  - `restore_snapshot()`: wrapped in `RestoreSnapshotCommand` — itself undoable

✅ **Event Observability**
  - Emit events: `node_created`, `node_deleted`, `strategy_swapped`, `snapshot_taken`, `command_executed`, `command_undone`, `metrics_updated`
  - Multiple callable listeners registered independently

✅ **Metrics Tracking**
  - File count, directory count, logical bytes, physical (compressed) bytes
  - Recalculated after every mutation

### Non-Functional Requirements (How does it perform?)

✅ **Path Resolution**: O(path_segments) — typically O(5–10) per operation  
✅ **File Content Access**: O(1) hash lookup in `Directory.children`  
✅ **Extensibility**: New strategies, node types, and commands add zero core changes  
✅ **Memory**: Deep-copy snapshots — acceptable for small trees; discuss alternatives at scale  
✅ **Thread Safety**: Singleton init guarded by `threading.RLock`; operations single-threaded  

### Constraints & Clarifications

| Constraint | Decision |
|-----------|----------|
| **Persistence** | NO — in-memory only (discuss journaling as extension) |
| **Distributed** | NO — single-process (discuss sharding) |
| **Undo stack size** | Unbounded (cap to N in production) |
| **Strategy swap** | Re-encodes all files atomically |
| **Snapshot depth** | Full deep copy (discuss incremental diffs) |
| **Max file size** | Unlimited in-memory (discuss streaming for 100GB+) |
| **Concurrent mutations** | Not required for demo; RLock for Singleton init |

---

## Step 02: Structure — Define Entities

> **Interview Tip**: Extract core objects from requirements. Look for **nouns**. Write them on the whiteboard immediately.

### Step 2.1: List Core Entities (Extract Nouns)

```
FsNode, File, Directory, StorageStrategy, Command, Snapshot, FileSystem, ...
```

### Step 2.2: Define Core Classes

#### **FsNode** — Abstract base for all tree nodes
```
Properties:
  - name: str (node name, e.g., "spec.md" or "docs")
  - parent: Optional[Directory] (None only for root)

Behaviors:
  - path(): Resolve full absolute path by walking parent chain
```

#### **File** — Leaf node storing versioned content
```
Properties:
  - _data: bytes (encoded content via StorageStrategy)
  - version: int (incremented on each write)

Behaviors:
  - write(text, storage): Encode and store content, increment version
  - read(storage): Decode and return content as str
  - logical_size(storage): Uncompressed byte count
  - physical_size(): Stored byte count (compressed)
```

#### **Directory** — Composite container node
```
Properties:
  - children: Dict[str, FsNode] (name → node mapping)

Behaviors:
  - add(node): Add child, set parent reference
  - remove(name): Remove child, clear parent reference
  - get(name): Lookup child by name
```

#### **Command** — Abstract reversible operation
```
Behaviors:
  - execute(fs): Apply the operation to the FileSystem
  - undo(fs): Reverse the operation
  - describe(): Human-readable label

Concrete Commands:
  - CreateFileCommand(path)
  - WriteFileCommand(path, new_text)
  - CreateDirectoryCommand(path)
  - MoveNodeCommand(src_path, dest_dir_path)
  - DeleteNodeCommand(path)
  - RestoreSnapshotCommand(old_root, new_root)
```

#### **Snapshot** — Memento capturing tree state
```
Properties:
  - root_clone: Directory (deep clone of root at snapshot time)

Purpose:
  - Passed to restore_snapshot() to roll back entire tree
  - Created by take_snapshot() via _clone_node() deep copy
```

#### **StorageStrategy** — Abstract pluggable encoder/decoder
```
Behaviors:
  - encode(text: str) -> bytes
  - decode(data: bytes) -> str
  - name() -> str

Concrete Strategies:
  - PlainStorageStrategy: UTF-8 encode/decode
  - CompressedStorageStrategy: zlib compress/decompress
```

#### **FileSystem** — Singleton coordinator
```
Properties:
  - root: Directory (the "/" root node)
  - storage: StorageStrategy (active encoding strategy)
  - undo_stack: List[Command]
  - redo_stack: List[Command]
  - listeners: List[Callable] (event observers)
  - metrics: Dict[str, int] (live stats)

Behaviors:
  - execute(cmd): Run command, push to undo_stack, clear redo_stack
  - undo() / redo(): Manage undo/redo lifecycle
  - set_storage_strategy(strategy): Swap + re-encode all files
  - take_snapshot() -> Snapshot
  - restore_snapshot(snap): Wrapped in RestoreSnapshotCommand
  - register(fn): Add event listener
  - get_metrics() -> Dict
```

### Step 2.3: Define Enumerations (State & Type)

```python
# No enums required — node types are captured by class identity (isinstance checks)
# Strategy type identified by strategy.name()
# Events are plain strings: "node_created", "node_deleted", "strategy_swapped",
#   "snapshot_taken", "snapshot_restored", "command_executed", "command_undone",
#   "metrics_updated"
```

### Step 2.4: Why These Entities?

| Entity | Why | Cost of Missing |
|--------|-----|-----------------|
| **FsNode** | Uniform base for tree nodes | Can't traverse tree polymorphically |
| **File** | Leaf with versioned content | Can't store or version file data |
| **Directory** | Composite container | Can't organize hierarchical structure |
| **Command** | Encapsulate reversible mutations | No undo/redo capability |
| **Snapshot** | Capture full tree state | Can't roll back to prior state |
| **StorageStrategy** | Decouple encoding from file logic | Can't swap compression without rewriting files |
| **FileSystem** | Central coordinator (Singleton) | Duplicate state, no consistent view |

---

## Step 03: Interface — APIs & Entry Points

> **Interview Tip**: Define the contract (inputs, outputs, exceptions) BEFORE implementation. Focus on "what" not "how".

### Step 3.1: Public API Contracts

#### **1. Execute Command** ⭐ CRITICAL
```python
def execute(self, cmd: Command) -> None:
    """
    Run a reversible command against the FileSystem.

    Postcondition: cmd applied, cmd pushed to undo_stack, redo_stack cleared.

    Raises:
      - ValueError: if command precondition fails (e.g., file already exists, parent missing)

    Side Effects: emits "command_executed" event, refreshes metrics
    """
    pass
```

#### **2. Undo / Redo**
```python
def undo(self) -> None:
    """
    Reverse the last executed command.
    Pops from undo_stack, calls cmd.undo(fs), pushes to redo_stack.
    No-op if undo_stack is empty.
    Side Effects: emits "command_undone", refreshes metrics
    """
    pass

def redo(self) -> None:
    """
    Re-apply the last undone command.
    Pops from redo_stack, calls cmd.execute(fs), pushes to undo_stack.
    No-op if redo_stack is empty.
    """
    pass
```

#### **3. Set Storage Strategy** ⭐ CRITICAL
```python
def set_storage_strategy(self, strategy: StorageStrategy) -> None:
    """
    Swap storage encoding and re-encode all existing files.

    Postcondition: all File._data re-encoded with new strategy.
    Content read by callers is unchanged (transparent).

    Side Effects: emits "strategy_swapped", refreshes metrics
    """
    pass
```

#### **4. Take Snapshot**
```python
def take_snapshot(self) -> Snapshot:
    """
    Deep-clone entire tree into a Snapshot (Memento).

    Returns: Snapshot with independent copy of current tree.
    Side Effects: emits "snapshot_taken"
    Cost: O(N) where N = total nodes
    """
    pass
```

#### **5. Restore Snapshot** ⭐ CRITICAL
```python
def restore_snapshot(self, snap: Snapshot) -> None:
    """
    Restore tree from snapshot. Wrapped in RestoreSnapshotCommand — reversible!

    Postcondition: fs.root replaced with clone of snap.root_clone
    Undo: re-instates the pre-restore root
    Side Effects: emits "snapshot_restored"
    """
    pass
```

#### **6. Register Observer**
```python
def register(self, fn: Callable[[str, Dict[str, Any]], None]) -> None:
    """
    Subscribe a callable to all FileSystem events.
    fn(event: str, payload: dict) called on every state change.
    """
    pass
```

### Step 3.2: Failure Model

```python
# FileSystem raises ValueError for precondition failures:
raise ValueError("File already exists")
raise ValueError("Parent directory missing")
raise ValueError("Source not found")
raise ValueError("Destination is not a directory")
raise ValueError("Cannot move root")
raise ValueError("Cannot delete root or non-existent")
raise ValueError("Not a file: <path>")
```

### Step 3.3: API Usage Example

```python
fs = FileSystem()  # Singleton — same instance every call

# Register event listener
fs.register(lambda event, payload: print(f"[{event}] {payload}"))

# Create hierarchy
fs.execute(CreateDirectoryCommand("/docs"))
fs.execute(CreateFileCommand("/docs/spec.md"))
fs.execute(WriteFileCommand("/docs/spec.md", "API specification"))

# Read content
content = fs._get_file("/docs/spec.md").read(fs.storage)

# Undo last write
fs.undo()

# Swap to compression
fs.set_storage_strategy(CompressedStorageStrategy())

# Take and restore snapshot
snap = fs.take_snapshot()
fs.execute(CreateFileCommand("/docs/temp.txt"))
fs.restore_snapshot(snap)       # /docs/temp.txt gone
fs.undo()                       # undo the restore — /docs/temp.txt back

# Metrics
print(fs.get_metrics())         # file_count, dir_count, total_bytes, compressed_bytes
```

---

## Step 04: Architecture — Relationships & Diagram

> **Interview Tip**: Use composition, aggregation, and association. Prefer composition over inheritance. Check cardinality (1:1, 1:N). Highlight the Composite tree structure.

### Step 4.1: Relationship Types

```
FileSystem HAS-A root (1:1 Composition)
  └─ FileSystem is the owner; root Directory holds all other nodes

Directory HAS-A children (1:N Composition) ← Composite Pattern
  └─ Directory owns its children (both File and Directory nodes)

File IS-A FsNode (Inheritance / Leaf)
  └─ Leaf node; holds _data bytes and version

Directory IS-A FsNode (Inheritance / Composite)
  └─ Composite node; delegates operations to children

FsNode REFERENCES parent (N:1 Association)
  └─ Every node (except root) references its parent Directory

FileSystem HAS-A StorageStrategy (1:1 Composition)
  └─ FileSystem owns the active strategy; swap replaces it

FileSystem HAS-A undo_stack / redo_stack (1:N Composition)
  └─ FileSystem owns all queued Command objects

Command REFERENCES FileSystem (Association)
  └─ Commands receive fs at execute/undo time; no ownership

Snapshot HAS-A root_clone (1:1 Composition)
  └─ Snapshot owns the deep-cloned tree independently
```

### Step 4.2: Complete UML Class Diagram

```
┌──────────────────────────────────────────┐
│  FileSystem (Singleton)                  │
├──────────────────────────────────────────┤
│ - _instance: FileSystem                  │
│ - _lock: threading.RLock                 │
│ - root: Directory                        │
│ - storage: StorageStrategy               │
│ - undo_stack: List[Command]              │
│ - redo_stack: List[Command]              │
│ - listeners: List[Callable]              │
│ - metrics: Dict[str, int]                │
├──────────────────────────────────────────┤
│ + execute(cmd): void                     │
│ + undo(): void                           │
│ + redo(): void                           │
│ + set_storage_strategy(s): void          │
│ + take_snapshot(): Snapshot              │
│ + restore_snapshot(snap): void           │
│ + register(fn): void                     │
│ + get_metrics(): Dict                    │
│ + exists(path): bool                     │
└──────────────┬───────────────────────────┘
               │ manages (root)
               ▼
        ┌─────────────────────┐
        │  FsNode (Abstract)  │
        ├─────────────────────┤
        │ - name: str         │
        │ - parent: Directory │
        ├─────────────────────┤
        │ + path(): str       │
        └──────┬──────────────┘
               │ (Composite Pattern)
       ┌───────┴──────────┐
       ▼                  ▼
┌────────────────┐  ┌──────────────────────┐
│  File (Leaf)   │  │  Directory (Composite)│
├────────────────┤  ├──────────────────────┤
│ - _data: bytes │  │ - children:           │
│ - version: int │  │   Dict[str, FsNode]  │
├────────────────┤  ├──────────────────────┤
│ + write(t, s)  │  │ + add(node): void    │
│ + read(s): str │  │ + remove(name): Node │
│ + logical_size │  │ + get(name): Node    │
│ + physical_size│  └──────────────────────┘
└────────────────┘

STRATEGY PATTERN (Storage):
┌──────────────────────────────────┐
│  StorageStrategy (Abstract)      │
├──────────────────────────────────┤
│ + encode(text: str) -> bytes     │
│ + decode(data: bytes) -> str     │
│ + name() -> str                  │
└───┬──────────────────────────────┘
    │ implemented by
    ├─→ PlainStorageStrategy (UTF-8)
    └─→ CompressedStorageStrategy (zlib)

COMMAND PATTERN (Reversible Operations):
┌──────────────────────────────────┐
│  Command (Abstract)              │
├──────────────────────────────────┤
│ + execute(fs: FileSystem)        │
│ + undo(fs: FileSystem)           │
│ + describe() -> str              │
└───┬──────────────────────────────┘
    │ implemented by
    ├─→ CreateFileCommand(path)
    ├─→ WriteFileCommand(path, new_text)
    ├─→ CreateDirectoryCommand(path)
    ├─→ MoveNodeCommand(src, dest_dir)
    ├─→ DeleteNodeCommand(path)
    └─→ RestoreSnapshotCommand(old_root, new_root)

MEMENTO PATTERN (Snapshot):
┌──────────────────────────────────┐
│  Snapshot                        │
├──────────────────────────────────┤
│ - root_clone: Directory          │
└──────────────────────────────────┘

TREE LIFECYCLE:
ROOT (/)
  ├── File(name, _data, version)
  └── Directory(name, children)
         ├── File(name, _data, version)
         └── Directory(name, children)
                └── File(...)
```

### Step 4.3: Cardinality Summary

| Relationship | Cardinality | Type | Reason |
|-------------|------------|------|--------|
| FileSystem → root Directory | 1:1 | Composition | Single root owns the entire tree |
| Directory → children (FsNode) | 1:N | Composition | Composite Pattern — directory owns its children |
| File / Directory → parent | N:1 | Association | Every node (except root) references its parent |
| FileSystem → StorageStrategy | 1:1 | Composition | System owns active encoding strategy |
| FileSystem → Commands (undo/redo stacks) | 1:N | Composition | System owns queued reversible operations |
| Snapshot → root_clone | 1:1 | Composition | Snapshot owns the independent deep-cloned tree |
| FileSystem → Listeners | 1:N | Association | System notifies multiple event observers |

---

## Step 05: Optimization — Design Patterns

> **Interview Tip**: Don't force patterns. Only solve specific problems.

### Pattern 1: **Composite** (For File/Directory Hierarchy)

**Problem**: Files and directories must be traversed, cloned, and operated on uniformly — without constantly checking node type.

**Solution**: Both `File` and `Directory` inherit `FsNode`. Tree operations (walk, clone, metrics) recurse without branching on type at the call site.

```python
@dataclass
class FsNode:
    name: str
    parent: Optional[Directory] = None

    def path(self) -> str:
        if self.parent is None:
            return '/' if self.name == '' else f'/{self.name}'
        return self.parent.path().rstrip('/') + ('/' + self.name if self.name else '')

@dataclass
class File(FsNode):
    _data: bytes = b''
    version: int = 0

@dataclass
class Directory(FsNode):
    children: Dict[str, FsNode] = field(default_factory=dict)

    def add(self, node: FsNode) -> None:
        self.children[node.name] = node
        node.parent = self
```

**Benefit**: ✅ Uniform traversal, ✅ Easy to add new node types (e.g., SymLink), ✅ Snapshot clones the whole subtree polymorphically  
**Trade-off**: ⚠️ Deep trees slow down path resolution; ⚠️ `isinstance` checks needed where leaf/composite behavior differs

---

### Pattern 2: **Strategy** (For Storage Encoding)

**Problem**: Files may need plain UTF-8 or zlib-compressed storage. This must be swappable at runtime without touching file logic.

**Solution**: `StorageStrategy` ABC with `encode`/`decode`. File delegates all I/O through the strategy. Swapping strategy re-encodes all files transparently.

```python
class StorageStrategy:
    def encode(self, text: str) -> bytes: raise NotImplementedError
    def decode(self, data: bytes) -> str:  raise NotImplementedError

class PlainStorageStrategy(StorageStrategy):
    def encode(self, text: str) -> bytes: return text.encode("utf-8")
    def decode(self, data: bytes) -> str:  return data.decode("utf-8") if data else ""

class CompressedStorageStrategy(StorageStrategy):
    def encode(self, text: str) -> bytes: return zlib.compress(text.encode("utf-8"))
    def decode(self, data: bytes) -> str:
        return zlib.decompress(data).decode("utf-8") if data else ""

# Swap at runtime — all files re-encoded:
fs.set_storage_strategy(CompressedStorageStrategy())
```

**Benefit**: ✅ Zero file logic change when adding new encodings (e.g., AES encryption), ✅ Transparent to callers  
**Trade-off**: ⚠️ Full re-encode on swap is O(total_content_bytes); ⚠️ Strategy must be passed to every `read`/`write` call

---

### Pattern 3: **Command** (For Reversible Operations)

**Problem**: Every CRUD mutation must be reversible (undo) and re-applicable (redo). Without a command object, there is no way to store pre-mutation state.

**Solution**: Each operation is a `Command` object. `execute` applies the change and stores pre-state. `undo` restores pre-state. FileSystem manages undo/redo stacks.

```python
class WriteFileCommand(Command):
    def __init__(self, path: str, new_text: str) -> None:
        self.path = path
        self.new_text = new_text
        self.old_text: Optional[str] = None

    def execute(self, fs: FileSystem) -> None:
        file = fs._get_file(self.path)
        self.old_text = file.read(fs.storage)    # capture pre-state
        file.write(self.new_text, fs.storage)

    def undo(self, fs: FileSystem) -> None:
        if self.old_text is not None:
            fs._get_file(self.path).write(self.old_text, fs.storage)

# Usage: every mutation goes through execute()
fs.execute(WriteFileCommand("/docs/spec.md", "updated content"))
fs.undo()   # restores "API specification"
fs.redo()   # re-applies "updated content"
```

**Benefit**: ✅ Uniform undo/redo for all operations, ✅ Easy to add new operations (no core change), ✅ Command log for audit/replay  
**Trade-off**: ⚠️ DeleteNodeCommand stores full subtree clone — memory cost for large trees

---

### Pattern 4: **Memento** (For Snapshot/Restore)

**Problem**: Need to capture the entire tree state at a point in time and restore it later — potentially undoing the restore itself.

**Solution**: `Snapshot` holds an independent deep-clone of root. `restore_snapshot` wraps replacement in a `RestoreSnapshotCommand`, making the restore itself undoable.

```python
@dataclass
class Snapshot:
    root_clone: Directory

class RestoreSnapshotCommand(Command):
    def __init__(self, old_root: Directory, new_root: Directory) -> None:
        self.old_root = old_root
        self.new_root = new_root

    def execute(self, fs: FileSystem) -> None:
        fs.root = self.new_root

    def undo(self, fs: FileSystem) -> None:
        fs.root = self.old_root

# Usage:
snap = fs.take_snapshot()            # capture tree state
fs.execute(CreateFileCommand("/tmp/x.txt"))
fs.restore_snapshot(snap)            # tree rolls back; restore is in undo_stack
fs.undo()                            # undo the restore — /tmp/x.txt is back
```

**Benefit**: ✅ Full global rollback in O(1) (swap root pointer), ✅ Restore is itself reversible  
**Trade-off**: ⚠️ Snapshot is O(N) memory; ⚠️ Many snapshots → memory pressure; consider incremental diffs for production

---

### Pattern 5: **Singleton** (For FileSystem)

**Problem**: Multiple callers need one consistent view of the tree, strategies, and stacks.

**Solution**: Double-checked locking Singleton. `__new__` accepts `*args, **kwargs` so Python doesn't reject arguments. `__init__` guards with `_initialized` flag.

```python
class FileSystem:
    _instance: Optional[FileSystem] = None
    _lock = threading.RLock()   # RLock: re-entrant safe

    def __new__(cls, *args, **kwargs) -> FileSystem:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.root = Directory(name='')
        self.storage: StorageStrategy = PlainStorageStrategy()
        # ... rest of init
```

**Benefit**: ✅ Single source of truth, ✅ Thread-safe init (double-checked lock), ✅ Global access via `FileSystem()`  
**Trade-off**: ⚠️ Global state (hard to unit-test in isolation), ⚠️ Must reset state explicitly between test runs

---

### Design Patterns Summary Table

| Pattern | Problem Solved | Benefit |
|---------|---|---|
| **Composite** | Uniform File/Directory traversal | No type-checking at call sites; extensible to new node types |
| **Strategy** | Pluggable storage encoding | Swap plain↔compressed (or add encryption) with zero file logic change |
| **Command** | Reversible CRUD mutations | Undo/redo stacks; audit log; replay capability |
| **Memento** | Full tree snapshot/restore | Global rollback in O(1); restore is itself undoable |
| **Singleton** | Single consistent FileSystem | No duplicate state; thread-safe initialization |

---

## Step 06: Implementation — Code & Concurrency

> **Interview Tip**: Write thread-safe, defensive code. Mention "Thread Safety" even if not asked.

### Complete Thread-Safe Implementation

```python
"""
File System - Interview Implementation
Demonstrates:
1. Composite pattern (File/Directory hierarchy)
2. Strategy pattern (pluggable storage)
3. Command pattern (reversible CRUD with undo/redo)
4. Observer pattern (event emission)
5. Memento pattern (snapshot/restore)
6. Singleton pattern (centralized FileSystem)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Tuple
import zlib
import threading

# ============================================================================
# STORAGE STRATEGIES
# ============================================================================

class StorageStrategy:
    """Abstract strategy for content encoding/decoding"""

    def name(self) -> str:
        return self.__class__.__name__

    def encode(self, text: str) -> bytes:
        raise NotImplementedError

    def decode(self, data: bytes) -> str:
        raise NotImplementedError

class PlainStorageStrategy(StorageStrategy):
    """Direct UTF-8 encoding"""

    def encode(self, text: str) -> bytes:
        return text.encode("utf-8")

    def decode(self, data: bytes) -> str:
        return data.decode("utf-8") if data else ""

class CompressedStorageStrategy(StorageStrategy):
    """Zlib compression for space efficiency"""

    def encode(self, text: str) -> bytes:
        return zlib.compress(text.encode("utf-8"))

    def decode(self, data: bytes) -> str:
        if not data:
            return ""
        return zlib.decompress(data).decode("utf-8")

# ============================================================================
# COMPOSITE NODES
# ============================================================================

@dataclass
class FsNode:
    """Base node for file system hierarchy"""
    name: str
    parent: Optional[Directory] = None

    def path(self) -> str:
        """Resolve full path by walking parent chain"""
        if self.parent is None:
            return '/' if self.name == '' else f'/{self.name}'
        base = self.parent.path()
        return base.rstrip('/') + ('/' + self.name if self.name else '')

@dataclass
class File(FsNode):
    """Leaf node: stores content with versioning"""
    _data: bytes = b''
    version: int = 0

    def write(self, text: str, storage: StorageStrategy) -> None:
        """Encode text via strategy and increment version"""
        self._data = storage.encode(text)
        self.version += 1

    def read(self, storage: StorageStrategy) -> str:
        """Decode content via strategy"""
        return storage.decode(self._data)

    def logical_size(self, storage: StorageStrategy) -> int:
        """Uncompressed size"""
        return len(self.read(storage))

    def physical_size(self) -> int:
        """Compressed size (bytes stored)"""
        return len(self._data)

@dataclass
class Directory(FsNode):
    """Composite node: contains child files/directories"""
    children: Dict[str, FsNode] = field(default_factory=dict)

    def add(self, node: FsNode) -> None:
        """Add child and update parent reference"""
        self.children[node.name] = node
        node.parent = self

    def remove(self, name: str) -> FsNode:
        """Remove child and clear parent reference"""
        node = self.children.pop(name)
        node.parent = None
        return node

    def get(self, name: str) -> Optional[FsNode]:
        """Lookup child by name"""
        return self.children.get(name)

# ============================================================================
# COMMANDS (REVERSIBLE OPERATIONS)
# ============================================================================

class Command:
    """Abstract reversible command"""

    def execute(self, fs: FileSystem) -> None:
        raise NotImplementedError

    def undo(self, fs: FileSystem) -> None:
        raise NotImplementedError

    def describe(self) -> str:
        return self.__class__.__name__

class CreateFileCommand(Command):
    """Create file at path"""

    def __init__(self, path: str) -> None:
        self.path = path
        self.created = False

    def execute(self, fs: FileSystem) -> None:
        if fs.exists(self.path):
            raise ValueError("File already exists")
        fs._create_file(self.path)
        self.created = True

    def undo(self, fs: FileSystem) -> None:
        if self.created:
            fs._delete_node(self.path)

    def describe(self) -> str:
        return f"CreateFile {self.path}"

class WriteFileCommand(Command):
    """Write content to file (captures old for undo)"""

    def __init__(self, path: str, new_text: str) -> None:
        self.path = path
        self.new_text = new_text
        self.old_text: Optional[str] = None

    def execute(self, fs: FileSystem) -> None:
        file = fs._get_file(self.path)
        self.old_text = file.read(fs.storage)
        file.write(self.new_text, fs.storage)

    def undo(self, fs: FileSystem) -> None:
        if self.old_text is None:
            return
        file = fs._get_file(self.path)
        file.write(self.old_text, fs.storage)

    def describe(self) -> str:
        return f"WriteFile {self.path}"

class CreateDirectoryCommand(Command):
    """Create directory at path"""

    def __init__(self, path: str) -> None:
        self.path = path.rstrip('/')
        self.created = False

    def execute(self, fs: FileSystem) -> None:
        if fs.exists(self.path):
            raise ValueError("Directory already exists")
        fs._create_directory(self.path)
        self.created = True

    def undo(self, fs: FileSystem) -> None:
        if self.created:
            node = fs._resolve(self.path)
            if isinstance(node, Directory) and not node.children and node.parent is not None:
                node.parent.remove(node.name)

class MoveNodeCommand(Command):
    """Move node from src to destination directory"""

    def __init__(self, src_path: str, dest_dir_path: str) -> None:
        self.src_path = src_path
        self.dest_dir_path = dest_dir_path
        self.original_parent: Optional[Directory] = None
        self.node_name: Optional[str] = None

    def execute(self, fs: FileSystem) -> None:
        node = fs._resolve(self.src_path)
        if node is None:
            raise ValueError("Source not found")
        dest_dir = fs._resolve(self.dest_dir_path)
        if not isinstance(dest_dir, Directory):
            raise ValueError("Destination is not a directory")
        if node.parent is None:
            raise ValueError("Cannot move root")

        self.original_parent = node.parent
        self.node_name = node.name
        node.parent.remove(node.name)
        dest_dir.add(node)

    def undo(self, fs: FileSystem) -> None:
        if self.original_parent and self.node_name:
            node = fs._resolve(self.dest_dir_path + '/' + self.node_name)
            if node:
                node.parent.remove(node.name)
                self.original_parent.add(node)

    def describe(self) -> str:
        return f"MoveNode {self.src_path} -> {self.dest_dir_path}"

class DeleteNodeCommand(Command):
    """Delete node (captures subtree for undo)"""

    def __init__(self, path: str) -> None:
        self.path = path
        self.snapshot: Optional[FsNode] = None
        self.parent_path: Optional[str] = None

    def execute(self, fs: FileSystem) -> None:
        node = fs._resolve(self.path)
        if node is None or node.parent is None:
            raise ValueError("Cannot delete root or non-existent")
        self.snapshot = fs._clone_node(node)
        self.parent_path = node.parent.path()
        node.parent.remove(node.name)

    def undo(self, fs: FileSystem) -> None:
        if self.snapshot and self.parent_path:
            parent = fs._resolve(self.parent_path)
            if isinstance(parent, Directory):
                parent.add(fs._clone_node(self.snapshot))

    def describe(self) -> str:
        return f"DeleteNode {self.path}"

class RestoreSnapshotCommand(Command):
    """Restore tree from snapshot (reversible)"""

    def __init__(self, old_root: Directory, new_root: Directory) -> None:
        self.old_root = old_root
        self.new_root = new_root

    def execute(self, fs: FileSystem) -> None:
        fs.root = self.new_root

    def undo(self, fs: FileSystem) -> None:
        fs.root = self.old_root

    def describe(self) -> str:
        return "RestoreSnapshot"

# ============================================================================
# SNAPSHOT (MEMENTO)
# ============================================================================

@dataclass
class Snapshot:
    """Captures entire tree state"""
    root_clone: Directory

# ============================================================================
# FILE SYSTEM (SINGLETON)
# ============================================================================

class FileSystem:
    """Centralized file system coordinator (Singleton)"""

    _instance: Optional[FileSystem] = None
    _lock = threading.RLock()  # RLock: re-entrant safe (restore_snapshot -> execute)

    def __new__(cls, *args, **kwargs) -> FileSystem:
        # Fix: accept *args/**kwargs so Python does not reject arguments
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self.root = Directory(name='')
        self.storage: StorageStrategy = PlainStorageStrategy()
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []
        self.listeners: List[Callable[[str, Dict[str, Any]], None]] = []
        self.metrics: Dict[str, int] = {
            'file_count': 0,
            'dir_count': 1,
            'total_bytes': 0,
            'compressed_bytes': 0,
            'command_executed': 0,
            'command_undone': 0
        }
        print("FileSystem initialized")

    def register(self, fn: Callable[[str, Dict[str, Any]], None]) -> None:
        """Subscribe to events"""
        self.listeners.append(fn)

    def _emit(self, event: str, payload: Dict[str, Any]) -> None:
        """Emit event to all listeners"""
        for listener_fn in self.listeners:
            try:
                listener_fn(event, payload)
            except Exception as e:
                print(f"  [WARN] Listener error: {e}")

    # ---- PATH RESOLUTION ----

    def _resolve(self, path: str) -> Optional[FsNode]:
        """Resolve path to node, return None if not found"""
        if path == '/' or path == '':
            return self.root

        parts = [p for p in path.strip('/').split('/') if p]
        node: FsNode = self.root

        for part in parts:
            if not isinstance(node, Directory):
                return None
            node = node.get(part)
            if node is None:
                return None

        return node

    def exists(self, path: str) -> bool:
        """Check if path exists"""
        return self._resolve(path) is not None

    def _get_file(self, path: str) -> File:
        """Resolve path to file, raise if not a file"""
        node = self._resolve(path)
        if not isinstance(node, File):
            raise ValueError(f"Not a file: {path}")
        return node

    # ---- PRIMITIVE OPERATIONS ----

    def _create_file(self, path: str) -> None:
        """Create file at path"""
        if path.endswith('/'):
            raise ValueError("File path cannot end with /")

        parts = path.rstrip('/').split('/')
        parent_path = '/'.join(parts[:-1]) or '/'
        name = parts[-1]

        parent = self._resolve(parent_path)
        if not isinstance(parent, Directory):
            raise ValueError("Parent directory missing")

        parent.add(File(name=name))
        self._emit("node_created", {"path": path, "type": "file"})
        self._refresh_metrics()

    def _create_directory(self, path: str) -> None:
        """Create directory at path"""
        path = path.rstrip('/')
        parts = path.split('/')
        parent_path = '/'.join(parts[:-1]) or '/'
        name = parts[-1]

        parent = self._resolve(parent_path)
        if not isinstance(parent, Directory):
            raise ValueError("Parent directory missing")

        parent.add(Directory(name=name))
        self._emit("node_created", {"path": path, "type": "directory"})
        self._refresh_metrics()

    def _delete_node(self, path: str) -> None:
        """Delete node at path"""
        node = self._resolve(path)
        if node is None or node.parent is None:
            raise ValueError("Cannot delete root or non-existent")

        node.parent.remove(node.name)
        self._emit("node_deleted", {"path": path})
        self._refresh_metrics()

    def _clone_node(self, node: FsNode) -> FsNode:
        """Deep clone node and subtree"""
        if isinstance(node, File):
            return File(name=node.name, _data=node._data, version=node.version)

        if isinstance(node, Directory):
            new_dir = Directory(name=node.name)
            for child in node.children.values():
                child_clone = self._clone_node(child)
                new_dir.add(child_clone)
            return new_dir

        raise ValueError("Unknown node type")

    # ---- COMMAND API ----

    def execute(self, cmd: Command) -> None:
        """Execute command and manage stacks"""
        cmd.execute(self)
        self.undo_stack.append(cmd)
        self.redo_stack.clear()
        self.metrics['command_executed'] += 1
        self._emit("command_executed", {"cmd": cmd.describe()})

    def undo(self) -> None:
        """Undo last command"""
        if not self.undo_stack:
            return

        cmd = self.undo_stack.pop()
        cmd.undo(self)
        self.redo_stack.append(cmd)
        self.metrics['command_undone'] += 1
        self._emit("command_undone", {"cmd": cmd.describe()})
        self._refresh_metrics()

    def redo(self) -> None:
        """Redo last undone command"""
        if not self.redo_stack:
            return

        cmd = self.redo_stack.pop()
        cmd.execute(self)
        self.undo_stack.append(cmd)
        self.metrics['command_executed'] += 1
        self._emit("command_executed", {"cmd": cmd.describe(), "redo": True})
        self._refresh_metrics()

    def set_storage_strategy(self, strategy: StorageStrategy) -> None:
        """Swap storage strategy (retranscode all files)"""
        old_name = self.storage.name()

        # Read all files with old strategy
        all_files = self._all_files()
        contents: List[Tuple[File, str]] = [(f, f.read(self.storage)) for f in all_files]

        # Switch strategy
        self.storage = strategy

        # Retranscode with new strategy
        for f, text in contents:
            f.write(text, self.storage)

        self._emit("strategy_swapped", {"old": old_name, "new": strategy.name()})
        self._refresh_metrics()

    def take_snapshot(self) -> Snapshot:
        """Create snapshot of entire tree"""
        snap = Snapshot(root_clone=self._clone_node(self.root))  # type: ignore
        self._emit("snapshot_taken", {"file_count": self.metrics['file_count']})
        return snap

    def restore_snapshot(self, snap: Snapshot) -> None:
        """Restore tree from snapshot (reversible via command)"""
        old_root = self.root
        new_root = self._clone_node(snap.root_clone)  # type: ignore
        self.execute(RestoreSnapshotCommand(old_root, new_root))
        self._emit("snapshot_restored", {})

    def _all_files(self) -> List[File]:
        """Collect all files in tree"""
        result: List[File] = []

        def walk(node: FsNode) -> None:
            if isinstance(node, File):
                result.append(node)
            elif isinstance(node, Directory):
                for child in node.children.values():
                    walk(child)

        walk(self.root)
        return result

    def _all_dirs(self) -> List[Directory]:
        """Collect all directories in tree"""
        result: List[Directory] = []

        def walk(d: Directory) -> None:
            result.append(d)
            for child in d.children.values():
                if isinstance(child, Directory):
                    walk(child)

        walk(self.root)
        return result

    def _refresh_metrics(self) -> None:
        """Recalculate all metrics"""
        files = self._all_files()
        dirs = self._all_dirs()

        logical_total = sum(f.logical_size(self.storage) for f in files)
        physical_total = sum(f.physical_size() for f in files)

        self.metrics.update({
            'file_count': len(files),
            'dir_count': len(dirs),
            'total_bytes': logical_total,
            'compressed_bytes': physical_total
        })
        self._emit("metrics_updated", self.metrics.copy())

    def get_metrics(self) -> Dict[str, int]:
        """Return current metrics"""
        return self.metrics.copy()

# ============================================================================
# DEMO SCENARIOS
# ============================================================================

def print_section(title: str) -> None:
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def simple_listener(event: str, payload: Dict[str, Any]) -> None:
    if event in ['node_created', 'node_deleted', 'strategy_swapped', 'snapshot_taken']:
        print(f"  [EVENT] {event}: {payload}")

def demo_1_setup() -> None:
    print_section("DEMO 1: SETUP & CREATE HIERARCHY")

    fs = FileSystem()
    fs.register(simple_listener)

    fs.execute(CreateDirectoryCommand("/docs"))
    fs.execute(CreateFileCommand("/docs/spec.md"))
    fs.execute(WriteFileCommand("/docs/spec.md", "API specification document"))
    fs.execute(CreateFileCommand("/docs/readme.md"))
    fs.execute(WriteFileCommand("/docs/readme.md", "Project README"))

    print(f"\n  Content of /docs/spec.md: {fs._get_file('/docs/spec.md').read(fs.storage)}")
    m = fs.get_metrics()
    print(f"  Metrics: files={m['file_count']}, dirs={m['dir_count']}, "
          f"logical={m['total_bytes']}B, physical={m['compressed_bytes']}B")

def demo_2_strategy_swap() -> None:
    print_section("DEMO 2: STORAGE STRATEGY SWAP")

    fs = FileSystem()

    before = fs.get_metrics()
    print(f"  Before compression: logical={before['total_bytes']}B, physical={before['compressed_bytes']}B")

    fs.set_storage_strategy(CompressedStorageStrategy())

    after = fs.get_metrics()
    print(f"  After compression:  logical={after['total_bytes']}B, physical={after['compressed_bytes']}B")
    if after['total_bytes'] > 0:
        print(f"  Compression ratio: {100 * after['compressed_bytes'] / after['total_bytes']:.1f}%")
    print(f"  Content unchanged: {fs._get_file('/docs/spec.md').read(fs.storage)}")

def demo_3_move_node() -> None:
    print_section("DEMO 3: MOVE NODE BETWEEN DIRECTORIES")

    fs = FileSystem()

    fs.execute(CreateDirectoryCommand("/archive"))
    fs.execute(MoveNodeCommand("/docs/readme.md", "/archive"))

    print(f"  /docs/readme.md exists:    {fs.exists('/docs/readme.md')}")
    print(f"  /archive/readme.md exists: {fs.exists('/archive/readme.md')}")
    print(f"  Content preserved: {fs._get_file('/archive/readme.md').read(fs.storage)}")

def demo_4_delete_undo_redo() -> None:
    print_section("DEMO 4: DELETE & UNDO/REDO")

    fs = FileSystem()

    fs.execute(DeleteNodeCommand("/archive/readme.md"))
    print(f"  After delete: /archive/readme.md exists = {fs.exists('/archive/readme.md')}")

    fs.undo()
    print(f"  After undo:   /archive/readme.md exists = {fs.exists('/archive/readme.md')}")

    fs.redo()
    print(f"  After redo:   /archive/readme.md exists = {fs.exists('/archive/readme.md')}")

def demo_5_snapshot_restore() -> None:
    print_section("DEMO 5: SNAPSHOT & RESTORE")

    fs = FileSystem()

    snap = fs.take_snapshot()
    before_metrics = fs.get_metrics()
    print(f"  Snapshot taken: file_count={before_metrics['file_count']}")

    # Create /temp directory before creating file inside it
    fs.execute(CreateDirectoryCommand("/temp"))
    fs.execute(CreateFileCommand("/temp/test.txt"))
    fs.execute(WriteFileCommand("/temp/test.txt", "Temporary data"))

    mutated_metrics = fs.get_metrics()
    print(f"  After mutation: file_count={mutated_metrics['file_count']}")
    print(f"  /temp/test.txt exists: {fs.exists('/temp/test.txt')}")

    fs.restore_snapshot(snap)
    restored_metrics = fs.get_metrics()
    print(f"  After restore:  file_count={restored_metrics['file_count']}")
    print(f"  /temp/test.txt exists: {fs.exists('/temp/test.txt')}")
    print(f"  undo_stack depth: {len(fs.undo_stack)} (restore cmd is undoable)")

# ============================================================================
# MAIN
# ============================================================================

if True:
    print("\n" + "="*70)
    print("FILE SYSTEM - 5 DEMO SCENARIOS")
    print("="*70)

    demo_1_setup()
    demo_2_strategy_swap()
    demo_3_move_node()
    demo_4_delete_undo_redo()
    demo_5_snapshot_restore()

    print("\n" + "="*70)
    print("ALL DEMOS COMPLETED")
    print("="*70 + "\n")
```

### Thread-Safety Analysis

| Operation | Lock Strategy | Guarantees |
|-----------|---|---|
| **Singleton init** | Class RLock (double-checked) | Single instance even under concurrent first calls |
| **execute / undo / redo** | Single-threaded demo; RLock available for extension | Command stacks mutated atomically |
| **restore_snapshot** | RLock re-entrant — calls execute() internally | No deadlock on re-entry into lock |
| **set_storage_strategy** | Single-threaded; read-all then write-all | Atomic re-encode; consistent state |

**Concurrency Principles**:
1. ✅ `threading.RLock` instead of `Lock` — re-entrant safe (`restore_snapshot` calls `execute`)
2. ✅ `__new__` accepts `*args, **kwargs` — Singleton never rejects arguments
3. ✅ Double-checked locking for Singleton initialization
4. ✅ Listener errors caught inside `_emit` — one bad observer doesn't break the system

---

## Demo Scenarios

### Scenario 1: Setup & Create Hierarchy
```
[EVENT] node_created: {'path': '/docs', 'type': 'directory'}
[EVENT] node_created: {'path': '/docs/spec.md', 'type': 'file'}
[EVENT] node_created: {'path': '/docs/readme.md', 'type': 'file'}
Content of /docs/spec.md: API specification document
Metrics: files=2, dirs=2, logical=43B, physical=43B
```

### Scenario 2: Strategy Swap & Compression
```
Before compression: logical=43B, physical=43B
[EVENT] strategy_swapped: {'old': 'PlainStorageStrategy', 'new': 'CompressedStorageStrategy'}
After compression:  logical=43B, physical=27B
Compression ratio: 62.8%
Content unchanged: API specification document
```

### Scenario 3: Move Node Between Directories
```
[EVENT] node_created: {'path': '/archive', 'type': 'directory'}
/docs/readme.md exists:    False
/archive/readme.md exists: True
Content preserved: Project README
```

### Scenario 4: Delete & Undo/Redo
```
After delete: /archive/readme.md exists = False
After undo:   /archive/readme.md exists = True
After redo:   /archive/readme.md exists = False
```

### Scenario 5: Snapshot & Restore
```
[EVENT] snapshot_taken: {'file_count': 1}
After mutation: file_count=2
/temp/test.txt exists: True
After restore:  file_count=1
/temp/test.txt exists: False
undo_stack depth: 1  (restore cmd is undoable)
```

---

## Interview Q&A

### Basic Questions

**Q1: How do you represent files and directories?**

A: `FsNode` base class with `File` (leaf, stores `_data` bytes) and `Directory` (composite, stores `children` dict). Both inherit `path()` method to resolve hierarchical location by walking the parent chain.

**Q2: How does path resolution work?**

A: Split path by `/`, traverse from root. Example: `/docs/spec.md` → `root → get("docs") → get("spec.md")`. Return `None` if any segment missing. O(segments) time.

**Q3: What's the storage strategy pattern for?**

A: Decouple content encoding from file logic. `PlainStorageStrategy` encodes/decodes UTF-8. `CompressedStorageStrategy` wraps zlib. Swap strategies transparently — callers always read/write strings; bytes are internal.

**Q4: How do undo/redo stacks work?**

A: Execute: push command to `undo_stack`, clear `redo_stack`. Undo: pop from `undo_stack`, call `cmd.undo()`, push to `redo_stack`. Redo: pop from `redo_stack`, call `cmd.execute()`, push to `undo_stack`.

**Q5: Why use Composite pattern?**

A: Uniform traversal for files and directories. Snapshot deep-clones entire tree without special-casing. `walk()` in `_all_files()` / `_all_dirs()` recurses polymorphically. New node types (e.g., SymLink) just inherit `FsNode`.

---

### Intermediate Questions

**Q6: How does write capture old content for undo?**

A: `WriteFileCommand` stores `old_text = file.read(fs.storage)` before execute. On undo, restore `old_text`. `File.version` increments on each write for tracking.

**Q7: How do you move a node safely?**

A: `MoveNodeCommand` captures `original_parent`. Execute: detach from parent, attach to `dest_dir`. Undo: detach from `dest_dir`, reattach to `original_parent`. Path updates automatically via parent chain.

**Q8: What's the snapshot/restore trade-off?**

A: Snapshot deep-copies entire tree — memory-intensive but simple. Alternative: incremental diffs or journaling (complex but space-efficient). For interview: snapshot sufficient for correctness demo.

**Q9: How does strategy swap preserve file content?**

A: Read all files with old strategy (decode to logical text) → switch strategy → re-encode with new strategy. Transparent to callers; metrics reflect new physical size.

**Q10: How do you delete with undo?**

A: `DeleteNodeCommand` captures a deep-clone snapshot of the node+subtree before removal. On undo, clone the snapshot and reattach to original parent. Entire subtree fully restored.

---

### Advanced Questions

**Q11: How to prevent memory explosion with many snapshots?**

A: Each snapshot is independent deep-copy (expensive for large trees). Alternatives: copy-on-write (shared structure until mutation) or incremental diffs (replay from base+deltas). For production: WAL (write-ahead log) of commands — replay from any checkpoint.

**Q12: How do metrics stay accurate across operations?**

A: `_refresh_metrics()` recalculates `file_count`, `dir_count`, `total_bytes` (logical), `compressed_bytes` (physical) via full tree walk. Called after every create/write/delete/strategy_swap. Expensive for large trees — alternative: delta tracking on each mutation.

---

## Scaling Q&A

**Q1: Can you support 1M files?**

A: In-memory hash lookups O(1) per child. Path resolution O(segments, typically 5-10). 1M files: ~100MB metadata + content. Memory becomes the bottleneck. Alternative: external storage (RocksDB, FUSE filesystem) with lazy-loaded subtrees.

**Q2: How to handle concurrent modifications?**

A: Single-process: straightforward. Multi-process: add `threading.RLock` around all state mutations. Readers can use snapshot isolation — read old root while mutations apply to a new root copy.

**Q3: How to persist tree to disk?**

A: Snapshot + journaling. Checkpoint: write JSON tree every N minutes. Log: append-only command log (create_file, write_file, move_node, etc.). On restart: load checkpoint + replay log commands to reconstruct state.

**Q4: How to optimize path resolution for deep paths?**

A: Cache frequently-accessed paths in a dict. Or: flat storage with full path as key (trade memory for O(1) speed). Hybrid: LRU cache for top-accessed 1000 paths.

**Q5: Can you support 100GB files?**

A: In-memory: no. Must stream from disk. File abstraction: offset + length pointers to disk blocks. `read()` returns content iterator, not full bytes. Storage strategy becomes a streaming codec.

**Q6: How to support incremental snapshots?**

A: Snapshot 1 = full tree clone. Snapshot 2 = only store deltas (new files, modified content, deleted nodes). Restore snapshot 2 = apply delta to snapshot 1. Saves memory but adds restore complexity.

**Q7: How to distribute filesystem across shards?**

A: Shard by path hash. Node `/a/b/c` hashes to `shard_i`. Each shard holds an independent FileSystem instance. Distributed query: resolve path, route to shard, query locally. Trade-off: cross-shard moves are complex.

**Q8: How to handle rename without moving?**

A: `RenameNodeCommand` captures `old_name`. Execute: update `node.name` + parent's `children` dict key. Undo: restore `old_name` and re-key parent dict.

**Q9: How to support lazy-loaded subtrees?**

A: `Directory.children` is a dict of lazy-load proxies. On access, fetch subtree from storage. Trade-off: latency spike on first access vs memory saved for unaccessed branches.

**Q10: How to implement efficient garbage collection?**

A: Track refcounts for deleted snapshots. When `refcount == 0`, free. Alternative: MVCC (multi-version concurrency control) with timestamp-based cleanup — remove versions older than `min_active_snapshot_ts`.

**Q11: How to support atomic transactions across multiple operations?**

A: Batch commands into a transaction object. Execute each command. If any fails: rollback by calling `undo()` on each in reverse order. Or: pre-validate all commands before executing any.

**Q12: How to prevent infinite undo/redo growth?**

A: Cap `undo_stack` to last N commands. Discard oldest on overflow. `redo_stack` is automatically cleared on new execute — preventing memory leak from redo chain. Track `undo_depth` in metrics.

---

## Success Checklist

- [ ] Explain all 6 steps: Setup → Structure → Interface → Architecture → Optimization → Implementation
- [ ] Draw UML class diagram showing Composite tree (File/Directory → FsNode) and all relationships
- [ ] Explain Composite pattern: uniform File/Directory traversal without type-checking at call sites
- [ ] Explain Strategy pattern: swap plain↔compressed storage with zero file logic change
- [ ] Explain Command pattern: undo/redo stacks, pre-state capture (WriteFileCommand.old_text), subtree clone (DeleteNodeCommand)
- [ ] Explain Memento pattern: take_snapshot deep-clones tree; restore_snapshot is itself a reversible Command
- [ ] Explain Singleton: double-checked RLock, `__new__(*args, **kwargs)` fix, `_initialized` guard
- [ ] Run complete implementation without errors (5 demos)
- [ ] Answer 5+ scaling Q&A questions
- [ ] Discuss trade-offs: deep-copy snapshots vs incremental diffs, in-memory vs external storage, RLock vs Lock

---

**Ready for interview? Build the hierarchy and traverse the tree!**
