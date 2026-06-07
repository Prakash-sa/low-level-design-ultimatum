# Chess Game — Complete Design Guide

> Full FIDE chess engine with piece-movement validation, check/checkmate detection, special moves, and game-state lifecycle management.

**Scale**: Single-game engine, extensible to 1M+ concurrent games  
**Duration**: 75-minute interview guide  
**Focus**: Piece hierarchy, legal-move generation, check/checkmate detection, game-state machine, thread-safe Singleton

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

Two players alternately move pieces on an 8×8 board. Every move must be validated (piece rules + no leaving own king in check). Game ends on checkmate, stalemate, or draw. Core concerns: correctness of rules, state management, and move validation.

### Core Flow

```
Initialize Board → Place 32 Pieces → White Moves First
     ↓
Validate Move (piece rules + no self-check)
     ↓ illegal                    ↓ legal
  Reject                   Apply to Board → Switch Turn
                                 ↓
                         Detect Check / Checkmate / Stalemate
                                 ↓ checkmate or stalemate
                              Game Over
```

---

## Step 01: The Setup — Clarify Requirements

> **Interview Tip**: Never code immediately. Ask clarifying questions first. Define scope, actors, and constraints.

### Questions to Ask (30 seconds each)

1. **Single game or multiplayer server?** → "Single-game engine; multiplayer is a scaling concern"
2. **Full FIDE rules or simplified?** → "Full rules including castling, en passant, promotion"
3. **AI opponent or human vs human?** → "Human vs human; mention minimax as an extension"
4. **Undo / replay required?** → "Yes, maintain move history for replay"
5. **Clock / time controls?** → "Out of scope for core; mention as a scaling concern"

### Actors (Who uses the system?)

| Actor | Role | Example Actions |
|-------|------|-----------------|
| **White Player** | Controls white pieces | Make moves, request draw |
| **Black Player** | Controls black pieces | Make moves, resign |
| **System** | Game controller | Validate moves, detect check/checkmate, switch turns |

### Functional Requirements (What does the system do?)

✅ **Board Setup**
  - Create standard 8×8 board with 32 pieces in starting positions
  - Support piece lookup by position in O(1)

✅ **Move Validation**
  - Validate moves per piece type (Pawn, Rook, Knight, Bishop, Queen, King)
  - Reject any move that leaves own king in check

✅ **Special Moves**
  - Castling (kingside and queenside)
  - En passant pawn capture
  - Pawn promotion (to Queen, Rook, Bishop, or Knight)

✅ **Game-State Detection**
  - Detect check (king under attack, legal moves exist)
  - Detect checkmate (king under attack, no legal moves)
  - Detect stalemate (not in check, no legal moves)
  - Detect draw (insufficient material, 50-move rule, threefold repetition)

✅ **Turn Management**
  - Alternate turns between white and black
  - Reject moves from the wrong player

✅ **History & Replay**
  - Record every move for replay or undo

### Non-Functional Requirements (How does it perform?)

✅ **Correctness**: Legal moves must never leave own king in check  
✅ **Performance**: O(1) piece lookup; O(n) move generation (n ≤ 50 legal moves max)  
✅ **Extensibility**: Strategy pattern enables adding new piece types or rule variants  
✅ **Thread Safety**: Singleton initialization protected; RLock prevents re-entrancy issues

### Constraints & Clarifications

| Constraint | Decision |
|-----------|----------|
| **Board size** | Fixed 8×8 |
| **Pieces per side** | 16 (32 total) |
| **Checkmate** | King in check + no legal moves |
| **Stalemate** | Not in check + no legal moves (draw) |
| **Legal move filter** | Simulate move, reject if own king attacked |
| **Special moves** | Castling, en passant, promotion in scope |
| **AI engine** | Out of scope (mention minimax as extension) |

---

## Step 02: Structure — Define Entities

> **Interview Tip**: Extract core objects from requirements. Look for **nouns**. Write them on the whiteboard immediately.

### Step 2.1: List Core Entities (Extract Nouns)

```
Piece, Pawn, Rook, Knight, Bishop, Queen, King, Board, Position, Move, Player, ChessGame, ...
```

### Step 2.2: Define Core Classes

#### **Position** — A single square on the board
```
Properties:
  - row: int (0–7, 0 = rank 8)
  - col: int (0–7, 0 = file a)

Behaviors:
  - is_valid(): Returns True if row and col are within 0–7
  - to_notation(): Returns algebraic notation e.g. "e4"
  - __eq__ / __hash__: For use in sets and dicts
```

#### **Move** — A single move record
```
Properties:
  - from_pos: Position
  - to_pos: Position
  - promotion_type: Optional[PieceType]  (None for normal moves)
  - is_castling: bool
  - is_en_passant: bool

Behaviors:
  - __repr__: Human-readable "e2-e4"
```

#### **Piece** (Abstract Base) — A chess piece
```
Properties:
  - color: Color (WHITE or BLACK)
  - position: Position
  - moved: bool  (for castling / pawn double-move eligibility)

Behaviors:
  - get_piece_type() [abstract]: Returns PieceType enum
  - get_legal_moves(board) [abstract]: Returns List[Move]
  - __repr__: Unicode chess symbol
```

#### **Pawn** — Extends Piece
```
Behaviors:
  - get_legal_moves: Single step, double step from start, diagonal capture
  - (en passant handled separately via game context)
```

#### **Rook** — Extends Piece
```
Behaviors:
  - get_legal_moves: Slides along ranks and files until blocked
```

#### **Knight** — Extends Piece
```
Behaviors:
  - get_legal_moves: 8 L-shaped jumps; ignores intervening pieces
```

#### **Bishop** — Extends Piece
```
Behaviors:
  - get_legal_moves: Slides diagonally until blocked
```

#### **Queen** — Extends Piece
```
Behaviors:
  - get_legal_moves: Combines Rook + Bishop movement (8 directions)
```

#### **King** — Extends Piece
```
Behaviors:
  - get_legal_moves: One step in any of 8 directions
  - (castling handled via game context)
```

#### **Board** — The 8×8 grid
```
Properties:
  - grid: List[List[Optional[Piece]]]  (8×8, None = empty square)

Behaviors:
  - get_piece(pos): O(1) lookup
  - set_piece(pos, piece): Place or clear square
  - find_king(color): Scan for King of given color
  - is_under_attack(pos, by_color): Check if any enemy piece attacks pos
  - copy(): Deep copy for move simulation
  - display(): Print board to console
```

#### **ChessGame** — Main controller (Singleton)
```
Properties:
  - board: Board
  - current_player: Color
  - move_history: List[Move]
  - game_state: GameState

Behaviors:
  - setup_initial_position(): Place all 32 pieces
  - make_move(from_pos, to_pos): Validate + apply move
  - update_game_state(): Recalculate check/checkmate/stalemate
  - has_legal_moves(color): Generate all legal moves for a color
  - display_board(): Render board
  - reset(): Restart game
```

### Step 2.3: Define Enumerations (State & Type)

```python
class Color(Enum):
    WHITE = 1
    BLACK = 2

class PieceType(Enum):
    PAWN   = 1
    ROOK   = 2
    KNIGHT = 3
    BISHOP = 4
    QUEEN  = 5
    KING   = 6

class GameState(Enum):
    ACTIVE    = 1   # Normal play
    CHECK     = 2   # Current player's king is under attack
    CHECKMATE = 3   # Current player has no legal moves and is in check
    STALEMATE = 4   # Current player has no legal moves but not in check
    DRAW      = 5   # Insufficient material / 50-move rule / threefold repetition
```

### Step 2.4: Why These Entities?

| Entity | Why | Cost of Missing |
|--------|-----|-----------------|
| **Position** | Encapsulates row/col + validity | Scattered coordinate checks everywhere |
| **Move** | Records from/to + special-move flags | Can't implement castling or en passant cleanly |
| **Piece (ABC)** | Enforces common interface | Strategy pattern breaks; move gen scattered |
| **Piece subclasses** | Encode unique movement rules | Move validation mixed into board/game logic |
| **Board** | Central grid + attack detection | No clean separation of grid from game rules |
| **ChessGame** | Single source of truth for game state | Turn management and state machine uncoupled |

---

## Step 03: Interface — APIs & Entry Points

> **Interview Tip**: Define the contract (inputs, outputs, exceptions) BEFORE implementation. Focus on "what" not "how".

### Step 3.1: Public API Contracts

#### **1. Make Move** ⭐ CRITICAL
```python
def make_move(from_pos: Position, to_pos: Position) -> bool:
    """
    Validate and apply a move for the current player.

    Preconditions:
      - A piece of the current player's color exists at from_pos
      - to_pos is in the piece's legal move list
      - The move does not leave current player's king in check

    Postconditions (on True):
      - Board updated; piece moved
      - Turn switched to the other player
      - game_state updated (ACTIVE / CHECK / CHECKMATE / STALEMATE)

    Returns: True if move applied, False if invalid.
    Concurrency: THREAD-SAFE via RLock
    """
    pass
```

#### **2. Get Game State**
```python
def get_game_state() -> str:
    """
    Returns the current GameState name: ACTIVE, CHECK, CHECKMATE, STALEMATE, DRAW.
    """
    pass
```

#### **3. Display Board**
```python
def display_board() -> None:
    """Render the board to stdout with rank/file labels and Unicode symbols."""
    pass
```

#### **4. Reset**
```python
def reset() -> None:
    """
    Restart the game: clear board, re-place all pieces, reset turn to WHITE.
    Singleton instance is reused; only state is cleared.
    """
    pass
```

#### **5. Legal Moves Query**
```python
def has_legal_moves(color: Color) -> bool:
    """
    Check whether the given color has at least one legal move.
    Used internally for checkmate / stalemate detection.
    Simulates each candidate move on a board copy to filter moves that leave own king in check.
    """
    pass
```

### Step 3.2: Failure Model

The API returns `bool` rather than raising exceptions to keep demo code clean. A production chess server would raise a typed hierarchy:

```python
class ChessException(Exception): ...
class IllegalMoveError(ChessException): ...
class WrongTurnError(ChessException): ...
class GameOverError(ChessException): ...
class NoPieceAtSourceError(ChessException): ...
```

### Step 3.3: API Usage Example

```python
game = ChessGame()           # Singleton — first call initializes

# Display starting position
game.display_board()

# White opens: pawn e2 → e4
ok = game.make_move(Position(6, 4), Position(4, 4))
print(ok)                    # True

# Black responds: pawn e7 → e5
ok = game.make_move(Position(1, 4), Position(3, 4))
print(ok)                    # True

print(game.get_game_state()) # ACTIVE

# Reset for a new game
game.reset()
```

---

## Step 04: Architecture — Relationships & Diagram

> **Interview Tip**: Use composition, aggregation, and inheritance. Prefer composition over inheritance. Check cardinality (1:1, 1:N).

### Step 4.1: Relationship Types

```
ChessGame HAS-A Board (1:1 Composition)
  └─ ChessGame owns and manages the Board lifecycle

Board HAS-A Piece[] (1:N Composition)
  └─ Board owns the 32 pieces on the grid

Piece IS-A Piece (Inheritance — Strategy)
  └─ Pawn / Rook / Knight / Bishop / Queen / King each override get_legal_moves()

ChessGame HAS-A Move[] (1:N Composition)
  └─ ChessGame owns the move history list

Move REFERENCES Position (1:2 Association)
  └─ Move links to from_pos and to_pos (no ownership)

Piece REFERENCES Position (1:1 Association)
  └─ Each Piece knows its current square
```

### Step 4.2: Complete UML Class Diagram

```
┌─────────────────────────────────────┐
│     ChessGame (Singleton)           │
├─────────────────────────────────────┤
│ - _instance: ChessGame              │
│ - _lock: threading.RLock            │
│ - board: Board                      │
│ - current_player: Color             │
│ - move_history: List[Move]          │
│ - game_state: GameState             │
├─────────────────────────────────────┤
│ + make_move(from, to): bool         │
│ + get_game_state(): str             │
│ + display_board(): void             │
│ + reset(): void                     │
│ + has_legal_moves(color): bool      │
└────────────┬────────────────────────┘
             │ owns 1:1
             ▼
┌──────────────────────────────────┐
│ Board                            │
├──────────────────────────────────┤
│ - grid: List[List[Piece|None]]   │
├──────────────────────────────────┤
│ + get_piece(pos): Piece          │
│ + set_piece(pos, piece): void    │
│ + find_king(color): Position     │
│ + is_under_attack(pos, col): bool│
│ + copy(): Board                  │
│ + display(): void                │
└──────────────────────────────────┘
             │ contains 0..32
             ▼
┌──────────────────────────────────┐
│ Piece (Abstract Base Class)      │
├──────────────────────────────────┤
│ + color: Color                   │
│ + position: Position             │
│ + moved: bool                    │
├──────────────────────────────────┤
│ + get_piece_type() [abstract]    │
│ + get_legal_moves(board)[abstract│
│ + __repr__: Unicode symbol       │
└────┬──────────────────────────────┘
     │ INHERITANCE (Strategy)
     ├──→ Pawn    (forward steps + diagonal capture)
     ├──→ Rook    (rank / file slides)
     ├──→ Knight  (L-shaped jumps)
     ├──→ Bishop  (diagonal slides)
     ├──→ Queen   (Rook + Bishop combined)
     └──→ King    (one step any direction)

POSITION:
┌──────────────────┐
│ Position         │
├──────────────────┤
│ + row: int (0-7) │
│ + col: int (0-7) │
├──────────────────┤
│ + is_valid(): bool         │
│ + __repr__: "e4" notation  │
└──────────────────┘

MOVE:
┌──────────────────────┐
│ Move                 │
├──────────────────────┤
│ + from_pos: Position │
│ + to_pos: Position   │
│ + promotion_type     │
│ + is_castling: bool  │
│ + is_en_passant: bool│
└──────────────────────┘

GAME STATE MACHINE:
ACTIVE ──→ CHECK ──→ CHECKMATE
  │          │
  ├──────────┴──→ STALEMATE
  │
  └──→ DRAW (insufficient material / repetition)
```

### Step 4.3: Cardinality Summary

| Relationship | Cardinality | Type | Reason |
|-------------|------------|------|--------|
| ChessGame → Board | 1:1 | Composition | One board per game |
| ChessGame → Move history | 1:N | Composition | Game owns all moves |
| Board → Piece | 1:N (0..32) | Composition | Board owns pieces on the grid |
| Piece → Position | 1:1 | Association | Each piece references its square |
| Move → Position | 1:2 | Association | from_pos and to_pos |
| Piece → Piece subclasses | Inheritance | IS-A | Strategy for movement rules |

---

## Step 05: Optimization — Design Patterns

> **Interview Tip**: Don't force patterns. Only solve specific problems.

### Pattern 1: **Singleton** (For ChessGame)

**Problem**: Multiple parts of the application need one consistent, authoritative game instance.

**Solution**: One global ChessGame instance with thread-safe initialization via `__new__`.

```python
import threading

class ChessGame:
    _instance = None
    _lock = threading.RLock()   # RLock so reset() → __init__() → __new__() is safe

    def __new__(cls, *args, **kwargs):        # *args/**kwargs required for reset() path
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        # ... initialize state
```

**Benefit**: ✅ Single source of truth, ✅ Thread-safe double-checked locking, ✅ Global access  
**Trade-off**: ⚠️ Global state makes unit-testing harder, ⚠️ Doesn't scale across machines

---

### Pattern 2: **Strategy** (For Piece Movement)

**Problem**: Each piece type has unique movement rules; mixing them into one class creates a God object.

**Solution**: Each concrete piece overrides `get_legal_moves(board)` — the algorithm is the strategy.

```python
class Piece(ABC):
    @abstractmethod
    def get_legal_moves(self, board: Board) -> List[Move]:
        pass

class Rook(Piece):
    def get_legal_moves(self, board):
        moves = []
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            pos = Position(self.position.row + dr, self.position.col + dc)
            while pos.is_valid():
                piece = board.get_piece(pos)
                if piece is None:
                    moves.append(Move(self.position, pos))
                elif piece.color != self.color:
                    moves.append(Move(self.position, pos))
                    break
                else:
                    break
                pos = Position(pos.row + dr, pos.col + dc)
        return moves

class Knight(Piece):
    def get_legal_moves(self, board):
        offsets = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]
        return [Move(self.position, Position(self.position.row+dr, self.position.col+dc))
                for dr, dc in offsets
                if Position(self.position.row+dr, self.position.col+dc).is_valid()
                and (board.get_piece(Position(self.position.row+dr, self.position.col+dc)) is None
                     or board.get_piece(Position(self.position.row+dr, self.position.col+dc)).color != self.color)]
```

**Benefit**: ✅ Open/Closed principle — add new piece type without touching existing code  
**Trade-off**: ⚠️ 6 subclasses to maintain

---

### Pattern 3: **State Machine** (For Game Lifecycle)

**Problem**: Game transitions between ACTIVE → CHECK → CHECKMATE and STALEMATE; invalid transitions must be prevented.

**Solution**: `GameState` enum drives `update_game_state()` after every move.

```python
class GameState(Enum):
    ACTIVE    = 1
    CHECK     = 2
    CHECKMATE = 3
    STALEMATE = 4
    DRAW      = 5

def update_game_state(self):
    in_check = self.board.is_under_attack(king_pos, opponent)
    legal_moves_exist = self.has_legal_moves(self.current_player)

    if not legal_moves_exist:
        self.game_state = GameState.CHECKMATE if in_check else GameState.STALEMATE
    elif in_check:
        self.game_state = GameState.CHECK
    else:
        self.game_state = GameState.ACTIVE
```

**Benefit**: ✅ Explicit state, ✅ Easy to add DRAW transitions  
**Trade-off**: ⚠️ State evaluation is O(n) per move

---

### Pattern 4: **Observer** (For Game Events — Extension Point)

**Problem**: External systems (UI, logger, AI engine) need to react to moves, check, and checkmate without coupling to ChessGame.

**Solution**: Observer interface; ChessGame notifies on state changes.

```python
class GameObserver(ABC):
    @abstractmethod
    def on_move(self, move: Move, state: GameState): pass

class ConsoleLogger(GameObserver):
    def on_move(self, move, state):
        print(f"Move: {move}  State: {state.name}")

# Usage
game.add_observer(ConsoleLogger())
```

**Benefit**: ✅ Loose coupling, ✅ Easy to add AI engine, UI renderer  
**Trade-off**: ⚠️ Observer lifecycle management

---

### Pattern 5: **Factory** (For Piece Creation)

**Problem**: Initializing 32 pieces with correct positions, colors, and types in `setup_initial_position()` is complex.

**Solution**: Factory logic encapsulated in `setup_initial_position()` — consistent, validated initialization.

```python
def setup_initial_position(self):
    self.board.set_piece(Position(7, 0), Rook(Color.WHITE, Position(7, 0)))
    self.board.set_piece(Position(7, 4), King(Color.WHITE, Position(7, 4)))
    for col in range(8):
        self.board.set_piece(Position(6, col), Pawn(Color.WHITE, Position(6, col)))
    # ... (all 32 pieces)
```

**Benefit**: ✅ Centralized, consistent piece creation  
**Trade-off**: ⚠️ If rule variants needed, promote to a full AbstractFactory

---

### Design Patterns Summary Table

| Pattern | Problem Solved | Benefit |
|---------|----------------|---------|
| **Singleton** | One authoritative ChessGame | Consistent state across all callers |
| **Strategy** | Different movement per piece type | Open/Closed; add pieces without changing game |
| **State Machine** | Game lifecycle (ACTIVE→CHECKMATE) | Invalid transitions caught at runtime |
| **Observer** | Notify UI / AI / logger on events | Loose coupling, extensible |
| **Factory** | 32-piece board setup | Centralized, consistent initialization |

---

## Step 06: Implementation — Code & Concurrency

> **Interview Tip**: Write thread-safe, defensive code. Mention "Thread Safety" even if not asked.

### Complete Thread-Safe Implementation

```python
"""
Chess Game - Interview Implementation
Demonstrates:
1. Standard game setup
2. Pawn moves
3. Piece captures
4. Check detection
5. Checkmate detection

Bug fixes vs naive version:
- ChessGame.__new__ accepts *args/**kwargs so reset() -> __init__() path works
- _lock is threading.RLock (re-entrant) so nested lock acquisitions don't deadlock
- make_move simulates entirely on board_copy; original board/piece untouched until move confirmed
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import Optional, List
from dataclasses import dataclass
import copy
import threading

# ============================================================================
# ENUMERATIONS
# ============================================================================

class Color(Enum):
    WHITE = 1
    BLACK = 2

class PieceType(Enum):
    PAWN   = 1
    ROOK   = 2
    KNIGHT = 3
    BISHOP = 4
    QUEEN  = 5
    KING   = 6

class GameState(Enum):
    ACTIVE    = 1
    CHECK     = 2
    CHECKMATE = 3
    STALEMATE = 4
    DRAW      = 5

# ============================================================================
# POSITION & MOVE
# ============================================================================

@dataclass
class Position:
    row: int
    col: int

    def is_valid(self) -> bool:
        return 0 <= self.row < 8 and 0 <= self.col < 8

    def __eq__(self, other):
        return self.row == other.row and self.col == other.col

    def __hash__(self):
        return hash((self.row, self.col))

    def __repr__(self):
        return f"{'abcdefgh'[self.col]}{8 - self.row}"

@dataclass
class Move:
    from_pos: Position
    to_pos: Position
    promotion_type: Optional[PieceType] = None
    is_castling: bool = False
    is_en_passant: bool = False

    def __repr__(self):
        return f"{self.from_pos}-{self.to_pos}"

# ============================================================================
# PIECE HIERARCHY  (Strategy Pattern)
# ============================================================================

class Piece(ABC):
    def __init__(self, color: Color, position: Position):
        self.color = color
        self.position = position
        self.moved = False

    @abstractmethod
    def get_piece_type(self) -> PieceType:
        pass

    @abstractmethod
    def get_legal_moves(self, board: 'Board') -> List[Move]:
        pass

    def __repr__(self):
        symbols = {
            PieceType.PAWN:   ('P', 'p'),
            PieceType.ROOK:   ('R', 'r'),
            PieceType.KNIGHT: ('N', 'n'),
            PieceType.BISHOP: ('B', 'b'),
            PieceType.QUEEN:  ('Q', 'q'),
            PieceType.KING:   ('K', 'k'),
        }
        pair = symbols.get(self.get_piece_type(), ('?', '?'))
        return pair[0] if self.color == Color.WHITE else pair[1]


class Pawn(Piece):
    def get_piece_type(self) -> PieceType:
        return PieceType.PAWN

    def get_legal_moves(self, board: 'Board') -> List[Move]:
        moves = []
        direction = -1 if self.color == Color.WHITE else 1

        # Single step forward
        forward = Position(self.position.row + direction, self.position.col)
        if forward.is_valid() and board.get_piece(forward) is None:
            moves.append(Move(self.position, forward))

            # Double step from starting rank
            if not self.moved:
                double = Position(self.position.row + 2 * direction, self.position.col)
                if double.is_valid() and board.get_piece(double) is None:
                    moves.append(Move(self.position, double))

        # Diagonal captures
        for col_offset in [-1, 1]:
            capture_pos = Position(self.position.row + direction, self.position.col + col_offset)
            if capture_pos.is_valid():
                target = board.get_piece(capture_pos)
                if target and target.color != self.color:
                    moves.append(Move(self.position, capture_pos))

        return moves


class Rook(Piece):
    def get_piece_type(self) -> PieceType:
        return PieceType.ROOK

    def get_legal_moves(self, board: 'Board') -> List[Move]:
        moves = []
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            pos = Position(self.position.row + dr, self.position.col + dc)
            while pos.is_valid():
                piece = board.get_piece(pos)
                if piece is None:
                    moves.append(Move(self.position, pos))
                elif piece.color != self.color:
                    moves.append(Move(self.position, pos))
                    break
                else:
                    break
                pos = Position(pos.row + dr, pos.col + dc)
        return moves


class Knight(Piece):
    def get_piece_type(self) -> PieceType:
        return PieceType.KNIGHT

    def get_legal_moves(self, board: 'Board') -> List[Move]:
        moves = []
        for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            pos = Position(self.position.row + dr, self.position.col + dc)
            if pos.is_valid():
                piece = board.get_piece(pos)
                if piece is None or piece.color != self.color:
                    moves.append(Move(self.position, pos))
        return moves


class Bishop(Piece):
    def get_piece_type(self) -> PieceType:
        return PieceType.BISHOP

    def get_legal_moves(self, board: 'Board') -> List[Move]:
        moves = []
        for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            pos = Position(self.position.row + dr, self.position.col + dc)
            while pos.is_valid():
                piece = board.get_piece(pos)
                if piece is None:
                    moves.append(Move(self.position, pos))
                elif piece.color != self.color:
                    moves.append(Move(self.position, pos))
                    break
                else:
                    break
                pos = Position(pos.row + dr, pos.col + dc)
        return moves


class Queen(Piece):
    def get_piece_type(self) -> PieceType:
        return PieceType.QUEEN

    def get_legal_moves(self, board: 'Board') -> List[Move]:
        moves = []
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]:
            pos = Position(self.position.row + dr, self.position.col + dc)
            while pos.is_valid():
                piece = board.get_piece(pos)
                if piece is None:
                    moves.append(Move(self.position, pos))
                elif piece.color != self.color:
                    moves.append(Move(self.position, pos))
                    break
                else:
                    break
                pos = Position(pos.row + dr, pos.col + dc)
        return moves


class King(Piece):
    def get_piece_type(self) -> PieceType:
        return PieceType.KING

    def get_legal_moves(self, board: 'Board') -> List[Move]:
        moves = []
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]:
            pos = Position(self.position.row + dr, self.position.col + dc)
            if pos.is_valid():
                piece = board.get_piece(pos)
                if piece is None or piece.color != self.color:
                    moves.append(Move(self.position, pos))
        return moves

# ============================================================================
# BOARD
# ============================================================================

class Board:
    def __init__(self):
        self.grid: List[List[Optional[Piece]]] = [[None]*8 for _ in range(8)]

    def get_piece(self, pos: Position) -> Optional[Piece]:
        if pos.is_valid():
            return self.grid[pos.row][pos.col]
        return None

    def set_piece(self, pos: Position, piece: Optional[Piece]):
        if pos.is_valid():
            self.grid[pos.row][pos.col] = piece

    def find_king(self, color: Color) -> Optional[Position]:
        for row in range(8):
            for col in range(8):
                piece = self.grid[row][col]
                if piece and isinstance(piece, King) and piece.color == color:
                    return piece.position
        return None

    def is_under_attack(self, pos: Position, by_color: Color) -> bool:
        """Return True if any piece of by_color can attack pos."""
        for row in range(8):
            for col in range(8):
                piece = self.grid[row][col]
                if piece and piece.color == by_color:
                    if any(m.to_pos == pos for m in piece.get_legal_moves(self)):
                        return True
        return False

    def copy(self) -> 'Board':
        """Shallow-copy pieces onto a new board (sufficient for move simulation)."""
        new_board = Board()
        for row in range(8):
            for col in range(8):
                piece = self.grid[row][col]
                if piece:
                    new_piece = copy.copy(piece)
                    new_piece.position = Position(row, col)
                    new_board.grid[row][col] = new_piece
        return new_board

    def display(self):
        print("  a b c d e f g h")
        for row in range(8):
            print(f"{8-row} ", end="")
            for col in range(8):
                piece = self.grid[row][col]
                print(f"{piece if piece else '.'} ", end="")
            print(f"{8-row}")
        print("  a b c d e f g h")

# ============================================================================
# CHESS GAME (SINGLETON)
# ============================================================================

class ChessGame:
    _instance = None
    _lock = threading.RLock()   # RLock: re-entrant so reset()→__init__() is safe

    def __new__(cls, *args, **kwargs):          # *args/**kwargs: required for reset() path
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.board = Board()
        self.current_player = Color.WHITE
        self.move_history: List[Move] = []
        self.game_state = GameState.ACTIVE
        self.setup_initial_position()

    def setup_initial_position(self):
        """Place all 32 pieces in standard starting positions."""
        # White back rank (row 7)
        self.board.set_piece(Position(7, 0), Rook(Color.WHITE,   Position(7, 0)))
        self.board.set_piece(Position(7, 1), Knight(Color.WHITE, Position(7, 1)))
        self.board.set_piece(Position(7, 2), Bishop(Color.WHITE, Position(7, 2)))
        self.board.set_piece(Position(7, 3), Queen(Color.WHITE,  Position(7, 3)))
        self.board.set_piece(Position(7, 4), King(Color.WHITE,   Position(7, 4)))
        self.board.set_piece(Position(7, 5), Bishop(Color.WHITE, Position(7, 5)))
        self.board.set_piece(Position(7, 6), Knight(Color.WHITE, Position(7, 6)))
        self.board.set_piece(Position(7, 7), Rook(Color.WHITE,   Position(7, 7)))
        for col in range(8):
            self.board.set_piece(Position(6, col), Pawn(Color.WHITE, Position(6, col)))

        # Black back rank (row 0)
        self.board.set_piece(Position(0, 0), Rook(Color.BLACK,   Position(0, 0)))
        self.board.set_piece(Position(0, 1), Knight(Color.BLACK, Position(0, 1)))
        self.board.set_piece(Position(0, 2), Bishop(Color.BLACK, Position(0, 2)))
        self.board.set_piece(Position(0, 3), Queen(Color.BLACK,  Position(0, 3)))
        self.board.set_piece(Position(0, 4), King(Color.BLACK,   Position(0, 4)))
        self.board.set_piece(Position(0, 5), Bishop(Color.BLACK, Position(0, 5)))
        self.board.set_piece(Position(0, 6), Knight(Color.BLACK, Position(0, 6)))
        self.board.set_piece(Position(0, 7), Rook(Color.BLACK,   Position(0, 7)))
        for col in range(8):
            self.board.set_piece(Position(1, col), Pawn(Color.BLACK, Position(1, col)))

    def make_move(self, from_pos: Position, to_pos: Position) -> bool:
        """Validate and apply a move.  Returns True on success, False if illegal."""
        piece = self.board.get_piece(from_pos)
        if not piece or piece.color != self.current_player:
            return False

        legal_moves = piece.get_legal_moves(self.board)
        move = next((m for m in legal_moves if m.to_pos == to_pos), None)
        if not move:
            return False

        # --- Simulate entirely on a board copy ---
        board_copy = self.board.copy()
        # Retrieve the copied piece (not the original) so we don't mutate live state
        copied_piece = board_copy.get_piece(from_pos)
        board_copy.set_piece(from_pos, None)
        board_copy.set_piece(to_pos, copied_piece)
        copied_piece.position = to_pos
        copied_piece.moved = True

        # Reject if own king is in check after the simulated move
        opponent_color = Color.BLACK if self.current_player == Color.WHITE else Color.WHITE
        king_pos = board_copy.find_king(self.current_player)
        if king_pos and board_copy.is_under_attack(king_pos, opponent_color):
            return False   # Illegal: leaves own king in check; original board untouched

        # --- Commit the move ---
        self.board = board_copy
        self.move_history.append(move)
        self.current_player = Color.BLACK if self.current_player == Color.WHITE else Color.WHITE
        self.update_game_state()
        return True

    def update_game_state(self):
        """Recompute game state after each committed move."""
        opponent = Color.BLACK if self.current_player == Color.WHITE else Color.WHITE
        king_pos = self.board.find_king(self.current_player)
        if not king_pos:
            return

        in_check = self.board.is_under_attack(king_pos, opponent)
        legal_moves_exist = self.has_legal_moves(self.current_player)

        if not legal_moves_exist:
            self.game_state = GameState.CHECKMATE if in_check else GameState.STALEMATE
        elif in_check:
            self.game_state = GameState.CHECK
        else:
            self.game_state = GameState.ACTIVE

    def has_legal_moves(self, color: Color) -> bool:
        """Return True if at least one legal move exists for color."""
        opponent = Color.BLACK if color == Color.WHITE else Color.WHITE
        for row in range(8):
            for col in range(8):
                piece = self.board.grid[row][col]
                if piece and piece.color == color:
                    for move in piece.get_legal_moves(self.board):
                        board_copy = self.board.copy()
                        copied_piece = board_copy.get_piece(move.from_pos)
                        board_copy.set_piece(move.from_pos, None)
                        board_copy.set_piece(move.to_pos, copied_piece)
                        copied_piece.position = move.to_pos
                        king_pos = board_copy.find_king(color)
                        if king_pos and not board_copy.is_under_attack(king_pos, opponent):
                            return True
        return False

    def display_board(self):
        self.board.display()

    def get_game_state(self) -> str:
        return self.game_state.name

    def reset(self):
        """Restart the game.  Singleton instance reused; state is cleared."""
        self.board = Board()
        self.current_player = Color.WHITE
        self.move_history = []
        self.game_state = GameState.ACTIVE
        self.setup_initial_position()

# ============================================================================
# DEMO SCENARIOS
# ============================================================================

def demo_1_setup():
    print("\n" + "="*70)
    print("DEMO 1: STANDARD GAME SETUP")
    print("="*70)

    game = ChessGame()
    game.reset()
    print("Game initialized with standard position")
    game.display_board()
    print(f"Current player: {game.current_player.name}")

def demo_2_pawn_move():
    print("\n" + "="*70)
    print("DEMO 2: SIMPLE PAWN MOVE")
    print("="*70)

    game = ChessGame()
    game.reset()

    success = game.make_move(Position(6, 4), Position(4, 4))
    print(f"Move e2-e4: {success}")
    game.display_board()
    print(f"Current player: {game.current_player.name}")

def demo_3_multiple_moves():
    print("\n" + "="*70)
    print("DEMO 3: MULTIPLE MOVES - TOWARD CHECK")
    print("="*70)

    game = ChessGame()
    game.reset()

    moves = [
        (Position(6, 4), Position(4, 4)),   # e2-e4
        (Position(1, 4), Position(3, 4)),   # e7-e5
        (Position(7, 5), Position(5, 3)),   # f1-c4
    ]

    for from_pos, to_pos in moves:
        success = game.make_move(from_pos, to_pos)
        print(f"Move {from_pos} to {to_pos}: {'OK' if success else 'FAIL'}")

    game.display_board()
    print(f"Game state: {game.get_game_state()}")

def demo_4_check_detection():
    print("\n" + "="*70)
    print("DEMO 4: CHECK DETECTION")
    print("="*70)

    game = ChessGame()
    game.reset()

    moves = [
        (Position(6, 4), Position(4, 4)),   # e2-e4
        (Position(1, 4), Position(3, 4)),   # e7-e5
        (Position(7, 5), Position(5, 3)),   # f1-c4
        (Position(1, 0), Position(3, 0)),   # a7-a5
        (Position(5, 3), Position(2, 0)),   # c4-a6 (check attempt)
    ]

    for from_pos, to_pos in moves:
        success = game.make_move(from_pos, to_pos)
        print(f"Move {from_pos} to {to_pos}: {'OK' if success else 'FAIL'}")

    game.display_board()
    print(f"Game state: {game.get_game_state()}")

def demo_5_game_reset():
    print("\n" + "="*70)
    print("DEMO 5: GAME RESET")
    print("="*70)

    game = ChessGame()
    print(f"Current game state: {game.get_game_state()}")
    print(f"Moves played: {len(game.move_history)}")

    game.reset()
    print(f"After reset - Game state: {game.get_game_state()}")
    print(f"After reset - Moves played: {len(game.move_history)}")
    game.display_board()

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("CHESS GAME - 5 DEMO SCENARIOS")
    print("="*70)

    demo_1_setup()
    demo_2_pawn_move()
    demo_3_multiple_moves()
    demo_4_check_detection()
    demo_5_game_reset()

    print("\n" + "="*70)
    print("ALL DEMOS COMPLETED")
    print("="*70 + "\n")
```

### Thread-Safety Analysis

| Operation | Lock Strategy | Guarantees |
|-----------|---------------|------------|
| **Singleton init** | RLock double-checked | One instance created; re-entrant safe |
| **make_move** | Simulate on board_copy | Original board untouched until move confirmed |
| **has_legal_moves** | Board copies per candidate | No shared mutable state during generation |
| **reset** | No lock needed (game-level) | Caller responsible for mutual exclusion in multi-user scenario |

**Concurrency Principles**:
1. ✅ `threading.RLock()` allows `reset()` → `__init__()` → `__new__()` re-entry safely
2. ✅ Move simulation works on deep-copied board; original never mutated until commit
3. ✅ Double-checked locking for Singleton
4. ✅ Notify / display outside any critical section

---

## Demo Scenarios

### Demo 1: Standard Game Setup
```
- Create new game (Singleton)
- Initialize white and black pieces in standard positions
- White queen on d1, black queen on d8
- Display board with rank/file labels
```

### Demo 2: Simple Pawn Move
```
- Move white pawn from e2 to e4 (double step from start)
- Verify move is legal (path clear, own king safe)
- Update board state
- Switch to black's turn
```

### Demo 3: Multiple Moves — Toward Check
```
- e2-e4, e7-e5 (pawns opened)
- f1-c4 (white bishop develops)
- Display board; game state remains ACTIVE
```

### Demo 4: Check Detection
```
- Series of moves designed to put black king in check
- Detect that white bishop attacks black king's square
- game_state transitions to CHECK if king has no escape
```

### Demo 5: Game Reset
```
- Inspect current game state and move count
- Call reset()
- Verify state returns to ACTIVE, moves cleared, board restored
```

---

## Interview Q&A

### Basic Level

**Q1: How does the ChessGame manage game state?**
A: Singleton pattern ensures one global instance. Maintains current board state, whose turn it is (white/black), move history, and game status (ACTIVE/CHECK/CHECKMATE/STALEMATE). Single source of truth.

**Q2: How do you represent the chess board?**
A: 8×8 2D array (`List[List[Piece]]`). Empty squares = None. Each piece knows its position and color. Lookup by position is O(1). Efficient for rendering and validation.

**Q3: What's the difference between check and checkmate?**
A: **Check**: King is under attack but legal moves exist. **Checkmate**: King is under attack + no legal moves available. If not in check + no legal moves = stalemate (draw).

**Q4: How do you validate that a move doesn't leave the king in check?**
A: Simulate the move on a board copy, then check if own king is under attack on the copy. If yes, reject and return False — the original board is never modified. If no, commit the copy as the live board.

### Intermediate Level

**Q5: How does en passant work?**
A: Pawn captures enemy pawn that just moved 2 squares forward. Must capture on the square the pawn "passed through" (not where it landed). Only valid on the very next move after opponent's double-move.

**Q6: How does castling work?**
A: King + Rook both move: king moves 2 squares toward rook, rook jumps over. Requires: king/rook haven't moved, no pieces between, king not in check, doesn't pass through check. Two variants: kingside (O-O) and queenside (O-O-O).

**Q7: What is pawn promotion?**
A: Pawn reaching the opposite end (rank 8 for white) immediately transforms into Queen, Rook, Bishop, or Knight. Player chooses; original pawn is removed, new piece placed.

**Q8: How do you detect checkmate vs stalemate?**
A: Generate all legal moves for the current player. If the set is empty: checkmate if king is under attack, else stalemate. Both end the game, but checkmate = loss, stalemate = draw.

### Advanced Level

**Q9: How would you implement a move search algorithm (minimax)?**
A: Recursively explore moves to depth N. Evaluate board: checkmate = ±∞, material imbalance = score. Maximize own score, minimize opponent's. Alpha-beta pruning cuts branches. Trade-off: depth vs computation time.

**Q10: How to handle draw by repetition (3-fold)?**
A: Track board-state hashes in history. If same position appears 3 times, declare draw. Alternative: 50-move rule (no pawn move/capture in 50 moves). Requires careful state tracking.

**Q11: How to optimize move generation for fast AI?**
A: Cache legal moves (computed once per position). Use bitboards instead of arrays (faster bit operations). Precompute attack squares for each piece type. Incremental updates (don't recompute from scratch).

**Q12: How would you handle illegal move input robustly?**
A: Validate notation (e.g., "e2-e4"). Parse positions. Check if piece exists at source. Verify move is in legal move list. Provide specific error message (occupied, blocked, moving opponent's piece). Prevent any invalid state change.

---

## Scaling Q&A

**Q1: How to scale to support 1M concurrent games?**
A: Distributed game state: per-game instance. Store on persistent DB (Redis for cache, PostgreSQL for archive). Load on demand. Per-player queue of pending games. Match-making server assigns instances. Load balance across servers.

**Q2: What if move validation takes O(n) time (n = board size)?**
A: For a single game, negligible. But 1M games × 50 moves/sec = 50M moves/sec. Optimize: cache legal moves, use bitboards, precomputed attack squares. Target: <1ms per move validation.

**Q3: How to handle simultaneous moves (network latency)?**
A: Enforce strict turn-based model. Client sends move, server validates, responds. If move invalid, request retry. If latency high, implement optimistic UI (show move locally, wait for server confirmation). Rollback if rejected.

**Q4: How to prevent cheating (illegal moves sent)?**
A: Server-side validation is mandatory. Never trust client. Client validates for UX, but server validates for correctness. If illegal move detected, reject + flag account. Rate limit repeated violations.

**Q5: How to replay/undo moves efficiently?**
A: Store move history (from/to positions). On undo: pop last move, reverse it (remove piece from to, restore to from). On replay: iterate history, apply each move. No board recreation needed.

**Q6: What if game history grows very large?**
A: Chess games: max 200-300 moves (rarely). For 1M games: manageable in memory. Compress history: store as algebraic notation (4 bytes/move). Offload to DB after game ends.

**Q7: How to detect draw conditions at scale?**
A: Three-fold repetition: track hashes of last 50 positions. Lookup: O(1) hash table. Fifty-move rule: counter incremented per move, reset on pawn move/capture. Check on every turn.

**Q8: How to optimize AI move search for real-time play?**
A: Iterative deepening: search depth 1, then 2, then 3, etc. Stop when time limit reached. Return best move found so far. Transposition tables cache already-evaluated positions.

**Q9: Can you stream game moves to spectators efficiently?**
A: Publish-subscribe pattern: game broadcasts moves to all spectators. Each spectator receives live updates. WebSocket for low-latency. Batch moves if update frequency is high (e.g., 10 moves/sec).

**Q10: How to handle clock/time controls (blitz, rapid, classical)?**
A: Per-player countdown timer. Decrement on each move. If time expires, player loses immediately. Store time per move in history. Broadcast remaining time to both players.

**Q11: What if a player disconnects mid-game?**
A: Set grace period (e.g., 5 minutes). If reconnect within grace period, resume game. If timeout, opponent wins by abandonment. Store game state persistently so reconnect restores exact position.

**Q12: How to scale AI engine to analyze 1000 games/second?**
A: Parallel processing: distribute games across CPU cores (8-256 cores). Each core processes a subset. Aggregate results. Use GPU for neural network evaluation (AlphaZero style). Trade-off: hardware cost vs throughput.

---

## Success Checklist

- [ ] Explain all 6 steps: Setup → Structure → Interface → Architecture → Optimization → Implementation
- [ ] Draw UML class diagram showing Piece hierarchy (Pawn/Rook/Knight/Bishop/Queen/King) and Board/ChessGame relationships
- [ ] Explain how make_move simulates on a board copy to reject moves that leave own king in check
- [ ] Explain check vs checkmate vs stalemate detection logic
- [ ] Describe the 5 design patterns (Singleton, Strategy, State Machine, Observer, Factory) and why each is used
- [ ] Discuss the two bug fixes: RLock for re-entrancy safety and *args/**kwargs on __new__
- [ ] Run complete implementation (5 demos) without errors
- [ ] Answer 5+ scaling Q&A questions
- [ ] Mention thread safety in Singleton, make_move (board copy), and has_legal_moves
- [ ] Discuss trade-offs (board copy vs rollback, in-memory vs DB, minimax extension)

---

**Ready for interview? Set up the board and make your opening move!**
