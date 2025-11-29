# Jigsaw Puzzle - Reference Guide

## System Overview
Interactive jigsaw puzzle game with intelligent piece matching, rotation support, hint generation, and undo/redo functionality. Features edge pattern validation and completion tracking.

---

## Core Entities

| Entity | Attributes | Responsibilities |
|--------|-----------|------------------|
| **Piece** | piece_id, edges[4], position, rotation, is_placed, correct_position | Store piece data, handle rotation, validate placement, track state |
| **Edge** | pattern (FLAT/IN/OUT), color_hash, piece_id, direction | Define piece boundaries, enable matching validation, store visual pattern |
| **Board** | width, height, grid[][], placed_count, total_pieces | Manage puzzle layout, track placements, validate positions, detect completion |
| **Game** | puzzle_id, board, available_pieces, move_history, start_time, status | Coordinate gameplay, manage state, track progress, handle game lifecycle |
| **Player** | player_id, name, score, games_played, total_time, hints_used | Track player stats, calculate rankings, store preferences |
| **Move** | piece, from_position, to_position, rotation, timestamp | Enable undo/redo, track history, support replay |
| **PuzzleGame** | current_game, players, matching_strategy, observers | Singleton coordinator, manage sessions, apply strategies |

---

## Design Patterns Implementation

| Pattern | Usage | Benefits |
|---------|-------|----------|
| **Singleton** | PuzzleGame - single instance manages game state | Centralized state, consistent board, single source of truth |
| **Factory** | PuzzleFactory creates puzzles from images with difficulty levels | Encapsulated generation, configurable complexity, consistent initialization |
| **Strategy** | Matching algorithms (Exact/ColorSimilarity/EdgePattern) | Pluggable validation, support different puzzle types |
| **Observer** | Event notifications (Player/Progress/Leaderboard) | Decoupled events, extensible handlers, real-time updates |
| **Memento** | Move history for undo/redo functionality | State preservation, efficient rollback, history tracking |

---

## Edge Pattern System

### Pattern Types

| Pattern | Description | Visual | Matches With |
|---------|-------------|--------|--------------|
| **FLAT** | Straight edge (border pieces) | `─` | FLAT only |
| **IN** | Socket/cavity (female) | `◠` | OUT only |
| **OUT** | Tab/protrusion (male) | `◡` | IN only |

### Matching Rules

```python
def can_connect(edge1: Edge, edge2: Edge) -> bool:
    """Validate if two edges can connect"""
    # Border pieces (FLAT) only connect to FLAT
    if edge1.pattern == EdgePattern.FLAT:
        return edge2.pattern == EdgePattern.FLAT
    
    # Socket (IN) connects to tab (OUT)
    if edge1.pattern == EdgePattern.IN:
        return edge2.pattern == EdgePattern.OUT
    
    # Tab (OUT) connects to socket (IN)
    if edge1.pattern == EdgePattern.OUT:
        return edge2.pattern == EdgePattern.IN
    
    return False
```

### Edge Directions

```
     TOP (0)
      ↑
      │
LEFT ←┼→ RIGHT (1)
(3)   │
      ↓
   BOTTOM (2)
```

**Rotation**: Edges rotate clockwise: `[TOP, RIGHT, BOTTOM, LEFT]`

---

## Matching Strategies Comparison

| Strategy | Logic | Accuracy | Performance | Use Case |
|----------|-------|----------|-------------|----------|
| **ExactMatchStrategy** | Pixel-perfect edge comparison | 100% | Fast | Traditional puzzles, solid colors |
| **ColorSimilarityStrategy** | Color histogram matching | ~95% | Medium | Photo puzzles, gradients |
| **EdgePatternStrategy** | Shape + color combination | ~98% | Fast | Hybrid approach, best overall |

**Example**:
```python
class ExactMatchStrategy(MatchingStrategy):
    def is_valid_placement(self, piece, position, board):
        # Check all 4 neighbors
        for direction in [TOP, RIGHT, BOTTOM, LEFT]:
            neighbor = board.get_neighbor(position, direction)
            if neighbor:
                edge1 = piece.edges[direction]
                edge2 = neighbor.edges[opposite(direction)]
                if not can_connect(edge1, edge2):
                    return False
        return True
```

---

## Rotation System

### How Rotation Works

```python
class Piece:
    def rotate_clockwise(self):
        """Rotate piece 90° clockwise"""
        self.rotation = (self.rotation + 90) % 360
        # Rotate edges: TOP→RIGHT, RIGHT→BOTTOM, etc.
        self.edges = [
            self.edges[3],  # LEFT becomes TOP
            self.edges[0],  # TOP becomes RIGHT
            self.edges[1],  # RIGHT becomes BOTTOM
            self.edges[2]   # BOTTOM becomes LEFT
        ]
```

### Rotation States

| Rotation | 0° | 90° | 180° | 270° |
|----------|----|----|------|------|
| **TOP** | Edge[0] | Edge[3] | Edge[2] | Edge[1] |
| **RIGHT** | Edge[1] | Edge[0] | Edge[3] | Edge[2] |
| **BOTTOM** | Edge[2] | Edge[1] | Edge[0] | Edge[3] |
| **LEFT** | Edge[3] | Edge[2] | Edge[1] | Edge[0] |

---

## Hint Generation Algorithm

```python
def generate_hint(board, available_pieces):
    """Find best next piece to place"""
    
    # Priority 1: Corner pieces (4 total)
    corners = [p for p in available_pieces 
               if p.edges[TOP].pattern == FLAT 
               and p.edges[LEFT].pattern == FLAT]
    if corners:
        return HintResult(corners[0], find_corner_position(board))
    
    # Priority 2: Edge pieces (borders)
    edges = [p for p in available_pieces if p.is_edge_piece()]
    if edges:
        position = find_best_edge_position(board, edges)
        return HintResult(edges[0], position)
    
    # Priority 3: Piece with most placed neighbors
    scored = [(p, count_matching_neighbors(p, board)) 
              for p in available_pieces]
    best_piece = max(scored, key=lambda x: x[1])[0]
    position = find_best_position(best_piece, board)
    
    return HintResult(best_piece, position)
```

**Complexity**: O(n) where n = available pieces
**Optimization**: Cache edge piece positions, pre-compute neighbor counts

---

## Completion Detection

```python
def check_completion(board):
    """Validate puzzle completion"""
    
    # Step 1: All positions filled
    for row in range(board.height):
        for col in range(board.width):
            if board.grid[row][col] is None:
                return False, "Incomplete puzzle"
    
    # Step 2: All pieces correctly placed
    for piece in board.get_all_pieces():
        if not piece.is_correct_position:
            return False, "Pieces incorrectly placed"
    
    # Step 3: All edges match neighbors
    for row in range(board.height):
        for col in range(board.width):
            piece = board.grid[row][col]
            if not validate_all_neighbors(piece, (row, col), board):
                return False, "Edge mismatch detected"
    
    return True, "Puzzle complete!"
```

---

## Observer Pattern Event Types

| Event | Triggered When | Notifiers Called | Example Message |
|-------|----------------|------------------|----------------|
| `piece_placed` | Piece successfully placed | Player, Progress | "Piece #42 placed at (3,5). 25% complete" |
| `piece_removed` | Piece removed from board | Player | "Piece #42 removed" |
| `rotation_changed` | Piece rotated | Player | "Piece rotated 90° clockwise" |
| `hint_requested` | Player asks for hint | Player, Progress | "Try corner piece #7 at (0,0)" |
| `move_undone` | Undo performed | Player | "Last move undone" |
| `puzzle_complete` | All pieces correctly placed | Player, Leaderboard | "Puzzle complete! Time: 15:32" |
| `achievement_unlocked` | Milestone reached | Player | "Achievement: Speed Solver (<10 min)" |

---

## SOLID Principles Applied

| Principle | Implementation |
|-----------|----------------|
| **Single Responsibility** | Piece handles piece data; Board handles layout; Game handles rules |
| **Open/Closed** | Add new matching strategies without modifying PuzzleGame |
| **Liskov Substitution** | All MatchingStrategy subclasses interchangeable at runtime |
| **Interface Segregation** | Observer requires only `update()`; Strategy requires single method |
| **Dependency Inversion** | PuzzleGame depends on abstract MatchingStrategy, not concrete classes |

---

## System Architecture Diagram

```
┌─────────────────────────────────────────┐
│      PuzzleGame (Singleton)             │
├─────────────────────────────────────────┤
│ - current_game: Game                    │
│ - players: Map<id, Player>              │
│ - matching_strategy: MatchingStrategy   │
│ - observers: List<Observer>             │
├─────────────────────────────────────────┤
│ + create_puzzle()                       │
│ + place_piece()                         │
│ + rotate_piece()                        │
│ + generate_hint()                       │
│ + undo_move()                           │
│ + check_completion()                    │
└─────────────────────────────────────────┘
         │              │
         ▼              ▼
    ┌────────┐    ┌──────────┐
    │  Game  │    │  Board   │
    ├────────┤    ├──────────┤
    │pieces  │    │grid[][]  │
    │history │    │width/h   │
    └────────┘    └──────────┘
         │
         ▼
    ┌────────┐
    │ Piece  │
    ├────────┤
    │edges[4]│
    │rotation│
    └────────┘
         │
         ▼
    ┌────────┐
    │  Edge  │
    ├────────┤
    │pattern │
    │color   │
    └────────┘
```

---

## Piece Classification

| Type | Characteristics | Count (n×m puzzle) | Edge Patterns |
|------|----------------|--------------------|-----------------|
| **Corner** | 2 FLAT edges, 2 non-FLAT | 4 | [FLAT,OUT,IN,FLAT] variants |
| **Edge** | 1 FLAT edge, 3 non-FLAT | 2(n+m-4) | [FLAT,OUT,IN,OUT] variants |
| **Interior** | 0 FLAT edges, 4 non-FLAT | (n-2)(m-2) | [OUT,IN,OUT,IN] variants |

**Example** (4×4 puzzle):
- 4 corners
- 8 edges (2×4 + 2×2)
- 4 interior
- **Total**: 16 pieces

---

## Performance Considerations

### Scalability Bottlenecks
1. **Placement Validation**: O(n) check all neighbors
2. **Hint Generation**: O(n × m) evaluate all piece-position pairs
3. **Completion Check**: O(n × m) validate entire board
4. **Memento Storage**: O(k) where k = number of moves

### Optimization Strategies
1. **Spatial Indexing**: Use quadtree for fast neighbor lookup
2. **Edge Caching**: Pre-compute compatible edge pairs
3. **Incremental Validation**: Only check changed pieces
4. **Lazy Hint Generation**: Compute hints on-demand, cache results
5. **Delta Memento**: Store only changed state, not full board
6. **Parallel Validation**: Multi-threaded completion checking

---

## Interview Success Checklist

- [ ] Explain all 6 core entities clearly
- [ ] Demonstrate edge pattern matching (FLAT/IN/OUT)
- [ ] Show rotation with edge cycling
- [ ] Implement hint algorithm with priorities
- [ ] Describe memento pattern for undo/redo
- [ ] Compare matching strategies (pros/cons)
- [ ] Explain observer pattern event flow
- [ ] Justify Singleton usage for PuzzleGame
- [ ] Propose 2+ scalability improvements
- [ ] Answer follow-up on 3D puzzles or collaborative mode

---

## Quick Commands

```bash
# Run all demos
python3 INTERVIEW_COMPACT.py

# Run with verbose output
python3 -u INTERVIEW_COMPACT.py

# Check for errors
python3 -m py_compile INTERVIEW_COMPACT.py
```

---

## Common Interview Follow-Ups

**Q: How would you implement puzzle generation from an image?**
A: Use image segmentation library (OpenCV). Divide image into n×m grid. For each piece, generate edge patterns randomly (ensuring matching neighbors). Extract color from edge pixels for ColorSimilarity matching. Apply edge effects (curved cuts) for realistic appearance.

**Q: How to handle irregular piece shapes (not rectangular)?**
A: Use polygon vertices instead of fixed edges. Implement point-in-polygon collision detection. Store bezier curves for piece boundaries. Increase complexity of matching algorithm (compare curve signatures).

**Q: How to support collaborative multi-player puzzles?**
A: Add piece locking (optimistic or pessimistic). Broadcast piece placements via WebSocket. Implement conflict resolution (last-write-wins or user prompt). Show other players' cursors in real-time. Use operational transformation for concurrent edits.

**Q: How to scale to 10,000 piece puzzles?**
A: Partition board into regions (quadtree). Load pieces on-demand (lazy loading). Use spatial index for fast lookups. Cache matching results in Redis. Implement progressive rendering (load high-priority pieces first). GPU acceleration for image processing.

**Q: How to add difficulty levels?**
A: **Easy**: 4×4 pieces, high contrast image, clear edges. **Medium**: 10×10, moderate contrast. **Hard**: 50×50, low contrast (sky/water). **Expert**: Irregular shapes, rotated pieces, mixed orientations.

**Q: How to implement realistic piece physics?**
A: Use Box2D physics engine. Add drag-and-drop with snap-to-grid. Implement collision detection for piece overlaps. Add rotation with mouse wheel or two-finger gesture. Magnetic snapping when edges align (within threshold).
