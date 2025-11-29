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
