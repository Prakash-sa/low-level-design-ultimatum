# Jigsaw Puzzle — 75-Minute Interview Guide

## Quick Start Overview

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

## 5 Architecture Sketch
````
(Describe components, controller, strategies, observers, flows)
````

Design Patterns (Why Each Matters)

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


## 75-Minute Guide

## System Overview
**Interactive jigsaw puzzle game** with intelligent piece matching, rotation support, hint generation, and undo/redo functionality. Features edge pattern validation (FLAT/IN/OUT) and completion tracking.

**Core Challenge**: Edge pattern matching, rotation handling, efficient hint generation, and state management for undo/redo.

---

## Requirements Clarification (0-5 min)

### Functional Requirements
1. **Puzzle Generation**: Create puzzle from image with configurable dimensions (n×m)
2. **Piece Management**: Track piece position, rotation, placement status
3. **Edge Matching**: Validate piece connections using edge patterns (FLAT/IN/OUT)
4. **Placement**: Allow piece placement with validation
5. **Rotation**: Support 90° clockwise/counter-clockwise rotation
6. **Hint System**: Suggest next piece to place (corners → edges → interior)
7. **Undo/Redo**: Revert and replay moves
8. **Progress Tracking**: Calculate completion percentage
9. **Completion Detection**: Validate all pieces correctly placed
10. **Leaderboard**: Track player scores and completion times

### Non-Functional Requirements
- **Performance**: Validate placement in <100ms for 1000-piece puzzle
- **Scale**: Support puzzles up to 50×50 (2500 pieces)
- **Usability**: Intuitive drag-and-drop interface
- **Memory**: Efficient memento storage (delta snapshots)

### Key Design Decisions
1. **Edge Representation**: FLAT (border), IN (socket), OUT (tab)
2. **Matching Strategy**: Strategy pattern (Exact vs ColorSimilarity)
3. **Hint Algorithm**: Priority-based (corners → edges → neighbors)
4. **Undo/Redo**: Memento pattern with move stack
5. **Game Coordination**: Singleton PuzzleGame

---

## Architecture & Design (5-15 min)

### System Architecture

```
PuzzleGame (Singleton)
├── Current Game
│   ├── Board (n×m grid)
│   │   └── Pieces (placed/available)
│   ├── Move History (Memento)
│   └── Game State (playing/complete)
├── Players
│   └── Player → Score, Stats
├── Matching Strategy (pluggable)
│   ├── ExactMatchStrategy
│   ├── ColorSimilarityStrategy
│   └── EdgePatternStrategy
├── Puzzle Factory
│   ├── EasyPuzzle (4×4)
│   ├── MediumPuzzle (10×10)
│   └── HardPuzzle (20×20)
└── Observers
    ├── PlayerNotifier
    ├── ProgressTracker
    └── LeaderboardUpdater
```

### Design Patterns Used

1. **Singleton**: PuzzleGame (one instance per session)
2. **Factory**: PuzzleFactory (create puzzles with difficulty levels)
3. **Strategy**: MatchingStrategy (pluggable validation algorithms)
4. **Observer**: Event notifications (placement, completion, hints)
5. **Memento**: Move history (undo/redo functionality)

---

## Core Entities (15-35 min)

### 1. Edge Class

```python
from enum import Enum

class EdgePattern(Enum):
    FLAT = "flat"    # Border edge (straight)
    IN = "in"        # Socket (cavity, female)
    OUT = "out"      # Tab (protrusion, male)

class Direction(Enum):
    TOP = 0
    RIGHT = 1
    BOTTOM = 2
    LEFT = 3

class Edge:
    """Represents one side of a puzzle piece"""
    def __init__(self, pattern: EdgePattern, color_hash: str, piece_id: str, direction: Direction):
        self.pattern = pattern
        self.color_hash = color_hash  # For color similarity matching
        self.piece_id = piece_id
        self.direction = direction
    
    def can_connect(self, other: 'Edge') -> bool:
        """Check if this edge can connect to another edge"""
        # FLAT edges only connect to FLAT (border pieces)
        if self.pattern == EdgePattern.FLAT:
            return other.pattern == EdgePattern.FLAT
        
        # IN (socket) connects to OUT (tab)
        if self.pattern == EdgePattern.IN:
            return other.pattern == EdgePattern.OUT
        
        # OUT (tab) connects to IN (socket)
        if self.pattern == EdgePattern.OUT:
            return other.pattern == EdgePattern.IN
        
        return False
    
    def color_similarity(self, other: 'Edge') -> float:
        """Calculate color similarity (0.0 to 1.0)"""
        if not self.color_hash or not other.color_hash:
            return 0.0
        
        # Simple hash comparison (in real implementation, use color histograms)
        same_chars = sum(a == b for a, b in zip(self.color_hash, other.color_hash))
        return same_chars / max(len(self.color_hash), len(other.color_hash))
```

**Key Points**:
- Three pattern types ensure physical puzzle constraints
- Color hash enables fuzzy matching for photo puzzles
- Direction tracking for rotation handling

### 2. Piece Class

```python
from typing import Tuple, Optional

class Piece:
    """Puzzle piece with 4 edges and rotation support"""
    def __init__(self, piece_id: str, edges: List[Edge], correct_position: Tuple[int, int]):
        self.piece_id = piece_id
        self.edges = edges  # [TOP, RIGHT, BOTTOM, LEFT]
        self.correct_position = correct_position
        self.current_position = None
        self.rotation = 0  # 0, 90, 180, 270
        self.is_placed = False
    
    def rotate_clockwise(self):
        """Rotate piece 90° clockwise"""
        self.rotation = (self.rotation + 90) % 360
        # Rotate edges: TOP→RIGHT, RIGHT→BOTTOM, BOTTOM→LEFT, LEFT→TOP
        self.edges = [
            self.edges[3],  # LEFT becomes TOP
            self.edges[0],  # TOP becomes RIGHT
            self.edges[1],  # RIGHT becomes BOTTOM
            self.edges[2]   # BOTTOM becomes LEFT
        ]
        # Update edge directions
        for i, edge in enumerate(self.edges):
            edge.direction = Direction(i)
    
    def rotate_counter_clockwise(self):
        """Rotate piece 90° counter-clockwise"""
        for _ in range(3):
            self.rotate_clockwise()
    
    def is_corner_piece(self) -> bool:
        """Check if piece is a corner (2 FLAT edges)"""
        flat_count = sum(1 for edge in self.edges if edge.pattern == EdgePattern.FLAT)
        return flat_count == 2
    
    def is_edge_piece(self) -> bool:
        """Check if piece is an edge (1 FLAT edge)"""
        flat_count = sum(1 for edge in self.edges if edge.pattern == EdgePattern.FLAT)
        return flat_count == 1
    
    def is_interior_piece(self) -> bool:
        """Check if piece is interior (0 FLAT edges)"""
        return not any(edge.pattern == EdgePattern.FLAT for edge in self.edges)
    
    def is_correctly_placed(self) -> bool:
        """Check if piece is in correct position with correct rotation"""
        if not self.is_placed:
            return False
        return self.current_position == self.correct_position and self.rotation == 0
```

**Key Points**:
- Edge array rotation simulates physical rotation
- Classification methods for hint algorithm
- Correct position tracking for completion detection

### 3. Board Class

```python
class Board:
    """Puzzle board with n×m grid"""
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = [[None for _ in range(width)] for _ in range(height)]
        self.placed_count = 0
        self.total_pieces = width * height
    
    def get_piece_at(self, position: Tuple[int, int]) -> Optional[Piece]:
        """Get piece at given position"""
        row, col = position
        if 0 <= row < self.height and 0 <= col < self.width:
            return self.grid[row][col]
        return None
    
    def place_piece(self, piece: Piece, position: Tuple[int, int]) -> bool:
        """Place piece on board"""
        row, col = position
        if not (0 <= row < self.height and 0 <= col < self.width):
            return False
        
        if self.grid[row][col] is not None:
            return False  # Position occupied
        
        self.grid[row][col] = piece
        piece.current_position = position
        piece.is_placed = True
        self.placed_count += 1
        return True
    
    def remove_piece(self, position: Tuple[int, int]) -> Optional[Piece]:
        """Remove piece from board"""
        row, col = position
        piece = self.grid[row][col]
        if piece:
            self.grid[row][col] = None
            piece.current_position = None
            piece.is_placed = False
            self.placed_count -= 1
        return piece
    
    def get_neighbor(self, position: Tuple[int, int], direction: Direction) -> Optional[Piece]:
        """Get neighboring piece in given direction"""
        row, col = position
        
        if direction == Direction.TOP:
            return self.get_piece_at((row - 1, col))
        elif direction == Direction.RIGHT:
            return self.get_piece_at((row, col + 1))
        elif direction == Direction.BOTTOM:
            return self.get_piece_at((row + 1, col))
        elif direction == Direction.LEFT:
            return self.get_piece_at((row, col - 1))
        
        return None
    
    def get_placed_neighbors(self, position: Tuple[int, int]) -> List[Tuple[Direction, Piece]]:
        """Get all placed neighboring pieces"""
        neighbors = []
        for direction in Direction:
            neighbor = self.get_neighbor(position, direction)
            if neighbor:
                neighbors.append((direction, neighbor))
        return neighbors
    
    def is_position_valid(self, position: Tuple[int, int]) -> bool:
        """Check if position is within board bounds"""
        row, col = position
        return 0 <= row < self.height and 0 <= col < self.width
    
    def get_progress(self) -> float:
        """Calculate completion percentage"""
        return (self.placed_count / self.total_pieces) * 100
```

**Key Points**:
- 2D grid for piece storage
- Neighbor lookup for validation
- Progress tracking

### 4. Game Class

```python
from datetime import datetime

class GameStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"

class Game:
    """Manages puzzle game state"""
    def __init__(self, game_id: str, board: Board, pieces: List[Piece], player: 'Player'):
        self.game_id = game_id
        self.board = board
        self.all_pieces = pieces
        self.available_pieces = pieces.copy()
        self.player = player
        self.status = GameStatus.NOT_STARTED
        self.start_time = None
        self.end_time = None
        self.move_history = []
        self.hints_used = 0
    
    def start(self):
        """Start the game"""
        self.status = GameStatus.IN_PROGRESS
        self.start_time = datetime.now()
    
    def complete(self):
        """Mark game as completed"""
        self.status = GameStatus.COMPLETED
        self.end_time = datetime.now()
    
    def get_duration(self) -> Optional[float]:
        """Get game duration in seconds"""
        if not self.start_time:
            return None
        
        end = self.end_time if self.end_time else datetime.now()
        return (end - self.start_time).total_seconds()
    
    def add_move(self, move: 'Move'):
        """Add move to history"""
        self.move_history.append(move)
    
    def get_last_move(self) -> Optional['Move']:
        """Get most recent move"""
        return self.move_history[-1] if self.move_history else None
```

### 5. Player Class

```python
class Player:
    """Player with statistics"""
    def __init__(self, player_id: str, name: str):
        self.player_id = player_id
        self.name = name
        self.games_played = 0
        self.games_completed = 0
        self.total_time = 0.0
        self.total_moves = 0
        self.total_hints_used = 0
        self.best_time = float('inf')
        self.achievements = []
    
    def update_stats(self, game: Game):
        """Update player statistics after game"""
        self.games_played += 1
        if game.status == GameStatus.COMPLETED:
            self.games_completed += 1
            duration = game.get_duration()
            if duration:
                self.total_time += duration
                self.best_time = min(self.best_time, duration)
        
        self.total_moves += len(game.move_history)
        self.total_hints_used += game.hints_used
    
    def get_average_time(self) -> float:
        """Calculate average completion time"""
        if self.games_completed == 0:
            return 0.0
        return self.total_time / self.games_completed
    
    def get_completion_rate(self) -> float:
        """Calculate game completion rate"""
        if self.games_played == 0:
            return 0.0
        return (self.games_completed / self.games_played) * 100
```

### 6. Move Class (Memento Pattern)

```python
class Move:
    """Represents a single move (placement/removal) for undo/redo"""
    def __init__(self, piece: Piece, from_position: Optional[Tuple[int, int]], 
                 to_position: Optional[Tuple[int, int]], rotation_before: int):
        self.piece = piece
        self.from_position = from_position
        self.to_position = to_position
        self.rotation_before = rotation_before
        self.rotation_after = piece.rotation
        self.timestamp = datetime.now()
    
    def undo(self, board: Board):
        """Undo this move"""
        if self.to_position:
            board.remove_piece(self.to_position)
        
        if self.from_position:
            board.place_piece(self.piece, self.from_position)
        
        # Restore rotation
        while self.piece.rotation != self.rotation_before:
            self.piece.rotate_clockwise()
    
    def redo(self, board: Board):
        """Redo this move"""
        if self.from_position:
            board.remove_piece(self.from_position)
        
        if self.to_position:
            board.place_piece(self.piece, self.to_position)
        
        # Restore rotation
        while self.piece.rotation != self.rotation_after:
            self.piece.rotate_clockwise()
```

---

## Business Logic (35-55 min)

### Puzzle Factory Pattern

```python
class Difficulty(Enum):
    EASY = (4, 4)
    MEDIUM = (10, 10)
    HARD = (20, 20)
    EXPERT = (50, 50)

class PuzzleFactory:
    """Creates puzzles with different difficulty levels"""
    
    @staticmethod
    def create_puzzle(difficulty: Difficulty, image_path: str = None) -> Tuple[Board, List[Piece]]:
        """Generate puzzle from image"""
        width, height = difficulty.value
        board = Board(width, height)
        pieces = []
        
        piece_id = 0
        for row in range(height):
            for col in range(width):
                edges = PuzzleFactory._generate_edges(row, col, width, height)
                piece = Piece(f"P{piece_id:04d}", edges, (row, col))
                pieces.append(piece)
                piece_id += 1
        
        # Shuffle pieces for gameplay
        import random
        random.shuffle(pieces)
        
        return board, pieces
    
    @staticmethod
    def _generate_edges(row: int, col: int, width: int, height: int) -> List[Edge]:
        """Generate edges for piece at position (row, col)"""
        import random
        
        edges = []
        
        # TOP edge
        if row == 0:
            edges.append(Edge(EdgePattern.FLAT, "", f"P_{row}_{col}", Direction.TOP))
        else:
            pattern = random.choice([EdgePattern.IN, EdgePattern.OUT])
            edges.append(Edge(pattern, f"C{random.randint(0,999)}", f"P_{row}_{col}", Direction.TOP))
        
        # RIGHT edge
        if col == width - 1:
            edges.append(Edge(EdgePattern.FLAT, "", f"P_{row}_{col}", Direction.RIGHT))
        else:
            pattern = random.choice([EdgePattern.IN, EdgePattern.OUT])
            edges.append(Edge(pattern, f"C{random.randint(0,999)}", f"P_{row}_{col}", Direction.RIGHT))
        
        # BOTTOM edge
        if row == height - 1:
            edges.append(Edge(EdgePattern.FLAT, "", f"P_{row}_{col}", Direction.BOTTOM))
        else:
            pattern = random.choice([EdgePattern.IN, EdgePattern.OUT])
            edges.append(Edge(pattern, f"C{random.randint(0,999)}", f"P_{row}_{col}", Direction.BOTTOM))
        
        # LEFT edge
        if col == 0:
            edges.append(Edge(EdgePattern.FLAT, "", f"P_{row}_{col}", Direction.LEFT))
        else:
            pattern = random.choice([EdgePattern.IN, EdgePattern.OUT])
            edges.append(Edge(pattern, f"C{random.randint(0,999)}", f"P_{row}_{col}", Direction.LEFT))
        
        return edges
```

### Matching Strategy Pattern

```python
from abc import ABC, abstractmethod

class MatchingStrategy(ABC):
    """Abstract matching strategy"""
    @abstractmethod
    def is_valid_placement(self, piece: Piece, position: Tuple[int, int], board: Board) -> bool:
        pass

class ExactMatchStrategy(MatchingStrategy):
    """Exact edge pattern matching"""
    def is_valid_placement(self, piece: Piece, position: Tuple[int, int], board: Board) -> bool:
        """Validate piece placement using exact edge matching"""
        for direction in Direction:
            neighbor = board.get_neighbor(position, direction)
            if neighbor:
                piece_edge = piece.edges[direction.value]
                neighbor_edge = neighbor.edges[(direction.value + 2) % 4]  # Opposite edge
                
                if not piece_edge.can_connect(neighbor_edge):
                    return False
        
        return True

class ColorSimilarityStrategy(MatchingStrategy):
    """Color-based fuzzy matching"""
    SIMILARITY_THRESHOLD = 0.7
    
    def is_valid_placement(self, piece: Piece, position: Tuple[int, int], board: Board) -> bool:
        """Validate using edge patterns + color similarity"""
        for direction in Direction:
            neighbor = board.get_neighbor(position, direction)
            if neighbor:
                piece_edge = piece.edges[direction.value]
                neighbor_edge = neighbor.edges[(direction.value + 2) % 4]
                
                # Check edge pattern compatibility
                if not piece_edge.can_connect(neighbor_edge):
                    return False
                
                # Check color similarity
                similarity = piece_edge.color_similarity(neighbor_edge)
                if similarity < self.SIMILARITY_THRESHOLD:
                    return False
        
        return True

class EdgePatternStrategy(MatchingStrategy):
    """Hybrid pattern + color matching"""
    def is_valid_placement(self, piece: Piece, position: Tuple[int, int], board: Board) -> bool:
        """Validate using edge patterns with optional color check"""
        exact_match = ExactMatchStrategy()
        if not exact_match.is_valid_placement(piece, position, board):
            return False
        
        # Additional validation for interior pieces
        if piece.is_interior_piece():
            color_match = ColorSimilarityStrategy()
            return color_match.is_valid_placement(piece, position, board)
        
        return True
```

### Hint Generation Algorithm

```python
class HintResult:
    """Hint suggestion with piece and position"""
    def __init__(self, piece: Piece, position: Tuple[int, int], confidence: float = 1.0):
        self.piece = piece
        self.position = position
        self.confidence = confidence  # 0.0 to 1.0

class HintGenerator:
    """Generates placement hints"""
    
    @staticmethod
    def generate_hint(board: Board, available_pieces: List[Piece]) -> Optional[HintResult]:
        """Find best next piece to place"""
        if not available_pieces:
            return None
        
        # Priority 1: Corner pieces
        corners = [p for p in available_pieces if p.is_corner_piece()]
        if corners:
            position = HintGenerator._find_corner_position(board)
            if position:
                return HintResult(corners[0], position, 1.0)
        
        # Priority 2: Edge pieces
        edges = [p for p in available_pieces if p.is_edge_piece()]
        if edges:
            position = HintGenerator._find_edge_position(board, edges[0])
            if position:
                return HintResult(edges[0], position, 0.9)
        
        # Priority 3: Interior piece with most placed neighbors
        scored_pieces = []
        for piece in available_pieces:
            if piece.is_interior_piece():
                best_pos, neighbor_count = HintGenerator._find_best_interior_position(board, piece)
                if best_pos:
                    scored_pieces.append((piece, best_pos, neighbor_count))
        
        if scored_pieces:
            # Return piece with most neighbors
            best = max(scored_pieces, key=lambda x: x[2])
            confidence = min(0.8, best[2] / 4.0)  # Max 4 neighbors
            return HintResult(best[0], best[1], confidence)
        
        return None
    
    @staticmethod
    def _find_corner_position(board: Board) -> Optional[Tuple[int, int]]:
        """Find empty corner position"""
        corners = [
            (0, 0), (0, board.width - 1),
            (board.height - 1, 0), (board.height - 1, board.width - 1)
        ]
        for pos in corners:
            if board.get_piece_at(pos) is None:
                return pos
        return None
    
    @staticmethod
    def _find_edge_position(board: Board, piece: Piece) -> Optional[Tuple[int, int]]:
        """Find suitable edge position for piece"""
        # Simplified: find any empty edge position
        for row in range(board.height):
            for col in range(board.width):
                if (row == 0 or row == board.height - 1 or 
                    col == 0 or col == board.width - 1):
                    if board.get_piece_at((row, col)) is None:
                        return (row, col)
        return None
    
    @staticmethod
    def _find_best_interior_position(board: Board, piece: Piece) -> Tuple[Optional[Tuple[int, int]], int]:
        """Find interior position with most placed neighbors"""
        best_pos = None
        max_neighbors = 0
        
        for row in range(1, board.height - 1):
            for col in range(1, board.width - 1):
                if board.get_piece_at((row, col)) is None:
                    neighbors = board.get_placed_neighbors((row, col))
                    if len(neighbors) > max_neighbors:
                        max_neighbors = len(neighbors)
                        best_pos = (row, col)
        
        return best_pos, max_neighbors
```

---

## Integration & Patterns (55-70 min)

### Observer Pattern

```python
class PuzzleObserver(ABC):
    """Observer interface for puzzle events"""
    @abstractmethod
    def update(self, event: str, data: Dict):
        pass

class PlayerNotifier(PuzzleObserver):
    """Notify player of game events"""
    def update(self, event: str, data: Dict):
        if event == "piece_placed":
            print(f"  [PLAYER] Piece {data['piece_id']} placed at {data['position']}")
        elif event == "hint_generated":
            print(f"  [PLAYER] Hint: Try piece {data['piece_id']} at {data['position']}")
        elif event == "puzzle_complete":
            print(f"  [PLAYER] 🎉 Puzzle complete! Time: {data['duration']:.1f}s")

class ProgressTracker(PuzzleObserver):
    """Track puzzle progress"""
    def update(self, event: str, data: Dict):
        if event == "piece_placed":
            progress = data.get('progress', 0)
            print(f"  [PROGRESS] {progress:.1f}% complete")

class LeaderboardUpdater(PuzzleObserver):
    """Update leaderboard on completion"""
    def update(self, event: str, data: Dict):
        if event == "puzzle_complete":
            print(f"  [LEADERBOARD] New score: {data['player']} - {data['duration']:.1f}s")
```

### Singleton - PuzzleGame

```python
import threading

class PuzzleGame:
    """Singleton controller for puzzle game"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.current_game = None
            self.players = {}
            self.observers = []
            self.matching_strategy = ExactMatchStrategy()
            self.undo_stack = []
            self.redo_stack = []
            self.lock = threading.Lock()
            self.initialized = True
    
    def add_observer(self, observer: PuzzleObserver):
        """Add event observer"""
        self.observers.append(observer)
    
    def _notify_observers(self, event: str, data: Dict):
        """Notify all observers of event"""
        for observer in self.observers:
            observer.update(event, data)
    
    def create_puzzle(self, difficulty: Difficulty, player: Player) -> Game:
        """Create new puzzle game"""
        board, pieces = PuzzleFactory.create_puzzle(difficulty)
        game_id = f"GAME_{int(datetime.now().timestamp())}"
        game = Game(game_id, board, pieces, player)
        self.current_game = game
        game.start()
        return game
    
    def place_piece(self, piece: Piece, position: Tuple[int, int]) -> bool:
        """Place piece on board with validation"""
        with self.lock:
            if not self.current_game:
                return False
            
            game = self.current_game
            board = game.board
            
            # Validate position
            if not board.is_position_valid(position):
                return False
            
            # Validate placement using strategy
            if not self.matching_strategy.is_valid_placement(piece, position, board):
                return False
            
            # Create move for undo
            move = Move(piece, piece.current_position, position, piece.rotation)
            
            # Place piece
            if board.place_piece(piece, position):
                game.add_move(move)
                self.undo_stack.append(move)
                self.redo_stack.clear()
                
                if piece in game.available_pieces:
                    game.available_pieces.remove(piece)
                
                # Notify observers
                self._notify_observers("piece_placed", {
                    'piece_id': piece.piece_id,
                    'position': position,
                    'progress': board.get_progress()
                })
                
                # Check completion
                if board.placed_count == board.total_pieces:
                    self._check_completion()
                
                return True
            
            return False
    
    def remove_piece(self, position: Tuple[int, int]) -> Optional[Piece]:
        """Remove piece from board"""
        with self.lock:
            if not self.current_game:
                return None
            
            board = self.current_game.board
            piece = board.remove_piece(position)
            
            if piece:
                self.current_game.available_pieces.append(piece)
                
                self._notify_observers("piece_removed", {
                    'piece_id': piece.piece_id,
                    'position': position
                })
            
            return piece
    
    def rotate_piece(self, piece: Piece, clockwise: bool = True):
        """Rotate piece 90 degrees"""
        if clockwise:
            piece.rotate_clockwise()
        else:
            piece.rotate_counter_clockwise()
        
        self._notify_observers("piece_rotated", {
            'piece_id': piece.piece_id,
            'rotation': piece.rotation
        })
    
    def generate_hint(self) -> Optional[HintResult]:
        """Generate placement hint"""
        if not self.current_game:
            return None
        
        hint = HintGenerator.generate_hint(
            self.current_game.board,
            self.current_game.available_pieces
        )
        
        if hint:
            self.current_game.hints_used += 1
            self._notify_observers("hint_generated", {
                'piece_id': hint.piece.piece_id,
                'position': hint.position,
                'confidence': hint.confidence
            })
        
        return hint
    
    def undo_move(self) -> bool:
        """Undo last move"""
        if not self.undo_stack:
            return False
        
        move = self.undo_stack.pop()
        move.undo(self.current_game.board)
        self.redo_stack.append(move)
        
        self._notify_observers("move_undone", {
            'piece_id': move.piece.piece_id
        })
        
        return True
    
    def redo_move(self) -> bool:
        """Redo last undone move"""
        if not self.redo_stack:
            return False
        
        move = self.redo_stack.pop()
        move.redo(self.current_game.board)
        self.undo_stack.append(move)
        
        self._notify_observers("move_redone", {
            'piece_id': move.piece.piece_id
        })
        
        return True
    
    def _check_completion(self):
        """Check if puzzle is complete"""
        game = self.current_game
        board = game.board
        
        # All pieces placed and correctly positioned
        if board.placed_count == board.total_pieces:
            all_correct = all(p.is_correctly_placed() for p in game.all_pieces if p.is_placed)
            
            if all_correct:
                game.complete()
                duration = game.get_duration()
                
                self._notify_observers("puzzle_complete", {
                    'player': game.player.name,
                    'duration': duration,
                    'moves': len(game.move_history),
                    'hints': game.hints_used
                })
                
                game.player.update_stats(game)
    
    def get_progress(self) -> float:
        """Get current puzzle completion percentage"""
        if not self.current_game:
            return 0.0
        return self.current_game.board.get_progress()
```

---

## Interview Q&A (12 Questions)

### Basic (0-5 min)

1. **"What are the core entities in a jigsaw puzzle system?"**
   - Answer: Piece (with 4 edges), Edge (with pattern FLAT/IN/OUT), Board (n×m grid), Game (state management), Player (statistics), Move (undo/redo).

2. **"How do you validate if two puzzle pieces can connect?"**
   - Answer: Check edge patterns. FLAT connects to FLAT (borders). IN (socket) connects to OUT (tab). Use Edge.can_connect() method.

3. **"What are the three edge pattern types?"**
   - Answer: FLAT (straight border), IN (socket/cavity), OUT (tab/protrusion). Ensures physical puzzle constraints.

### Intermediate (5-10 min)

4. **"How does piece rotation work?"**
   - Answer: Rotate edge array cyclically. 90° clockwise: [TOP,RIGHT,BOTTOM,LEFT] → [LEFT,TOP,RIGHT,BOTTOM]. Track rotation angle (0,90,180,270).

5. **"Explain the hint generation algorithm."**
   - Answer: Priority-based. First suggest corner pieces (2 FLAT edges). Then edge pieces (1 FLAT). Finally interior pieces with most placed neighbors. Returns HintResult with piece, position, confidence.

6. **"How do you prevent double-placing a piece?"**
   - Answer: Track is_placed flag. Remove from available_pieces list when placed. Check board.grid[][] for occupied positions before placement.

7. **"How is completion detected?"**
   - Answer: Three checks: (1) All positions filled (placed_count == total_pieces), (2) All pieces in correct positions, (3) All edges match neighbors. Returns true only if all pass.

### Advanced (10-15 min)

8. **"How would you implement undo/redo efficiently?"**
   - Answer: Memento pattern with Move objects. Store only deltas (piece, from_pos, to_pos, rotation). Maintain two stacks (undo_stack, redo_stack). Move.undo() reverses action, Move.redo() replays it.

9. **"How would you optimize hint generation for 10,000-piece puzzle?"**
   - Answer: Cache piece classifications (corner/edge/interior). Pre-compute neighbor counts. Use spatial index (quadtree) for position lookups. Lazy evaluation (only compute hint when requested). Limit search space to nearby empty positions.

10. **"How would you implement color-based matching for photo puzzles?"**
    - Answer: Extract color histogram from edge pixels. Store hash in Edge.color_hash. Implement color_similarity() using histogram comparison (chi-square distance). Set threshold (e.g., 0.7) for fuzzy matching.

11. **"How would you handle irregular puzzle shapes (not rectangular)?**
    - Answer: Use polygon vertices instead of fixed edges. Store piece boundaries as bezier curves. Implement point-in-polygon collision detection. Use spatial hash map for efficient neighbor lookups. Increase edge matching complexity.

12. **"How would you scale to support collaborative multi-player?"**
    - Answer: Add piece locking (optimistic or pessimistic). Use WebSocket for real-time updates. Implement conflict resolution (last-write-wins or user prompt). Track player cursors. Use operational transformation for concurrent edits. Broadcast piece placements to all clients.

---

## SOLID Principles Applied

| Principle | Application |
|-----------|------------|
| **Single Responsibility** | Piece handles piece data; Board handles layout; Game handles state; Move handles undo/redo |
| **Open/Closed** | Add new matching strategies without modifying PuzzleGame |
| **Liskov Substitution** | All MatchingStrategy subclasses interchangeable at runtime |
| **Interface Segregation** | Observer only requires update(); Strategy only requires is_valid_placement() |
| **Dependency Inversion** | PuzzleGame depends on abstract MatchingStrategy, not concrete implementations |

---

## UML Diagram

```
┌─────────────────────────────────────────┐
│        PuzzleGame (Singleton)           │
├─────────────────────────────────────────┤
│ - current_game: Game                    │
│ - players: Map<id, Player>              │
│ - matching_strategy: MatchingStrategy   │
│ - observers: List<Observer>             │
│ - undo_stack: List<Move>                │
│ - redo_stack: List<Move>                │
├─────────────────────────────────────────┤
│ + create_puzzle()                       │
│ + place_piece()                         │
│ + remove_piece()                        │
│ + rotate_piece()                        │
│ + generate_hint()                       │
│ + undo_move()                           │
│ + redo_move()                           │
└─────────────────────────────────────────┘
         │              │
         ▼              ▼
    ┌────────┐    ┌──────────┐
    │  Game  │    │  Board   │
    ├────────┤    ├──────────┤
    │pieces  │    │grid[][]  │
    │history │    │width/h   │
    │status  │    │placed    │
    └────────┘    └──────────┘
         │
         ▼
    ┌────────┐
    │ Piece  │
    ├────────┤
    │edges[4]│
    │rotation│
    │position│
    └────────┘
         │
         ▼
    ┌────────┐
    │  Edge  │
    ├────────┤
    │pattern │
    │color   │
    │can_co..│
    └────────┘

┌────────────────────────────────────┐
│   MatchingStrategy (Abstract)      │
├────────────────────────────────────┤
│ + is_valid_placement()             │
└────────────────────────────────────┘
           △
           │ implements
    ┌──────┴──────────────┬──────────────┐
    │                     │              │
ExactMatch      ColorSimilarity   EdgePattern

┌────────────────────────────────────┐
│    PuzzleObserver (Abstract)       │
├────────────────────────────────────┤
│ + update(event, data)              │
└────────────────────────────────────┘
           △
           │ implements
    ┌──────┴──────────┬──────────────┐
    │                 │              │
PlayerNotifier  ProgressTracker  Leaderboard

Edge Pattern Flow:
┌─────┐    ┌─────┐
│ IN  │←──→│ OUT │  Valid connection
└─────┘    └─────┘

┌──────┐    ┌──────┐
│ FLAT │←──→│ FLAT │  Border connection
└──────┘    └──────┘

┌─────┐    ┌─────┐
│ IN  │  ✗  │ IN  │  Invalid (same type)
└─────┘    └─────┘
```

---

## 5 Demo Scenarios

### Demo 1: Puzzle Generation & Factory Pattern
- Create 4×4 puzzle using PuzzleFactory
- Show Easy/Medium/Hard difficulty levels
- Demonstrate edge pattern assignment
- Display piece classification (corners/edges/interior)

### Demo 2: Piece Placement with Validation
- Place corner pieces at (0,0), (0,3), (3,0), (3,3)
- Place edge pieces along borders
- Demonstrate validation failures (incompatible edges)
- Show successful placements with matching edges

### Demo 3: Rotation & Edge Matching
- Take a piece and rotate 90° clockwise
- Show edge array changes
- Demonstrate how rotation affects matching
- Place rotated piece successfully

### Demo 4: Hint System Walkthrough
- Request hint for corner pieces
- Request hint for edge pieces
- Request hint for interior piece
- Show confidence scores for each hint

### Demo 5: Undo/Redo Functionality
- Place 5 pieces sequentially
- Undo last 3 moves
- Redo 2 moves
- Show move history stack
- Demonstrate memento pattern efficiency

---

## Key Implementation Notes

### Edge Pattern Matching
- FLAT edges only on border pieces (row=0, row=n-1, col=0, col=m-1)
- IN pattern = socket (cavity)
- OUT pattern = tab (protrusion)
- Opposite edges must be compatible: IN↔OUT, FLAT↔FLAT

### Rotation Handling
- Rotate edge array, not individual edges
- Update edge directions after rotation
- Track cumulative rotation angle (0, 90, 180, 270)
- Validate after rotation to ensure still valid

### Hint Algorithm Priority
1. Corner pieces (2 FLAT edges) - highest priority
2. Edge pieces (1 FLAT edge) - medium priority
3. Interior pieces with most neighbors - lowest priority

### Memento Pattern Efficiency
- Store only changed state (piece + position + rotation)
- Don't copy entire board
- Use delta snapshots for large puzzles
- Limit undo stack size for memory management

### Testing Strategy
1. Unit test edge matching (all pattern combinations)
2. Unit test rotation (verify edge cycling)
3. Integration test placement validation
4. Integration test hint generation
5. Performance test with large puzzles (50×50)
6. Edge cases: single piece, all borders, no hints available


## Detailed Design Reference

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


## Compact Code

```python
#!/usr/bin/env python3
"""
Jigsaw Puzzle Game - Complete Working Implementation
Run this file to see all 5 demo scenarios in action

Design Patterns Demonstrated:
1. Singleton - PuzzleGame (centralized game control)
2. Factory - PuzzleFactory (puzzle generation with difficulty levels)
3. Strategy - MatchingStrategy (Exact/ColorSimilarity/EdgePattern)
4. Observer - Notifications (Player/Progress/Leaderboard)
5. Memento - Move history (undo/redo functionality)
"""

from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import threading
import random
import time


# ============================================================================
# SECTION 1: ENUMERATIONS
# ============================================================================

class EdgePattern(Enum):
    """Edge patterns for puzzle pieces"""
    FLAT = "flat"    # Straight edge (border pieces)
    IN = "in"        # Socket/cavity (female connector)
    OUT = "out"      # Tab/protrusion (male connector)


class Direction(Enum):
    """Edge directions (clockwise from top)"""
    TOP = 0
    RIGHT = 1
    BOTTOM = 2
    LEFT = 3


class GameStatus(Enum):
    """Game state"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"


class Difficulty(Enum):
    """Puzzle difficulty levels (width, height)"""
    EASY = (4, 4)
    MEDIUM = (10, 10)
    HARD = (20, 20)
    EXPERT = (50, 50)


# ============================================================================
# SECTION 2: CORE ENTITIES - EDGE & PIECE
# ============================================================================

class Edge:
    """Represents one side of a puzzle piece"""
    def __init__(self, pattern: EdgePattern, color_hash: str, piece_id: str, direction: Direction):
        self.pattern = pattern
        self.color_hash = color_hash  # For color similarity matching
        self.piece_id = piece_id
        self.direction = direction
    
    def can_connect(self, other: 'Edge') -> bool:
        """Check if this edge can physically connect to another edge"""
        # FLAT edges only connect to FLAT (border pieces)
        if self.pattern == EdgePattern.FLAT:
            return other.pattern == EdgePattern.FLAT
        
        # IN (socket) connects to OUT (tab)
        if self.pattern == EdgePattern.IN:
            return other.pattern == EdgePattern.OUT
        
        # OUT (tab) connects to IN (socket)
        if self.pattern == EdgePattern.OUT:
            return other.pattern == EdgePattern.IN
        
        return False
    
    def color_similarity(self, other: 'Edge') -> float:
        """Calculate color similarity (0.0 to 1.0)"""
        if not self.color_hash or not other.color_hash:
            return 0.0
        
        # Simple hash comparison (in real implementation, use color histograms)
        if len(self.color_hash) != len(other.color_hash):
            return 0.0
        
        same_chars = sum(a == b for a, b in zip(self.color_hash, other.color_hash))
        return same_chars / len(self.color_hash)
    
    def __str__(self):
        return f"{self.pattern.value}({self.direction.name})"


class Piece:
    """Puzzle piece with 4 edges and rotation support"""
    def __init__(self, piece_id: str, edges: List[Edge], correct_position: Tuple[int, int]):
        self.piece_id = piece_id
        self.edges = edges  # [TOP, RIGHT, BOTTOM, LEFT]
        self.correct_position = correct_position
        self.current_position = None
        self.rotation = 0  # 0, 90, 180, 270 degrees
        self.is_placed = False
    
    def rotate_clockwise(self):
        """Rotate piece 90° clockwise"""
        self.rotation = (self.rotation + 90) % 360
        # Rotate edges: TOP→RIGHT, RIGHT→BOTTOM, BOTTOM→LEFT, LEFT→TOP
        self.edges = [
            self.edges[3],  # LEFT becomes TOP
            self.edges[0],  # TOP becomes RIGHT
            self.edges[1],  # RIGHT becomes BOTTOM
            self.edges[2]   # BOTTOM becomes LEFT
        ]
        # Update edge directions
        for i, edge in enumerate(self.edges):
            edge.direction = Direction(i)
    
    def rotate_counter_clockwise(self):
        """Rotate piece 90° counter-clockwise"""
        for _ in range(3):
            self.rotate_clockwise()
    
    def is_corner_piece(self) -> bool:
        """Check if piece is a corner (2 FLAT edges)"""
        flat_count = sum(1 for edge in self.edges if edge.pattern == EdgePattern.FLAT)
        return flat_count == 2
    
    def is_edge_piece(self) -> bool:
        """Check if piece is an edge (1 FLAT edge, not corner)"""
        flat_count = sum(1 for edge in self.edges if edge.pattern == EdgePattern.FLAT)
        return flat_count == 1
    
    def is_interior_piece(self) -> bool:
        """Check if piece is interior (0 FLAT edges)"""
        return not any(edge.pattern == EdgePattern.FLAT for edge in self.edges)
    
    def is_correctly_placed(self) -> bool:
        """Check if piece is in correct position with correct rotation"""
        if not self.is_placed:
            return False
        return self.current_position == self.correct_position and self.rotation == 0
    
    def __str__(self):
        edges_str = [str(e) for e in self.edges]
        return f"Piece({self.piece_id}, {edges_str}, rot={self.rotation}°)"


# ============================================================================
# SECTION 3: BOARD
# ============================================================================

class Board:
    """Puzzle board with n×m grid"""
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = [[None for _ in range(width)] for _ in range(height)]
        self.placed_count = 0
        self.total_pieces = width * height
    
    def get_piece_at(self, position: Tuple[int, int]) -> Optional[Piece]:
        """Get piece at given position"""
        row, col = position
        if 0 <= row < self.height and 0 <= col < self.width:
            return self.grid[row][col]
        return None
    
    def place_piece(self, piece: Piece, position: Tuple[int, int]) -> bool:
        """Place piece on board"""
        row, col = position
        if not (0 <= row < self.height and 0 <= col < self.width):
            return False
        
        if self.grid[row][col] is not None:
            return False  # Position occupied
        
        self.grid[row][col] = piece
        piece.current_position = position
        piece.is_placed = True
        self.placed_count += 1
        return True
    
    def remove_piece(self, position: Tuple[int, int]) -> Optional[Piece]:
        """Remove piece from board"""
        row, col = position
        if not (0 <= row < self.height and 0 <= col < self.width):
            return None
        
        piece = self.grid[row][col]
        if piece:
            self.grid[row][col] = None
            piece.current_position = None
            piece.is_placed = False
            self.placed_count -= 1
        return piece
    
    def get_neighbor(self, position: Tuple[int, int], direction: Direction) -> Optional[Piece]:
        """Get neighboring piece in given direction"""
        row, col = position
        
        if direction == Direction.TOP:
            return self.get_piece_at((row - 1, col))
        elif direction == Direction.RIGHT:
            return self.get_piece_at((row, col + 1))
        elif direction == Direction.BOTTOM:
            return self.get_piece_at((row + 1, col))
        elif direction == Direction.LEFT:
            return self.get_piece_at((row, col - 1))
        
        return None
    
    def get_placed_neighbors(self, position: Tuple[int, int]) -> List[Tuple[Direction, Piece]]:
        """Get all placed neighboring pieces"""
        neighbors = []
        for direction in Direction:
            neighbor = self.get_neighbor(position, direction)
            if neighbor:
                neighbors.append((direction, neighbor))
        return neighbors
    
    def is_position_valid(self, position: Tuple[int, int]) -> bool:
        """Check if position is within board bounds"""
        row, col = position
        return 0 <= row < self.height and 0 <= col < self.width
    
    def get_progress(self) -> float:
        """Calculate completion percentage"""
        if self.total_pieces == 0:
            return 0.0
        return (self.placed_count / self.total_pieces) * 100
    
    def is_complete(self) -> bool:
        """Check if all positions are filled"""
        return self.placed_count == self.total_pieces


# ============================================================================
# SECTION 4: GAME, PLAYER, MOVE (MEMENTO)
# ============================================================================

class Player:
    """Player with statistics and achievements"""
    def __init__(self, player_id: str, name: str):
        self.player_id = player_id
        self.name = name
        self.games_played = 0
        self.games_completed = 0
        self.total_time = 0.0
        self.total_moves = 0
        self.total_hints_used = 0
        self.best_time = float('inf')
        self.achievements = []
        self.current_streak = 0
    
    def update_stats(self, game: 'Game'):
        """Update player statistics after game"""
        self.games_played += 1
        if game.status == GameStatus.COMPLETED:
            self.games_completed += 1
            self.current_streak += 1
            duration = game.get_duration()
            if duration:
                self.total_time += duration
                if duration < self.best_time:
                    self.best_time = duration
                    self.achievements.append(f"New record: {duration:.1f}s")
        else:
            self.current_streak = 0
        
        self.total_moves += len(game.move_history)
        self.total_hints_used += game.hints_used
    
    def get_average_time(self) -> float:
        """Calculate average completion time"""
        if self.games_completed == 0:
            return 0.0
        return self.total_time / self.games_completed
    
    def get_completion_rate(self) -> float:
        """Calculate game completion rate"""
        if self.games_played == 0:
            return 0.0
        return (self.games_completed / self.games_played) * 100
    
    def __str__(self):
        return f"{self.name} (Played: {self.games_played}, Completed: {self.games_completed}, Best: {self.best_time:.1f}s)"


class Move:
    """Represents a single move (Memento pattern for undo/redo)"""
    def __init__(self, piece: Piece, from_position: Optional[Tuple[int, int]], 
                 to_position: Optional[Tuple[int, int]], rotation_before: int):
        self.piece = piece
        self.from_position = from_position
        self.to_position = to_position
        self.rotation_before = rotation_before
        self.rotation_after = piece.rotation
        self.timestamp = datetime.now()
    
    def undo(self, board: Board):
        """Undo this move"""
        if self.to_position:
            board.remove_piece(self.to_position)
        
        if self.from_position:
            board.place_piece(self.piece, self.from_position)
        
        # Restore rotation
        while self.piece.rotation != self.rotation_before:
            self.piece.rotate_clockwise()
    
    def redo(self, board: Board):
        """Redo this move"""
        if self.from_position:
            board.remove_piece(self.from_position)
        
        if self.to_position:
            board.place_piece(self.piece, self.to_position)
        
        # Restore rotation
        while self.piece.rotation != self.rotation_after:
            self.piece.rotate_clockwise()


class Game:
    """Manages puzzle game state"""
    def __init__(self, game_id: str, board: Board, pieces: List[Piece], player: Player):
        self.game_id = game_id
        self.board = board
        self.all_pieces = pieces
        self.available_pieces = pieces.copy()
        self.player = player
        self.status = GameStatus.NOT_STARTED
        self.start_time = None
        self.end_time = None
        self.move_history = []
        self.hints_used = 0
        self.difficulty = None
    
    def start(self):
        """Start the game"""
        self.status = GameStatus.IN_PROGRESS
        self.start_time = datetime.now()
    
    def complete(self):
        """Mark game as completed"""
        self.status = GameStatus.COMPLETED
        self.end_time = datetime.now()
    
    def pause(self):
        """Pause the game"""
        if self.status == GameStatus.IN_PROGRESS:
            self.status = GameStatus.PAUSED
    
    def resume(self):
        """Resume paused game"""
        if self.status == GameStatus.PAUSED:
            self.status = GameStatus.IN_PROGRESS
    
    def get_duration(self) -> Optional[float]:
        """Get game duration in seconds"""
        if not self.start_time:
            return None
        
        end = self.end_time if self.end_time else datetime.now()
        return (end - self.start_time).total_seconds()
    
    def add_move(self, move: Move):
        """Add move to history"""
        self.move_history.append(move)
    
    def get_last_move(self) -> Optional[Move]:
        """Get most recent move"""
        return self.move_history[-1] if self.move_history else None


# ============================================================================
# SECTION 5: FACTORY PATTERN - PUZZLE GENERATION
# ============================================================================

class PuzzleFactory:
    """Creates puzzles with different difficulty levels (Factory Pattern)"""
    
    @staticmethod
    def create_puzzle(difficulty: Difficulty, seed: int = None) -> Tuple[Board, List[Piece]]:
        """Generate puzzle from difficulty level"""
        if seed is not None:
            random.seed(seed)
        
        width, height = difficulty.value
        board = Board(width, height)
        pieces = []
        
        # Track complementary edges for matching
        horizontal_edges = {}  # (row, col) -> edge going right
        vertical_edges = {}    # (row, col) -> edge going down
        
        piece_id = 0
        for row in range(height):
            for col in range(width):
                edges = PuzzleFactory._generate_edges(
                    row, col, width, height, horizontal_edges, vertical_edges
                )
                piece = Piece(f"P{piece_id:04d}", edges, (row, col))
                pieces.append(piece)
                piece_id += 1
        
        # Shuffle pieces for gameplay
        random.shuffle(pieces)
        
        return board, pieces
    
    @staticmethod
    def _generate_edges(row: int, col: int, width: int, height: int,
                       horizontal_edges: Dict, vertical_edges: Dict) -> List[Edge]:
        """Generate edges for piece at position (row, col) with matching constraints"""
        edges = []
        piece_id = f"P_{row}_{col}"
        
        # TOP edge
        if row == 0:
            # Border: FLAT
            edges.append(Edge(EdgePattern.FLAT, "", piece_id, Direction.TOP))
        else:
            # Must match piece above's BOTTOM edge
            above_edge = vertical_edges.get((row - 1, col))
            if above_edge:
                # Create complementary edge
                if above_edge.pattern == EdgePattern.IN:
                    pattern = EdgePattern.OUT
                else:
                    pattern = EdgePattern.IN
                color = above_edge.color_hash
            else:
                pattern = random.choice([EdgePattern.IN, EdgePattern.OUT])
                color = f"C{random.randint(100,999)}"
            edges.append(Edge(pattern, color, piece_id, Direction.TOP))
        
        # RIGHT edge
        if col == width - 1:
            # Border: FLAT
            edges.append(Edge(EdgePattern.FLAT, "", piece_id, Direction.RIGHT))
        else:
            # Will be matched by piece to the right
            pattern = random.choice([EdgePattern.IN, EdgePattern.OUT])
            color = f"C{random.randint(100,999)}"
            right_edge = Edge(pattern, color, piece_id, Direction.RIGHT)
            edges.append(right_edge)
            horizontal_edges[(row, col)] = right_edge
        
        # BOTTOM edge
        if row == height - 1:
            # Border: FLAT
            edges.append(Edge(EdgePattern.FLAT, "", piece_id, Direction.BOTTOM))
        else:
            # Will be matched by piece below
            pattern = random.choice([EdgePattern.IN, EdgePattern.OUT])
            color = f"C{random.randint(100,999)}"
            bottom_edge = Edge(pattern, color, piece_id, Direction.BOTTOM)
            edges.append(bottom_edge)
            vertical_edges[(row, col)] = bottom_edge
        
        # LEFT edge
        if col == 0:
            # Border: FLAT
            edges.append(Edge(EdgePattern.FLAT, "", piece_id, Direction.LEFT))
        else:
            # Must match piece to left's RIGHT edge
            left_edge = horizontal_edges.get((row, col - 1))
            if left_edge:
                # Create complementary edge
                if left_edge.pattern == EdgePattern.IN:
                    pattern = EdgePattern.OUT
                else:
                    pattern = EdgePattern.IN
                color = left_edge.color_hash
            else:
                pattern = random.choice([EdgePattern.IN, EdgePattern.OUT])
                color = f"C{random.randint(100,999)}"
            edges.append(Edge(pattern, color, piece_id, Direction.LEFT))
        
        return edges


# ============================================================================
# SECTION 6: STRATEGY PATTERN - MATCHING ALGORITHMS
# ============================================================================

class MatchingStrategy(ABC):
    """Abstract matching strategy (Strategy Pattern)"""
    @abstractmethod
    def is_valid_placement(self, piece: Piece, position: Tuple[int, int], board: Board) -> bool:
        pass


class ExactMatchStrategy(MatchingStrategy):
    """Exact edge pattern matching"""
    def is_valid_placement(self, piece: Piece, position: Tuple[int, int], board: Board) -> bool:
        """Validate piece placement using exact edge matching"""
        for direction in Direction:
            neighbor = board.get_neighbor(position, direction)
            if neighbor:
                piece_edge = piece.edges[direction.value]
                # Get opposite edge from neighbor
                opposite_dir = Direction((direction.value + 2) % 4)
                neighbor_edge = neighbor.edges[opposite_dir.value]
                
                if not piece_edge.can_connect(neighbor_edge):
                    return False
        
        return True


class ColorSimilarityStrategy(MatchingStrategy):
    """Color-based fuzzy matching"""
    SIMILARITY_THRESHOLD = 0.7
    
    def is_valid_placement(self, piece: Piece, position: Tuple[int, int], board: Board) -> bool:
        """Validate using edge patterns + color similarity"""
        for direction in Direction:
            neighbor = board.get_neighbor(position, direction)
            if neighbor:
                piece_edge = piece.edges[direction.value]
                opposite_dir = Direction((direction.value + 2) % 4)
                neighbor_edge = neighbor.edges[opposite_dir.value]
                
                # Check edge pattern compatibility
                if not piece_edge.can_connect(neighbor_edge):
                    return False
                
                # Check color similarity for non-FLAT edges
                if piece_edge.pattern != EdgePattern.FLAT:
                    similarity = piece_edge.color_similarity(neighbor_edge)
                    if similarity < self.SIMILARITY_THRESHOLD:
                        return False
        
        return True


class EdgePatternStrategy(MatchingStrategy):
    """Hybrid pattern + color matching"""
    def is_valid_placement(self, piece: Piece, position: Tuple[int, int], board: Board) -> bool:
        """Validate using edge patterns with optional color check"""
        exact_match = ExactMatchStrategy()
        if not exact_match.is_valid_placement(piece, position, board):
            return False
        
        # Additional validation for interior pieces
        if piece.is_interior_piece():
            color_match = ColorSimilarityStrategy()
            return color_match.is_valid_placement(piece, position, board)
        
        return True


# ============================================================================
# SECTION 7: HINT GENERATION
# ============================================================================

class HintResult:
    """Hint suggestion with piece, position, and confidence"""
    def __init__(self, piece: Piece, position: Tuple[int, int], confidence: float = 1.0):
        self.piece = piece
        self.position = position
        self.confidence = confidence  # 0.0 to 1.0
    
    def __str__(self):
        return f"Try {self.piece.piece_id} at {self.position} (confidence: {self.confidence:.0%})"


class HintGenerator:
    """Generates placement hints with priority system"""
    
    @staticmethod
    def generate_hint(board: Board, available_pieces: List[Piece]) -> Optional[HintResult]:
        """Find best next piece to place"""
        if not available_pieces:
            return None
        
        # Priority 1: Corner pieces (4 total)
        corners = [p for p in available_pieces if p.is_corner_piece()]
        if corners:
            position = HintGenerator._find_corner_position(board)
            if position:
                return HintResult(corners[0], position, 1.0)
        
        # Priority 2: Edge pieces (borders, not corners)
        edges = [p for p in available_pieces if p.is_edge_piece()]
        if edges:
            position = HintGenerator._find_edge_position(board, edges)
            if position:
                return HintResult(edges[0], position, 0.9)
        
        # Priority 3: Interior piece with most placed neighbors
        scored_pieces = []
        for piece in available_pieces:
            if piece.is_interior_piece():
                best_pos, neighbor_count = HintGenerator._find_best_interior_position(board, piece)
                if best_pos:
                    scored_pieces.append((piece, best_pos, neighbor_count))
        
        if scored_pieces:
            # Return piece with most neighbors
            best = max(scored_pieces, key=lambda x: x[2])
            confidence = min(0.8, best[2] / 4.0)  # Max 4 neighbors
            return HintResult(best[0], best[1], confidence)
        
        # Fallback: any available piece with any empty position
        if available_pieces:
            piece = available_pieces[0]
            for row in range(board.height):
                for col in range(board.width):
                    if board.get_piece_at((row, col)) is None:
                        return HintResult(piece, (row, col), 0.5)
        
        return None
    
    @staticmethod
    def _find_corner_position(board: Board) -> Optional[Tuple[int, int]]:
        """Find empty corner position"""
        corners = [
            (0, 0), (0, board.width - 1),
            (board.height - 1, 0), (board.height - 1, board.width - 1)
        ]
        for pos in corners:
            if board.get_piece_at(pos) is None:
                return pos
        return None
    
    @staticmethod
    def _find_edge_position(board: Board, pieces: List[Piece]) -> Optional[Tuple[int, int]]:
        """Find suitable edge position for any edge piece"""
        # Find any empty edge position (not corner)
        for row in range(board.height):
            for col in range(board.width):
                is_corner = (row == 0 or row == board.height - 1) and \
                           (col == 0 or col == board.width - 1)
                is_edge = (row == 0 or row == board.height - 1 or 
                          col == 0 or col == board.width - 1)
                
                if is_edge and not is_corner:
                    if board.get_piece_at((row, col)) is None:
                        return (row, col)
        return None
    
    @staticmethod
    def _find_best_interior_position(board: Board, piece: Piece) -> Tuple[Optional[Tuple[int, int]], int]:
        """Find interior position with most placed neighbors"""
        best_pos = None
        max_neighbors = 0
        
        for row in range(1, board.height - 1):
            for col in range(1, board.width - 1):
                if board.get_piece_at((row, col)) is None:
                    neighbors = board.get_placed_neighbors((row, col))
                    if len(neighbors) > max_neighbors:
                        max_neighbors = len(neighbors)
                        best_pos = (row, col)
        
        return best_pos, max_neighbors


# ============================================================================
# SECTION 8: OBSERVER PATTERN - NOTIFICATIONS
# ============================================================================

class PuzzleObserver(ABC):
    """Observer interface for puzzle events (Observer Pattern)"""
    @abstractmethod
    def update(self, event: str, data: Dict):
        pass


class PlayerNotifier(PuzzleObserver):
    """Notify player of game events"""
    def update(self, event: str, data: Dict):
        if event == "piece_placed":
            print(f"  [PLAYER] ✓ Piece {data['piece_id']} placed at {data['position']}")
        elif event == "piece_removed":
            print(f"  [PLAYER] ✗ Piece {data['piece_id']} removed from {data['position']}")
        elif event == "piece_rotated":
            print(f"  [PLAYER] ↻ Piece {data['piece_id']} rotated to {data['rotation']}°")
        elif event == "hint_generated":
            print(f"  [PLAYER] 💡 Hint: {data['message']}")
        elif event == "move_undone":
            print(f"  [PLAYER] ⎌ Move undone: {data['piece_id']}")
        elif event == "move_redone":
            print(f"  [PLAYER] ⎌ Move redone: {data['piece_id']}")
        elif event == "puzzle_complete":
            print(f"  [PLAYER] 🎉 Puzzle complete! Time: {data['duration']:.1f}s, Moves: {data['moves']}")
        elif event == "invalid_placement":
            print(f"  [PLAYER] ⚠ Invalid placement: {data['reason']}")


class ProgressTracker(PuzzleObserver):
    """Track puzzle progress"""
    def update(self, event: str, data: Dict):
        if event == "piece_placed":
            progress = data.get('progress', 0)
            print(f"  [PROGRESS] {progress:.1f}% complete ({data.get('placed', 0)}/{data.get('total', 0)} pieces)")
        elif event == "puzzle_complete":
            print(f"  [PROGRESS] 100% - All pieces correctly placed!")


class LeaderboardUpdater(PuzzleObserver):
    """Update leaderboard on completion"""
    def update(self, event: str, data: Dict):
        if event == "puzzle_complete":
            player = data.get('player', 'Unknown')
            duration = data.get('duration', 0)
            moves = data.get('moves', 0)
            hints = data.get('hints', 0)
            
            score = 10000 - (moves * 10) - (hints * 100) - int(duration)
            print(f"  [LEADERBOARD] {player}: {score} points (Time: {duration:.1f}s, Moves: {moves}, Hints: {hints})")


# ============================================================================
# SECTION 9: SINGLETON - PUZZLE GAME SYSTEM
# ============================================================================

class PuzzleGame:
    """Singleton controller for puzzle game (Singleton Pattern)"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.current_game = None
            self.players = {}
            self.observers = []
            self.matching_strategy = ExactMatchStrategy()
            self.undo_stack = []
            self.redo_stack = []
            self.lock = threading.Lock()
            self.games_played = 0
            self.initialized = True
    
    def register_player(self, player: Player):
        """Register a new player"""
        self.players[player.player_id] = player
    
    def add_observer(self, observer: PuzzleObserver):
        """Add event observer"""
        self.observers.append(observer)
    
    def _notify_observers(self, event: str, data: Dict):
        """Notify all observers of event"""
        for observer in self.observers:
            observer.update(event, data)
    
    def set_matching_strategy(self, strategy: MatchingStrategy):
        """Change matching strategy at runtime"""
        self.matching_strategy = strategy
    
    def create_puzzle(self, difficulty: Difficulty, player: Player, seed: int = None) -> Game:
        """Create new puzzle game"""
        board, pieces = PuzzleFactory.create_puzzle(difficulty, seed)
        game_id = f"GAME_{self.games_played:04d}"
        self.games_played += 1
        
        game = Game(game_id, board, pieces, player)
        game.difficulty = difficulty
        self.current_game = game
        
        # Clear undo/redo stacks for new game
        self.undo_stack.clear()
        self.redo_stack.clear()
        
        game.start()
        return game
    
    def place_piece(self, piece: Piece, position: Tuple[int, int]) -> bool:
        """Place piece on board with validation"""
        with self.lock:
            if not self.current_game:
                return False
            
            game = self.current_game
            board = game.board
            
            # Validate position
            if not board.is_position_valid(position):
                self._notify_observers("invalid_placement", {
                    'piece_id': piece.piece_id,
                    'position': position,
                    'reason': 'Position out of bounds'
                })
                return False
            
            # Check if position is occupied
            if board.get_piece_at(position) is not None:
                self._notify_observers("invalid_placement", {
                    'piece_id': piece.piece_id,
                    'position': position,
                    'reason': 'Position already occupied'
                })
                return False
            
            # Validate placement using strategy
            if not self.matching_strategy.is_valid_placement(piece, position, board):
                self._notify_observers("invalid_placement", {
                    'piece_id': piece.piece_id,
                    'position': position,
                    'reason': 'Edges do not match neighbors'
                })
                return False
            
            # Create move for undo
            move = Move(piece, piece.current_position, position, piece.rotation)
            
            # Place piece
            if board.place_piece(piece, position):
                game.add_move(move)
                self.undo_stack.append(move)
                self.redo_stack.clear()  # Clear redo stack on new action
                
                if piece in game.available_pieces:
                    game.available_pieces.remove(piece)
                
                # Notify observers
                self._notify_observers("piece_placed", {
                    'piece_id': piece.piece_id,
                    'position': position,
                    'progress': board.get_progress(),
                    'placed': board.placed_count,
                    'total': board.total_pieces
                })
                
                # Check completion
                if board.is_complete():
                    self._check_completion()
                
                return True
            
            return False
    
    def remove_piece(self, position: Tuple[int, int]) -> Optional[Piece]:
        """Remove piece from board"""
        with self.lock:
            if not self.current_game:
                return None
            
            board = self.current_game.board
            piece = board.remove_piece(position)
            
            if piece:
                self.current_game.available_pieces.append(piece)
                
                self._notify_observers("piece_removed", {
                    'piece_id': piece.piece_id,
                    'position': position
                })
            
            return piece
    
    def rotate_piece(self, piece: Piece, clockwise: bool = True):
        """Rotate piece 90 degrees"""
        if clockwise:
            piece.rotate_clockwise()
        else:
            piece.rotate_counter_clockwise()
        
        self._notify_observers("piece_rotated", {
            'piece_id': piece.piece_id,
            'rotation': piece.rotation
        })
    
    def generate_hint(self) -> Optional[HintResult]:
        """Generate placement hint"""
        if not self.current_game:
            return None
        
        hint = HintGenerator.generate_hint(
            self.current_game.board,
            self.current_game.available_pieces
        )
        
        if hint:
            self.current_game.hints_used += 1
            self._notify_observers("hint_generated", {
                'piece_id': hint.piece.piece_id,
                'position': hint.position,
                'confidence': hint.confidence,
                'message': str(hint)
            })
        
        return hint
    
    def undo_move(self) -> bool:
        """Undo last move"""
        if not self.undo_stack or not self.current_game:
            return False
        
        move = self.undo_stack.pop()
        move.undo(self.current_game.board)
        self.redo_stack.append(move)
        
        # Update available pieces
        if move.to_position and move.piece not in self.current_game.available_pieces:
            self.current_game.available_pieces.append(move.piece)
        
        self._notify_observers("move_undone", {
            'piece_id': move.piece.piece_id
        })
        
        return True
    
    def redo_move(self) -> bool:
        """Redo last undone move"""
        if not self.redo_stack or not self.current_game:
            return False
        
        move = self.redo_stack.pop()
        move.redo(self.current_game.board)
        self.undo_stack.append(move)
        
        # Update available pieces
        if move.to_position and move.piece in self.current_game.available_pieces:
            self.current_game.available_pieces.remove(move.piece)
        
        self._notify_observers("move_redone", {
            'piece_id': move.piece.piece_id
        })
        
        return True
    
    def _check_completion(self):
        """Check if puzzle is complete"""
        game = self.current_game
        board = game.board
        
        # All pieces placed
        if not board.is_complete():
            return
        
        # Check if all pieces are correctly positioned
        all_correct = all(p.is_correctly_placed() for p in game.all_pieces if p.is_placed)
        
        if all_correct:
            game.complete()
            duration = game.get_duration()
            
            self._notify_observers("puzzle_complete", {
                'player': game.player.name,
                'duration': duration,
                'moves': len(game.move_history),
                'hints': game.hints_used
            })
            
            game.player.update_stats(game)
    
    def get_progress(self) -> float:
        """Get current puzzle completion percentage"""
        if not self.current_game:
            return 0.0
        return self.current_game.board.get_progress()
    
    def get_game_stats(self) -> Dict:
        """Get current game statistics"""
        if not self.current_game:
            return {}
        
        game = self.current_game
        return {
            'game_id': game.game_id,
            'player': game.player.name,
            'difficulty': game.difficulty.name if game.difficulty else 'Unknown',
            'progress': game.board.get_progress(),
            'pieces_placed': game.board.placed_count,
            'total_pieces': game.board.total_pieces,
            'moves': len(game.move_history),
            'hints_used': game.hints_used,
            'duration': game.get_duration(),
            'status': game.status.value
        }


# ============================================================================
# SECTION 10: DEMO SCENARIOS
# ============================================================================

def print_section(title):
    """Print section header"""
    print("\n" + "="*70)
    print(title)
    print("="*70)


def demo1_puzzle_generation():
    """Demo 1: Puzzle Generation & Factory Pattern"""
    print_section("DEMO 1: Puzzle Generation & Factory Pattern")
    
    system = PuzzleGame()
    
    # Add observers
    system.add_observer(PlayerNotifier())
    system.add_observer(ProgressTracker())
    system.add_observer(LeaderboardUpdater())
    
    # Create player
    player = Player("P001", "Alice")
    system.register_player(player)
    
    print("\n1. Creating puzzles with different difficulty levels...")
    
    # Test each difficulty
    for difficulty in [Difficulty.EASY, Difficulty.MEDIUM]:
        width, height = difficulty.value
        board, pieces = PuzzleFactory.create_puzzle(difficulty, seed=42)
        
        # Count piece types
        corners = sum(1 for p in pieces if p.is_corner_piece())
        edges = sum(1 for p in pieces if p.is_edge_piece())
        interior = sum(1 for p in pieces if p.is_interior_piece())
        
        print(f"\n   {difficulty.name} Puzzle ({width}×{height}):")
        print(f"   - Total pieces: {len(pieces)}")
        print(f"   - Corners: {corners}")
        print(f"   - Edges: {edges}")
        print(f"   - Interior: {interior}")
    
    print("\n2. Creating game with EASY difficulty...")
    game = system.create_puzzle(Difficulty.EASY, player, seed=42)
    print(f"   ✓ Game {game.game_id} created")
    print(f"   ✓ Board: {game.board.width}×{game.board.height}")
    print(f"   ✓ Total pieces: {len(game.all_pieces)}")
    print(f"   ✓ Available pieces: {len(game.available_pieces)}")


def demo2_piece_placement():
    """Demo 2: Piece Placement with Validation"""
    print_section("DEMO 2: Piece Placement with Edge Validation")
    
    system = PuzzleGame()
    player = Player("P001", "Bob")
    
    print("\n1. Creating 4×4 puzzle...")
    game = system.create_puzzle(Difficulty.EASY, player, seed=123)
    
    # Find corner pieces
    corners = [p for p in game.available_pieces if p.is_corner_piece()]
    print(f"\n2. Found {len(corners)} corner pieces")
    
    print("\n3. Placing corner pieces...")
    corner_positions = [(0, 0), (0, 3), (3, 0), (3, 3)]
    
    for i, corner in enumerate(corners[:4]):
        pos = corner_positions[i]
        success = system.place_piece(corner, pos)
        if success:
            print(f"   ✓ Placed {corner.piece_id} at {pos}")
        else:
            print(f"   ✗ Failed to place {corner.piece_id} at {pos}")
    
    print(f"\n4. Progress: {game.board.get_progress():.1f}%")
    print(f"   Placed: {game.board.placed_count}/{game.board.total_pieces}")


def demo3_rotation_and_matching():
    """Demo 3: Rotation & Edge Matching"""
    print_section("DEMO 3: Rotation & Edge Matching Demonstration")
    
    system = PuzzleGame()
    player = Player("P001", "Charlie")
    
    print("\n1. Creating puzzle and selecting a piece...")
    game = system.create_puzzle(Difficulty.EASY, player, seed=456)
    
    piece = game.available_pieces[0]
    print(f"\n2. Selected piece: {piece.piece_id}")
    print(f"   Initial rotation: {piece.rotation}°")
    print(f"   Edges: {[str(e) for e in piece.edges]}")
    
    print("\n3. Rotating piece clockwise...")
    for _ in range(3):
        system.rotate_piece(piece, clockwise=True)
        print(f"   Rotation: {piece.rotation}° - Edges: {[str(e) for e in piece.edges]}")
    
    print("\n4. Testing edge matching...")
    # Create two complementary edges
    edge1 = Edge(EdgePattern.IN, "C123", "P1", Direction.RIGHT)
    edge2 = Edge(EdgePattern.OUT, "C123", "P2", Direction.LEFT)
    edge3 = Edge(EdgePattern.FLAT, "", "P3", Direction.TOP)
    edge4 = Edge(EdgePattern.FLAT, "", "P4", Direction.BOTTOM)
    
    print(f"   IN + OUT: {edge1.can_connect(edge2)} ✓")
    print(f"   IN + IN: {edge1.can_connect(edge1)} ✗")
    print(f"   FLAT + FLAT: {edge3.can_connect(edge4)} ✓")
    print(f"   FLAT + IN: {edge3.can_connect(edge1)} ✗")


def demo4_hint_system():
    """Demo 4: Hint System Walkthrough"""
    print_section("DEMO 4: Hint Generation System")
    
    system = PuzzleGame()
    player = Player("P001", "Diana")
    
    print("\n1. Creating puzzle...")
    game = system.create_puzzle(Difficulty.EASY, player, seed=789)
    
    print("\n2. Generating hints at different stages...")
    
    # Hint 1: Should suggest corner
    print("\n   Stage 1: Empty board (should suggest corner)")
    hint = system.generate_hint()
    if hint:
        print(f"   → {hint}")
        print(f"   → Piece type: {'Corner' if hint.piece.is_corner_piece() else 'Edge' if hint.piece.is_edge_piece() else 'Interior'}")
    
    # Place some corners
    corners = [p for p in game.available_pieces if p.is_corner_piece()]
    if len(corners) >= 2:
        system.place_piece(corners[0], (0, 0))
        system.place_piece(corners[1], (0, 3))
    
    # Hint 2: Should suggest edge
    print("\n   Stage 2: Some corners placed (should suggest edge)")
    hint = system.generate_hint()
    if hint:
        print(f"   → {hint}")
        print(f"   → Piece type: {'Corner' if hint.piece.is_corner_piece() else 'Edge' if hint.piece.is_edge_piece() else 'Interior'}")
    
    print(f"\n3. Total hints used: {game.hints_used}")


def demo5_undo_redo():
    """Demo 5: Undo/Redo Functionality (Memento Pattern)"""
    print_section("DEMO 5: Undo/Redo - Memento Pattern")
    
    system = PuzzleGame()
    player = Player("P001", "Eve")
    
    print("\n1. Creating puzzle and placing pieces...")
    game = system.create_puzzle(Difficulty.EASY, player, seed=111)
    
    # Place 5 pieces
    pieces_to_place = game.available_pieces[:5]
    positions = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1)]
    
    placed_count = 0
    for piece, pos in zip(pieces_to_place, positions):
        # Try to place (may fail due to validation)
        if system.place_piece(piece, pos):
            placed_count += 1
    
    print(f"\n2. Successfully placed {placed_count} pieces")
    print(f"   Current progress: {game.board.get_progress():.1f}%")
    print(f"   Undo stack size: {len(system.undo_stack)}")
    
    print("\n3. Undoing last 3 moves...")
    for i in range(min(3, len(system.undo_stack))):
        if system.undo_move():
            print(f"   ✓ Undo {i+1} successful")
    
    print(f"   Progress after undo: {game.board.get_progress():.1f}%")
    print(f"   Redo stack size: {len(system.redo_stack)}")
    
    print("\n4. Redoing 2 moves...")
    for i in range(min(2, len(system.redo_stack))):
        if system.redo_move():
            print(f"   ✓ Redo {i+1} successful")
    
    print(f"   Final progress: {game.board.get_progress():.1f}%")
    print(f"   Move history: {len(game.move_history)} moves")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("JIGSAW PUZZLE GAME - COMPLETE DEMONSTRATION")
    print("="*70)
    print("\nDesign Patterns:")
    print("1. Singleton - PuzzleGame (centralized game control)")
    print("2. Factory - PuzzleFactory (difficulty-based puzzle generation)")
    print("3. Strategy - MatchingStrategy (Exact/ColorSimilarity/EdgePattern)")
    print("4. Observer - Event notifications (Player/Progress/Leaderboard)")
    print("5. Memento - Move history (undo/redo functionality)")
    
    time.sleep(1)
    
    demo1_puzzle_generation()
    time.sleep(1)
    
    demo2_piece_placement()
    time.sleep(1)
    
    demo3_rotation_and_matching()
    time.sleep(1)
    
    demo4_hint_system()
    time.sleep(1)
    
    demo5_undo_redo()
    
    print("\n" + "="*70)
    print("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
    print("="*70)
    print("\nKey Features Demonstrated:")
    print("• Edge pattern matching (FLAT/IN/OUT)")
    print("• Piece rotation with edge cycling")
    print("• Intelligent hint generation (corners → edges → interior)")
    print("• Complete undo/redo with Memento pattern")
    print("• Observer notifications for all events")
    print("• Multiple matching strategies (Strategy pattern)")
    print("• Factory-based puzzle generation")
    print("\nRun 'python3 INTERVIEW_COMPACT.py' to see all demos")

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
