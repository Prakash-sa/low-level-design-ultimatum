# Chess Game - Reference Guide

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

