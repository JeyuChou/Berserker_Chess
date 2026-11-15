import chess

class BerserkerBoard(chess.Board):
    #Variant 1: extra move when taken (no banking)
    #Rules: 
    #1. When a piece is taken, the player who took it gets an extra move immediately.
    #2. The extra move must be used immediately and cannot be banked for later use.
    #3. The extra move can be any legal move according to standard chess rules.
    #4: Cannot accumulate extra moves. (2 consecutive moves at most)
    #5: Checking at move 1 forfeits the extra move.
    #6: The extra move is only allowed if the player is not in check after the first move.
    #7: The extra move cannot be used to capture the opponent's king.

    aliases = ["Berserker"]

    def __init__(self, fen: str | None = chess.STARTING_FEN, chess960: bool = False):
        # Track whether the current turn is the player's bonus move
        self.is_bonus_turn = False
        #Also create a custom stack for tracking bonus moves
        self.bonus_move_stack: list[bool] = []
        # Initialize the board with the given FEN and chess960 setting
        super().__init__(fen, chess960=chess960)

    #Override push and pop (make move and reverse --> reverse for AI)
    def push(self, move: chess.Move) -> None:
        #Record the current bonus turn state before making the move
        self.bonus_move_stack.append(self.is_bonus_turn)

        #If null move
        if move == chess.Move.null():
            self.is_bonus_turn = False
            super().push(move)
            return

        #since push auto flips, we need to check the turn before making the move
        move_color = self.turn
        captured = self.is_capture(move)
        super().push(move)

        #Check logic
        if captured and not self.is_bonus_turn and not self.is_check():
            self.is_bonus_turn = True
            #revert to the player who just captured
            self.turn = move_color
            #Since full move only increments after black
            if move_color == chess.BLACK:
                self.fullmove_number -= 1
        else:
            self.is_bonus_turn = False

    #Now popping
    def pop(self) -> chess.Move:
        move = super().pop()
        self.is_bonus_turn = self.bonus_move_stack.pop()
        return move

    #Since we also have null moves, we must update the legal moves accordingly
    def generate_legal_moves(self, from_mask: int = chess.BB_ALL, to_mask: int = chess.BB_ALL):
        yield from super().generate_legal_moves(from_mask, to_mask)
        #if bonus, allow null
        if self.is_bonus_turn and not self.is_check():
            yield chess.Move.null()

    def is_legal(self, move: chess.Move) -> bool:
        if move == chess.Move.null():
            return self.is_bonus_turn and not self.is_check()
        return super().is_legal(move)

    #a quick copy command for future AI's: copy, reset, clear, and clear_stack
    def copy(self, stack: bool | int = True):
        board = super().copy(stack=stack)
        board.is_bonus_turn = self.is_bonus_turn
        board.bonus_move_stack = list(self.bonus_move_stack) if stack else []
        return board
    def reset(self) -> None:
        self.is_bonus_turn = False
        self.bonus_move_stack.clear()
        super().reset()

    def clear(self) -> None:
        self.is_bonus_turn = False
        self.bonus_move_stack.clear()
        super().clear()

    def clear_stack(self) -> None:
        self.bonus_move_stack.clear()
        super().clear_stack()
    
    
    