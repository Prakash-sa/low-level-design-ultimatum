# 📁 File System – Quick Start (5‑Minute Reference)

## ⏱️ Timeline
| Time | Focus | Output |
|------|-------|--------|
| 0–5  | Requirements | Hierarchy, CRUD, undo, strategy |
| 5–15 | Architecture | Composite + FS singleton + commands |
| 15–35 | Core Entities | File, Directory, path resolution |
| 35–55 | Commands & Strategy | Create/Write/Move/Delete + compression |
| 55–70 | Snapshot & Demos | Tree capture & restore |
| 70–75 | Q&A | Trade-offs & scaling story |

## 🧱 Entities Cheat Sheet
File(path, content, version)
Directory(path, children)
FileSystem(root, storage_strategy, undo_stack, redo_stack)
StorageStrategy.encode(str)->bytes / decode(bytes)->str
Commands: CreateFile, WriteFile, MoveNode, DeleteNode
Snapshot(root_clone)

## 🛠 Patterns
Composite (File/Directory)
Strategy (Storage transformation)
Command (Reversible operations)
Observer (Events emission)
Memento (Snapshot)
Singleton (FileSystem instance)

## 🎯 Demo Order
1. Create directories/files
2. Write + read + swap compression strategy
3. Move a file
4. Delete file then undo/redo
5. Snapshot + mutate + restore

Run:
```bash
python3 INTERVIEW_COMPACT.py
```

## ✅ Checklist
- [ ] Redo cleared after new execute
- [ ] Storage strategy swap does not corrupt content
- [ ] Snapshot restores previous hierarchy accurately
- [ ] Move updates paths & tree structure
- [ ] Delete undo resurrects file at original path

## 💬 Quick Answers
Why Composite? → Uniform handling of directories/files for traversal & snapshot.
Why Strategy? → Swap compression logic without changing file nodes.
Why Command undo? → Interview-ready reversible operations with consistent invariants.
Why snapshot vs commands? → Fast global rollback; commands only step-wise.
Scaling path? → Persist nodes externally + concurrency control & journaling.

## 🆘 If Behind
<20m: Build File/Directory + FileSystem + create/write.
20–40m: Add commands + undo/redo stacks.
40–55m: Add compression strategy swap.
>55m: Add snapshot, move, delete, events.

Focus on lifecycle clarity & extensibility narrative.
