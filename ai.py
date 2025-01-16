import time
import numpy as np
import random

from fianco import ZOBRIST, owner_to_id, get_board_hash, initialize_zobrist
from board import BOARD_SIZE

def get_all_possible_capture_moves(game, player):
    capture_moves = []

    if player == 'Player1':
        directions = np.array([[2, 2], [2, -2]], dtype=np.int8)
    else:
        directions = np.array([[-2, 2], [-2, -2]], dtype=np.int8)

    for piece in game.pieces:
        if piece.owner == player:
            if piece.row < 0 or piece.col < 0:
                continue

            candidates = piece.position + directions
            valid_mask = (
                (candidates[:,0] >= 0) & (candidates[:,0] < BOARD_SIZE) &
                (candidates[:,1] >= 0) & (candidates[:,1] < BOARD_SIZE)
            )
            candidates = candidates[valid_mask]

            for cand in candidates:
                r, c = cand
                is_ok, _, cap = game.is_valid_move(piece, r, c)
                if is_ok and cap is not None:
                    capture_moves.append((piece, r, c, cap))

    return capture_moves

def get_all_possible_moves(game, player):
    all_moves = []
    capture_moves = []

    if player == 'Player1':
        directions = np.array([
            [1, 0],
            [0, 1],
            [0, -1],
            [2, 2],
            [2, -2],
        ], dtype=np.int8)
    else:
        directions = np.array([
            [-1, 0],
            [0, 1],
            [0, -1],
            [-2, 2],
            [-2, -2],
        ], dtype=np.int8)

    for piece in game.pieces:
        if piece.owner == player:
            if piece.row < 0 or piece.col < 0:
                continue

            candidates = piece.position + directions
            valid_mask = (
                (candidates[:,0] >= 0) & (candidates[:,0] < BOARD_SIZE) &
                (candidates[:,1] >= 0) & (candidates[:,1] < BOARD_SIZE)
            )
            candidates = candidates[valid_mask]

            for cand in candidates:
                r, c = cand
                is_ok, _, cap = game.is_valid_move(piece, r, c)
                if is_ok:
                    if cap is not None:
                        capture_moves.append((piece, r, c, cap))
                    else:
                        all_moves.append((piece, r, c, None))

    # mandatory capture
    if capture_moves:
        return capture_moves
    else:
        return all_moves

def evaluate_position(game):
    owners = [p.owner for p in game.pieces if p.row >= 0 and p.col >= 0]
    arr = np.array([1 if o == 'Player1' else -1 for o in owners], dtype=np.int8)
    val = arr.sum()
    return val

def order_moves(game, moves, depth):
    captures = []
    normal = []
    for m in moves:
        piece, r, c, captured = m
        if captured is not None:
            captures.append(m)
        else:
            normal.append(m)
    return captures + normal

def update_ai_time_limit(game):
    remaining_time = game.player_times[game.ai_player]
    if remaining_time < 60000:
        game.iterative_time_limit = max(2000, remaining_time // 20)
    else:
        game.iterative_time_limit = 5000

# ------------------ AI Search (Negamax) --------------------
def make_ai_move(game):
    start_ms = time.time() * 1000
    best_move = None
    depth = 5  # sabit derinlik

    update_ai_time_limit(game)
    best_move = negamax_root(game, depth, -999999, 999999)

    if best_move:
        game.make_move(best_move)
        elapsed_time = time.time() * 1000 - start_ms
        game.player_times[game.ai_player] -= elapsed_time
        print(f"[AI] depth={depth}, prune_count={game.prune_count}, nodes={game.nodes_searched}")
        game.total_prunes += game.prune_count
        if game.prune_count > game.max_prune_per_move:
            game.max_prune_per_move = game.prune_count
    else:
        print("[AI] No valid move found. pass")

def negamax_root(game, depth, alpha, beta):
    moves = get_all_possible_moves(game, game.current_player)
    moves = order_moves(game, moves, depth)

    best_score = -999999
    best_move = None

    for move in moves:
        prev = game.make_move(move, store_previous_state=True)
        game.current_player = 'Player2' if game.current_player == 'Player1' else 'Player1'

        score = -negamax(game, depth - 1, -beta, -alpha, 1)
        game.unmake_move(prev)

        if score > best_score:
            best_score = score
            best_move = move
        if best_score > alpha:
            alpha = best_score
        if alpha >= beta:
            game.prune_count += 1
            break

    return best_move

def negamax(game, depth, alpha, beta, color):
    # TT Access
    board_hash = get_board_hash(game)
    game.tt_accesses += 1

    if board_hash in game.ttable:
        stored_score, stored_depth = game.ttable[board_hash]
        if stored_depth >= depth:
            return stored_score * color

    if depth == 0 or game.game_over:
        game.nodes_searched += 1
        eval_score = evaluate_position(game)
        # Save to TT
        game.ttable[board_hash] = (eval_score, depth)
        return eval_score * color

    moves = get_all_possible_moves(game, game.current_player)
    if not moves:
        game.nodes_searched += 1
        eval_score = evaluate_position(game)
        game.ttable[board_hash] = (eval_score, depth)
        return eval_score * color

    moves = order_moves(game, moves, depth)
    best_score = -999999

    for move in moves:
        prev = game.make_move(move, store_previous_state=True)
        game.current_player = 'Player2' if game.current_player == 'Player1' else 'Player1'

        score = -negamax(game, depth - 1, -beta, -alpha, -color)
        game.unmake_move(prev)

        if score > best_score:
            best_score = score
        if best_score > alpha:
            alpha = best_score
        if alpha >= beta:
            game.prune_count += 1
            break

    raw_score = best_score if color == 1 else -best_score
    game.ttable[board_hash] = (raw_score, depth)
    return best_score
