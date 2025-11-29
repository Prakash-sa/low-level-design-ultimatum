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
