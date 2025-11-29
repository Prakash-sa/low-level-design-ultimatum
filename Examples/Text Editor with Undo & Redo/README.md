# 📝 Text Editor with Undo & Redo – 75 Minute Interview Overview

Minimal text editor core featuring command execution, undo/redo stacks, document versioning, and event notifications. Structured to mirror the Airline Management System style (patterns table, timeline, demos, extensibility).

**Scale (Assumed)**: Single user session, document size <1MB, latency negligible.  
**Focus**: Command pattern for operations, robust undo/redo lifecycle, observer-based event emission, extensible strategies for storage & formatting.

---

## Core Domain Entities
| Entity | Purpose | Relationships |
|--------|---------|--------------|
| **Document** | Holds current text & version | Modified by Commands |
| **EditorSession** | Manages stacks & document | Singleton controller |
| **Command** | Encapsulated operation (execute/undo) | Stored on undo stack |
| **Strategy** | Pluggable storage/format logic | Selected by session |
| **Observer** | Receives events (executed, undone, redone) | Subscribed to session |

---

## Design Patterns Implemented
| Pattern | Purpose | Example |
|---------|---------|---------|
| **Singleton** | Single active editor session | `EditorSession.get_instance()` |
| **Command** | Encapsulate reversible operations | `InsertTextCommand`, `DeleteRangeCommand` |
| **Strategy** | Swap storage or formatting rules | `InMemoryStorageStrategy` vs `TrimWhitespaceStrategy` |
| **Observer** | Event notifications | `ConsoleObserver` subscribes to session |
| **State** | Track editing lifecycle | `EditorState` (IDLE→EDITING→UNDOING→REDOING) |
| **Factory** | Centralized command creation | `CommandFactory.create_insert(...)` |

Optional: Memento for snapshot checkpoints, Decorator for command logging.

---

## 75-Minute Timeline
| Time | Phase | What to Code |
|------|-------|--------------|
| 0–5  | Requirements | Clarify operations & constraints |
| 5–15 | Architecture | Entities, stacks, events, patterns |
| 15–35 | Core Entities | Document, Command hierarchy, session |
| 35–55 | Logic | execute, undo, redo, strategy swap, events |
| 55–70 | Integration | Demo scenarios + summary methods |
| 70–75 | Q&A & Trade-offs | Show performance & extensibility points |

---

## Demo Scenarios (5)
1. Setup: Create session & document
2. Insert & Delete: Basic commands + undo/redo
3. Multi-Step Undo Chain: Multiple operations undone/redone sequentially
4. Strategy Swap: Apply a formatting strategy (trim trailing spaces)
5. Snapshot & Restore (Memento Optional): Save checkpoint, modify, restore

Run all demos:
```bash
python3 INTERVIEW_COMPACT.py
```

---

## Interview Checklist
- [ ] Explain Command pattern (execute + undo symmetry)
- [ ] Show undo/redo stack invariants (redo cleared on new exec)
- [ ] Discuss editor state transitions
- [ ] Justify Strategy usage (storage/formatting swap)
- [ ] Emit & interpret events (`command_executed`, `command_undone`, `command_redone`)
- [ ] Mention scaling & persistence (versioning, snapshots)

---

## Key Concepts to Explain
**Command Pattern**: Each editing action packaged with logic to reverse itself; enables consistent undo/redo handling.

**Stacks Invariant**: Undo stack grows with executed commands; redo stack populated only by undone commands; cleared when a new command executes.

**Observer Events**: Decouple UI refresh or analytics from core editing logic.

**Strategy**: Changing storage or formatting rule without touching command logic (e.g., auto-trim, uppercasing variant).

---

## File Roles
| File | Purpose |
|------|---------|
| `README.md` | High-level overview & checklist |
| `START_HERE.md` | Quick timeline & talking points |
| `75_MINUTE_GUIDE.md` | Deep dive (UML, Q&A, edge cases) |
| `INTERVIEW_COMPACT.py` | Working implementation & demos |

---

## Tips for Success
✅ Keep command logic atomic & reversible  
✅ Clear redo stack on any new execution  
✅ Emit events after each stack mutation  
✅ Provide snapshot facility for resilience  
✅ Clarify exclusions (collaboration, diffing engine, syntax highlighting)

---

See `75_MINUTE_GUIDE.md` for full implementation details. Use `START_HERE.md` for rapid recall. Run demos via `python3 INTERVIEW_COMPACT.py`.
