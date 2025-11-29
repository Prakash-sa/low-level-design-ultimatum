# 📝 Text Editor with Undo & Redo – Quick Start (5‑Minute Reference)

## ⏱️ Timeline
| Time | Focus | Output |
|------|-------|--------|
| 0–5  | Requirements | Define supported commands & limits |
| 5–15 | Architecture | Command interface, stacks, events |
| 15–35 | Core Entities | Document + command classes + session |
| 35–55 | Logic | execute, undo, redo, strategy swap |
| 55–70 | Integration | Demos + snapshot utility |
| 70–75 | Q&A | Explain patterns & trade-offs |

## 🧱 Core Entities Cheat Sheet
Document(text, version)
EditorSession (Singleton) – undo_stack[], redo_stack[], state, strategies
Command (execute(), undo()) base
InsertTextCommand(pos, text)
DeleteRangeCommand(start, length, removed_text)
ReplaceRangeCommand(start, length, new_text, old_text)

Enums: EditorState(IDLE, EDITING, UNDOING, REDOING)

## 🛠 Patterns Talking Points
Command: Reversible actions unify undo/redo logic.
Singleton: Single editing context for simplicity.
Observer: Events for UI/analytics decoupled from logic.
Strategy: Pluggable formatting/storage (e.g., trim whitespace).
Factory: Simplified creation of commands from parameters.
State: Prevent nested undo/redo race; reflect current operation phase.

## 🎯 Demo Order
1. Setup session & doc
2. Insert & Delete + undo/redo
3. Multi undo chain then redo all
4. Strategy swap (trim trailing spaces) reformat document
5. Snapshot & restore (optional memento)

Run:
```bash
python3 INTERVIEW_COMPACT.py
```

## ✅ Success Checklist
- [ ] Redo cleared after new command execution
- [ ] All undo operations restore previous text correctly
- [ ] Events printed for execute/undo/redo
- [ ] Strategy modifies document without breaking stacks
- [ ] Snapshot restore works
- [ ] Can explain Command undo symmetry

## 💬 Quick Answers
Why Command? → Encapsulates reversible change; consistent undo/redo.
Why clear redo on new exec? → Prevent invalid redo chain referencing outdated state.
How handle large documents? → Use diff segments / rope data structure (mention future).
What about collaboration? → Event bus + OT / CRDT (out of current scope).
Strategy use? → Swap formatting or persistence mechanisms.

## 🆘 If Behind
<20m: Implement Document + Insert/Delete + undo.
20–50m: Add redo + replace + events.
>50m: Add strategy + snapshot; narrate potential advanced structures.

Keep operations atomic; emphasize invariants & extensibility.
