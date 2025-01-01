import time
import random
from board import BOARD_SIZE
import pygame

# ----------- Zobrist Hashing ----------
ZOBRIST = {}

def owner_to_id(owner):
    if owner == 'Player1':
        return 0
    elif owner == 'Player2':
        return 1
    return 2

def initialize_zobrist():
    global ZOBRIST
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            for owner_id in range(3):  # 0 (White), 1 (Black), 2 (None)
                ZOBRIST[(row, col, owner_id)] = random.getrandbits(64)
# --------------------------------------

def get_all_possible_capture_moves(game, player):
    """ Sadece capture (yeme) hamlelerini döndürür.
        İnsan tarafı da fianco.py içerisinden buna erişebilir.
    """
    capture_moves = []
    for piece in game.pieces:
        if piece.owner == player:
            # Yeme için çift atlama bakıyoruz
            if player == 'Player1':
                poss = [
                    (piece.row + 2, piece.col + 2),
                    (piece.row + 2, piece.col - 2)
                ]
            else:
                poss = [
                    (piece.row - 2, piece.col + 2),
                    (piece.row - 2, piece.col - 2)
                ]
            for (r, c) in poss:
                is_ok, _, cap = game.is_valid_move(piece, r, c)
                if is_ok and cap is not None:
                    capture_moves.append((piece, r, c, cap))
    return capture_moves

def get_all_possible_moves(game, player):
    """ Oyuncu player için tüm olası hamleleri döndürür.
        Eğer herhangi bir capture hamlesi varsa, normal hamleler
        listeden çıkar (mandatory capture).
    """
    all_moves = []
    capture_moves = []

    for piece in game.pieces:
        if piece.owner == player:
            if player == 'Player1':
                poss = [
                    (piece.row + 1, piece.col),
                    (piece.row, piece.col + 1),
                    (piece.row, piece.col - 1),
                    (piece.row + 2, piece.col + 2),
                    (piece.row + 2, piece.col - 2)
                ]
            else:
                poss = [
                    (piece.row - 1, piece.col),
                    (piece.row, piece.col + 1),
                    (piece.row, piece.col - 1),
                    (piece.row - 2, piece.col + 2),
                    (piece.row - 2, piece.col - 2)
                ]
            for (r, c) in poss:
                is_ok, _, cap = game.is_valid_move(piece, r, c)
                if is_ok:
                    if cap is not None:
                        capture_moves.append((piece, r, c, cap))
                    else:
                        all_moves.append((piece, r, c, None))

    # ZORUNLU YEME
    if capture_moves:
        return capture_moves
    return all_moves


# ------------------ AI Search (Negamax) --------------------

def make_ai_move(game):
    """ AI'nin hamle yapması. """
    start_ms = time.time() * 1000
    best_move = None
    depth_reached = 1

    # Olası hamle sayısına göre ufak adaptif derinlik limiti
    num_moves = len(get_all_possible_moves(game, game.current_player))
    if num_moves > 20:
        local_depth_limit = 5
    else:
        local_depth_limit = 8

    for depth in range(1, local_depth_limit + 1):
        now = time.time() * 1000
        if now - start_ms > game.iterative_time_limit:
            break
        game.prune_count = 0
        game.nodes_searched = 0
        move_candidate = negamax_root(game, depth, -999999, 999999)
        if move_candidate:
            best_move = move_candidate
            depth_reached = depth
        else:
            break

    if best_move:
        game.make_move(best_move)
        print(f"[AI] depth={depth_reached}, prune_count={game.prune_count}, nodes={game.nodes_searched}")
        # İstatistik güncelleme
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
    original_alpha = alpha

    board_hash = get_board_hash(game)
    # TT key: (board_hash, depth, alpha, beta)
    # root'ta alpha/beta sabit gibi, ama yine de kaydedebiliriz

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

    # TT Bound ve best_move saklama
    if best_score <= original_alpha:
        bound_flag = 'UPPER'
    elif best_score >= beta:
        bound_flag = 'LOWER'
    else:
        bound_flag = 'EXACT'

    tt_key = (board_hash, depth, original_alpha, beta)
    game.ttable[tt_key] = {
        "score": best_score,
        "flag": bound_flag,
        "best_move": best_move
    }

    return best_move

def negamax(game, depth, alpha, beta, color):
    if depth == 0 or game.game_over:
        game.nodes_searched += 1
        return evaluate_position(game) * color

    # TT sorgusu
    board_hash = get_board_hash(game)
    original_alpha = alpha
    tt_key = (board_hash, depth, alpha, beta)

    game.tt_accesses += 1
    if tt_key in game.ttable:
        entry = game.ttable[tt_key]
        flag = entry.get("flag", "EXACT")
        cached_score = entry["score"]

        # TT Bound kullanımı
        if flag == 'EXACT':
            return cached_score
        elif flag == 'LOWER':  # score >= gerçek beta
            alpha = max(alpha, cached_score)
        elif flag == 'UPPER':  # score <= gerçek alpha
            beta = min(beta, cached_score)
        if alpha >= beta:
            return cached_score

    moves = get_all_possible_moves(game, game.current_player)
    if not moves:
        game.nodes_searched += 1
        return evaluate_position(game) * color

    moves = order_moves(game, moves, depth)
    best_score = -999999
    best_move = None

    for move in moves:
        prev = game.make_move(move, store_previous_state=True)
        game.current_player = 'Player2' if game.current_player == 'Player1' else 'Player1'
        score = -negamax(game, depth - 1, -beta, -alpha, -color)
        game.unmake_move(prev)

        if score > best_score:
            best_score = score
            best_move = move
        if best_score > alpha:
            alpha = best_score
        if alpha >= beta:
            game.prune_count += 1
            # killer move
            kset = game.killer_moves.get(depth, set())
            kset.add(move)
            game.killer_moves[depth] = kset
            break

    # TT'ye kaydet
    if best_score <= original_alpha:
        bound_flag = 'UPPER'
    elif best_score >= beta:
        bound_flag = 'LOWER'
    else:
        bound_flag = 'EXACT'

    game.ttable[tt_key] = {
        "score": best_score,
        "flag": bound_flag,
        "best_move": best_move
    }
    return best_score

def evaluate_position(game):
    # Basit evaluate: Beyaz taş sayısı - Siyah taş sayısı
    w = len([p for p in game.pieces if p.owner == 'Player1'])
    b = len([p for p in game.pieces if p.owner == 'Player2'])
    return w - b

def get_board_hash(game):
    h = 0
    for p in game.pieces:
        oid = owner_to_id(p.owner)
        h ^= ZOBRIST[(p.row, p.col, oid)]
    return h

def order_moves(game, moves, depth):
    """
    1) TT move
    2) Capture
    3) Killer
    4) Normal
    """
    # TT move bul
    board_hash = get_board_hash(game)
    best_move_from_tt = None
    # En basit yoldan: tabloyu gezip
    for key, entry in game.ttable.items():
        # key: (hash, d, a, b)
        if key[0] == board_hash and key[1] == depth:
            bm = entry.get("best_move", None)
            if bm:
                best_move_from_tt = bm
                break

    captures = []
    killers = []
    normal = []
    kset = game.killer_moves.get(depth, set())

    for m in moves:
        piece, r, c, captured = m
        if best_move_from_tt is not None and m == best_move_from_tt:
            # TT move en başa
            captures.insert(0, m)  # liste başına ekleyelim
        elif captured is not None:
            captures.append(m)
        elif m in kset:
            killers.append(m)
        else:
            normal.append(m)

    return captures + list(killers) + normal
