# 📁 File System – 75 Minute Deep Dive

## 1. Problem Framing (0–5)
Design an in-memory hierarchical file system with directories and files, supporting CRUD, move, delete, pluggable content storage (plain/compressed), undo/redo via commands, snapshot/restore, and events.

Must:
- Create/read/write/delete files
- Create directories
- Move nodes
- Undo/redo operations
- Strategy-based content encoding
- Snapshot restore

Stretch:
- Compression strategy
- Metrics
- Time/version tracking

## 2. Requirements & Constraints (5–10)
Functional:
- Path resolution ("/dir/sub/file.txt")
- Isolation of storage transformation
- Consistent undo/redo semantics (redo cleared after new exec)

Non-Functional:
- Extensible strategies (encryption, compression)
- Observability via events
- Simplicity: O(segments) path traversal

Assumptions:
- Single thread, no concurrent modification
- Small dataset; deep copying acceptable

## 3. Domain Model (10–18)
Entities:
- File(content_bytes, version, logical_size)
- Directory(children: name -> FsNode)
- FileSystem(root, storage_strategy, undo_stack, redo_stack)
- StorageStrategy(encode, decode)
- Commands(execute, undo)
- Snapshot(root_clone)

Relationships:
- Directory composes FsNodes.
- FileSystem mediates path operations and command execution.
- Strategy transforms file content at boundaries.

## 4. Patterns (18–26)
Composite: Hierarchy of directories/files.
Strategy: Content transformation isolated (compression now; encryption later).
Command: Reversible operations unify undo/redo logic.
Observer: Event emission for instrumentation.
Memento: Snapshot deep copy for restore.
Singleton: Single FileSystem instance.

## 5. Lifecycle (26–32)
CREATE_FILE → WRITE → MOVE/DELETE → UNDO/REDO → SNAPSHOT → MUTATE → RESTORE.

Invariants:
1. Undo reverses exactly last executed command.
2. Redo stack cleared upon new execute.
3. Snapshot restore pushes a command (optional) to allow undo (we include RestoreSnapshotCommand for consistency).
4. File version increments on each content write.

## 6. Storage Strategy (32–38)
PlainStorageStrategy:
- encode(str)->bytes
- decode(bytes)->str
CompressedStorageStrategy(zlib):
- encode compresses; decode inflates
Metrics track logical vs physical size.

## 7. Commands (38–48)
CreateFileCommand(path): undo deletes created file.
WriteFileCommand(path,new_text): captures old content for undo.
MoveNodeCommand(src,dest_dir): undo restores to original parent.
DeleteNodeCommand(path): captures subtree for restoration.
RestoreSnapshotCommand(old_root,new_root): undo reverts to old_root.

Undo/Redo Stacks:
- execute: push cmd -> clear redo -> emit event.
- undo: pop undo -> cmd.undo() -> push to redo.
- redo: pop redo -> cmd.execute() -> push to undo.

## 8. Snapshot (48–55)
Deep clone entire root tree.
Restore replaces root with snapshot clone.
Trade-off: memory cost vs implementation simplicity.
Future: incremental (copy-on-write) or journaling for diff replay.

## 9. Events (55–60)
Events:
- node_created, node_deleted, node_moved, file_written, strategy_swapped, command_executed, command_undone, snapshot_taken, snapshot_restored, metrics_updated
Payload includes path(s) and sizes.

## 10. Metrics (60–63)
- file_count
- dir_count
- total_bytes (logical sum of decoded lengths)
- compressed_bytes (stored bytes length)
- command_executed / command_undone
Update recalculated after structural/content changes.

## 11. Demo Scenarios (63–68)
1. Setup: directories + files, basic write.
2. Write additional content then swap to compression.
3. Move file between directories.
4. Delete file, undo, redo.
5. Snapshot, mutate, restore.

## 12. Trade-offs (68–72)
Compression vs speed: space savings vs CPU overhead.
Snapshot deep copy vs incremental diff: simplicity vs memory efficiency.
Command-based undo vs journaling: targeted reversal vs replay sequence.
Single FS instance vs multi-instance isolation: simplicity vs testing flexibility.

## 13. Extensions (72–75)
- Encryption strategy
- Access control strategy (permissions)
- Journaling log for crash recovery
- Concurrent locking mechanism
- Incremental snapshot diffs

## Summary
Modular file system: composite hierarchy, reversible operations, pluggable storage, rich event instrumentation, and straightforward snapshot recovery — ready narrative for scaling to real OS-level concerns.
