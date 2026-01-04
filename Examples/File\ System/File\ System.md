# File System — 75-Minute Interview Guide

## Quick Start

**What is it?** In-memory hierarchical file system supporting directories and files with CRUD operations, pluggable storage strategies (plain/compressed), reversible commands (undo/redo), snapshot/restore, and event observability.

**Key Classes:**
- `FileSystem` (Singleton): Centralized coordinator
- `FsNode` (Abstract): Base for File and Directory
- `File`: Leaf node with versioned content
- `Directory`: Composite container for files/subdirectories
- `StorageStrategy` (ABC): Pluggable encode/decode (plain vs compressed)
- `Command`: Reversible operations (create, write, move, delete)
- `Snapshot`: Memento for state recovery

**Core Flows:**
1. **Create File/Directory**: Resolve parent path → Add node → Emit event
2. **Write Content**: Fetch file → Apply storage strategy → Increment version → Emit event
3. **Move Node**: Resolve source → Detach from parent → Attach to destination → Emit event
4. **Delete Node**: Capture snapshot of subtree → Remove from parent → Enable undo
5. **Snapshot/Restore**: Deep-clone entire tree → Restore replaces root → Reversible via command

**5 Design Patterns:**
- **Composite**: Uniform File/Directory traversal and operations
- **Strategy**: Pluggable storage (plain vs compressed) independent of file logic
- **Command**: Reversible CRUD with undo/redo stacks
- **Observer**: Events (created, written, moved, deleted, strategy_swapped) for instrumentation
- **Memento**: Snapshot captures entire tree state for restore
- **Singleton**: One FileSystem instance manages all state

---

## System Overview

In-memory hierarchical file system for directories and files with content transformation, reversible operations, and lifecycle observability.

### Requirements

**Functional:**
- Create/read/write/delete files and directories
- Hierarchical path resolution ("/dir/sub/file.txt")
- Move nodes between directories
- Undo/redo operations (redo cleared after new execute)
- Pluggable storage strategies (plain, compressed, extensible)
- Snapshot entire tree state and restore
- Emit events for lifecycle tracking
- Track file versions and sizes

**Non-Functional:**
- O(path_segments) path resolution
- O(1) file content access
- Extensible strategy pattern for future encryption/permissions
- Observable via event listeners
- Memory-efficient when using compression

**Constraints:**
- Single-process, in-memory only (no persistence by default)
- Deep copy acceptable (small dataset assumption)
- Strategy swap reencodes all files transparently
- Snapshot restore is reversible command (enable undo of restore)

---

## Architecture Diagram (ASCII UML)

```
┌──────────────────────────────────────┐
│ FileSystem (Singleton)               │
│ - root: Directory                    │
│ - storage: StorageStrategy           │
│ - undo_stack: [Command]              │
│ - redo_stack: [Command]              │
│ - listeners: [Callable]              │
│ + execute(cmd), undo(), redo()       │
│ + take_snapshot(), restore_snapshot()│
│ + set_storage_strategy(s)            │
└────────────┬──────────────────────────┘
             │
             │ manages
             ▼
        ┌─────────────┐
        │ FsNode(ABC) │
        └──────┬──────┘
               │
       ┌───────┴────────┐
       ▼                ▼
   ┌────────┐      ┌───────────────┐
   │  File  │      │  Directory    │
   ├────────┤      ├───────────────┤
   │ _data  │      │ children:     │
   │version │      │ {name:Node}   │
   │        │      │               │
   │read()  │      │add(node)      │
   │write() │      │remove(name)   │
   └────────┘      │get(name)      │
                   └───────────────┘
             │
             ▼
       ┌──────────────────────┐
       │ StorageStrategy(ABC) │
       ├──────────────────────┤
       │ + encode(str)->bytes │
       │ + decode(bytes)->str │
       │ + name()->str        │
       └──────┬───────┬───────┘
              │       │
       ┌──────▼──┐  ┌─▼──────────────┐
       │ Plain   │  │ Compressed     │
       │Strategy │  │ Strategy(zlib) │
       └─────────┘  └────────────────┘
             │
             ▼
       ┌──────────────────────┐
       │ Command(ABC)         │
       ├──────────────────────┤
       │ + execute(fs)        │
       │ + undo(fs)           │
       │ + describe()->str    │
       └──────┬───┬───┬───────┘
              │   │   │
    ┌─────────┤   │   ├──────────────┐
    │         │   │   │              │
    ▼         ▼   ▼   ▼              ▼
CreateFile WriteFile Move Delete RestoreSnapshot
Command    Command    Node   Node  Command
           Command    Cmd    Cmd

Lifecycle:
ROOT (/)
  ├── File(name, _data, version)
  └── Directory(name, children)
         │
         ├── File(name, _data, version)
         └── Directory(name, children)
            
COMMAND FLOW:
RECORD → STRATEGY_ENCODE → EXECUTE → PUSH_UNDO → CLEAR_REDO → EMIT_EVENT
                                       ↓
                                  [UNDO]→REDO_STACK
                                       ↓
                                  [REDO]→UNDO_STACK

SNAPSHOT:
take_snapshot() → deep_clone(root) → Snapshot(root_clone)
restore_snapshot(snap) → execute(RestoreSnapshotCommand(old,new))
```

---

## Interview Q&A (12 Questions)

### Basic Level

**Q1: How do you represent files and directories?**
A: FsNode base class with File (leaf, stores _data bytes) and Directory (composite, stores children dict). File/Directory inherit path() method to resolve hierarchical location.

**Q2: How do path resolution work?**
A: Split path by '/', traverse from root. Example: "/docs/spec.md" → root→get("docs")→get("spec.md"). Return None if path invalid. O(segments).

**Q3: What's the storage strategy pattern for?**
A: Decouple content encoding from file logic. PlainStorageStrategy encodes/decodes UTF-8. CompressedStorageStrategy wraps zlib. Swap strategies transparently without rewriting file logic.

**Q4: How do undo/redo stacks work?**
A: Execute: push command to undo_stack, clear redo_stack. Undo: pop from undo_stack, call cmd.undo(), push to redo_stack. Redo: pop from redo_stack, call cmd.execute(), push to undo_stack.

**Q5: Why use Composite pattern?**
A: Uniform traversal for files and directories. Snapshot deep-clones entire tree without special-casing. Enables extensibility (new node types inherit FsNode).

### Intermediate Level

**Q6: How does write capture old content for undo?**
A: WriteFileCommand stores old_text before execute. On undo, restore old_text. File.version increments on each write for tracking.

**Q7: How do you move a node safely?**
A: MoveNodeCommand captures original_parent. Execute: detach from parent, attach to dest_dir. Undo: detach from dest_dir, reattach to original_parent. Path updates automatically.

**Q8: What's the snapshot/restore trade-off?**
A: Snapshot deep-copies entire tree (memory-intensive but simple). Alternative: incremental diffs or journaling (complex but space-efficient). For interview: snapshot sufficient for correctness demo.

**Q9: How does strategy swap preserve file content?**
A: Read all files with old strategy → decode to logical text. Switch strategy → re-encode with new strategy. Transparent to callers, metrics reflect new physical size.

**Q10: How do you delete with undo?**
A: DeleteNodeCommand captures snapshot of node+subtree before removal. On undo, deep-clone snapshot and reattach to original parent. Subtree fully restored.

### Advanced Level

**Q11: How to prevent memory explosion with many snapshots?**
A: Each snapshot is independent deep-copy (expensive for large trees). Alternative: copy-on-write (shared structure until mutation), or incremental diffs (replay from base+deltas). For production: journal WAL (write-ahead log) of commands.

**Q12: How do metrics stay accurate across operations?**
A: _refresh_metrics() recalculates file_count, dir_count, total_bytes (logical), compressed_bytes (physical) via tree walk. Called after create/write/delete/strategy_swap. Expensive for large trees; alternative: delta tracking.

---

## Scaling Q&A (12 Questions)

**Q1: Can you support 1M files?**
A: In-memory hash lookups O(1) per child. Path resolution O(segments, typically 5-10). Total traversal ~10μs. 1M files: 100MB metadata + content. Memory bottleneck. Alternative: external storage (RocksDB, FUSE filesystem).

**Q2: How to handle concurrent modifications?**
A: Single-process: simple. Multi-process: add threading.Lock around all state mutations. Readers can be lock-free with snapshot isolation (read old root while mutations on new root).

**Q3: How to persist tree to disk?**
A: Snapshot + journaling. Checkpoint: write JSON tree every N minutes. Log: append-only command log (create_file, write_file, move_node). On restart: load checkpoint + replay log.

**Q4: How to optimize path resolution for deep paths?**
A: Cache frequently-accessed paths in dict. Or: flat storage with full path as key (trade memory for speed). Hybrid: LRU cache for top-accessed 1000 paths.

**Q5: Can you support 100GB files?**
A: In-memory: no. Must stream from disk. File abstraction: offset + length pointers to disk blocks. Read returns content iterator, not full bytes. Storage strategy becomes streaming codec.

**Q6: How to support incremental snapshots?**
A: Snapshot 1: full tree clone. Snapshot 2: only store deltas (new files, modified content, deleted nodes). Restore 2: apply delta to snapshot 1. Save memory but add complexity.

**Q7: How to distribute filesystem across shards?**
A: Shard by path hash. Node /a/b/c hashes to shard_i. Each shard holds independent FileSystem instance. Distributed query: resolve path, route to shard, query locally. Trade: cross-shard moves complex.

**Q8: How to handle rename without moving?**
A: Rename is file.name change + parent update. Command: RenameNodeCommand captures old_name. Execute: update name + parent's children dict key. Undo: restore old_name.

**Q9: How to support lazy-loaded subtrees?**
A: Directory.children is dict of lazy-load proxies. On access, fetch subtree from storage. Storage returns hydrated Directory. Trade: latency spike on first access, memory saved.

**Q10: How to implement efficient garbage collection?**
A: Track refcounts for deleted snapshots. When refcount=0, free. Alternative: MVCC (multi-version concurrency control) with timestamp-based cleanup. Remove versions older than min_active_snapshot_ts.

**Q11: How to support atomic transactions across multiple operations?**
A: Batch commands into transaction. Execute each command. If any fails: rollback (undo each in reverse order). Or: pre-validate transaction before executing any command.

**Q12: How to prevent infinite undo/redo growth?**
A: Cap undo_stack to last N commands. Discard oldest. Or: cleanup old redo_stack entries after new execute (prevents memory leak from redo chain). Metrics track undo_depth.

---

## Demo Scenarios (5 Examples)

### Demo 1: Setup & Create Hierarchy
```
- Create /docs directory
- Create /docs/spec.md file
- Write "API specification" to spec.md
- Create /docs/readme.md file
- Verify metrics: 2 files, 2 directories
```

### Demo 2: Strategy Swap & Compression
```
- Write 1KB text to spec.md with PlainStorageStrategy
- Observe: physical_size = 1KB
- Swap to CompressedStorageStrategy
- Observe: physical_size ≈ 150 bytes (zlib)
- Read file: still returns "API specification" (transparent)
```

### Demo 3: Move Node Between Directories
```
- Create /docs/archive directory
- Move /docs/spec.md to /docs/archive/spec.md
- Verify: /docs/spec.md doesn't exist
- Verify: /docs/archive/spec.md exists with same content
```

### Demo 4: Delete & Undo/Redo
```
- Delete /docs/archive/spec.md
- Verify: file gone
- Undo: file restored to /docs/archive/spec.md
- Redo: file deleted again
```

### Demo 5: Snapshot & Restore
```
- Take snapshot of entire tree
- Create /temp directory and /temp/test.txt
- Write "temporary" to test.txt
- Restore snapshot
- Verify: /temp gone, tree reverted
- Check undo_stack: restore command can be undone
```

---

## Complete Implementation

```python
"""
🗂️ File System - Interview Implementation
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
        return f"MoveNode {self.src_path} → {self.dest_dir_path}"

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
    """Centralized file system coordinator"""
    
    _instance: Optional[FileSystem] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> FileSystem:
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
        print("🗂️ FileSystem initialized")
    
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
    
    fs = FileSystem.instance()
    fs.register(simple_listener)
    
    fs.execute(CreateDirectoryCommand("/docs"))
    fs.execute(CreateFileCommand("/docs/spec.md"))
    fs.execute(WriteFileCommand("/docs/spec.md", "API specification document"))
    fs.execute(CreateFileCommand("/docs/readme.md"))
    fs.execute(WriteFileCommand("/docs/readme.md", "Project README"))
    
    print(f"\n  Content of /docs/spec.md: {fs._get_file('/docs/spec.md').read(fs.storage)}")
    print(f"  Metrics: {fs.get_metrics()}")

def demo_2_strategy_swap() -> None:
    print_section("DEMO 2: STORAGE STRATEGY SWAP")
    
    fs = FileSystem.instance()
    
    before = fs.get_metrics()
    print(f"  Before compression: logical={before['total_bytes']}, physical={before['compressed_bytes']}")
    
    fs.set_storage_strategy(CompressedStorageStrategy())
    
    after = fs.get_metrics()
    print(f"  After compression:  logical={after['total_bytes']}, physical={after['compressed_bytes']}")
    print(f"  Compression ratio: {100 * after['compressed_bytes'] / after['total_bytes']:.1f}%")

def demo_3_move_node() -> None:
    print_section("DEMO 3: MOVE NODE BETWEEN DIRECTORIES")
    
    fs = FileSystem.instance()
    
    fs.execute(CreateDirectoryCommand("/archive"))
    fs.execute(MoveNodeCommand("/docs/readme.md", "/archive"))
    
    print(f"  /docs/readme.md exists: {fs.exists('/docs/readme.md')}")
    print(f"  /archive/readme.md exists: {fs.exists('/archive/readme.md')}")
    print(f"  Content preserved: {fs._get_file('/archive/readme.md').read(fs.storage)}")

def demo_4_delete_undo_redo() -> None:
    print_section("DEMO 4: DELETE & UNDO/REDO")
    
    fs = FileSystem.instance()
    
    fs.execute(DeleteNodeCommand("/archive/readme.md"))
    print(f"  After delete: /archive/readme.md exists = {fs.exists('/archive/readme.md')}")
    
    fs.undo()
    print(f"  After undo:   /archive/readme.md exists = {fs.exists('/archive/readme.md')}")
    
    fs.redo()
    print(f"  After redo:   /archive/readme.md exists = {fs.exists('/archive/readme.md')}")

def demo_5_snapshot_restore() -> None:
    print_section("DEMO 5: SNAPSHOT & RESTORE")
    
    fs = FileSystem.instance()
    
    snap = fs.take_snapshot()
    before_metrics = fs.get_metrics()
    print(f"  Snapshot taken: file_count={before_metrics['file_count']}")
    
    fs.execute(CreateFileCommand("/temp/test.txt"))
    fs.execute(WriteFileCommand("/temp/test.txt", "Temporary data"))
    
    mutated_metrics = fs.get_metrics()
    print(f"  After mutation: file_count={mutated_metrics['file_count']}")
    print(f"  /temp/test.txt exists: {fs.exists('/temp/test.txt')}")
    
    fs.restore_snapshot(snap)
    restored_metrics = fs.get_metrics()
    print(f"  After restore:  file_count={restored_metrics['file_count']}")
    print(f"  /temp/test.txt exists: {fs.exists('/temp/test.txt')}")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🗂️ FILE SYSTEM - 5 DEMO SCENARIOS")
    print("="*70)
    
    demo_1_setup()
    demo_2_strategy_swap()
    demo_3_move_node()
    demo_4_delete_undo_redo()
    demo_5_snapshot_restore()
    
    print("\n" + "="*70)
    print("✅ ALL DEMOS COMPLETED")
    print("="*70 + "\n")
```

---

## Design Patterns

| Pattern | Usage | Benefit |
|---------|-------|---------|
| **Composite** | File/Directory hierarchy | Uniform traversal, extensible node types |
| **Strategy** | Storage encode/decode | Transparent content transformation (plain vs compressed) |
| **Command** | Reversible operations | Undo/redo with consistent semantics, extensible |
| **Observer** | Event listeners | Lifecycle observability, decoupled instrumentation |
| **Memento** | Snapshot/restore | Fast global rollback, state recovery |
| **Singleton** | FileSystem instance | Centralized state, no duplication |

---

## Summary

✅ **Hierarchical structure** with paths, directories, and files
✅ **CRUD operations** (create, read, write, delete)
✅ **Reversible commands** with undo/redo stacks
✅ **Pluggable storage** (plain, compressed, extensible)
✅ **Snapshot/restore** for state recovery
✅ **Event emission** for lifecycle tracking
✅ **Metrics tracking** (file count, sizes, compression ratios)
✅ **Composite pattern** for uniform traversal
✅ **Strategy pattern** for content transformation
✅ **Extensible design** (new strategies, commands, node types)

**Key Takeaway**: File system demonstrates composite hierarchy (uniform File/Directory handling), strategy pattern (pluggable storage), command pattern (reversible operations with undo/redo), and observability via events. Focus: separation of concerns, extensibility narrative, and scaling trade-offs (in-memory vs external storage, deep copy snapshots vs incremental diffs).
