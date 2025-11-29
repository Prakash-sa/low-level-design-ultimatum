# 📝 Text Editor with Undo & Redo – 75 Minute Deep Dive

## 1. Problem Framing (Minutes 0–5)
Design a lightweight single-user text editor supporting insert, delete, replace operations with robust undo/redo. Preserve a clean separation between command logic, document model, session control, and pluggable behaviors.

Must Have:
- Insert, delete, replace operations
- Unlimited undo/redo (bounded by memory)
- Redo invalidated on new command
- Event notifications
- Strategy hook for formatting/persistence

Stretch:
- Snapshot (Memento) restore
- Composite command batching
- Validation (e.g., bounds)
- History inspection

## 2. Core Requirements & Constraints (Minutes 5–10)
Functional:
- O(1) push/pop for undo/redo stacks
- Each command fully reversible
- Document version increments on each confirmed change

Non-Functional:
- Extensible (add new commands with minimal coupling)
- Observability via events
- Swappable strategies without editing core logic

Assumptions:
- In-memory text string (acceptable for small size)
- Single-threaded (no concurrency concerns)

## 3. Domain Model (Minutes 10–18)
Entities:
- Document: holds text, version
- EditorSession (Singleton): orchestrates command execution, holds stacks
- Command: base interface (execute, undo)
- ConcreteCommands: InsertText, DeleteRange, ReplaceRange
- Strategy: FormattingStrategy / PersistenceStrategy (placeholder)
- Snapshot: frozen copy of Document state

Relationships:
- Session → Document (composition)
- Session → Commands (lifecycle management)
- Commands → Document (mutation)

## 4. Key Design Patterns (Minutes 18–26)
Command: Encapsulate reversible edits; unify execute/undo.
Singleton: Single session prevents competing states.
Observer: Publish events (on_execute, on_undo, on_redo, on_strategy_swap).
Strategy: Swap formatting (e.g., trimming, normalization) without altering command code.
Memento (optional): Snapshot for version rollback.
State: Track whether currently undoing/redoing to prevent nested side-effects.

## 5. Undo/Redo Mechanics (Minutes 26–35)
Invariant 1: After executing a new command, redo stack is cleared.
Invariant 2: Undo pushes the reversed command onto redo stack only after successful undo.
Invariant 3: Commands are pure in their undo effect (no side mutation besides text + version).
Invariant 4: Document version strictly increases on execute, and also increases on undo/redo (alternatively could decrement on undo—choose monotonic for auditing).

Pseudo-flow:
execute(cmd):
  cmd.execute(doc)
  undo_stack.push(cmd)
  redo_stack.clear()
  version++
undo():
  if empty return
  cmd = undo_stack.pop()
  cmd.undo(doc)
  redo_stack.push(cmd)
  version++
redo():
  if empty return
  cmd = redo_stack.pop()
  cmd.execute(doc) (idempotent orientation)
  undo_stack.push(cmd)
  version++

## 6. Command Design (Minutes 35–45)
InsertTextCommand:
- Stores position, text
- Undo: remove inserted length
DeleteRangeCommand:
- Stores start, length, removed_text (captured on execute)
- Undo: reinsert removed_text
ReplaceRangeCommand:
- Stores start, length, new_text, old_text
- Execute: substitute
- Undo: restore old_text

Validation: ensure indices 0 <= pos <= len(text), ranges within bounds.

## 7. Strategy Extension (Minutes 45–52)
FormattingStrategy:
- apply(text) -> transformed_text
Use cases: trim trailing spaces, normalize line endings, markdown auto-fix.
Invocation: manual trigger (e.g., session.apply_formatting()).
Effect: treat formatting change as a synthetic ReplaceRangeCommand or a dedicated FormattingCommand to keep undo semantics consistent.

## 8. Observer Events (Minutes 52–58)
Event names:
- command_executed, command_undone, command_redone, formatting_applied, snapshot_taken, snapshot_restored
Listener registration: session.register(listener_func)
Dispatch: session._emit(event_name, payload)

## 9. Snapshot / Memento (Minutes 58–63)
Snapshot = {text, version, timestamp}
Take snapshot: shallow copy of Document.
Restore: replace text with snapshot.text, increment version, push a RestoreSnapshotCommand (optional) to keep history.

## 10. Demo Scenarios (Minutes 63–68)
1. Setup + initial insert
2. Insert + delete chain, undo last two
3. Redo all undone operations
4. Apply formatting strategy (trim) as command
5. Snapshot, mutate heavily, restore snapshot

## 11. Trade-offs & Alternatives (Minutes 68–72)
String storage vs Rope: Rope/GapBuffer for large docs
Monotonic version vs reversible version: monotonic simpler for audit
Redo invalidation: necessary to prevent divergent history
Command storage memory growth: cap & truncate (not implemented now)
Composite Commands: batch complex operations with transactional rollback

## 12. Interview Narration Tips (Minutes 72–75)
Lead with Command pattern rationale.
Highlight undo/redo invariants early.
Explain why redo is cleared (non-linear history avoidance).
Show extensibility: add UppercaseSelectionCommand easily.
Discuss scaling path (rope, persistence, CRDT for multi-user).
Close with how formatting strategy integrates without touching existing commands.

## 13. Future Enhancements (Bonus)
- Persistent command log
- Conflict-free replicated data types (CRDT) for collaboration
- Plugin architecture via event system
- Syntax highlighting strategy layer

## Summary
A modular editor: core is command execution with clean undo/redo stacks, enriched by strategies and events, optionally extended by snapshots. Emphasis on invariants and extensibility ensures clean evolution.
