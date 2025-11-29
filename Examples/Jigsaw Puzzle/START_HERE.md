# Jigsaw Puzzle - Quick Start (5 Minutes)

## What You're Building
Interactive jigsaw puzzle game with piece placement, edge/corner detection, rotation, hint system, and completion tracking. Features intelligent matching algorithms and undo/redo functionality.

---

## 75-Minute Timeline

| Time | Phase | Focus |
|------|-------|-------|
| 0-5 min | **Requirements** | Clarify functional (placement, validation, rotation, hints) and non-functional (performance, scalability) |
| 5-15 min | **Architecture** | Design 6 core entities, choose 5 patterns (Singleton, Factory, Strategy, Observer, Memento) |
| 15-35 min | **Entities** | Implement Piece, Edge, Board, Game, Player, Move with business logic |
| 35-55 min | **Logic** | Implement matching strategies, hint algorithms, rotation, validation |
| 55-70 min | **Integration** | Wire PuzzleGame singleton, add observers, demo 5 scenarios |
| 70-75 min | **Demo** | Walk through working code, explain patterns, answer questions |

---

## Core Entities (3-Sentence Each)

### 1. Piece
Puzzle piece with unique ID, position, rotation, and four edges (TOP/RIGHT/BOTTOM/LEFT). Each edge has a pattern (FLAT/IN/OUT) for matching with neighbors. Tracks if correctly placed and current board position.

### 2. Edge
Represents one side of a puzzle piece with pattern type (FLAT for borders, IN for socket, OUT for tab). Stores color pattern for matching. Used to validate piece connections.

### 3. Board
2D grid representing puzzle layout with width × height dimensions. Tracks placed pieces at each position. Validates placement attempts and detects completion.

### 4. Game
Manages puzzle game state, available pieces, current board, and move history. Tracks start time, completion time, and player progress. Implements game rules and scoring.

### 5. Player
User playing the puzzle with name, score, and statistics. Tracks moves made, hints used, and completion time. Maintains leaderboard ranking.

### 6. Move (Memento Pattern)
Represents a single placement action with piece, position, and rotation. Supports undo/redo functionality. Stores timestamp for move history.

---

## 5 Design Patterns (Why Each Matters)

### 1. Singleton - PuzzleGame
**What**: Single instance manages entire game state  
**Why**: Centralized board state, consistent piece tracking, single source of truth  
**Talk Point**: "Ensures all placements see same board state. Alternative: Dependency injection for multi-game support."

### 2. Factory - PuzzleFactory
**What**: Creates puzzles from images with different difficulty levels (EASY/MEDIUM/HARD)  
**Why**: Encapsulates complex piece generation, edge matching logic  
**Talk Point**: "Adding new difficulty just requires new factory method. No changes to game logic."

### 3. Strategy - Matching Algorithms
**What**: ExactMatchStrategy, ColorSimilarityStrategy, EdgePatternStrategy  
**Why**: Different validation rules for different puzzle types  
**Talk Point**: "Can switch from exact matching to fuzzy matching for photo puzzles."

### 4. Observer - Game Events
**What**: PlayerNotifier, ProgressTracker, LeaderboardUpdater  
**Why**: Decoupled event handling for placements, completions, achievements  
**Talk Point**: "Adding sound effects just requires new SoundNotifier observer."

### 5. Memento - Undo/Redo
**What**: Stores previous game states for undo functionality  
**Why**: Allows players to revert mistakes without losing progress  
**Talk Point**: "Memento pattern preserves game state. Can undo 50+ moves efficiently."

---

## Key Algorithms (30-Second Explanations)

### Edge Matching Validation
```python
# Check if two edges can connect
def can_connect(edge1, edge2):
    # FLAT edges only on borders
    if edge1.pattern == EdgePattern.FLAT:
        return edge2.pattern == EdgePattern.FLAT
    # IN matches OUT
    if edge1.pattern == EdgePattern.IN:
        return edge2.pattern == EdgePattern.OUT
    # OUT matches IN
    return edge2.pattern == EdgePattern.IN
```
**Why**: Ensures physical puzzle constraints, prevents invalid placements.

### Hint Generation
```python
# Find best next piece to place
def generate_hint():
    # Prioritize corner pieces
    corners = [p for p in available if p.is_corner()]
    if corners: return corners[0]
    
    # Then edge pieces
    edges = [p for p in available if p.is_edge()]
    if edges: return edges[0]
    
    # Find piece with most placed neighbors
    return max(available, key=lambda p: count_placed_neighbors(p))
```
**Why**: Corner→Edge→Interior strategy mimics human solving approach.

### Completion Detection
```python
# Check if puzzle is complete
def is_complete():
    # All positions filled
    if any(board[r][c] is None for r, c in positions):
        return False
    
    # All pieces correctly placed
    return all(piece.is_correct_position for piece in placed_pieces)
```
**Why**: Validates both placement and correctness.

---

## Interview Talking Points

### Opening (0-5 min)
- "I'll design a jigsaw puzzle game with intelligent piece matching and hint system"
- "Core challenge: edge pattern validation, rotation handling, efficient placement checking"
- "Will use Singleton for game state, Factory for puzzle generation, Strategy for matching"

### During Implementation (15-55 min)
- "Using edge pattern matching (IN/OUT/FLAT) to validate piece connections"
- "Memento pattern enables unlimited undo/redo without memory bloat"
- "Hint algorithm prioritizes corners, then edges, then pieces with placed neighbors"
- "Rotation handled by cycling edge array: [TOP,RIGHT,BOTTOM,LEFT]"

### Closing Demo (70-75 min)
- "Demo 1: Generate 4×4 puzzle - shows factory pattern"
- "Demo 2: Place corner and edge pieces - shows validation"
- "Demo 3: Rotation and matching - shows edge pattern logic"
- "Demo 4: Hint system walkthrough - shows strategy pattern"
- "Demo 5: Undo/redo functionality - shows memento pattern"

---

## Success Checklist

- [ ] Draw system architecture with 6 entities
- [ ] Explain edge pattern matching (IN/OUT/FLAT)
- [ ] Show 2 matching strategies side-by-side
- [ ] Demonstrate rotation with edge cycling
- [ ] Describe observer pattern event flow
- [ ] Calculate completion percentage on whiteboard
- [ ] Discuss memento pattern for undo/redo
- [ ] Propose 2 scalability improvements (hints cache, parallel validation)
- [ ] Answer follow-up on 3D puzzles or collaborative mode
- [ ] Run working code with 5 demos

---

## Anti-Patterns to Avoid

**DON'T**:
- Hard-code puzzle dimensions in Game (violates Open/Closed)
- Create multiple PuzzleGame instances (violates Singleton)
- Allow piece placement without edge validation (causes invalid state)
- Store entire board state in each Memento (memory waste)
- Skip rotation normalization (causes matching failures)

**DO**:
- Make matching strategies pluggable with abstract base class
- Validate edge patterns before placement
- Store only changed pieces in Memento (efficient undo)
- Explain trade-offs (exact vs fuzzy matching, memory vs speed)
- Propose optimizations (spatial hashing, edge pre-matching)

---

## 3 Advanced Follow-Ups (Be Ready)

### 1. 3D Puzzle Support
"Add Piece.faces[] for 6 faces. Implement 3D board with x/y/z coordinates. Validate edge matching on all 6 sides. Render with perspective projection."

### 2. Collaborative Multi-Player
"Add Player.cursor_position for real-time tracking. Implement optimistic locking for simultaneous placements. Broadcast moves via WebSocket. Handle conflicts with last-write-wins."

### 3. Scaling to 10,000 Piece Puzzle
"Partition board into regions for parallel validation. Use spatial index (quadtree) for piece lookup. Cache edge matching results. Stream pieces on-demand. GPU acceleration for image processing."

---

## Run Commands

```bash
# Execute all 5 demos
python3 INTERVIEW_COMPACT.py

# Check syntax
python3 -m py_compile INTERVIEW_COMPACT.py

# View guide
cat 75_MINUTE_GUIDE.md
```

---

## The 60-Second Pitch

"I designed a jigsaw puzzle game with 6 core entities: Piece, Edge, Board, Game, Player, Move. Uses Singleton for game state, Factory for puzzle generation (4×4 to 50×50), Strategy pattern for matching (Exact/ColorSimilarity/EdgePattern), Observer for events, and Memento for undo/redo. Key algorithm is edge pattern matching with IN/OUT/FLAT validation. Hint system prioritizes corners→edges→pieces with neighbors. Demo shows 4×4 puzzle generation, piece placement with rotation, edge validation, hint generation, and undo/redo. Scales with spatial indexing and parallel validation."

---

## What Interviewers Look For

1. **Clarity**: Can you explain edge matching logic simply?
2. **Patterns**: Do you recognize when to apply design patterns?
3. **Trade-offs**: Do you discuss pros/cons of approaches?
4. **Scalability**: Can you think beyond small puzzles?
5. **Code Quality**: Is code clean, readable, well-structured?
6. **Problem-Solving**: How do you handle edge cases?
7. **Communication**: Do you think out loud?

---

## Final Tips

- **Draw first, code later**: Spend 10 minutes on architecture diagram
- **State assumptions clearly**: "Assuming rectangular puzzles, no irregular shapes"
- **Test edge cases**: Corner pieces, rotation, invalid placements
- **Explain as you code**: "Using IN/OUT pattern to ensure tabs fit sockets"
- **Time management**: Leave 5 minutes for demo, don't over-engineer

**Good luck!** Run the code, understand the patterns, and explain trade-offs confidently.
