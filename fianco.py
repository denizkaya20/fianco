import pygame
import sys
import time

# board.py ve ui.py'den import
from board import (BOARD_SIZE, TILE_SIZE, BOARD_OFFSET_X, BOARD_OFFSET_Y,
                   SCOREBOARD_WIDTH, WIDTH, HEIGHT, FPS,
                   WOOD_COLOR, BLACK, WHITE, ERROR_OVERLAY_COLOR, Piece)
from ui import Button
# ai.py'den import
from ai import (ZOBRIST, initialize_zobrist, get_all_possible_moves,
                get_all_possible_capture_moves, make_ai_move)

pygame.init()

# Fontlar
FONT_SMALL = pygame.font.SysFont('Arial', 20)
FONT_MEDIUM = pygame.font.SysFont('Arial', 28)
FONT_LARGE = pygame.font.SysFont('Arial', 54)

PLAYERS = {
    'Player1': {'name': 'White', 'color': WHITE},
    'Player2': {'name': 'Black', 'color': BLACK}
}

def quit_game():
    pygame.quit()
    sys.exit()

# Zobrist hashing'i başlat
initialize_zobrist()

class Fianco:
    def __init__(self):
        self.window = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('FIANCO GAME')
        self.clock = pygame.time.Clock()

        self.state = 'menu'  # OYUN İLK AÇILDIĞINDA MENÜDE BAŞLA
        self.human_player = None
        self.ai_player = None

        self.create_buttons()

        self.pieces = []
        self.selected_piece = None
        self.current_player = 'Player1'
        self.game_over = False
        self.error_message = ''
        self.show_error = False
        self.winner = None
        self.winner_name = ''
        self.must_continue_capture = False

        self.captured_white = []
        self.captured_black = []

        # 10 dakika (ms cinsinden)
        self.player_times = {'Player1': 600000, 'Player2': 600000}
        self.last_update_time = pygame.time.get_ticks()

        # AI & Arama Değişkenleri
        self.ttable = {}
        self.prune_count = 0
        self.nodes_searched = 0
        self.total_prunes = 0
        self.max_prune_per_move = 0
        self.tt_accesses = 0
        self.stats_printed = False

        self.killer_moves = {}
        self.iterative_time_limit = 2000  # 2 saniye
        self.max_depth = 20

    def create_buttons(self):
        import pygame
        menu_button_width = 200
        menu_button_height = 60
        menu_button_font = pygame.font.SysFont('Arial', 24)
        menu_button_bg = WHITE
        menu_button_text = BLACK

        # MENÜ EKRANINDAKİ DÜĞMELER
        self.menu_play_white_button = Button(
            x=WIDTH // 2 - menu_button_width - 20,
            y=HEIGHT // 2,
            width=menu_button_width,
            height=menu_button_height,
            text='Play as White',
            font=menu_button_font,
            bg_color=menu_button_bg,
            text_color=menu_button_text,
            action=lambda: self.select_color('white')
        )
        self.menu_play_black_button = Button(
            x=WIDTH // 2 + 20,
            y=HEIGHT // 2,
            width=menu_button_width,
            height=menu_button_height,
            text='Play as Black',
            font=menu_button_font,
            bg_color=menu_button_bg,
            text_color=menu_button_text,
            action=lambda: self.select_color('black')
        )

        base_y = BOARD_OFFSET_Y + BOARD_SIZE * TILE_SIZE + 70
        button_width = 100
        button_height = 35
        button_font = pygame.font.SysFont('Arial', 20)
        button_bg_color = WHITE
        button_text_color = BLACK

        # OYUN İÇİ DÜĞMELER
        self.restart_button = Button(
            x=BOARD_OFFSET_X, y=base_y, width=button_width, height=button_height,
            text='Restart', font=button_font, bg_color=button_bg_color, text_color=button_text_color,
            action=self.back_to_menu  # ARTIK MENÜYE DÖNMEK
        )
        self.in_game_quit_button = Button(
            x=BOARD_OFFSET_X + button_width + 10, y=base_y, width=button_width, height=button_height,
            text='Quit', font=button_font, bg_color=button_bg_color, text_color=button_text_color,
            action=quit_game
        )

        # OYUN BİTİNCE GÖRÜNEN DÜĞMELER
        game_over_button_width = 200
        game_over_button_height = 60
        game_over_button_font = pygame.font.SysFont('Arial', 28)
        self.game_over_restart_button = Button(
            x=WIDTH // 2 - game_over_button_width // 2, y=HEIGHT // 2 + 20,
            width=game_over_button_width, height=game_over_button_height,
            text='Restart Game', font=game_over_button_font, bg_color=button_bg_color, text_color=button_text_color,
            action=self.back_to_menu  # MENÜYE DÖN
        )
        self.game_over_quit_button = Button(
            x=WIDTH // 2 - game_over_button_width // 2, y=HEIGHT // 2 + 100,
            width=game_over_button_width, height=game_over_button_height,
            text='Quit Game', font=game_over_button_font, bg_color=button_bg_color, text_color=button_text_color,
            action=quit_game
        )

        close_button_font = pygame.font.SysFont('Arial', 24)
        close_button_text = close_button_font.render('X', True, WHITE)
        close_button_image = pygame.Surface((30, 30), pygame.SRCALPHA)
        close_button_image.blit(close_button_text, (5, 0))

        close_button_rect = pygame.Rect(0, 0, 30, 30)
        close_button_rect.x = (self.window.get_width() - 50)
        close_button_rect.y = 10
        self.close_button = Button(
            x=close_button_rect.x, y=close_button_rect.y,
            width=close_button_rect.width, height=close_button_rect.height,
            text='', font=None, bg_color=None, text_color=None,
            action=self.close_error_message, image=close_button_image
        )

    def back_to_menu(self):
        """ Oyun içinden veya game_over ekranından
            menüye geri dönmek için çağırılır.
        """
        self.state = 'menu'
        self.error_message = ''
        self.show_error = False
        # Taşlar vb. sıfırlamadık. Menüde tekrar 'Play as White/Black' seçilince reset_game yapılacak.

    def select_color(self, color):
        """ Kullanıcı menüdeyken White/Siyah seçince çağrılır. """
        if color == 'white':
            self.human_player = 'Player1'
            self.ai_player = 'Player2'
        else:
            self.human_player = 'Player2'
            self.ai_player = 'Player1'

        # Renk seçildikten sonra oyunu sıfırla + oyuna geç
        self.reset_game()
        self.state = 'game'

    def close_error_message(self):
        self.show_error = False
        self.error_message = ''

    def create_initial_pieces(self):
        self.pieces = []
        # Player1 (White) initial pieces
        for col in range(BOARD_SIZE):
            self.pieces.append(Piece(0, col, PLAYERS['Player1']['color'], 'Player1'))
        for i in range(1, 4):
            self.pieces.append(Piece(i, i, PLAYERS['Player1']['color'], 'Player1'))
            self.pieces.append(Piece(i, BOARD_SIZE - 1 - i, PLAYERS['Player1']['color'], 'Player1'))

        # Player2 (Black) initial pieces
        for col in range(BOARD_SIZE):
            self.pieces.append(Piece(BOARD_SIZE - 1, col, PLAYERS['Player2']['color'], 'Player2'))
        for i in range(1, 4):
            self.pieces.append(Piece(BOARD_SIZE - 1 - i, i, PLAYERS['Player2']['color'], 'Player2'))
            self.pieces.append(Piece(BOARD_SIZE - 1 - i, BOARD_SIZE - 1 - i, PLAYERS['Player2']['color'], 'Player2'))

    def draw_board(self):
        self.window.fill(WOOD_COLOR)
        for row in range(BOARD_SIZE + 1):
            pygame.draw.line(
                self.window, BLACK,
                (BOARD_OFFSET_X, BOARD_OFFSET_Y + row * TILE_SIZE),
                (BOARD_OFFSET_X + BOARD_SIZE * TILE_SIZE, BOARD_OFFSET_Y + row * TILE_SIZE),
                1
            )
        for col in range(BOARD_SIZE + 1):
            pygame.draw.line(
                self.window, BLACK,
                (BOARD_OFFSET_X + col * TILE_SIZE, BOARD_OFFSET_Y),
                (BOARD_OFFSET_X + col * TILE_SIZE, BOARD_OFFSET_Y + BOARD_SIZE * TILE_SIZE),
                1
            )

        if self.selected_piece:
            x = self.selected_piece.x
            y = self.selected_piece.y
            radius = TILE_SIZE // 2 - 5
            pygame.draw.circle(self.window, (255, 215, 0), (x, y), radius + 3, 3)

        for piece in self.pieces:
            piece.draw(self.window)

        self.draw_captured_pieces()

        player_info = PLAYERS[self.current_player]
        turn_text = FONT_MEDIUM.render(f"{player_info['name']}'s Turn", True, player_info['color'])
        turn_rect = turn_text.get_rect(
            center=(BOARD_OFFSET_X + (BOARD_SIZE * TILE_SIZE) // 2,
                    BOARD_OFFSET_Y + BOARD_SIZE * TILE_SIZE + 30))
        self.window.blit(turn_text, turn_rect)

    def draw_captured_pieces(self):
        # White captured
        start_x_white = BOARD_OFFSET_X // 2
        start_y_white = BOARD_OFFSET_Y
        for index, piece in enumerate(self.captured_white):
            x = start_x_white
            y = start_y_white + index * (TILE_SIZE // 2)
            radius = TILE_SIZE // 3
            if y + radius > BOARD_OFFSET_Y + BOARD_SIZE * TILE_SIZE:
                break
            pygame.draw.circle(self.window, PLAYERS['Player1']['color'], (x, y), radius)

        # Black captured
        start_x_black = BOARD_OFFSET_X + BOARD_SIZE * TILE_SIZE + (BOARD_OFFSET_X // 2)
        start_y_black = BOARD_OFFSET_Y
        for index, piece in enumerate(self.captured_black):
            x = start_x_black
            y = start_y_black + index * (TILE_SIZE // 2)
            radius = TILE_SIZE // 3
            if y + radius > BOARD_OFFSET_Y + BOARD_SIZE * TILE_SIZE:
                break
            pygame.draw.circle(self.window, PLAYERS['Player2']['color'], (x, y), radius)

    def draw_timers(self):
        sidebar_x = BOARD_OFFSET_X * 2 + BOARD_SIZE * TILE_SIZE + 10
        top_margin = 20
        box_width = SCOREBOARD_WIDTH - 20
        box_height = 80
        box_spacing = 20

        box_y_p1 = top_margin
        box_y_p2 = box_y_p1 + box_height + box_spacing

        pygame.draw.rect(self.window, WHITE,
                         (BOARD_OFFSET_X * 2 + BOARD_SIZE * TILE_SIZE, 0, SCOREBOARD_WIDTH, HEIGHT))

        pygame.draw.rect(self.window, (230, 230, 230),
                         (sidebar_x, box_y_p1, box_width, box_height))
        pygame.draw.rect(self.window, BLACK,
                         (sidebar_x, box_y_p1, box_width, box_height), 2)

        pygame.draw.rect(self.window, (230, 230, 230),
                         (sidebar_x, box_y_p2, box_width, box_height))
        pygame.draw.rect(self.window, BLACK,
                         (sidebar_x, box_y_p2, box_width, box_height), 2)

        time_left_p1 = self.player_times['Player1'] // 1000
        m1 = time_left_p1 // 60
        s1 = time_left_p1 % 60
        time_str_p1 = f"{m1:02d}:{s1:02d}"

        time_left_p2 = self.player_times['Player2'] // 1000
        m2 = time_left_p2 // 60
        s2 = time_left_p2 % 60
        time_str_p2 = f"{m2:02d}:{s2:02d}"

        player_name_p1 = FONT_MEDIUM.render("WHITE", True, BLACK)
        player_name_p2 = FONT_MEDIUM.render("BLACK", True, BLACK)
        time_font = pygame.font.SysFont('Arial', 32)

        time_surf_p1 = time_font.render(time_str_p1, True, BLACK)
        time_surf_p2 = time_font.render(time_str_p2, True, BLACK)

        name_rect_p1 = player_name_p1.get_rect(center=(sidebar_x + box_width // 2, box_y_p1 + 20))
        self.window.blit(player_name_p1, name_rect_p1)
        time_rect_p1 = time_surf_p1.get_rect(center=(sidebar_x + box_width // 2, box_y_p1 + box_height - 20))
        self.window.blit(time_surf_p1, time_rect_p1)

        name_rect_p2 = player_name_p2.get_rect(center=(sidebar_x + box_width // 2, box_y_p2 + 20))
        self.window.blit(player_name_p2, name_rect_p2)
        time_rect_p2 = time_surf_p2.get_rect(center=(sidebar_x + box_width // 2, box_y_p2 + box_height - 20))
        self.window.blit(time_surf_p2, time_rect_p2)

    def display_error_message(self, message, close_button):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill(ERROR_OVERLAY_COLOR)
        self.window.blit(overlay, (0, 0))

        error_text = FONT_MEDIUM.render(message, True, WHITE)
        error_rect = error_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.window.blit(error_text, error_rect)

        close_button.draw(self.window)

    def get_piece_at_position(self, row, col):
        for p in self.pieces:
            if p.row == row and p.col == col:
                return p
        return None

    def get_mouse_board_position(self, pos):
        x, y = pos
        x -= BOARD_OFFSET_X
        y -= BOARD_OFFSET_Y
        c = x // TILE_SIZE
        r = y // TILE_SIZE
        return r, c

    def remove_piece(self, piece):
        self.pieces.remove(piece)
        if piece.owner == 'Player1':
            self.captured_white.append(piece)
        else:
            self.captured_black.append(piece)
        piece.row = None
        piece.col = None
        piece.reset_position()

    def is_valid_move(self, piece, r, c):
        # (Aynı kalabilir veya ufak iyileştirmeler)
        if piece.row == r and piece.col == c:
            return False, "", None
        if r < 0 or r >= BOARD_SIZE or c < 0 or c >= BOARD_SIZE:
            return False, "", None
        occ = self.get_piece_at_position(r, c)
        if occ:
            return False, "", None

        if piece.owner == 'Player1':
            fw = 1
        else:
            fw = -1

        dr = r - piece.row
        dc = c - piece.col

        # Geri gitmeyi engellemek, vs.
        if dr == -fw:
            return False, "", None

        # Normal yürüyüş
        if dr == fw and dc == 0:
            return True, "", None
        # Yan hareket
        elif dr == 0 and abs(dc) == 1:
            return True, "", None
        # Capture hamlesi
        elif dr == fw * 2 and abs(dc) == 2:
            middle_row = piece.row + fw
            middle_col = piece.col + (dc // 2)
            mid_piece = self.get_piece_at_position(middle_row, middle_col)
            if mid_piece and mid_piece.owner != piece.owner:
                return True, "", mid_piece

        return False, "", None

    def check_for_win(self):
        for piece in self.pieces:
            if piece.owner == 'Player1' and piece.row == BOARD_SIZE - 1:
                return 'Player1'
            elif piece.owner == 'Player2' and piece.row == 0:
                return 'Player2'
        return None

    def check_for_piece_depletion(self):
        p1 = [p for p in self.pieces if p.owner == 'Player1']
        p2 = [p for p in self.pieces if p.owner == 'Player2']
        if not p1:
            return 'Player2'
        elif not p2:
            return 'Player1'
        return None

    def reset_game(self):
        """ Tüm oyun verilerini sıfırlar.
            Artık state'i burada 'game' yapmıyoruz.
            Renk seçilince veya menüden oyuna dönünce set ediyoruz.
        """
        self.create_initial_pieces()
        self.selected_piece = None
        self.current_player = self.human_player
        self.game_over = False
        self.error_message = ''
        self.show_error = False
        self.winner = None
        self.winner_name = ''
        self.must_continue_capture = False
        self.captured_white.clear()
        self.captured_black.clear()

        self.player_times['Player1'] = 600000
        self.player_times['Player2'] = 600000
        self.last_update_time = pygame.time.get_ticks()

        # TT ve istatistikleri sıfırla
        self.ttable.clear()
        self.prune_count = 0
        self.nodes_searched = 0
        self.total_prunes = 0
        self.max_prune_per_move = 0
        self.tt_accesses = 0
        self.killer_moves.clear()
        self.stats_printed = False

    def make_move(self, move, store_previous_state=False):
        piece, r, c, captured = move
        prev = None
        if store_previous_state:
            prev = {
                'piece': piece,
                'piece_row': piece.row,
                'piece_col': piece.col,
                'captured_piece': captured,
                'captured_row': captured.row if captured else None,
                'captured_col': captured.col if captured else None,
                'current_player': self.current_player,
                'must_continue_capture': self.must_continue_capture,
                'game_over': self.game_over,
                'winner': self.winner,
                'winner_name': self.winner_name,
                'state': self.state,
                'selected_piece': self.selected_piece
            }

        piece.row = r
        piece.col = c
        piece.reset_position()

        if captured and captured in self.pieces:
            self.remove_piece(captured)

        w = self.check_for_win()
        if not w:
            w = self.check_for_piece_depletion()
        if w:
            self.winner = w
            self.game_over = True
            self.state = 'game_over'
            self.winner_name = PLAYERS[w]['name']
        else:
            if captured and self.has_available_captures(piece):
                self.must_continue_capture = True
                self.selected_piece = piece
            else:
                self.must_continue_capture = False
                self.selected_piece = None
                if not self.must_continue_capture:
                    self.current_player = 'Player2' if self.current_player == 'Player1' else 'Player1'

        if store_previous_state:
            return prev

        # Eğer oyun bitmediyse ve şu an AI sırası ise:
        if not self.game_over and self.current_player == self.ai_player:
            make_ai_move(self)

    def unmake_move(self, prev):
        piece = prev['piece']
        piece.row = prev['piece_row']
        piece.col = prev['piece_col']
        piece.reset_position()

        captured_piece = prev['captured_piece']
        if captured_piece:
            captured_piece.row = prev['captured_row']
            captured_piece.col = prev['captured_col']
            captured_piece.reset_position()
            self.pieces.append(captured_piece)
            if captured_piece.owner == 'Player1':
                self.captured_white.remove(captured_piece)
            else:
                self.captured_black.remove(captured_piece)

        self.current_player = prev['current_player']
        self.must_continue_capture = prev['must_continue_capture']
        self.game_over = prev['game_over']
        self.winner = prev['winner']
        self.winner_name = prev['winner_name']
        self.state = prev['state']
        self.selected_piece = prev['selected_piece']

    def has_available_captures(self, piece):
        if piece.owner == 'Player1':
            fw = 1
        else:
            fw = -1

        for dc in [-2, 2]:
            nr = piece.row + fw * 2
            nc = piece.col + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                if not self.get_piece_at_position(nr, nc):
                    mr = piece.row + fw
                    mc = piece.col + (dc // 2)
                    mid = self.get_piece_at_position(mr, mc)
                    if mid and mid.owner != piece.owner:
                        return True
        return False

    def handle_event_manual(self, event):
        if self.show_error:
            self.close_button.handle_event(event)

        if self.state == 'menu':
            self.menu_play_white_button.handle_event(event)
            self.menu_play_black_button.handle_event(event)
            return

        if self.state == 'game':
            self.in_game_quit_button.handle_event(event)
            self.restart_button.handle_event(event)

            if not self.game_over:
                if self.current_player == self.human_player:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        pos = pygame.mouse.get_pos()
                        if not self.selected_piece:
                            for p in self.pieces:
                                rad = TILE_SIZE // 2 - 5
                                dist = ((p.x - pos[0])**2 + (p.y - pos[1])**2)**0.5
                                if dist <= rad and p.owner == self.current_player:
                                    self.selected_piece = p
                                    break
                        else:
                            rr, cc = self.get_mouse_board_position(pos)
                            from ai import get_all_possible_capture_moves
                            all_capture_moves = get_all_possible_capture_moves(self, self.current_player)

                            if 0 <= rr < BOARD_SIZE and 0 <= cc < BOARD_SIZE:
                                clicked_piece = self.get_piece_at_position(rr, cc)
                                if clicked_piece and clicked_piece.owner == self.current_player:
                                    self.selected_piece = clicked_piece
                                else:
                                    is_ok, _, cap = self.is_valid_move(self.selected_piece, rr, cc)
                                    if is_ok:
                                        # Zorunlu yeme
                                        if all_capture_moves and cap is None:
                                            self.error_message = 'Capture is mandatory!'
                                            self.show_error = True
                                            self.error_start_time = pygame.time.get_ticks()
                                        else:
                                            self.make_move((self.selected_piece, rr, cc, cap))
                                            self.error_message = ''
                                            if self.game_over:
                                                return
                                    else:
                                        self.error_message = 'Invalid Move!'
                                        self.show_error = True
                                        self.error_start_time = pygame.time.get_ticks()
                            else:
                                self.selected_piece = None

        elif self.state == 'game_over':
            self.game_over_restart_button.handle_event(event)
            self.game_over_quit_button.handle_event(event)
