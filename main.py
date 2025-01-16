import pygame
import sys

# fianco.py'deki Fianco ve gerekli sabitleri import et
from fianco import Fianco, PLAYERS, FONT_LARGE, WOOD_COLOR, WIDTH, HEIGHT, FPS

def main():
    game = Fianco()

    while True:
        elapsed = game.clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            game.handle_event_manual(event)

        # Oyun devam ediyorsa ve herhangi bir hata mesajı yoksa zamanlayıcıları güncelle
        if game.state == 'game' and not game.game_over and not game.show_error:
            game.player_times[game.current_player] -= elapsed
            if game.player_times[game.current_player] <= 0:
                # Süre bitti, rakip kazanır
                game.player_times[game.current_player] = 0
                game.winner = 'Player2' if game.current_player == 'Player1' else 'Player1'
                game.game_over = True
                game.state = 'game_over'
                game.winner_name = PLAYERS[game.winner]['name']

        # Hata mesajlarını 2 saniye sonra gizle
        if game.show_error:
            current_time = pygame.time.get_ticks()
            if current_time - game.error_start_time > 2000:
                game.show_error = False
                game.error_message = ''

        # Ekran çizimleri
        if game.state == 'menu':
            game.window.fill(WOOD_COLOR)
            game.menu_play_white_button.draw(game.window)
            game.menu_play_black_button.draw(game.window)
            pygame.display.flip()
            continue

        if game.state == 'game':
            game.draw_board()
            game.draw_timers()
            game.in_game_quit_button.draw(game.window)
            game.restart_button.draw(game.window)
            if game.show_error and game.error_message:
                game.display_error_message(game.error_message, game.close_button)

        elif game.state == 'game_over':
            game.window.fill(WOOD_COLOR)
            win_text = FONT_LARGE.render(f"{game.winner_name} Wins!", True, PLAYERS[game.winner]['color'])
            win_rect = win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60))
            game.window.blit(win_text, win_rect)

            game.draw_timers()
            game.game_over_restart_button.draw(game.window)
            game.game_over_quit_button.draw(game.window)

            # FINAL STATS sadece bir kez
            if not game.stats_printed:
                print("=== FINAL STATS ===")
                print(f"Total prune count: {game.total_prunes}")
                print(f"Max prune in single move: {game.max_prune_per_move}")
                print(f"Transposition Table size: {len(game.ttable)}")
                print(f"TT accesses: {game.tt_accesses}")

                game.stats_printed = True

        pygame.display.flip()

if __name__ == '__main__':
    main()
