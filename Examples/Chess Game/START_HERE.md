# Chess Game - 5 Minute Quick Start

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

## 5 Design Patterns Explained

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

