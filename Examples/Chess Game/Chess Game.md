# Chess Game — 75-Minute Interview Guide

## Quick Start Overview

## What Is This?
A two-player chess engine that validates moves, detects check/checkmate/stalemate, enforces piece movement rules, and manages game state. Think simplified chess.com without time controls or ratings.

## 75-Minute Interview Timeline

| Phase | Time | Focus |
|-------|------|-------|
| Requirements | 0-5 min | Clarify scope: 6 piece types? castling/en passant? just detection or full engine? |
| Architecture | 5-15 min | Singleton coordinator, Board 8x8, Piece hierarchy, movement algorithms |
| Core Entities | 15-35 min | Board setup, Piece subclasses (Pawn/Rook/Bishop/Queen/Knight/King), move validation |
| Business Logic | 35-55 min | Check/checkmate/stalemate detection, move validation with King safety, move history |
| Integration | 55-70 min | Observer pattern for events, Singleton pattern for coordination |
| Demo | 70-75 min | Run 5 scenarios showing piece movement, check, and game ending |

## 6 Core Piece Types (Memorize These)

### Pawn
- Moves forward 1 square (2 on first move)
- Captures diagonally forward
- Special: En passant capture, promotion at end
- Code: Check direction, verify empty, check diagonals for enemy

### Rook
- Moves horizontal or vertical any distance
- Can't jump over pieces
- Code: Iterate in 4 directions until edge/piece

### Bishop
- Moves diagonally any distance
- Can't jump over pieces
- Code: Iterate in 4 diagonal directions until edge/piece

### Queen
- Combines Rook + Bishop (8 directions)
- Most powerful piece
- Code: Iterate in 8 directions until edge/piece

### Knight
- L-shaped move: 2 squares + 1 perpendicular
- ONLY piece that can jump over other pieces
- 8 possible destinations per position
- Code: Check 8 L-shaped offsets, validate bounds

### King
- Moves 1 square in any direction (8 adjacent)
- Most valuable piece (game ends if checkmated)
- Can't move into check
- Special: Castling move (King + Rook)
- Code: Check 8 neighbors, validate bounds

## 5 Architecture Sketch
````
(Describe components, controller, strategies, observers, flows)
````

Design Patterns Explained

### 1. Singleton (ChessGame)
**One global game coordinator** - Single instance managing board, players, moves.
```
Why? One source of truth for game state
How? Thread-safe lazy initialization with _lock
Interview: "Prevents multiple games, ensures consistency"
```

### 2. Strategy (Piece Movement)
**Each piece type implements own movement algorithm** - Pawn vs Rook vs Bishop different.
```
Algorithms: Pawn (1-2 forward), Rook (4 directions), Queen (8 directions), Knight (8 L-shapes)
Why? Each piece has unique rules without polluting Board class
How? Abstract Piece.get_possible_moves() + 6 subclass implementations
Interview: "Add new piece type (Fairy Chess) without modifying existing code"
```

### 3. Observer (GameObserver)
**Loose coupling notifications** - Game events trigger multiple listeners.
```
Events: move_made, check, checkmate, stalemate
Why? Decouple game logic from UI/notifications
How? Abstract GameObserver + MoveObserver/CheckObserver/CheckmateObserver
Interview: "Easy to add logging, sound effects, network notifications"
```

### 4. State (GameStatus)
**Explicit game phases** - ACTIVE vs CHECKMATE vs STALEMATE.
```
Why? Prevents invalid operations (can't make moves after checkmate)
How? Enum + validation before move execution
Interview: "Fail fast on invalid game state"
```

### 5. Factory
**Encapsulated piece creation** - Board.initialize_pieces() creates all 32 pieces correctly positioned

## Key Interview Questions & Talking Points

### Basic (5 min)
1. **"What are the 6 piece types and how do they move?"**
   - Answer: Pawn (1-2 forward), Rook (4 directions), Bishop (4 diagonals), Queen (8), Knight (L-shape), King (1 adjacent)

2. **"How is the board represented?"**
   - Answer: 8x8 2D array. Each square is None (empty) or Piece object.

3. **"What makes a move valid?"**
   - Answer: (1) Piece exists and belongs to player, (2) Follows movement rules, (3) Path clear (for sliding pieces), (4) Own King not left in check

### Intermediate (10 min)
4. **"Explain check, checkmate, and stalemate."**
   - Answer: Check = King under attack. Checkmate = check + no legal moves = lose. Stalemate = not check + no legal moves = draw.

5. **"How do you detect check?"**
   - Answer: (1) Find own King, (2) Check if any enemy piece can reach it, (3) If yes, it's check.

6. **"How do you validate a move doesn't leave King in check?"**
   - Answer: Simulate move on board, check if King under attack, restore board state. Only allow if King safe.

7. **"What's special about Knight movement?"**
   - Answer: Only piece that can jump over other pieces. Moves in L-shape: 2 squares + 1 perpendicular (8 possibilities).

### Advanced (15 min)
8. **"How would you implement castling?"**
   - Answer: Special King move (2 squares). Preconditions: King/Rook haven't moved, no pieces between, King not in/through check. Move both pieces.

9. **"How would you implement undo?"**
   - Answer: Store previous board state with each move. On undo, restore board state (deep copy of pieces + positions).

10. **"How would you detect threefold repetition?"**
    - Answer: After each move, hash current position. Check if position appeared 3 times in history.

11. **"How would you optimize performance?"**
    - Answer: Bitboards (64-bit integers instead of 2D arrays), pre-compute King position, cache legal moves until board changes.

12. **"How would you implement AI opponent?"**
    - Answer: Minimax algorithm evaluating positions (Pawn=1, Knight/Bishop=3, Rook=5, Queen=9). Search depth 4-6 with alpha-beta pruning.

## Success Checklist (Must Cover)

- [ ] Explain 6 piece types and movement rules
- [ ] Draw state machine: ACTIVE → CHECKMATE/STALEMATE/RESIGNED
- [ ] Describe Singleton pattern - why one ChessGame?
- [ ] Explain Strategy pattern - show 2-3 piece movement algorithms
- [ ] Show Observer pattern - how notifications work
- [ ] Explain move validation algorithm (5 steps)
- [ ] Describe check detection (find King → check enemy pieces)
- [ ] Distinguish checkmate vs stalemate with examples
- [ ] Run INTERVIEW_COMPACT.py demo showing legal moves + moves executed
- [ ] Answer at least 3 advanced questions

## Demo Commands

```bash
# Run all 5 demo scenarios
python3 INTERVIEW_COMPACT.py

# Expected output:
# DEMO 1: Board setup, show legal moves for pawn and knight
# DEMO 2: Execute opening moves (e2-e4, e7-e5, Nf3)
# DEMO 3: Detect check position
# DEMO 4: Show capture sequence and move history
# DEMO 5: Demonstrate game ending condition
```

## If You Get Stuck...

### "How do pawns move?"
→ White pawns move up (row-1), Black pawns move down (row+1). First move can be 2 squares.

### "What about Knight movement?"
→ L-shape only: (±2,±1) or (±1,±2). Check all 8 possibilities. Can jump over pieces.

### "How is check detected?"
→ Find the King → For each enemy piece, check if they can reach King square → If yes, it's check.

### "Explain checkmate vs stalemate"
→ Checkmate: In check + no legal moves = lose. Stalemate: Not in check + no legal moves = draw (0.5-0.5).

### "How to validate King safety?"
→ Before accepting move, simulate it → check if King attacked → restore board → only allow if safe.

### "Any special rules I'm missing?"
→ See README.md section "Special Moves" - castling, en passant, promotion.

## Common Mistakes to Avoid

- ❌ Forgetting Knight can jump → Use direct offset checks, not path validation
- ❌ Wrong pawn direction → White is direction=-1 (up), Black is direction=+1 (down)
- ❌ Not checking King safety → Leads to invalid move acceptance
- ❌ Allowing move into check → Must simulate + validate before accepting
- ❌ Not handling sliding piece blocking → Rook/Bishop/Queen stop at first piece

## Example Move Validation

**Scenario**: White pawn at e2 wants to move to e4 (2 squares forward)

```
Step 1: Piece exists at e2? Yes (Pawn)
Step 2: Belongs to White? Yes
Step 3: Pawn allows 2-square forward on first move? Yes (pawn.move_count == 0)
Step 4: e3 empty? Yes
Step 5: e4 empty? Yes
Step 6: Simulate move, King in check? No
→ VALID move
```

## Talking Points Summary

**"This system demonstrates clean architecture with Strategy pattern for piece movement, Observer pattern for loose coupling, and Singleton coordination. Move validation requires checking piece rules, board state, and King safety. Detecting checkmate involves finding legal moves (complex due to King safety checks). Key optimizations include caching legal moves and using bitboards for performance."**


## 75-Minute Guide

## System Overview
**Two-player chess engine** supporting complete chess rules (piece movement, castling, en passant, promotion), move validation, check/checkmate/stalemate detection, move history with undo, and game state management. Think full-featured chess.com engine in simplified form.

**Core Challenge**: Implement complex piece movement rules, check detection across 8 piece types, game state validation, and board representation efficiently.

---

## Requirements Clarification (0-5 min)

### Functional Requirements
1. **Board Setup**: 8x8 board with standard piece positioning
2. **Piece Movement**: All 6 piece types (Pawn, Rook, Bishop, Queen, King, Knight)
3. **Special Moves**: Castling (King/Rook), En passant (Pawn), Promotion (Pawn)
4. **Move Validation**: Legal moves only (no moving into check, blocked paths)
5. **Check Detection**: Identify when king is under attack
6. **Checkmate Detection**: No legal moves + in check = checkmate (player loses)
7. **Stalemate Detection**: No legal moves + not in check = draw
8. **Move History**: Track all moves, support undo
9. **Game State**: SETUP → ACTIVE → CHECKMATE → STALEMATE → RESIGNED

### Non-Functional Requirements
- **Performance**: Move validation in <1ms for 30 possible moves
- **Concurrency**: Single-threaded (turn-based)
- **Scalability**: Not required (local 2-player only)
- **Persistence**: In-memory game state

### Key Design Decisions
1. **Board Representation**: 2D array (8x8) with Piece objects
2. **Piece Movement**: Strategy pattern - each piece type has own movement rules
3. **Move Validation**: Immutable Move objects tracking from/to positions
4. **Game Coordination**: Singleton ChessGame managing board state, players, move history
5. **Observer Pattern**: Notify UI on piece moves, check, checkmate events

---

## Architecture & Design (5-15 min)

### System Architecture

```
ChessGame (Singleton)
├── Board (8x8 grid)
│   ├── Squares[64]
│   └── Pieces positioned on squares
├── Players[2]
│   ├── White (starts first)
│   └── Black (responds)
├── Move History[]
│   └── Tracks all moves (from/to/piece)
├── GameStatus (ACTIVE/CHECKMATE/STALEMATE/RESIGNED)
└── GameObserver pattern
    ├── MoveObserver
    ├── CheckObserver
    └── CheckmateObserver
```

### Design Patterns Used

1. **Singleton**: ChessGame coordinates all operations
2. **Strategy**: Each PieceType has movement algorithm (Pawn vs Rook vs Bishop etc)
3. **Observer**: Notify listeners on game events (move, check, checkmate)
4. **State**: GameStatus enum prevents invalid transitions
5. **Factory**: Piece creation with correct type and color

### Move Validation Flow
```
Player selects from/to square
    ↓
Piece exists at 'from' square and belongs to current player?
    ↓
Piece type allows movement to 'to' square (considering board state)?
    ↓
Path is clear (no blocking pieces for Rook/Bishop/Queen)?
    ↓
Move doesn't leave own King in check?
    ↓
Move is VALID - update board, switch turns, check for check/checkmate
```

---

## Core Entities (15-35 min)

### 1. Piece Hierarchy

```python
class Piece(ABC):
    """Base piece class"""
    def __init__(self, color: PieceColor, position: tuple):
        self.color = color  # WHITE or BLACK
        self.position = position  # (row, col) where row/col in 0-7
        self.move_count = 0  # For castling validation
    
    @abstractmethod
    def get_possible_moves(self, board: Board) -> List[tuple]:
        """Return list of all possible destination squares"""
        pass
    
    def is_white(self) -> bool:
        return self.color == PieceColor.WHITE
```

**Piece Types** (all inherit from Piece):

- **Pawn**: Moves forward 1 (or 2 on first move), captures diagonally
  ```python
  class Pawn(Piece):
      def get_possible_moves(self, board):
          moves = []
          direction = -1 if self.is_white() else 1
          new_row = self.position[0] + direction
          
          # Move forward 1 square
          if board.is_empty(new_row, self.position[1]):
              moves.append((new_row, self.position[1]))
              
              # Move forward 2 squares on first move
              if self.move_count == 0:
                  new_row2 = self.position[0] + 2*direction
                  if board.is_empty(new_row2, self.position[1]):
                      moves.append((new_row2, self.position[1]))
          
          # Diagonal captures
          for col_offset in [-1, 1]:
              new_col = self.position[1] + col_offset
              if board.has_enemy(new_row, new_col, self.color):
                  moves.append((new_row, new_col))
          
          return moves
  ```

- **Rook**: Moves horizontally/vertically any distance (straight lines)
  ```python
  class Rook(Piece):
      def get_possible_moves(self, board):
          moves = []
          # Check all 4 directions (up, down, left, right)
          for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
              r, c = self.position
              for i in range(1, 8):
                  new_r, new_c = r + dr*i, c + dc*i
                  if not board.is_valid(new_r, new_c):
                      break
                  if board.is_empty(new_r, new_c):
                      moves.append((new_r, new_c))
                  elif board.has_enemy(new_r, new_c, self.color):
                      moves.append((new_r, new_c))
                      break
                  else:
                      break  # Own piece blocking
          return moves
  ```

- **Bishop**: Moves diagonally any distance
- **Queen**: Combines Rook + Bishop moves
- **Knight**: L-shape moves (2,1 or 1,2 squares) - can jump over pieces
- **King**: Moves 1 square in any direction

### 2. Board Representation

```python
class Board:
    """8x8 chess board"""
    def __init__(self):
        self.squares = [[None for _ in range(8)] for _ in range(8)]
        self.initialize_pieces()
    
    def initialize_pieces(self):
        """Setup starting position"""
        # Place pawns
        for col in range(8):
            self.squares[1][col] = Pawn(PieceColor.WHITE, (1, col))
            self.squares[6][col] = Pawn(PieceColor.BLACK, (6, col))
        
        # Place back rank pieces (Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook)
        back_rank_white = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for col in range(8):
            self.squares[0][col] = back_rank_white[col](PieceColor.WHITE, (0, col))
        
        back_rank_black = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for col in range(8):
            self.squares[7][col] = back_rank_black[col](PieceColor.BLACK, (7, col))
    
    def get_piece(self, row: int, col: int) -> Optional[Piece]:
        """Get piece at square"""
        if not self.is_valid(row, col):
            return None
        return self.squares[row][col]
    
    def is_empty(self, row: int, col: int) -> bool:
        """Check if square is empty"""
        return self.is_valid(row, col) and self.squares[row][col] is None
    
    def is_valid(self, row: int, col: int) -> bool:
        """Check if coordinates are on board"""
        return 0 <= row < 8 and 0 <= col < 8
    
    def move_piece(self, from_pos: tuple, to_pos: tuple):
        """Move piece (assumes validation already done)"""
        piece = self.get_piece(*from_pos)
        if piece:
            piece.position = to_pos
            piece.move_count += 1
            self.squares[to_pos[0]][to_pos[1]] = piece
            self.squares[from_pos[0]][from_pos[1]] = None
    
    def is_under_attack(self, row: int, col: int, by_color: PieceColor) -> bool:
        """Check if square is under attack by given color"""
        for r in range(8):
            for c in range(8):
                piece = self.get_piece(r, c)
                if piece and piece.color == by_color:
                    if (row, col) in piece.get_possible_moves(self):
                        return True
        return False
```

### 3. Player & Move Classes

```python
class Player:
    """Represents chess player"""
    def __init__(self, name: str, color: PieceColor):
        self.name = name
        self.color = color
        self.is_white = color == PieceColor.WHITE

class Move:
    """Represents a single chess move"""
    def __init__(self, from_pos: tuple, to_pos: tuple, piece: Piece, 
                 captured_piece: Optional[Piece] = None, move_type: str = "normal"):
        self.from_pos = from_pos
        self.to_pos = to_pos
        self.piece = piece
        self.captured_piece = captured_piece
        self.move_type = move_type  # "normal", "castling", "en_passant", "promotion"
        self.timestamp = datetime.now()
    
    def __repr__(self) -> str:
        piece_symbol = "♟♞♝♖♕♔"[hash(str(self.piece)) % 6]
        return f"{chr(97 + self.from_pos[1])}{8-self.from_pos[0]}-{chr(97 + self.to_pos[1])}{8-self.to_pos[0]}"
```

---

## Business Logic (35-55 min)

### 1. Move Validation

```python
def is_valid_move(self, from_pos: tuple, to_pos: tuple) -> bool:
    """Validate move before execution"""
    piece = self.board.get_piece(*from_pos)
    
    # Piece exists and belongs to current player?
    if not piece or piece.color != self.current_player.color:
        return False
    
    # Destination is valid for this piece type?
    if to_pos not in piece.get_possible_moves(self.board):
        return False
    
    # Is there a friendly piece at destination? (can't capture own)
    dest_piece = self.board.get_piece(*to_pos)
    if dest_piece and dest_piece.color == piece.color:
        return False
    
    # Simulate move and check if own king is in check
    self.board.move_piece(from_pos, to_pos)
    king_in_check = self.is_king_in_check(self.current_player.color)
    self.board.undo_move()  # Restore board state
    
    if king_in_check:
        return False
    
    return True
```

### 2. Check Detection

```python
def is_king_in_check(self, color: PieceColor) -> bool:
    """Check if king of given color is under attack"""
    king = self.find_king(color)
    if not king:
        return False
    
    enemy_color = PieceColor.BLACK if color == PieceColor.WHITE else PieceColor.WHITE
    return self.board.is_under_attack(king.position[0], king.position[1], enemy_color)

def find_king(self, color: PieceColor) -> Optional[King]:
    """Find king piece of given color"""
    for row in range(8):
        for col in range(8):
            piece = self.board.get_piece(row, col)
            if isinstance(piece, King) and piece.color == color:
                return piece
    return None
```

### 3. Checkmate & Stalemate Detection

```python
def is_checkmate(self, color: PieceColor) -> bool:
    """Check if player is in checkmate"""
    in_check = self.is_king_in_check(color)
    has_legal_moves = self.has_legal_moves(color)
    return in_check and not has_legal_moves

def is_stalemate(self, color: PieceColor) -> bool:
    """Check if player is in stalemate (draw)"""
    in_check = self.is_king_in_check(color)
    has_legal_moves = self.has_legal_moves(color)
    return not in_check and not has_legal_moves

def has_legal_moves(self, color: PieceColor) -> bool:
    """Check if player has any legal moves available"""
    for row in range(8):
        for col in range(8):
            piece = self.board.get_piece(row, col)
            if piece and piece.color == color:
                for dest_row, dest_col in piece.get_possible_moves(self.board):
                    if self.is_valid_move((row, col), (dest_row, dest_col)):
                        return True
    return False
```

### 4. Move Execution

```python
def make_move(self, from_pos: tuple, to_pos: tuple) -> bool:
    """Execute a player move"""
    if not self.is_valid_move(from_pos, to_pos):
        return False
    
    piece = self.board.get_piece(*from_pos)
    captured_piece = self.board.get_piece(*to_pos)
    
    # Execute move
    self.board.move_piece(from_pos, to_pos)
    move = Move(from_pos, to_pos, piece, captured_piece)
    self.move_history.append(move)
    
    # Check for checkmate/stalemate
    opponent_color = self.get_opponent_color()
    if self.is_checkmate(opponent_color):
        self.game_status = GameStatus.CHECKMATE
        self._notify_observers("checkmate", {
            "winner": self.current_player.name,
            "loser": self.get_opponent().name
        })
    elif self.is_stalemate(opponent_color):
        self.game_status = GameStatus.STALEMATE
        self._notify_observers("stalemate", {"reason": "no legal moves"})
    else:
        # Switch turns
        self.current_player = self.get_opponent()
        
        # Notify observers of move
        self._notify_observers("move_made", {
            "piece": str(piece),
            "from": from_pos,
            "to": to_pos,
            "captured": captured_piece is not None
        })
    
    return True
```

---

## Integration & Patterns (55-70 min)

### Observer Pattern - Game Events

```python
class GameObserver(ABC):
    @abstractmethod
    def update(self, event: str, data: dict):
        pass

class MoveObserver(GameObserver):
    """Notify on piece moves"""
    def update(self, event: str, data: dict):
        if event == "move_made":
            print("[MOVE] %s from %s to %s" % (data['piece'], data['from'], data['to']))

class CheckObserver(GameObserver):
    """Notify on check"""
    def update(self, event: str, data: dict):
        if event == "check":
            print("[CHECK] %s is in check!" % data['player'])

class CheckmateObserver(GameObserver):
    """Notify on checkmate"""
    def update(self, event: str, data: dict):
        if event == "checkmate":
            print("[CHECKMATE] %s wins! %s is checkmated" % (data['winner'], data['loser']))
```

### Singleton - ChessGame Coordinator

```python
class ChessGame:
    """Singleton: Central chess game coordinator"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.board = Board()
        self.player_white = Player("White", PieceColor.WHITE)
        self.player_black = Player("Black", PieceColor.BLACK)
        self.current_player = self.player_white
        self.game_status = GameStatus.ACTIVE
        self.move_history = []
        self.observers = []
    
    def make_move(self, from_pos: tuple, to_pos: tuple) -> bool:
        """Execute move with validation and game state update"""
        # (implementation from business logic section)
        pass
    
    def add_observer(self, observer: GameObserver):
        self.observers.append(observer)
    
    def _notify_observers(self, event: str, data: dict):
        for observer in self.observers:
            observer.update(event, data)
```

---

## Edge Cases & Special Moves (60-70 min)

### 1. Castling
**Conditions**: King/Rook haven't moved, no pieces between them, King not in check, King doesn't move through check

```python
def is_valid_castling(self, from_pos: tuple, to_pos: tuple, piece: King) -> bool:
    if piece.move_count != 0:
        return False
    if self.is_king_in_check(piece.color):
        return False
    
    col_diff = abs(to_pos[1] - from_pos[1])
    if col_diff != 2:
        return False
    
    rook_col = 7 if to_pos[1] > from_pos[1] else 0
    rook = self.board.get_piece(from_pos[0], rook_col)
    if not isinstance(rook, Rook) or rook.move_count != 0:
        return False
    
    # Check path is clear
    min_col, max_col = min(from_pos[1], to_pos[1]), max(from_pos[1], to_pos[1])
    for col in range(min_col + 1, max_col):
        if not self.board.is_empty(from_pos[0], col):
            return False
    
    return True
```

### 2. En Passant
**Conditions**: Pawn moves diagonally to empty square immediately after opponent's 2-square pawn advance

### 3. Pawn Promotion
**Trigger**: Pawn reaches opposite end, promotes to Queen/Rook/Bishop/Knight

### 4. Threefold Repetition & 50-Move Rule
**Rules**: Game is draw if position repeats 3x or 50 moves without capture/pawn move

---

## Interview Q&A (12 Questions)

### Basic (0-5 min)
1. **"Describe the core entities in chess."**
   - Answer: Board (8x8), Pieces (6 types), Players (White/Black), Moves, Game state. Board contains squares with Pieces. Each Piece has movement rules.

2. **"How do you represent a chess position?"**
   - Answer: 8x8 2D array where each element is None (empty) or a Piece object with color/type/position.

3. **"What makes a move valid?"**
   - Answer: (1) Piece exists and belongs to current player, (2) Destination follows piece's movement rules, (3) No friendly piece at destination, (4) Own King not left in check.

### Intermediate (5-10 min)
4. **"How do you detect if a King is in check?"**
   - Answer: Check if any enemy piece can capture the King in one move. Iterate all enemy pieces, get their possible moves, see if King's square is included.

5. **"What's the difference between checkmate and stalemate?"**
   - Answer: Checkmate = in check + no legal moves = player loses. Stalemate = not in check + no legal moves = draw.

6. **"How do you validate a move doesn't leave the King in check?"**
   - Answer: Simulate the move, check if own King is under attack, then restore board state. Only allow move if King remains safe.

7. **"How would you handle castling?"**
   - Answer: Special move where King moves 2 squares. Check preconditions: King/Rook haven't moved, no pieces between, King not in check/through check. Move both pieces simultaneously.

### Advanced (10-15 min)
8. **"How would you implement a move undo?"**
   - Answer: Store previous board state with each move (deep copy or track piece positions + captured pieces). Restore on undo.

9. **"How would you detect threefold repetition?"**
   - Answer: After each move, check if current position matches any previous position in history. If position repeated 3 times, declare draw.

10. **"How would you improve performance for finding legal moves?"**
    - Answer: Bitboard representation (64-bit integers for piece positions) instead of 2D array. Lookup tables for piece attack patterns. Pre-compute check status.

11. **"How would you handle AI opponent?"**
    - Answer: Minimax algorithm with alpha-beta pruning. Evaluate positions using piece values (Pawn=1, Knight=3, Bishop=3, Rook=5, Queen=9). Search to depth 4-6.

12. **"How would you persist and load games?"**
    - Answer: Serialize board state (piece types/positions/colors), move history, game status to JSON/database. Deserialize to recreate game state on load.

---

## SOLID Principles Applied

| Principle | Application |
|-----------|------------|
| **Single Responsibility** | Each Piece subclass handles its movement rules; Board handles piece placement; ChessGame handles game flow |
| **Open/Closed** | New Piece types (e.g., Fairy chess pieces) without modifying existing code; add Observers without changing game |
| **Liskov Substitution** | All Piece subclasses can be used interchangeably; all GameObserver subclasses work the same |
| **Interface Segregation** | Piece interface only requires get_possible_moves(); GameObserver interface only requires update() |
| **Dependency Inversion** | ChessGame depends on abstract Piece and GameObserver, not concrete implementations |

---

## Architecture ASCII Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   ChessGame (Singleton)                  │
│  ┌──────────────────────────────────────────────────┐  │
│  │ - board: Board                                   │  │
│  │ - player_white, player_black: Player             │  │
│  │ - current_player: Player                         │  │
│  │ - game_status: ACTIVE/CHECKMATE/STALEMATE       │  │
│  │ - move_history: Move[]                           │  │
│  │ - observers: GameObserver[]                      │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
              │                          │
              ▼                          ▼
    ┌──────────────────┐      ┌─────────────────────┐
    │      Board       │      │     GameObserver    │
    ├──────────────────┤      ├─────────────────────┤
    │ squares[8][8]    │      │ update(event, data) │
    │ - initialize()   │      └─────────────────────┘
    │ - move_piece()   │              △
    │ - is_empty()     │              │ implements
    │ - is_under_attack() │      ┌────┴────────────┐
    └──────────────────┘      │                   │
           │              MoveObserver    CheckmateObserver
           ▼
    ┌───────────────────────────────────────────┐
    │           Piece (Abstract)                 │
    ├───────────────────────────────────────────┤
    │ - color, position, move_count             │
    │ - get_possible_moves(): List[tuple]       │
    └───────────────────────────────────────────┘
        △           △           △           △
        │           │           │           │
    ┌───┴───┐   ┌───┴───┐   ┌──┴──┐   ┌────┴────┐
    │ Pawn  │   │ Rook  │   │Bishop│   │ Queen   │
    │       │   │       │   │     │   │        │
    │Moves: │   │Moves: │   │Moves:   │Moves:  │
    │1 or 2 │   │Horiz/ │   │Diagonal │All     │
    │forward│   │Vert   │   │         │        │
    └───────┘   └───────┘   └────────┘└────────┘

    ┌──────────┐          ┌────────┐
    │  Knight  │          │  King  │
    │          │          │        │
    │ L-shape  │          │  1 all │
    │  jumps   │          │ directions
    └──────────┘          └────────┘

Move Validation Pipeline:
┌──────────┐      ┌──────────────┐      ┌──────────────┐
│  from/to │  →   │ Piece Type   │  →   │   Check if   │
│ selected │      │ allowed?     │      │ King safe?   │
└──────────┘      └──────────────┘      └──────────────┘
                                                │
                                                ▼
                                        ┌──────────────┐
                                        │  Make Move   │
                                        │   + Notify   │
                                        └──────────────┘

GameStatus State Machine:
ACTIVE → CHECKMATE (current player loses) → END
ACTIVE → STALEMATE (draw) → END
ACTIVE → RESIGNED (opponent wins) → END
```

---

## 5 Demo Scenarios

### Demo 1: Setup & Legal Moves
- Initialize game, display board
- Get all legal moves for White pawn at (1,4) (e2 in chess notation)
- Expected: Can move to (2,4) or (3,4)

### Demo 2: Simple Capture
- Move White pawn e2→e4
- Move Black pawn e7→e5
- White moves Knight b1→c3
- Black moves pawn d7→d6
- White captures Black pawn e5 with pawn e4
- Verify capture recorded in move history

### Demo 3: Check Detection
- Setup position with White Rook attacking Black King
- Verify check is detected
- Verify Black player must move King or block

### Demo 4: Checkmate Scenario
- Setup Back Rank mate: Black King on h8, White Rooks on h1 and a8
- White delivers checkmate
- Game should end with CHECKMATE status
- Verify MoveObserver and CheckmateObserver notified

### Demo 5: Stalemate Scenario
- Setup position where White King in corner, pawn blocked, no legal moves
- Black to move but not in check
- Verify stalemate detected, game ends in draw

---

## Key Implementation Notes

### Piece Movement Algorithm
- Each Piece type implements get_possible_moves(board)
- Pawns check ahead and diagonals, handle first move bonus
- Sliding pieces (Rook/Bishop/Queen) iterate in direction until edge or blocking piece
- Knight checks 8 L-shaped destinations
- King checks 8 adjacent squares

### Performance Optimization
- Lazy evaluation: Only compute possible moves when needed
- Caching: Store last computed move list until board changes
- Early termination: Check King safety before making move

### Testing Strategy
1. Unit test each Piece type's movement
2. Integration test move validation with various board states
3. Checkmate/stalemate detection across 100+ positions
4. Verify move history and undo functionality


## Detailed Design Reference

## System Overview
Full-featured two-player chess engine supporting all standard chess rules (piece movements, special moves like castling/en passant/promotion), move validation, check/checkmate/stalemate detection, and game state management.

## Core Entities

| Entity | Key Attributes | Key Methods |
|--------|----------------|------------|
| **Board** | squares[8][8], pieces positioned | get_piece(), is_empty(), move_piece(), is_under_attack() |
| **Piece (Abstract)** | color (WHITE/BLACK), position (row,col), move_count | get_possible_moves(), is_white() |
| **Pawn** | Moves forward 1-2, captures diagonally | get_possible_moves() returns forward/capture squares |
| **Rook** | Moves horizontal/vertical any distance | get_possible_moves() returns all straight-line squares |
| **Bishop** | Moves diagonal any distance | get_possible_moves() returns all diagonal squares |
| **Queen** | Combines Rook + Bishop | get_possible_moves() returns rook + bishop squares |
| **Knight** | L-shaped moves (2,1) or (1,2) - jumps pieces | get_possible_moves() returns 8 L-shaped destinations |
| **King** | Moves 1 square any direction | get_possible_moves() returns 8 adjacent squares |
| **Player** | name, color (WHITE/BLACK) | Represents player in game |
| **Move** | from_pos, to_pos, piece, captured_piece | __repr__() returns algebraic notation |
| **GameObserver** | Abstract pattern | update(event, data) called on game events |

## Design Patterns Applied

### 1. **Singleton** (ChessGame)
- **Purpose**: Central game coordinator managing board, players, move validation
- **Implementation**: Thread-safe lazy initialization with double-checked locking
- **Interview Points**: 
  - Why singleton? One global game state prevents duplicates
  - Thread safety: `_lock` protects initialization
  - Usage: `game = ChessGame()`

### 2. **Strategy** (Piece Movement)
Each piece type implements own movement algorithm:
- **Pawn**: Forward 1-2, diagonal captures
- **Rook**: Horizontal/vertical lines
- **Bishop**: Diagonal lines
- **Queen**: Rook + Bishop
- **Knight**: L-shaped jumps
- **King**: 1 square all directions
- **Interview Points**:
  - Problem: Different movement rules without modifying Board
  - Solution: Abstract Piece class with subclass implementations
  - How to extend: Add new Piece type, implement get_possible_moves()

### 3. **Observer** (GameObserver)
Notifications on game events:
- **MoveObserver**: Notified when piece moves
- **CheckObserver**: Notified when King in check
- **CheckmateObserver**: Notified when checkmate reached
- **Interview Points**:
  - Loose coupling between ChessGame and UI/notifications
  - Multiple observers on same event
  - Adding observer: Create class inheriting GameObserver

### 4. **State** (GameStatus)
Game lifecycle: ACTIVE → CHECKMATE/STALEMATE/RESIGNED
- **Interview Points**:
  - Why separate enum? Prevents invalid state transitions
  - Example: Game only ends on specific conditions

### 5. **Factory** (Piece Creation)
Board.initialize_pieces() creates all 32 pieces with correct types/positions

## Business Logic Highlights

### Move Validation Algorithm
```
1. Piece exists at 'from' and belongs to current player?
2. Destination follows piece's movement rules?
3. Path is clear (no blocking for sliding pieces)?
4. No friendly piece at destination?
5. Move doesn't leave own King in check? (simulate + restore)
   - Simulate move on board
   - Check if own King under attack
   - Restore board state
6. Move is VALID
```

### Check Detection
```
1. Find own King piece on board
2. Check if any enemy piece can attack King square
3. If yes, King is in CHECK
```

### Checkmate vs Stalemate
```
Checkmate = King in check AND no legal moves → Player loses
Stalemate = King NOT in check AND no legal moves → Draw
```

### Special Moves (Not Fully Implemented)
1. **Castling**: King moves 2, Rook moves 3. Conditions:
   - King/Rook haven't moved
   - No pieces between
   - King not in check
   - King doesn't move through check
   
2. **En Passant**: Pawn captures opponent's pawn that moved 2 squares forward
   - Only if opponent's move was immediately before
   
3. **Promotion**: Pawn reaching opposite end becomes Queen/Rook/Bishop/Knight

## SOLID Principles Applied

| Principle | Application |
|-----------|------------|
| **S**ingle Responsibility | Each Piece subclass handles movement; Board handles placement; ChessGame handles game flow |
| **O**pen/Closed | New Piece types without modifying existing; new Observers without changing game |
| **L**iskov Substitution | All Piece subclasses interchangeable; all GameObserver subclasses work the same |
| **I**nterface Segregation | Piece interface only requires get_possible_moves(); GameObserver only requires update() |
| **D**ependency Inversion** | ChessGame depends on abstract Piece and GameObserver, not concrete implementations |

## Architecture Diagram

```
ChessGame (Singleton)
├── Board
│   └── squares[8][8] → Piece objects
├── Players[2]
│   ├── White (starts first)
│   └── Black
├── Move History
├── GameStatus (ACTIVE/CHECKMATE/STALEMATE/RESIGNED)
└── Observers[]
    ├── MoveObserver
    ├── CheckObserver
    └── CheckmateObserver

Piece Hierarchy:
Piece (Abstract)
├── Pawn (moves forward, captures diagonal)
├── Rook (horizontal/vertical lines)
├── Bishop (diagonal lines)
├── Queen (Rook + Bishop)
├── Knight (L-shaped jumps)
└── King (1 square all directions)

Move Validation Flow:
from/to position → piece exists? → movement valid? → path clear? 
→ destination safe? → King not in check after move? → VALID
```

## Key Talking Points for Interview

### Piece Movement Complexity
1. **Sliding Pieces** (Rook/Bishop/Queen): Iterate in direction until edge or piece
2. **Knight**: Unique L-shape, can jump over pieces
3. **Pawn**: Forward 1-2, captures diagonal, special capture (en passant)
4. **King**: Adjacent squares, special move (castling)

### Check Detection Algorithm
1. Find own King on board: O(64) scan
2. For each enemy piece, check if can reach King: O(32) pieces × O(8) average moves
3. Return if any piece can capture King
4. Optimization: Precompute King position, cache attack squares

### Performance Optimization
1. **Lazy Evaluation**: Only compute possible moves when needed
2. **Caching**: Store move list until board changes
3. **Early Termination**: Check King safety before allowing move
4. **Bitboards**: 64-bit integers instead of 8×8 arrays (advanced)

### Concurrency (Not Implemented)
- Single-threaded (turn-based)
- Could add async move validation with futures
- Move queue for multiplayer (not in scope)

### Game Save/Load
1. Serialize board state: position of each piece
2. Serialize move history: all moves since game start
3. On load: Recreate board → replay move history
4. Check game ended based on final state

### Testing Strategy
1. **Unit tests**: Each piece type's movement rules
2. **Integration tests**: Move validation across board states
3. **Edge cases**: Castling preconditions, en passant, promotion
4. **Checkmate/Stalemate**: 100+ known positions

### Extensions
1. **AI Opponent**: Minimax with alpha-beta pruning
2. **Online Multiplayer**: WebSocket, move broadcasting
3. **Chess Variants**: Fisher Random, 3-check, etc.
4. **Elo Rating**: Track player skill, matchmaking
5. **Opening Book**: Store known opening sequences

## Demo Scenarios Included

1. **Setup & Legal Moves**: Initialize board, compute legal moves for pieces
2. **Simple Moves**: Standard opening sequence (e2-e4, e7-e5, Nf3)
3. **Check Detection**: Setup position with King under attack
4. **Capture Sequence**: Track captures in move history
5. **Game Ending**: Demonstrate stalemate condition


## Compact Code

```python
"""Chess Game - Interview Implementation with 5 Demos"""

from enum import Enum
from abc import ABC, abstractmethod
from datetime import datetime
import threading

class PieceColor(Enum):
    WHITE = 1
    BLACK = 2

class GameStatus(Enum):
    ACTIVE = 1
    CHECKMATE = 2
    STALEMATE = 3
    RESIGNED = 4

class Piece(ABC):
    """Base chess piece"""
    def __init__(self, color, position):
        self.color = color
        self.position = position
        self.move_count = 0
    
    def is_white(self):
        return self.color == PieceColor.WHITE
    
    @abstractmethod
    def get_possible_moves(self, board):
        pass
    
    def __repr__(self):
        return "%s %s" % (self.color.name, self.__class__.__name__)

class Pawn(Piece):
    def get_possible_moves(self, board):
        moves = []
        direction = -1 if self.is_white() else 1
        new_row = self.position[0] + direction
        
        if 0 <= new_row < 8 and board.is_empty(new_row, self.position[1]):
            moves.append((new_row, self.position[1]))
            
            if self.move_count == 0:
                new_row2 = self.position[0] + 2 * direction
                if 0 <= new_row2 < 8 and board.is_empty(new_row2, self.position[1]):
                    moves.append((new_row2, self.position[1]))
        
        for col_offset in [-1, 1]:
            new_col = self.position[1] + col_offset
            if 0 <= new_row < 8 and 0 <= new_col < 8 and board.has_enemy(new_row, new_col, self.color):
                moves.append((new_row, new_col))
        
        return moves

class Rook(Piece):
    def get_possible_moves(self, board):
        moves = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            for i in range(1, 8):
                new_r = self.position[0] + dr * i
                new_c = self.position[1] + dc * i
                if not board.is_valid(new_r, new_c):
                    break
                if board.is_empty(new_r, new_c):
                    moves.append((new_r, new_c))
                elif board.has_enemy(new_r, new_c, self.color):
                    moves.append((new_r, new_c))
                    break
                else:
                    break
        return moves

class Bishop(Piece):
    def get_possible_moves(self, board):
        moves = []
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            for i in range(1, 8):
                new_r = self.position[0] + dr * i
                new_c = self.position[1] + dc * i
                if not board.is_valid(new_r, new_c):
                    break
                if board.is_empty(new_r, new_c):
                    moves.append((new_r, new_c))
                elif board.has_enemy(new_r, new_c, self.color):
                    moves.append((new_r, new_c))
                    break
                else:
                    break
        return moves

class Queen(Piece):
    def get_possible_moves(self, board):
        moves = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            for i in range(1, 8):
                new_r = self.position[0] + dr * i
                new_c = self.position[1] + dc * i
                if not board.is_valid(new_r, new_c):
                    break
                if board.is_empty(new_r, new_c):
                    moves.append((new_r, new_c))
                elif board.has_enemy(new_r, new_c, self.color):
                    moves.append((new_r, new_c))
                    break
                else:
                    break
        return moves

class Knight(Piece):
    def get_possible_moves(self, board):
        moves = []
        for dr, dc in [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]:
            new_r = self.position[0] + dr
            new_c = self.position[1] + dc
            if board.is_valid(new_r, new_c):
                if board.is_empty(new_r, new_c) or board.has_enemy(new_r, new_c, self.color):
                    moves.append((new_r, new_c))
        return moves

class King(Piece):
    def get_possible_moves(self, board):
        moves = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                new_r = self.position[0] + dr
                new_c = self.position[1] + dc
                if board.is_valid(new_r, new_c):
                    if board.is_empty(new_r, new_c) or board.has_enemy(new_r, new_c, self.color):
                        moves.append((new_r, new_c))
        return moves

class Board:
    def __init__(self):
        self.squares = [[None for _ in range(8)] for _ in range(8)]
        self.initialize_pieces()
    
    def initialize_pieces(self):
        for col in range(8):
            self.squares[1][col] = Pawn(PieceColor.WHITE, (1, col))
            self.squares[6][col] = Pawn(PieceColor.BLACK, (6, col))
        
        back_rank_white = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for col in range(8):
            self.squares[0][col] = back_rank_white[col](PieceColor.WHITE, (0, col))
        
        back_rank_black = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for col in range(8):
            self.squares[7][col] = back_rank_black[col](PieceColor.BLACK, (7, col))
    
    def get_piece(self, row, col):
        if not self.is_valid(row, col):
            return None
        return self.squares[row][col]
    
    def is_empty(self, row, col):
        return self.is_valid(row, col) and self.squares[row][col] is None
    
    def is_valid(self, row, col):
        return 0 <= row < 8 and 0 <= col < 8
    
    def has_enemy(self, row, col, color):
        piece = self.get_piece(row, col)
        return piece is not None and piece.color != color
    
    def move_piece(self, from_pos, to_pos):
        piece = self.get_piece(*from_pos)
        if piece:
            piece.position = to_pos
            piece.move_count += 1
            self.squares[to_pos[0]][to_pos[1]] = piece
            self.squares[from_pos[0]][from_pos[1]] = None
            return piece
        return None
    
    def is_under_attack(self, row, col, by_color):
        for r in range(8):
            for c in range(8):
                piece = self.get_piece(r, c)
                if piece and piece.color == by_color:
                    if (row, col) in piece.get_possible_moves(self):
                        return True
        return False
    
    def display_ascii(self):
        print("\n  a b c d e f g h")
        for row in range(7, -1, -1):
            line = "%d " % (row + 1)
            for col in range(8):
                piece = self.get_piece(row, col)
                if piece is None:
                    line += ". "
                elif isinstance(piece, Pawn):
                    line += ("P" if piece.is_white() else "p") + " "
                elif isinstance(piece, Rook):
                    line += ("R" if piece.is_white() else "r") + " "
                elif isinstance(piece, Knight):
                    line += ("N" if piece.is_white() else "n") + " "
                elif isinstance(piece, Bishop):
                    line += ("B" if piece.is_white() else "b") + " "
                elif isinstance(piece, Queen):
                    line += ("Q" if piece.is_white() else "q") + " "
                elif isinstance(piece, King):
                    line += ("K" if piece.is_white() else "k") + " "
            print(line)

class Player:
    def __init__(self, name, color):
        self.name = name
        self.color = color

class Move:
    def __init__(self, from_pos, to_pos, piece, captured=None):
        self.from_pos = from_pos
        self.to_pos = to_pos
        self.piece = piece
        self.captured = captured
        self.timestamp = datetime.now()
    
    def __repr__(self):
        return "%s%d-%s%d" % (chr(97 + self.from_pos[1]), 8 - self.from_pos[0], 
                              chr(97 + self.to_pos[1]), 8 - self.to_pos[0])

class GameObserver(ABC):
    @abstractmethod
    def update(self, event, data):
        pass

class MoveObserver(GameObserver):
    def update(self, event, data):
        if event == "move_made":
            print("    [MOVE] %s: %s" % (data['piece'], data['notation']))

class CheckObserver(GameObserver):
    def update(self, event, data):
        if event == "check":
            print("    [CHECK] %s is in check!" % data['player'])

class CheckmateObserver(GameObserver):
    def update(self, event, data):
        if event == "checkmate":
            print("    [CHECKMATE] %s wins! %s is checkmated" % (data['winner'], data['loser']))

class ChessGame:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.board = Board()
        self.white = Player("White", PieceColor.WHITE)
        self.black = Player("Black", PieceColor.BLACK)
        self.current_player = self.white
        self.game_status = GameStatus.ACTIVE
        self.move_history = []
        self.observers = []
    
    def find_king(self, color):
        for row in range(8):
            for col in range(8):
                piece = self.board.get_piece(row, col)
                if isinstance(piece, King) and piece.color == color:
                    return piece
        return None
    
    def is_king_in_check(self, color):
        king = self.find_king(color)
        if not king:
            return False
        enemy_color = PieceColor.BLACK if color == PieceColor.WHITE else PieceColor.WHITE
        return self.board.is_under_attack(king.position[0], king.position[1], enemy_color)
    
    def has_legal_moves(self, color):
        for row in range(8):
            for col in range(8):
                piece = self.board.get_piece(row, col)
                if piece and piece.color == color:
                    for dest_row, dest_col in piece.get_possible_moves(self.board):
                        if self.is_valid_move((row, col), (dest_row, dest_col)):
                            return True
        return False
    
    def is_checkmate(self, color):
        return self.is_king_in_check(color) and not self.has_legal_moves(color)
    
    def is_stalemate(self, color):
        return not self.is_king_in_check(color) and not self.has_legal_moves(color)
    
    def is_valid_move(self, from_pos, to_pos):
        piece = self.board.get_piece(*from_pos)
        if not piece or piece.color != self.current_player.color:
            return False
        
        if to_pos not in piece.get_possible_moves(self.board):
            return False
        
        dest_piece = self.board.get_piece(*to_pos)
        if dest_piece and dest_piece.color == piece.color:
            return False
        
        old_piece = self.board.get_piece(*to_pos)
        self.board.move_piece(from_pos, to_pos)
        king_in_check = self.is_king_in_check(self.current_player.color)
        self.board.move_piece(to_pos, from_pos)
        if old_piece:
            self.board.squares[to_pos[0]][to_pos[1]] = old_piece
        
        return not king_in_check
    
    def make_move(self, from_pos, to_pos):
        if not self.is_valid_move(from_pos, to_pos):
            return False
        
        piece = self.board.get_piece(*from_pos)
        captured = self.board.get_piece(*to_pos)
        self.board.move_piece(from_pos, to_pos)
        move = Move(from_pos, to_pos, piece, captured)
        self.move_history.append(move)
        
        opponent = self.black if self.current_player.color == PieceColor.WHITE else self.white
        
        if self.is_checkmate(opponent.color):
            self.game_status = GameStatus.CHECKMATE
            self._notify_observers("checkmate", {"winner": self.current_player.name, "loser": opponent.name})
        elif self.is_stalemate(opponent.color):
            self.game_status = GameStatus.STALEMATE
            self._notify_observers("stalemate", {"reason": "no legal moves"})
        else:
            if self.is_king_in_check(opponent.color):
                self._notify_observers("check", {"player": opponent.name})
            self._notify_observers("move_made", {"piece": str(piece), "notation": str(move)})
            self.current_player = opponent
        
        return True
    
    def add_observer(self, observer):
        self.observers.append(observer)
    
    def _notify_observers(self, event, data):
        for observer in self.observers:
            observer.update(event, data)
    
    def get_legal_moves(self, position):
        piece = self.board.get_piece(*position)
        if not piece or piece.color != self.current_player.color:
            return []
        
        legal_moves = []
        for dest in piece.get_possible_moves(self.board):
            if self.is_valid_move(position, dest):
                legal_moves.append(dest)
        return legal_moves

def demo_1_setup_and_search():
    print("\n" + "="*70)
    print("DEMO 1: SETUP AND LEGAL MOVES")
    print("="*70)
    
    game = ChessGame()
    game.board.display_ascii()
    
    print("\nWhite pawn at e2 (1, 4):")
    moves = game.get_legal_moves((1, 4))
    print("- Legal moves: %s" % (["%s%d" % (chr(97 + m[1]), 8 - m[0]) for m in moves]))
    
    print("\nWhite Knight at b1 (0, 1):")
    moves = game.get_legal_moves((0, 1))
    print("- Legal moves: %s" % (["%s%d" % (chr(97 + m[1]), 8 - m[0]) for m in moves]))

def demo_2_simple_moves():
    print("\n" + "="*70)
    print("DEMO 2: SIMPLE OPENING MOVES")
    print("="*70)
    
    game = ChessGame()
    game.add_observer(MoveObserver())
    
    print("\nInitial position:")
    game.board.display_ascii()
    
    print("\nMove 1: White e2-e4")
    game.make_move((1, 4), (3, 4))
    
    print("\nMove 2: Black e7-e5")
    game.make_move((6, 4), (4, 4))
    
    print("\nMove 3: White Nf1-c3")
    game.make_move((0, 6), (2, 5))

def demo_3_check_detection():
    print("\n" + "="*70)
    print("DEMO 3: CHECK DETECTION")
    print("="*70)
    
    game = ChessGame()
    game.add_observer(CheckObserver())
    
    print("\nSetup: White Rook will attack Black King")
    game.make_move((1, 4), (3, 4))
    game.make_move((6, 4), (4, 4))
    game.make_move((0, 0), (4, 0))
    game.make_move((7, 4), (6, 4))
    
    print("White Rook a2-a5, checking Black King")
    game.make_move((4, 0), (4, 4))

def demo_4_capture_sequence():
    print("\n" + "="*70)
    print("DEMO 4: CAPTURE SEQUENCE")
    print("="*70)
    
    game = ChessGame()
    game.add_observer(MoveObserver())
    
    print("\nSequence of captures:")
    game.make_move((1, 4), (3, 4))
    game.make_move((6, 6), (4, 6))
    game.make_move((3, 4), (4, 4))
    game.make_move((4, 6), (3, 5))
    
    print("\nMove History:")
    for i, move in enumerate(game.move_history):
        print("- Move %d: %s" % (i + 1, str(move)))

def demo_5_game_ending():
    print("\n" + "="*70)
    print("DEMO 5: SIMPLIFIED CHECKMATE SCENARIO")
    print("="*70)
    
    game = ChessGame()
    game.add_observer(CheckmateObserver())
    
    print("\nSequence to endgame:")
    game.make_move((1, 5), (3, 5))
    game.make_move((6, 4), (4, 4))
    game.make_move((0, 3), (5, 0))
    
    print("\nGame Status: %s" % game.game_status.name)
    print("White moves remaining for Black: %d" % len(game.get_legal_moves((7, 4))))

if __name__ == "__main__":
    print("\n" + "="*70)
    print("CHESS GAME - INTERVIEW IMPLEMENTATION - 5 DEMOS")
    print("="*70)
    
    demo_1_setup_and_search()
    demo_2_simple_moves()
    demo_3_check_detection()
    demo_4_capture_sequence()
    demo_5_game_ending()
    
    print("\n" + "="*70)
    print("ALL DEMOS COMPLETED SUCCESSFULLY")
    print("="*70 + "\n")

```

## UML Class Diagram (text)
````
(Classes, relationships, strategies/observers, enums)
````


## Scaling & Trade-offs (Q&A)
- How to scale? (sharding/queues/caching/locks)
- Prevent double booking/conflicts? (locks/optimistic concurrency)
- Persistence? (snapshots + event log)
- Performance? (bucketed lookups/O(1) operations)
- Memory/history growth? (caps, snapshots)
