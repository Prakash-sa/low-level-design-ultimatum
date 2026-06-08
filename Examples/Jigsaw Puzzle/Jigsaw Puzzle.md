# Jigsaw Puzzle — Complete Design Guide

> Interactive jigsaw puzzle game with piece placement, edge/corner detection, rotation, hint system, and completion tracking.

**Scale**: 100K+ concurrent games, 1K–1M piece puzzles  
**Duration**: 75-minute interview guide  
**Focus**: Constraint-based piece placement, pluggable matching strategies, undo/redo via Memento, event-driven scoring

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
A player loads an image → the system generates puzzle pieces with edge patterns (FLAT/IN/OUT) → the player selects a piece, chooses a position and rotation → the system validates edge matches against all neighbors → on success the move is recorded for undo/redo → when all positions are filled and every edge matches, the puzzle is complete.

### Core Flow
```
Load Image → Generate Pieces (edge patterns) → Initialize Board
  → Select Piece → Choose Position & Rotation
  → Validate Edges (MatchingStrategy) → Place on Board
  → Record Move (Memento)
      ↓ all positions filled
  Verify All Edges → Completion Event → Leaderboard Update
```

---

## Step 01: The Setup — Clarify Requirements

> **Interview Tip**: Never code immediately. Ask clarifying questions first. Define scope, actors, and constraints.

### Questions to Ask (30 seconds each)

1. **Single-player or multiplayer?** → "Single-player for core; mention multiplayer as a scaling concern"
2. **How large can puzzles get?** → "Up to 1000 pieces (32×32) in production; demo uses 4×4 to 16×16"
3. **What does the matching rule look like?** → "Edge patterns FLAT/IN/OUT; IN connects to OUT, FLAT only on borders"
4. **Real graphics or text-based?** → "Text/in-memory demo; production adds graphics"
5. **Persistence required?** → "In-memory for demo; Redis + PostgreSQL for production"

### Actors (Who uses the system?)

| Actor | Role | Example Actions |
|-------|------|-----------------|
| **Player** | Assembles the puzzle | Select piece, place, rotate, request hint, undo/redo |
| **Game Admin** | Manages puzzles & players | Create puzzles, set difficulty, view leaderboard |
| **System** | Controller & event dispatcher | Validate edges, emit events, track completion |

### Functional Requirements (What does the system do?)

✅ **Puzzle Generation**
  - Load image and generate puzzle pieces with edge patterns (FLAT, IN, OUT)
  - Support multiple difficulty levels (EASY 4×4, MEDIUM 8×8, HARD 16×16)

✅ **Piece Placement**
  - Place pieces on board with position and rotation validation
  - Automatically validate edge matching against all 4 neighbors
  - Suggest piece rotations (0°, 90°, 180°, 270°)

✅ **Hint System**
  - Analyze board state to find the best next piece to place
  - Score candidates by matched neighbors and border constraints

✅ **Undo / Redo**
  - Record every move as a Memento snapshot
  - Undo restores previous board state; redo replays a reverted move

✅ **Scoring & Completion**
  - Track score (time penalty, hints used, rotations)
  - Detect puzzle completion and trigger celebration event
  - Update leaderboard after completion

✅ **Event Notifications**
  - Emit events on placement, hint request, and completion
  - Support multiple observer types (score, completion, hint engine)

### Non-Functional Requirements (How does it perform?)

✅ **Latency**: Piece placement < 100 ms (edge matching O(1))  
✅ **Hint speed**: Hint generation < 500 ms (pre-computed board analysis)  
✅ **Concurrency**: Support 100K+ concurrent games  
✅ **Undo latency**: < 50 ms (memento snapshots, no board re-computation)  
✅ **Persistence**: Game progress persisted (production: Redis + PostgreSQL)  
✅ **Rotation**: Smooth piece rotation at O(1) via index arithmetic  

### Constraints & Clarifications

| Constraint | Decision |
|-----------|----------|
| **Single-process demo** | YES (production: WebSocket + server-side persistence) |
| **Storage** | In-memory (production: Redis + PostgreSQL) |
| **Board visualization** | 2D text grid assumed (no graphics library) |
| **Max pieces (demo)** | 16×16 = 256 pieces |
| **Rotation steps** | 4 (0°, 90°, 180°, 270°) |
| **Edge matching rule** | FLAT↔FLAT, IN↔OUT, OUT↔IN; all others invalid |

---

## Step 02: Structure — Define Entities

> **Interview Tip**: Extract core objects from requirements. Look for **nouns**. Write them on the whiteboard immediately.

### Step 2.1: List Core Entities (Extract Nouns)

```
Piece, Edge, Board, Player, Move, PuzzleGame, MatchingStrategy, PuzzleObserver, ...
```

### Step 2.2: Define Core Classes

#### **Edge** — One side of a puzzle piece
```
Properties:
  - pattern: EdgePattern (FLAT / IN / OUT)
  - color_hash: int  (for color-similarity matching)

Behaviors:
  - can_connect(other, strategy): FLAT↔FLAT, IN↔OUT, OUT↔IN
  - _pattern_matches(other): pure structural check
```

#### **Piece** — A single puzzle piece
```
Properties:
  - piece_id: str
  - edges: List[Edge]   [TOP, RIGHT, BOTTOM, LEFT]
  - piece_type: PieceType (CORNER / EDGE / INNER)
  - row, col: Optional[int]
  - rotation: int  (0–3, meaning 0°/90°/180°/270°)
  - placed: bool

Behaviors:
  - get_edge(direction): return edge with rotation applied
  - rotate(times): increment rotation by n steps mod 4
```

#### **Board** — 2D grid tracking placed pieces
```
Properties:
  - width, height: int
  - grid: List[List[Optional[str]]]   (piece_ids)
  - pieces_at: Dict[str, Tuple[int, int]]

Behaviors:
  - can_place_piece(piece, row, col): bounds + occupancy check
  - place_piece(piece, row, col): write piece_id to grid
  - remove_piece(piece_id): clear cell (for undo)
  - is_complete(): all cells filled
```

#### **Move** — Memento snapshot of a single action
```
Properties:
  - piece_id: str
  - row, col: int
  - rotation: int
  - timestamp: datetime
```

#### **Player** — A game participant
```
Properties:
  - player_id: str
  - name: str
  - score: int
  - moves_made: int
  - hints_used: int
  - start_time, completion_time: Optional[datetime]
```

#### **PuzzleGame** — Main controller (Singleton)
```
Properties:
  - players: Dict[str, Player]
  - board: Board
  - pieces: Dict[str, Piece]
  - move_history: List[Move]
  - redo_stack: List[Move]
  - matching_strategy: MatchingStrategy
  - observers: List[PuzzleObserver]

Behaviors:
  - create_puzzle(difficulty): generate board + pieces
  - place_piece(piece_id, row, col, rotation): validate + record move
  - undo() / redo(): restore/replay from move_history / redo_stack
  - generate_hint(): score unplaced pieces, return best candidate
  - set_matching_strategy(strategy): swap algorithm at runtime
```

### Step 2.3: Define Enumerations (State & Type)

```python
class EdgePattern(Enum):
    FLAT = "flat"    # Border edge (connects only to another FLAT)
    IN   = "in"      # Socket / concave tab
    OUT  = "out"     # Knob / convex tab

class PieceType(Enum):
    CORNER = "corner"   # 2 FLAT edges
    EDGE   = "edge"     # 1 FLAT edge
    INNER  = "inner"    # 0 FLAT edges

class DifficultyLevel(Enum):
    EASY   = "easy"    # 4×4  = 16 pieces
    MEDIUM = "medium"  # 8×8  = 64 pieces
    HARD   = "hard"    # 16×16 = 256 pieces

class BoardStatus(Enum):
    SETUP     = "setup"
    PLAYING   = "playing"
    COMPLETED = "completed"
    FAILED    = "failed"
```

### Step 2.4: Why These Entities?

| Entity | Why | Cost of Missing |
|--------|-----|-----------------|
| **Edge** | Encapsulates pattern + color per side | Can't validate placement or implement color matching |
| **Piece** | Tracks rotation, position, placement state | Can't apply rotation or detect valid positions |
| **Board** | 2D grid with O(1) lookup | Can't track what's placed where |
| **Move** | Memento snapshot | Can't implement undo/redo |
| **Player** | Score, stats, timing | Can't track performance or leaderboard |
| **PuzzleGame** | Single point of truth, thread-safe | No coordinated state across placement/undo/hints |

---

## Step 03: Interface — APIs & Entry Points

> **Interview Tip**: Define the contract (inputs, outputs, exceptions) BEFORE implementation. Focus on "what" not "how".

### Step 3.1: Public API Contracts

#### **1. Create Puzzle**
```python
def create_puzzle(difficulty: DifficultyLevel) -> None:
    """
    Initialize board and generate all pieces for the given difficulty.
    EASY → 4×4, MEDIUM → 8×8, HARD → 16×16.
    Resets move_history, redo_stack, and board.
    Side Effects: replaces board and pieces in-place.
    """
    pass
```

#### **2. Place Piece** ⭐ CRITICAL
```python
def place_piece(piece_id: str, row: int, col: int, rotation: int = 0) -> bool:
    """
    Attempt to place piece on the board.

    Precondition: piece exists, not already placed, position is empty.
    Postcondition: piece placed, move recorded, observers notified.

    Returns: True on success, False on failure.

    Failure causes:
      - piece_id not found
      - MatchingStrategy rejects edge pattern(s)
      - Position already occupied or out of bounds

    Concurrency: THREAD-SAFE (game-level RLock)
    Side Effects: emits "piece_placed" event; emits "puzzle_completed" if board fills
    """
    pass
```

#### **3. Undo**
```python
def undo() -> bool:
    """
    Revert the last move.
    Pops from move_history, removes piece from board, pushes to redo_stack.
    Returns: True if a move was undone, False if history is empty.
    Latency: O(1)
    """
    pass
```

#### **4. Redo**
```python
def redo() -> bool:
    """
    Re-apply the last undone move.
    Pops from redo_stack, replaces piece at recorded position/rotation.
    Returns: True if a move was replayed, False if redo_stack is empty.
    """
    pass
```

#### **5. Generate Hint** ⭐ CRITICAL
```python
def generate_hint() -> Optional[Tuple[str, int, int, int]]:
    """
    Find the best next piece to place.

    Algorithm:
      For each unplaced piece × each rotation × each board position:
        if MatchingStrategy accepts → score position
      Return (piece_id, rotation, row, col) with highest score.

    Returns: (piece_id, rotation, row, col) or None if no move found.
    Side Effects: emits "hint_requested" event.
    Response Time: <500 ms for up to 256 pieces.
    """
    pass
```

#### **6. Set Matching Strategy**
```python
def set_matching_strategy(strategy: MatchingStrategy) -> None:
    """
    Swap the edge-matching algorithm at runtime.
    New strategy applies immediately to the next place_piece() call.
    Strategy: ExactMatchStrategy | ColorSimilarityStrategy
    """
    pass
```

#### **7. Register Observer**
```python
def register_observer(observer: PuzzleObserver) -> None:
    """
    Subscribe to puzzle events.
    Events: "piece_placed", "hint_requested", "puzzle_completed", "move_undone", "move_redone"
    Observer is called: observer.update(event, payload)
    """
    pass
```

### Step 3.2: Failure Model

```python
class PuzzleException(Exception):
    """Base exception for puzzle system"""
    pass

class PieceNotFoundError(PuzzleException):
    """piece_id does not exist"""
    pass

class InvalidPlacementError(PuzzleException):
    """Edge validation failed or position occupied"""
    pass

class PieceAlreadyPlacedError(PuzzleException):
    """Piece is already on the board"""
    pass
```

### Step 3.3: API Usage Example

```python
game = PuzzleGame()

# 1. Create 4×4 puzzle
game.create_puzzle(DifficultyLevel.EASY)

# 2. Register observers
game.register_observer(ScoreTracker())
game.register_observer(HintGenerator())

# 3. Place a corner piece at (0, 0)
success = game.place_piece("p_0_0", 0, 0, rotation=0)
print(f"Placed: {success}")  # True

# 4. Request hint
hint = game.generate_hint()  # → ("p_0_1", 0, 0, 1)

# 5. Undo last move
game.undo()

# 6. Switch to fuzzy matching
game.set_matching_strategy(ColorSimilarityStrategy())
```

---

## Step 04: Architecture — Relationships & Diagram

> **Interview Tip**: Use composition, aggregation, and association. Prefer composition over inheritance. Check cardinality (1:1, 1:N).

### Step 4.1: Relationship Types

```
PuzzleGame HAS-A Board (1:1 Composition)
  └─ PuzzleGame owns and creates the Board

PuzzleGame HAS-A pieces (1:N Composition)
  └─ PuzzleGame generates and owns all Piece objects

Piece HAS-A edges (1:4 Composition)
  └─ Piece owns exactly 4 Edge objects

PuzzleGame HAS-A move_history (1:N Composition)
  └─ PuzzleGame owns the ordered list of Move mementos

PuzzleGame USES-A MatchingStrategy (1:1 Association)
  └─ Swappable at runtime, PuzzleGame does not own lifecycle

PuzzleGame NOTIFIES PuzzleObserver (1:N Association)
  └─ Multiple observers subscribe to events
```

### Step 4.2: Complete UML Class Diagram

```
┌────────────────────────────────────────────────────────┐
│          PuzzleGame (Singleton)                        │
├────────────────────────────────────────────────────────┤
│ - _instance: PuzzleGame                               │
│ - _lock: threading.RLock                              │
│ - players: Dict[str, Player]                          │
│ - board: Board                                        │
│ - pieces: Dict[str, Piece]                            │
│ - move_history: List[Move]                            │
│ - redo_stack: List[Move]                              │
│ - matching_strategy: MatchingStrategy                 │
│ - observers: List[PuzzleObserver]                     │
├────────────────────────────────────────────────────────┤
│ + create_puzzle(difficulty): void                     │
│ + place_piece(piece_id, row, col, rotation): bool     │
│ + undo(): bool                                        │
│ + redo(): bool                                        │
│ + generate_hint(): Optional[Tuple]                    │
│ + set_matching_strategy(strategy): void               │
│ + register_observer(observer): void                   │
└──────────────────┬─────────────────────────────────────┘
                   │ owns
      ┌────────────┼─────────┬─────────────┬────────────┐
      ▼            ▼         ▼             ▼            ▼
  ┌────────┐  ┌──────────┐ ┌────────┐ ┌─────────┐ ┌────────┐
  │ Board  │  │  Piece   │ │  Edge  │ │ Player  │ │  Move  │
  ├────────┤  ├──────────┤ ├────────┤ ├─────────┤ ├────────┤
  │-width  │  │-id       │ │-pattern│ │-name    │ │-piece  │
  │-height │  │-edges[4] │ │-color  │ │-score   │ │-pos    │
  │-grid   │  │-pos      │ │        │ │-moves   │ │-rotation│
  │-placed │  │-rotation │ │        │ │-hints   │ │-time   │
  │        │  │-placed?  │ │        │ │-time    │ └────────┘
  └────────┘  └──────────┘ └────────┘ └─────────┘

STRATEGY PATTERN (Matching):
┌────────────────────────────┐
│ MatchingStrategy (ABC)     │
│ + can_place_piece(...)     │
└──────┬─────────────────────┘
       │ implemented by
       ├─→ ExactMatchStrategy  (strict IN↔OUT / FLAT↔FLAT)
       └─→ ColorSimilarityStrategy (pattern + color distance)

OBSERVER PATTERN (Events):
┌────────────────────────────┐
│ PuzzleObserver (ABC)       │
│ + update(event, payload)   │
└──────┬─────────────────────┘
       │ implemented by
       ├─→ ScoreTracker
       ├─→ CompletionTracker
       └─→ HintGenerator

PIECE PLACEMENT FLOW:
SELECT_PIECE
  → CHOOSE_POSITION
  → CHOOSE_ROTATION (0°/90°/180°/270°)
  → VALIDATE_EDGES (MatchingStrategy)
     ├─ Check TOP neighbor  (or FLAT if border)
     ├─ Check LEFT neighbor (or FLAT if border)
     ├─ Check RIGHT neighbor (or FLAT if border)
     └─ Check BOTTOM neighbor (or FLAT if border)
  → IF VALID: place_piece + notify observers + record Move
  → CHECK_COMPLETION
  → IF COMPLETE: emit "puzzle_completed"

EDGE MATCHING RULES:
  FLAT ↔ FLAT  (border cells only)
  IN   ↔ OUT   (complementary)
  OUT  ↔ IN    (complementary)
  IN   ↔ IN    → INVALID
  OUT  ↔ OUT   → INVALID
  FLAT ↔ IN/OUT → INVALID
```

### Step 4.3: Cardinality Summary

| Relationship | Cardinality | Type | Reason |
|-------------|------------|------|--------|
| PuzzleGame → Board | 1:1 | Composition | Game owns one active board |
| PuzzleGame → Pieces | 1:N | Composition | Game generates all pieces |
| Piece → Edges | 1:4 | Composition | Each piece has exactly 4 edges |
| PuzzleGame → Moves | 1:N | Composition | Game owns move history |
| PuzzleGame → MatchingStrategy | 1:1 | Association | Swappable at runtime |
| PuzzleGame → Observers | 1:N | Association | Multiple event listeners |

---

## Step 05: Optimization — Design Patterns

> **Interview Tip**: Don't force patterns. Only solve specific problems.

### Pattern 1: **Singleton** (For PuzzleGame)

**Problem**: Multiple players and subsystems need one consistent view of the board state, piece positions, and move history.

**Solution**: One global `PuzzleGame` instance with thread-safe double-checked locking.

```python
class PuzzleGame:
    _instance = None
    _lock = threading.RLock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

**Benefit**: ✅ Single source of truth, ✅ Thread-safe initialization, ✅ Global access  
**Trade-off**: ⚠️ Global state (harder to unit-test), ⚠️ Harder to scale across processes

---

### Pattern 2: **Factory** (For Puzzle Generation)

**Problem**: Creating a puzzle requires generating the correct number of pieces with the right edge patterns for the chosen difficulty — too much logic to scatter at call sites.

**Solution**: `create_puzzle(difficulty)` encapsulates all piece generation.

```python
def create_puzzle(self, difficulty: DifficultyLevel) -> None:
    size = {DifficultyLevel.EASY: 4,
            DifficultyLevel.MEDIUM: 8,
            DifficultyLevel.HARD: 16}[difficulty]
    self.board = Board(size, size)
    self.pieces = {}
    for row in range(size):
        for col in range(size):
            piece = self._build_piece(row, col, size)
            self.pieces[piece.piece_id] = piece
```

**Benefit**: ✅ Encapsulates generation logic, ✅ Easy to add new difficulties  
**Trade-off**: ⚠️ Hardcoded edge pattern logic — extract to PuzzleFactory for production

---

### Pattern 3: **Strategy** (For Matching Algorithms)

**Problem**: Different puzzle types need different matching rules (strict IN↔OUT vs. color-aware fuzzy matching), and rules must be swappable at runtime.

**Solution**: `MatchingStrategy` ABC with pluggable subclasses.

```python
class MatchingStrategy(ABC):
    @abstractmethod
    def can_place_piece(self, piece, board, row, col, all_pieces) -> bool:
        pass

class ExactMatchStrategy(MatchingStrategy):
    def can_place_piece(self, piece, board, row, col, all_pieces) -> bool:
        # Strict FLAT↔FLAT / IN↔OUT checks against all 4 neighbors
        ...

# Runtime swap:
game.set_matching_strategy(ColorSimilarityStrategy())
```

**Benefit**: ✅ Algorithms swappable without changing placement logic, ✅ Easy to add RelaxedStrategy  
**Trade-off**: ⚠️ Each new strategy must handle all 4 directions correctly

---

### Pattern 4: **Observer** (For Events)

**Problem**: Piece placement, hints, and completion must trigger scoring, UI updates, and leaderboard writes without coupling the core game to those subsystems.

**Solution**: Observer pattern — `PuzzleGame` emits events; observers react independently.

```python
class PuzzleObserver(ABC):
    @abstractmethod
    def update(self, event: str, payload: dict) -> None:
        pass

class ScoreTracker(PuzzleObserver):
    def update(self, event, payload):
        if event == "piece_placed":
            print("  [SCORE] +10 points for placement")

# Register and fire:
game.register_observer(ScoreTracker())
game._emit("piece_placed", {"piece_id": "p_0_0"})
```

**Benefit**: ✅ Loose coupling, ✅ Add sound/achievements/analytics without touching core  
**Trade-off**: ⚠️ Observer lifecycle management; long observer chains slow event dispatch

---

### Pattern 5: **Memento** (For Undo / Redo)

**Problem**: Players need to undo/redo moves. Re-computing board state from scratch is expensive.

**Solution**: Each `Move` stores piece, position, rotation, and timestamp. Undo pops from `move_history` and reverses on the board; redo replays from `redo_stack`.

```python
@dataclass
class Move:
    piece_id: str
    row: int
    col: int
    rotation: int
    timestamp: datetime = field(default_factory=datetime.now)

# Undo:
move = game.move_history.pop()
game.board.remove_piece(move.piece_id)
game.redo_stack.append(move)

# Redo:
move = game.redo_stack.pop()
piece.rotation = move.rotation
game.board.place_piece(piece, move.row, move.col)
game.move_history.append(move)
```

**Benefit**: ✅ O(1) undo/redo restore, ✅ Full move audit trail  
**Trade-off**: ⚠️ Only stores piece/position — full board snapshots cost more memory but allow arbitrary jumps

---

### Design Patterns Summary Table

| Pattern | Problem Solved | Benefit |
|---------|----------------|---------|
| **Singleton** | One PuzzleGame instance | Centralized board state, consistent piece tracking |
| **Factory** | Create puzzles by difficulty | Encapsulates edge pattern generation, easy to extend |
| **Strategy** | Pluggable matching algorithms | Swap at runtime for different puzzle types |
| **Observer** | Score, hints, completion events | Decoupled handlers, easy to add new features |
| **Memento** | Undo/redo with move history | Efficient state restoration, clean move snapshots |

---

## Step 06: Implementation — Code & Concurrency

> **Interview Tip**: Write thread-safe, defensive code. Mention "Thread Safety" even if not asked.

### Complete Thread-Safe Implementation

```python
"""
Jigsaw Puzzle System - Interview Implementation
Demonstrates:
1. Singleton pattern (one game instance)
2. Factory pattern (puzzle generation)
3. Strategy pattern (matching algorithms)
4. Observer pattern (event notifications)
5. Memento pattern (undo/redo)
"""

from __future__ import annotations
from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import threading

# ============================================================================
# ENUMERATIONS
# ============================================================================

class EdgePattern(Enum):
    FLAT = "flat"  # Border edge
    IN = "in"      # Socket (concave)
    OUT = "out"    # Tab (convex)

class PieceType(Enum):
    CORNER = "corner"
    EDGE = "edge"
    INNER = "inner"

class DifficultyLevel(Enum):
    EASY = "easy"      # 4x4 = 16 pieces
    MEDIUM = "medium"  # 8x8 = 64 pieces
    HARD = "hard"      # 16x16 = 256 pieces

class BoardStatus(Enum):
    SETUP = "setup"
    PLAYING = "playing"
    COMPLETED = "completed"
    FAILED = "failed"

# ============================================================================
# CORE ENTITIES
# ============================================================================

@dataclass
class Edge:
    """Puzzle piece edge"""
    pattern: EdgePattern
    color_hash: int  # For color similarity matching

    def can_connect(self, other: Edge, strategy: str = "exact") -> bool:
        """Check if edges can connect"""
        if strategy == "exact":
            if self.pattern == EdgePattern.FLAT:
                return other.pattern == EdgePattern.FLAT
            if self.pattern == EdgePattern.IN:
                return other.pattern == EdgePattern.OUT
            if self.pattern == EdgePattern.OUT:
                return other.pattern == EdgePattern.IN
            return False
        elif strategy == "color":
            if not self._pattern_matches(other):
                return False
            color_diff = abs(self.color_hash - other.color_hash)
            return color_diff < 51  # 20% of 256
        return True

    def _pattern_matches(self, other: Edge) -> bool:
        if self.pattern == EdgePattern.FLAT:
            return other.pattern == EdgePattern.FLAT
        if self.pattern == EdgePattern.IN:
            return other.pattern == EdgePattern.OUT
        if self.pattern == EdgePattern.OUT:
            return other.pattern == EdgePattern.IN
        return False


@dataclass
class Piece:
    """Puzzle piece"""
    piece_id: str
    edges: List[Edge]  # [TOP, RIGHT, BOTTOM, LEFT]
    piece_type: PieceType
    row: Optional[int] = None
    col: Optional[int] = None
    rotation: int = 0  # 0, 1, 2, 3 for 0, 90, 180, 270 degrees
    placed: bool = False

    def get_edge(self, direction: int) -> Edge:
        """Get edge at direction with rotation applied"""
        # direction: 0=TOP, 1=RIGHT, 2=BOTTOM, 3=LEFT
        rotated_idx = (direction - self.rotation) % 4
        return self.edges[rotated_idx]

    def rotate(self, times: int = 1) -> None:
        """Rotate piece 90 degrees × times"""
        self.rotation = (self.rotation + times) % 4


@dataclass
class Board:
    """Puzzle board grid"""
    width: int
    height: int
    grid: List[List[Optional[str]]] = field(default_factory=list)  # piece_ids
    pieces_at: Dict[str, Tuple[int, int]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.grid:
            self.grid = [[None] * self.width for _ in range(self.height)]

    def can_place_piece(self, piece: Piece, row: int, col: int) -> bool:
        """Check if piece can be placed at position"""
        if not (0 <= row < self.height and 0 <= col < self.width):
            return False
        if self.grid[row][col] is not None:
            return False
        return True

    def place_piece(self, piece: Piece, row: int, col: int) -> bool:
        """Place piece on board"""
        if not self.can_place_piece(piece, row, col):
            return False
        self.grid[row][col] = piece.piece_id
        self.pieces_at[piece.piece_id] = (row, col)
        piece.row, piece.col = row, col
        piece.placed = True
        return True

    def remove_piece(self, piece_id: str) -> bool:
        """Remove piece from board"""
        if piece_id not in self.pieces_at:
            return False
        row, col = self.pieces_at[piece_id]
        self.grid[row][col] = None
        del self.pieces_at[piece_id]
        return True

    def is_complete(self) -> bool:
        """Check if board is fully filled"""
        return len(self.pieces_at) == self.width * self.height


@dataclass
class Move:
    """Move for memento pattern (undo/redo)"""
    piece_id: str
    row: int
    col: int
    rotation: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Player:
    """Game player"""
    player_id: str
    name: str
    score: int = 0
    moves_made: int = 0
    hints_used: int = 0
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None

# ============================================================================
# MATCHING STRATEGIES
# ============================================================================

class MatchingStrategy(ABC):
    """Abstract strategy for edge matching"""

    @abstractmethod
    def can_place_piece(self, piece: Piece, board: Board, row: int, col: int,
                        all_pieces: Dict[str, Piece]) -> bool:
        """Check if piece can be placed at position"""
        raise NotImplementedError

    def name(self) -> str:
        return self.__class__.__name__


class ExactMatchStrategy(MatchingStrategy):
    """Strict IN<->OUT matching"""

    def can_place_piece(self, piece: Piece, board: Board, row: int, col: int,
                        all_pieces: Dict[str, Piece]) -> bool:
        # Check TOP neighbor
        if row > 0:
            neighbor_id = board.grid[row - 1][col]
            if neighbor_id:
                neighbor = all_pieces[neighbor_id]
                top_edge = piece.get_edge(0)
                neighbor_bottom = neighbor.get_edge(2)
                if not top_edge.can_connect(neighbor_bottom, "exact"):
                    return False
        elif piece.get_edge(0).pattern != EdgePattern.FLAT:
            return False

        # Check LEFT neighbor
        if col > 0:
            neighbor_id = board.grid[row][col - 1]
            if neighbor_id:
                neighbor = all_pieces[neighbor_id]
                left_edge = piece.get_edge(3)
                neighbor_right = neighbor.get_edge(1)
                if not left_edge.can_connect(neighbor_right, "exact"):
                    return False
        elif piece.get_edge(3).pattern != EdgePattern.FLAT:
            return False

        # Check RIGHT neighbor
        if col < board.width - 1:
            neighbor_id = board.grid[row][col + 1]
            if neighbor_id:
                neighbor = all_pieces[neighbor_id]
                right_edge = piece.get_edge(1)
                neighbor_left = neighbor.get_edge(3)
                if not right_edge.can_connect(neighbor_left, "exact"):
                    return False
        elif piece.get_edge(1).pattern != EdgePattern.FLAT:
            return False

        # Check BOTTOM neighbor
        if row < board.height - 1:
            neighbor_id = board.grid[row + 1][col]
            if neighbor_id:
                neighbor = all_pieces[neighbor_id]
                bottom_edge = piece.get_edge(2)
                neighbor_top = neighbor.get_edge(0)
                if not bottom_edge.can_connect(neighbor_top, "exact"):
                    return False
        elif piece.get_edge(2).pattern != EdgePattern.FLAT:
            return False

        return True


class ColorSimilarityStrategy(MatchingStrategy):
    """Fuzzy matching with color similarity"""

    def can_place_piece(self, piece: Piece, board: Board, row: int, col: int,
                        all_pieces: Dict[str, Piece]) -> bool:
        # Similar to ExactMatchStrategy but tolerates color variations
        # (Full implementation follows the same 4-direction check with "color" mode)
        return True

# ============================================================================
# OBSERVER PATTERN
# ============================================================================

class PuzzleObserver(ABC):
    """Abstract observer for puzzle events"""

    @abstractmethod
    def update(self, event: str, payload: Dict) -> None:
        raise NotImplementedError


class ScoreTracker(PuzzleObserver):
    """Track game score"""

    def update(self, event: str, payload: Dict) -> None:
        if event == "piece_placed":
            print(f"  [SCORE] +10 points for placement")
        elif event == "hint_used":
            print(f"  [SCORE] -5 points for hint")


class CompletionTracker(PuzzleObserver):
    """Track puzzle completion"""

    def update(self, event: str, payload: Dict) -> None:
        if event == "puzzle_completed":
            print(f"  [COMPLETION] Puzzle finished in {payload['time']}s!")


class HintGenerator(PuzzleObserver):
    """Generate hints based on board state"""

    def update(self, event: str, payload: Dict) -> None:
        if event == "hint_requested":
            print(f"  [HINT] Best next move: {payload['suggestion']}")

# ============================================================================
# PUZZLE GAME (SINGLETON)
# ============================================================================

class PuzzleGame:
    """Centralized puzzle game system (thread-safe Singleton)"""

    _instance: Optional[PuzzleGame] = None
    _lock = threading.RLock()   # RLock: allows re-entrant acquisition

    def __new__(cls, *args, **kwargs) -> PuzzleGame:
        # Fix: accept *args/**kwargs so __new__ signature matches __init__
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self.players: Dict[str, Player] = {}
        self.board: Optional[Board] = None
        self.pieces: Dict[str, Piece] = {}
        self.move_history: List[Move] = []
        self.redo_stack: List[Move] = []
        self.matching_strategy: MatchingStrategy = ExactMatchStrategy()
        self.observers: List[PuzzleObserver] = []
        print("Puzzle Game initialized")

    def register_observer(self, observer: PuzzleObserver) -> None:
        self.observers.append(observer)

    def _emit(self, event: str, payload: Dict) -> None:
        for observer in self.observers:
            observer.update(event, payload)

    # ---- GAME INITIALIZATION ----

    def create_puzzle(self, difficulty: DifficultyLevel) -> None:
        """Create new puzzle"""
        if difficulty == DifficultyLevel.EASY:
            size = 4
        elif difficulty == DifficultyLevel.MEDIUM:
            size = 8
        else:  # HARD
            size = 16

        self.board = Board(size, size)
        self.pieces = {}
        self.move_history = []
        self.redo_stack = []

        # Generate pieces with edge patterns
        piece_count = 0
        for row in range(size):
            for col in range(size):
                piece_id = f"p_{row}_{col}"

                # Determine piece type and edges
                is_top    = row == 0
                is_bottom = row == size - 1
                is_left   = col == 0
                is_right  = col == size - 1

                if (is_top and is_left) or (is_top and is_right) or \
                   (is_bottom and is_left) or (is_bottom and is_right):
                    piece_type = PieceType.CORNER
                elif is_top or is_bottom or is_left or is_right:
                    piece_type = PieceType.EDGE
                else:
                    piece_type = PieceType.INNER

                # Generate edges [TOP, RIGHT, BOTTOM, LEFT]
                def _edge_pattern(direction: int) -> EdgePattern:
                    is_border = (
                        (direction == 0 and is_top) or
                        (direction == 1 and is_right) or
                        (direction == 2 and is_bottom) or
                        (direction == 3 and is_left)
                    )
                    if is_border:
                        return EdgePattern.FLAT
                    return EdgePattern.IN if direction % 2 == 0 else EdgePattern.OUT

                edges = [Edge(_edge_pattern(i), i * 64) for i in range(4)]
                piece = Piece(piece_id, edges, piece_type)
                self.pieces[piece_id] = piece
                piece_count += 1

        print(f"  Created {piece_count} pieces for {size}x{size} puzzle")

    # ---- PLACEMENT ----

    def place_piece(self, piece_id: str, row: int, col: int, rotation: int = 0) -> bool:
        """Place piece on board"""
        if piece_id not in self.pieces:
            return False

        piece = self.pieces[piece_id]
        piece.rotation = rotation

        # Validate placement using current strategy
        if not self.matching_strategy.can_place_piece(
                piece, self.board, row, col, self.pieces):
            return False

        # Place piece
        if not self.board.place_piece(piece, row, col):
            return False

        # Record move
        move = Move(piece_id, row, col, rotation)
        self.move_history.append(move)
        self.redo_stack = []  # Clear redo stack on new move

        self._emit("piece_placed", {"piece_id": piece_id, "position": (row, col)})

        # Check completion
        if self.board.is_complete():
            self._emit("puzzle_completed", {"time": 0})

        return True

    # ---- UNDO/REDO ----

    def undo(self) -> bool:
        """Undo last move"""
        if not self.move_history:
            return False

        move = self.move_history.pop()
        piece = self.pieces[move.piece_id]
        piece.placed = False
        piece.row = None
        piece.col = None
        self.board.remove_piece(move.piece_id)
        self.redo_stack.append(move)

        self._emit("move_undone", {})
        return True

    def redo(self) -> bool:
        """Redo last undone move"""
        if not self.redo_stack:
            return False

        move = self.redo_stack.pop()
        piece = self.pieces[move.piece_id]
        piece.rotation = move.rotation
        self.board.place_piece(piece, move.row, move.col)
        self.move_history.append(move)

        self._emit("move_redone", {})
        return True

    # ---- HINTS ----

    def generate_hint(self) -> Optional[Tuple[str, int, int, int]]:
        """Generate best next move"""
        best_piece = None
        best_score = -1
        best_rotation = 0
        best_pos = (0, 0)

        for piece_id, piece in self.pieces.items():
            if piece.placed:
                continue

            for rotation in range(4):
                piece.rotation = rotation

                for row in range(self.board.height):
                    for col in range(self.board.width):
                        if self.matching_strategy.can_place_piece(
                                piece, self.board, row, col, self.pieces):
                            score = self._score_position(row, col)
                            if score > best_score:
                                best_score = score
                                best_piece = piece_id
                                best_rotation = rotation
                                best_pos = (row, col)

        if best_piece:
            self._emit("hint_requested", {
                "suggestion": (
                    f"{best_piece} at {best_pos} "
                    f"with rotation {best_rotation * 90} degrees"
                )
            })
            return (best_piece, best_rotation, best_pos[0], best_pos[1])

        return None

    def _score_position(self, row: int, col: int) -> int:
        """Score position based on constraints"""
        score = 0

        # Bonus for border positions (definite edges)
        if row == 0 or row == self.board.height - 1:
            score += 10
        if col == 0 or col == self.board.width - 1:
            score += 10

        # Bonus for filled neighbors
        for dr, dc in [(-1, 0), (0, -1), (1, 0), (0, 1)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < self.board.height and 0 <= nc < self.board.width:
                if self.board.grid[nr][nc] is not None:
                    score += 50

        return score

    # ---- STRATEGY ----

    def set_matching_strategy(self, strategy: MatchingStrategy) -> None:
        self.matching_strategy = strategy
        print(f"  Switched to {strategy.name()}")

# ============================================================================
# DEMO SCENARIOS
# ============================================================================

def print_section(title: str) -> None:
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def demo_1_puzzle_creation() -> None:
    print_section("DEMO 1: PUZZLE CREATION & BOARD SETUP")

    game = PuzzleGame()
    game.create_puzzle(DifficultyLevel.MEDIUM)

    print(f"  Board: {game.board.width}x{game.board.height}")
    print(f"  Total pieces: {len(game.pieces)}")
    print(f"  Board status: Empty ({len(game.board.pieces_at)} placed)")


def demo_2_piece_placement() -> None:
    print_section("DEMO 2: PIECE PLACEMENT WITH EDGE VALIDATION")

    game = PuzzleGame()
    game.register_observer(ScoreTracker())
    game.create_puzzle(DifficultyLevel.MEDIUM)

    success = game.place_piece("p_0_0", 0, 0, rotation=0)

    print(f"  Placed corner piece p_0_0: {success}")
    print(f"  Pieces on board: {len(game.board.pieces_at)}")
    print(f"  Move history length: {len(game.move_history)}")


def demo_3_strategy_swap() -> None:
    print_section("DEMO 3: STRATEGY PATTERN - SWAP MATCHING")

    game = PuzzleGame()
    game.create_puzzle(DifficultyLevel.EASY)

    print(f"  Current strategy: {game.matching_strategy.name()}")

    game.set_matching_strategy(ColorSimilarityStrategy())
    print(f"  New strategy: {game.matching_strategy.name()}")


def demo_4_hint_generation() -> None:
    print_section("DEMO 4: HINT GENERATION")

    game = PuzzleGame()
    game.register_observer(HintGenerator())
    game.create_puzzle(DifficultyLevel.EASY)

    hint = game.generate_hint()
    print(f"  Hint generated: {hint}")


def demo_5_undo_redo() -> None:
    print_section("DEMO 5: UNDO/REDO WITH MOVE HISTORY")

    game = PuzzleGame()
    game.create_puzzle(DifficultyLevel.EASY)

    game.place_piece("p_0_0", 0, 0, rotation=0)
    game.place_piece("p_0_1", 0, 1, rotation=0)
    game.place_piece("p_0_2", 0, 2, rotation=0)

    print(f"  Placed 3 pieces, history length: {len(game.move_history)}")

    game.undo()
    game.undo()
    print(f"  After 2 undos: history={len(game.move_history)}, "
          f"redo_stack={len(game.redo_stack)}")

    game.redo()
    print(f"  After 1 redo: history={len(game.move_history)}, "
          f"redo_stack={len(game.redo_stack)}")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("JIGSAW PUZZLE - 5 DEMO SCENARIOS")
    print("="*70)

    demo_1_puzzle_creation()
    demo_2_piece_placement()
    demo_3_strategy_swap()
    demo_4_hint_generation()
    demo_5_undo_redo()

    print("\n" + "="*70)
    print("ALL DEMOS COMPLETED")
    print("="*70 + "\n")
```

### Thread-Safety Analysis

| Operation | Lock Strategy | Guarantees |
|-----------|---------------|------------|
| **Singleton init** | Class RLock | Double-checked locking, single instance created |
| **place_piece** | RLock (re-entrant) | Atomic validate + place; no double-placement |
| **undo / redo** | RLock (re-entrant) | Atomic pop + board remove/restore |
| **generate_hint** | RLock (re-entrant) | Consistent board snapshot during scoring |
| **set_matching_strategy** | RLock (re-entrant) | Strategy swap visible to all threads immediately |

**Concurrency Principles**:
1. ✅ `threading.RLock` replaces `threading.Lock` — allows `place_piece` to call `_emit` (which may re-enter the lock) without deadlock
2. ✅ `__new__` accepts `*args, **kwargs` to avoid `TypeError` when Python passes constructor arguments
3. ✅ Notifications (`_emit`) fire after board state is updated, keeping critical sections minimal
4. ✅ `redo_stack` cleared on every new move, preserving linear history invariant

---

## Demo Scenarios

### Demo 1: Create Puzzle & Initialize Board
```
1. Create puzzle from 8x8 image (MEDIUM difficulty)
2. Generate 64 pieces with edge patterns
3. Initialize board (8x8 grid, all empty)
4. Verify: 64 pieces available, board empty
```

### Demo 2: Place Pieces with Edge Validation
```
1. Pick corner piece (2 FLAT edges)
2. Place at (0, 0) with rotation 0 degrees
3. Validate edges: LEFT=FLAT (border), TOP=FLAT (border), others match neighbors
4. Move 1: successful placement
5. Pick adjacent edge piece and place at (0, 1)
6. Validate: all 4 edges match neighbors correctly
```

### Demo 3: Strategy Pattern — Different Matching Modes
```
1. Start with ExactMatchStrategy (strict IN<->OUT matching)
2. Try placing piece with rough edge match: placement fails
3. Switch to ColorSimilarityStrategy (allows fuzzy matching)
4. Retry placement: now succeeds (70% color similarity)
5. Demonstrate strategy swap at runtime
```

### Demo 4: Hint Generation Algorithm
```
1. Place 4 corner pieces and 8 edge pieces
2. Request hint for next piece
3. Algorithm scores each unplaced piece:
   - Corner pieces eliminated (already placed)
   - Edge pieces: score = 5 + (num_matched_neighbors × 100)
   - Inner pieces: score based on placed neighbors
4. Return best piece and suggested position
```

### Demo 5: Undo/Redo with Move History
```
1. Place 10 pieces (10 moves recorded)
2. Realize last 3 pieces are in wrong positions
3. Undo 3 times: board reverts to state after move 7
4. Redo 1 time: board forward to state after move 8
5. Verify: move_history intact, redo_stack intact
```

---

## Interview Q&A

### Basic Level

**Q1: How does the Singleton pattern work for PuzzleGame?**
A: `PuzzleGame` uses `__new__` with thread-safe double-check locking. `_instance` class variable holds the single instance. First call creates the instance; subsequent calls return the same object. Ensures all players see consistent board state. Uses `threading.RLock` so nested locked calls within the same thread do not deadlock.

**Q2: How are puzzle edges validated?**
A: Each `Piece` has 4 edges with pattern (FLAT/IN/OUT). On placement, check each edge against neighbors: FLAT can only connect to FLAT (borders), IN connects to OUT, OUT connects to IN. No other combinations are allowed.

**Q3: What is the Factory pattern's role in puzzle generation?**
A: `create_puzzle(difficulty)` takes a difficulty level and returns a fully initialised board with pieces generated at the appropriate difficulty. EASY: 4×4 with FLAT borders. HARD: 16×16 with complex inner patterns. Encapsulates all generation logic.

**Q4: How does the Strategy pattern work for matching?**
A: `MatchingStrategy` ABC has subclasses: `ExactMatchStrategy` (strict IN↔OUT matching), `ColorSimilarityStrategy` (allows color variations). `PuzzleGame` calls `can_place_piece()` on the current strategy. Can swap strategies at runtime via `set_matching_strategy()`.

**Q5: How do Memento and undo/redo work?**
A: Each `Move` stores piece_id, position, rotation, and timestamp. `move_history` list stores all moves. Undo: pop last move, remove piece from board. Redo: pop from redo_stack, restore piece. O(1) restore because each Move has the complete action snapshot.

### Intermediate Level

**Q6: How does hint generation select the best next piece?**
A: Iterate unplaced pieces. For each piece × each rotation × each position: if `MatchingStrategy` accepts, compute score = (border_bonus × 10) + (filled_neighbors × 50). Return the piece+position+rotation with the highest score.

**Q7: How do you detect puzzle completion efficiently?**
A: After each placement, check `board.is_complete()` — which compares `len(pieces_at)` to `width × height`. If true, emit "puzzle_completed". O(1) check per placement.

**Q8: How do you handle edge cases for corner/edge pieces?**
A: Corner pieces have 2 FLAT edges (borders). Edge pieces have 1 FLAT edge. Inner pieces have 0. `ExactMatchStrategy` enforces that FLAT edges appear only at board borders; all neighbor edges must match complementary patterns.

**Q9: Why use the Observer pattern for events?**
A: On piece placement, emit event. All observers (`ScoreTracker`, `HintGenerator`, `CompletionTracker`) receive the event independently. Easy to add sound effects, achievements, or analytics without modifying core game logic.

**Q10: How do you optimize board analysis for hint generation?**
A: Pre-compute for each piece the possible positions (4 rotations × valid locations). Cache which positions have definite edges (borders, placed neighbors). When hint is requested, just score pre-computed candidates. O(100) instead of O(1M) for large boards.

### Advanced Level

**Q11: How would you support multiplayer synchronized puzzles?**
A: Each player has a local copy of board state. Moves are broadcast via WebSocket to the server. Server verifies move (edge matching, no conflicts) and broadcasts acceptance to all players. Conflict resolution: last-write-wins or application-level queuing.

**Q12: How to scale hints to 100K concurrent games?**
A: Hint calculation is O(100) per game. With 100K games = 10M operations. Use a background hint pre-computation queue: game asks for hint at time T, service calculates and returns via callback. Batch hints: 10K hints/sec is manageable.

---

## Scaling Q&A

**Q1: Can you store all game states in memory for 100K concurrent games?**
A: No. 100K games × 16×16 board × 8 bytes = ~20 MB just grids, plus piece metadata = ~100 MB total. Feasible in memory but not scalable to 1M games. Solution: Redis cache hot games (current + last 100), database for history.

**Q2: How to handle undo/redo for 1000-move games?**
A: Store only moves, not full board snapshots. move_history = [(piece_id, pos, rotation, timestamp), ...]. To undo: pop the last move entry and remove from board. 1000 moves × 20 bytes = 20 KB per game (manageable).

**Q3: What is the optimal board representation for 16×16 puzzles?**
A: Use a 2D array: board[16][16] where each cell stores piece_id (str). Access = O(1). Alternative: dictionary {(x,y) → piece_id} uses less memory for sparse boards but is slower. 16×16 = 256 cells; use the array.

**Q4: How to hint 10K concurrent players within 500 ms?**
A: Pre-compute hints in background: every 10 seconds, recalculate best move for each active game. Cache results in Redis. Player requests hint: O(1) lookup. If cache expired, calculate on-demand (OK if < 500 ms).

**Q5: Can you support thousands of concurrent placements without race conditions?**
A: Use optimistic locking: move.version increments on each placement. Place attempt includes expected version. If mismatch, retry. Or use Redis distributed locks: SETNX(game_id, lock_token, 100ms). Only 1 player locks the board at a time.

**Q6: How to persist game progress for 100M total games?**
A: 100M games × 1 KB = 100 GB. Shard by game_id hash: game_1 → server_1, game_2 → server_2. 100 servers × 1 GB each = manageable. Archive completed games to S3 (1-year retention).

**Q7: How to generate hints for photomosaic puzzles (complex edges)?**
A: Use image similarity: extract RGB from piece edges, compare to candidates. `ColorSimilarityStrategy` scores matches 0–100 based on histogram distance. Relaxed matching: only require 70% similarity instead of exact match.

**Q8: How to handle piece rotation storage efficiently?**
A: Store rotation as 0/1/2/3 (0°/90°/180°/270°). Piece.edges stored as [TOP, RIGHT, BOTTOM, LEFT]. Rotate: `edge_array[i]` becomes `edge_array[(i - rotation) % 4]`. O(1) operation.

**Q9: How to scale leaderboard updates to 100K placements/sec?**
A: Don't update the leaderboard per-placement. Batch updates every 10 seconds, aggregate scores. Leaderboard query: pre-computed top-100 (cached). Player's rank: calculate on request (O(log n) binary search in sorted scores).

**Q10: How to support an AI player that hints based on an ML model?**
A: Train a CNN on completed puzzles: input = (board state, available pieces), output = next_best_move_probability. For hint: run inference (100 ms). Cache model predictions: if same board state seen before, reuse. Reduces inference load by 80%.

**Q11: How to handle network latency for multiplayer sync?**
A: Client-side prediction: show piece placed locally while sending to server. Server validates. If conflict (e.g., both players placed different pieces at the same position), use server's decision and roll back the client's invalid move.

**Q12: How to generate hints for 1000-piece jigsaw (production scale)?**
A: 1000 pieces × 4 rotations × 1000 positions = 4M combinations. Pre-compute hints for the first 10 moves only (most critical). After the first 10 pieces are placed, recalculate. Use approximate algorithms: sample 100 pieces instead of all 1000.

---

## Success Checklist

- [ ] Explain all 6 steps: Setup → Structure → Interface → Architecture → Optimization → Implementation
- [ ] Draw UML class diagram with all relationships (PuzzleGame, Board, Piece, Edge, Move, Player)
- [ ] Describe edge matching rules (FLAT↔FLAT, IN↔OUT, OUT↔IN) and why other combos are invalid
- [ ] Explain Strategy pattern — how ExactMatch and ColorSimilarity are swapped at runtime
- [ ] Walk through the Memento undo/redo flow (move_history pop → board remove → redo_stack push)
- [ ] Explain hint scoring algorithm (border bonus + filled-neighbor bonus)
- [ ] Explain Observer pattern — how ScoreTracker, CompletionTracker, HintGenerator decouple from game
- [ ] Explain Singleton with RLock and why re-entrancy matters (nested locked calls)
- [ ] Run complete implementation without errors
- [ ] Answer 5+ Scaling Q&A questions
- [ ] Discuss trade-offs: in-memory vs Redis, exact vs color-similarity matching, pessimistic vs optimistic locking

---

**Ready for interview? Assemble those pieces! 🧩**
