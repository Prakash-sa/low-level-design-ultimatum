# Jigsaw Puzzle - 75 Minute Interview Guide

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
