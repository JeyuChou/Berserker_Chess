import chess
from BerserkerBoard import BerserkerBoard
import random

def test_berserker_board():
    board = BerserkerBoard()

    #Normal move
    board.push_san("e4")
    assert not board.is_bonus_turn
    assert board.turn == chess.BLACK

    board.push_san("d5")
    assert not board.is_bonus_turn
    assert board.turn == chess.WHITE

    #Capture move
    #board.push_san("d5")
    board.push_san("exd5")
    assert board.is_bonus_turn
    assert board.turn == chess.WHITE

    board.reset()
    #can have null move
    board.push_san("e4") #w
    board.push_san('d5') #b
    board.push_san('exd5') #w
    assert chess.Move.null() in board.legal_moves
    board.push(chess.Move.null()) #w
    assert chess.Move.null() not in board.legal_moves
    assert not board.is_bonus_turn
    assert board.turn == chess.BLACK

    #clear the board
    board.reset()

    check_board = BerserkerBoard("4k3/4p3/8/8/8/8/4Q3/4K3 w - - 0 1")
    check_board.push_san("Qxe7+")
    assert check_board.is_check() is True
    assert check_board.is_bonus_turn is False  # Bonus forfeited!
    assert check_board.turn == chess.BLACK

    # 1. No chaining (Rule #4: 2nd capture during bonus turn passes the turn)
    chain_board = BerserkerBoard("4k3/8/3p4/4p3/3P4/8/8/4K3 w - - 0 1")
    chain_board.push_san("dxe5")  # Capture 1 -> earns bonus
    assert chain_board.is_bonus_turn is True
    chain_board.push_san("exd6")  # Capture 2 -> must NOT earn a 3rd move
    assert chain_board.is_bonus_turn is False
    assert chain_board.turn == chess.BLACK

    # 2. Undo (pop) restores bonus turn state
    chain_board.pop()  # Undo exd6
    assert chain_board.is_bonus_turn is True
    assert chain_board.turn == chess.WHITE
    chain_board.pop()  # Undo dxe5
    assert chain_board.is_bonus_turn is False
    assert chain_board.turn == chess.WHITE

    # 3. Black fullmove_number stays accurate during bonus turn
    black_board = BerserkerBoard()
    black_board.push_san("e4")    # Move 1 (White)
    black_board.push_san("d5")    # Move 1 (Black) -> fullmove_number becomes 2
    black_board.push_san("Nf3")   # Move 2 (White)
    black_board.push_san("dxe4")  # Move 2 (Black capture) -> should stay on Move 2!
    assert black_board.is_bonus_turn is True
    assert black_board.fullmove_number == 2
    black_board.push_san("Nc6")   # Move 2 (Black bonus) -> now increments to 3
    assert black_board.fullmove_number == 3

    #checking en passant
    board.reset()
    board.push_san("e4")
    board.push_san('a6')
    board.push_san('e5')
    board.push_san('d5')
    board.push_san('exd6')
    assert board.is_bonus_turn
    assert board.turn == chess.WHITE

    # 5. Promotion: capture-promotion grants bonus, quiet promotion does not
    # White pawn on e7, Black rook on d8 (not giving check on d8=Q)
    promo_board = BerserkerBoard("3r3k/4P3/8/8/8/8/8/4K3 w - - 0 1")
    promo_board.push_san("exd8=Q")  # Capture + promotion without check
    assert promo_board.is_bonus_turn is False #false since check
    assert promo_board.turn == chess.BLACK

    promo2 = BerserkerBoard('3r4/4P2k/8/8/8/8/8/4K3 w - - 0 1')
    promo2.push_san("exd8=Q")
    assert promo2.is_bonus_turn is True
    assert promo2.turn == chess.WHITE

    # Quiet promotion (no capture) should NOT grant a bonus move
    quiet_promo = BerserkerBoard("7k/4P3/8/8/8/8/8/4K3 w - - 0 1")
    quiet_promo.push_san("e8=Q")
    assert quiet_promo.is_bonus_turn is False
    assert quiet_promo.turn == chess.BLACK

    print("All tests passed!")

def test_fuzz_berserker(num_games: int = 100):
    board = BerserkerBoard()

    for game_idx in range(num_games):
        board.reset()
        consecutive_moves = 0
        last_turn = board.turn

        while not board.is_game_over():
            legal_moves = list(board.legal_moves)
            move = random.choice(legal_moves)

            # Invariant check: every generated move must pass is_legal()
            assert board.is_legal(move)

            board.push(move)

            # Invariant check: Rule #4 (never more than 2 consecutive moves)
            if board.turn == last_turn:
                consecutive_moves += 1
                assert consecutive_moves <= 1  # 1 initial + 1 bonus = 2 moves max
            else:
                consecutive_moves = 0
                last_turn = board.turn

        # Rewind the entire game to test pop() and bonus_move_stack integrity
        while board.move_stack:
            board.pop()

        assert board.fen() == chess.STARTING_FEN
        assert board.is_bonus_turn is False
        assert len(board.bonus_move_stack) == 0

    print(f"Fuzz test passed across {num_games} random games!")

if __name__ == "__main__":
    test_berserker_board()
    test_fuzz_berserker(100)
