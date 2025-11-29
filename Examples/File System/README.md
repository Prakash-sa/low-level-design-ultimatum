# 📁 In-Memory File System Design

Aligned with Airline Management System structure: clear lifecycle, modular strategies, observer events, reversible commands, snapshots.

---
## 🎯 Goal
Provide a simple in‑process file system supporting hierarchical directories, file CRUD, path resolution, pluggable storage (plain vs compressed), reversible commands (undo/redo), event emission, and snapshots.

---
## 🧱 Core Components
| Component | Responsibility | Patterns |
|-----------|----------------|----------|
| `FsNode` | Base for `File` / `Directory` | Composite |
| `File` | Content, size, version tracking | Composite leaf, State |
| `Directory` | Holds children mapping | Composite composite |
| `FileSystem` | Root management, path operations | Singleton, Facade, Observer |
| `StorageStrategy` | Encode/decode file content | Strategy |
| `Command` | Reversible FS operations | Command, Memento-lite |
| `Snapshot` | Frozen tree state | Memento |
| `Events` | Lifecycle notifications | Observer |

---
## 🔄 Typical Lifecycle
CREATE_FILE → WRITE_CONTENT → READ/UPDATE → (MOVE | DELETE) → (UNDO/REDO) → SNAPSHOT → RESTORE.

---
## 🧠 Patterns
- Composite: Directories contain files or subdirectories; uniform operations.
- Strategy: Storage (plain vs compression) decoupled from file management.
- Command: Reversible operations with undo/redo stacks.
- Observer: Events for create, write, move, delete, strategy swap, snapshot.
- Memento: Snapshot captures whole hierarchy for restore.
- Singleton: One `FileSystem` instance centralizes state.

---
## ⚙ Storage Strategies
1. `PlainStorageStrategy` – direct string storage.
2. `CompressedStorageStrategy` – zlib compress/decompress transparently (simulates space optimization).

---
## 🛡 Commands
- `CreateFileCommand(path)`
- `WriteFileCommand(path, new_content)`
- `MoveNodeCommand(src, dest_dir)`
- `DeleteNodeCommand(path)`
Each implements `execute()` and `undo()`.

---
## 📊 Metrics
- file_count
- dir_count
- total_bytes (logical, uncompressed)
- compressed_bytes (physical when compressed strategy active)
- command_executed
- command_undone

---
## 🧪 Demo Scenarios
1. Setup + create directories/files
2. Write & read plain, then swap to compression
3. Move file between directories
4. Delete + undo/redo
5. Snapshot & restore entire tree

---
## 🗂 Files
- `START_HERE.md` – quick 5‑minute cheat sheet
- `75_MINUTE_GUIDE.md` – structured deep dive
- `INTERVIEW_COMPACT.py` – runnable demo code

Run:
```bash
python3 INTERVIEW_COMPACT.py
```

---
## 💬 Talking Points
- Composite simplifies uniform traversal & snapshot.
- Strategy swap shows transparent content transformation without rewriting file logic.
- Command pattern ensures undo integrity & redo invalidation rules.
- Snapshot trade-offs: deep copy memory vs incremental diff.
- Scaling: would externalize storage & add concurrency control (locks).

---
## 🚀 Future Enhancements
- Permission / ACL strategy
- Journaling + crash recovery
- Concurrent operations (locking layer)
- Lazy loading & caching
- Incremental snapshots (delta)

---
## ✅ Interview Closure
Highlight separation of concerns: structure (Composite), behavior (Strategy), reversibility (Command), observability (Observer), recoverability (Snapshot). Clear path to production-grade features.
