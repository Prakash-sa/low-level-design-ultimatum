# Chess Game - 75 Minute Interview Implementation Guide

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

