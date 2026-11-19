
import pygame
from shell.highscores import HighscoreManager
from shell.config import Config
from shell.game_renderer import GameRenderer
from mazegenerator import MazeGenerator
from engine.grid import Grid
from engine.gameengine import Engine
from engine.models import Direction
from engine.gameengine import Engine, GameState


class Renderer:
    def __init__(self, config: Config) -> None:
        # Initialize pygame
        pygame.init()
        self.is_paused = False
        self.selected_option = 0

        # Configuration
        self.config = config

        # Window
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Pac-Man 42")
        self.clock = pygame.time.Clock()

        self.game_renderer = GameRenderer(self.screen)

        generator = MazeGenerator(
            size=(15, 15),
            perfect=False,
            seed=42,
        )
        generator.generate(seed=42)

        self.grid = Grid(15, 15, generator.maze)

        # Application state
        self.current_screen = "menu"
        self.player_name = ""
        self.final_score = 0
        self.message = ""

        # Highscore manager
        self.highscore_manager = HighscoreManager(
            self.config.highscore_filename
        )
        self.highscore_manager.load()

        # Fonts
        self.font = pygame.font.Font(None, 36)
        self.title_font = pygame.font.Font(None, 70)
        self.small_font = pygame.font.Font(None, 26)

        # Menu text surfaces
        self.title = self.title_font.render(
            "PAC-MAN 42", True, (166, 166, 70)
        )
        self.start_game_text = self.font.render(
            "START GAME", True, (212, 212, 184)
        )
        self.high_scores = self.font.render(
            "HIGH SCORES", True, (212, 212, 184)
        )
        self.instructions_text = self.font.render(
            "INSTRUCTIONS", True, (212, 212, 184)
        )
        self.quit_game = self.font.render(
            "QUIT", True, (212, 212, 184)
        )

        # Menu rectangles
        self.title_rect = self.title.get_rect(center=(400, 70))
        self.start_rect = self.start_game_text.get_rect(
            center=(400, 200)
        )
        self.scores_rect = self.high_scores.get_rect(
            center=(400, 280)
        )
        self.instructions_rect = self.instructions_text.get_rect(
            center=(400, 350)
        )
        self.quit_rect = self.quit_game.get_rect(
            center=(400, 430)
        )

    def draw_game(self) -> None:
        snapshot = self.engine.get_snapshot()
        start_row, start_col = snapshot.pacu_position

        ghosts = [
            position
            for position, state in snapshot.ghosts
        ]

        self.game_renderer.draw_maze(self.engine.grid)
        self.game_renderer.draw_pacgums(snapshot.pacgums)
        self.game_renderer.draw_supergums(snapshot.supergums)
        self.game_renderer.draw_pacman(
            start_row,
            start_col,
        )

        self.game_renderer.draw_ghosts(ghosts)
        self.game_renderer.draw_hud(
            score=snapshot.score,
            lives=snapshot.lives,
            level=snapshot.level,
            time_left=int(self.engine.level_timer),
        )

        # Cheat mode status indicators
        cheats = [
            ("1: INVINCIBLE", self.engine.invincible),
            ("2: FREEZE", self.engine.freeze),
            ("3: SPEED", self.engine.speed),
        ]

        x = 25
        y = 520

        for label, enabled in cheats:
            color = (0, 255, 100) if enabled else (110, 110, 110)

            text = self.font.render(label, True, color)
            self.screen.blit(text, (x, y))

            x += text.get_width() + 25

        # Game controls
        self.draw_text(
            "Press P to Pause | ESC to return to Menu",
            160,
            560,
            (166, 166, 70),
        )

        if self.is_paused:
            self.draw_pause()

    def draw_text(
        self,
        text: str,
        x: int,
        y: int,
        color: tuple[int, int, int] = (255, 255, 255),
    ) -> None:
        surface = self.font.render(text, True, color)
        self.screen.blit(surface, (x, y))

    def draw_menu(self) -> None:
        self.screen.blit(self.title, self.title_rect)
        menu_items = [
            (self.start_game_text, self.start_rect),
            (self.high_scores, self.scores_rect),
            (self.instructions_text, self.instructions_rect),
            (self.quit_game, self.quit_rect),
        ]
        for index, (text, rect) in enumerate(menu_items):
            self.screen.blit(text, rect)

            if index == self.selected_option:
                pygame.draw.rect(
                    self.screen,
                    (255, 255, 0),
                    rect.inflate(20, 10),
                    2,
                )

    def draw_highscores(self) -> None:
        heading = self.title_font.render(
            "HIGH SCORES", True, (255, 255, 0)
        )
        heading_rect = heading.get_rect(center=(400, 75))
        self.screen.blit(heading, heading_rect)

        scores = self.highscore_manager.scores[:10]

        table_x = 150
        table_y = 140
        table_width = 500
        header_height = 45
        row_height = 35

        # Adjust table height to the number of players.
        table_height = header_height + len(scores) * row_height

        table_rect = pygame.Rect(
            table_x, table_y, table_width, table_height
        )

        pygame.draw.rect(
            self.screen, (212, 212, 184), table_rect, 2
        )

        # Column headings
        self.draw_text("RANK", 170, 150, (255, 255, 0))
        self.draw_text("PLAYER", 280, 150, (255, 255, 0))
        self.draw_text("SCORE", 500, 150, (255, 255, 0))

        pygame.draw.line(
            self.screen,
            (212, 212, 184),
            (table_x, table_y + header_height),
            (table_x + table_width, table_y + header_height),
        )

        # Player rows
        for rank, entry in enumerate(scores, start=1):
            y = table_y + header_height + (rank - 1) * row_height + 5

            self.draw_text(str(rank), 170, y)
            self.draw_text(str(entry["name"]), 280, y)
            self.draw_text(str(entry["score"]), 500, y)

        if not scores:
            self.draw_text(
                "No scores saved yet",
                265,
                table_y + header_height + 30,
            )

        self.draw_text(
            "Press ESC to return",
            280,
            555,
            (166, 166, 70),
        )

    def draw_name_input(self) -> None:
        heading = self.title_font.render(
            "ENTER YOUR NAME", True, (166, 166, 70)
        )
        self.screen.blit(
            heading,
            heading.get_rect(center=(400, 110)),
        )

        score_text = self.font.render(
            f"FINAL SCORE: {self.final_score}",
            True,
            (255, 255, 0),
        )
        self.screen.blit(
            score_text,
            score_text.get_rect(center=(400, 180)),
        )

        self.draw_text("Player name:", 300, 235)

        input_rect = pygame.Rect(250, 280, 300, 60)
        pygame.draw.rect(
            self.screen, (212, 212, 184), input_rect, 2
        )

        self.draw_text(
            self.player_name,
            input_rect.x + 10,
            input_rect.y + 15,
            (255, 255, 0),
        )

        self.draw_text(
            "Press ENTER to save",
            265,
            390,
            (166, 166, 70),
        )
        self.draw_text(
            "Press ESC to return",
            265,
            435,
            (166, 166, 70),
        )

        if self.message:
            message_surface = self.small_font.render(
                self.message, True, (255, 100, 100)
            )
            self.screen.blit(
                message_surface,
                message_surface.get_rect(center=(400, 500)),
            )

    def start_game(self) -> None:
        self.engine = Engine(self.config)
        self.current_screen = "playing"
        self.is_paused = False
        self.player_name = ""
        self.message = ""
        # TEMPORARY TEST:
        # Replace with the real game engine later.
        # self.current_screen = "playing"

    def activate_menu_option(self, option: int) -> bool:
        if option == 0:
            self.start_game()
        elif option == 1:
            self.current_screen = "highscores"
        elif option == 2:
            self.current_screen = "instructions"
        elif option == 3:
            return False
        return True

    def handle_name_input(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_ESCAPE:
            self.current_screen = "menu"

        elif event.key == pygame.K_BACKSPACE:
            self.player_name = self.player_name[:-1]
            self.message = ""

        elif event.key == pygame.K_RETURN:
            name = self.player_name.strip()

            if not name:
                self.message = "Please enter a valid name"
                return

            try:
                self.highscore_manager.add(name, self.final_score)
                self.highscore_manager.save()
            except ValueError as error:
                self.message = str(error)
                return

            self.current_screen = "menu"
            self.player_name = ""
            self.message = ""

        else:
            character = event.unicode

            if (
                len(self.player_name) < 10
                and len(character) == 1
                and (character.isascii() and character.isalnum()
                     or character == " ")
            ):
                self.player_name += character
                self.message = ""

    def draw_instructions(self) -> None:
        """Draw the game instructions and cheat controls."""

        title = self.title_font.render(
            "HOW TO PLAY", True, (255, 255, 0)
        )
        title_rect = title.get_rect(center=(400, 55))
        self.screen.blit(title, title_rect)

        instructions = [
            "ARROW KEYS - MOVE PAC-MAN",
            "EAT PACGUMS TO EARN POINTS",
            "AVOID THE GHOSTS",
            "EAT SUPER PACGUMS TO EAT GHOSTS",
            "COMPLETE ALL LEVELS TO WIN",
            "P - PAUSE / RESUME",
        ]

        y = 115

        for instruction in instructions:
            text = self.font.render(
                instruction, True, (212, 212, 184)
            )
            text_rect = text.get_rect(center=(400, y))
            self.screen.blit(text, text_rect)
            y += 43

        # Cheat mode section
        cheat_title = self.font.render(
            "CHEAT MODE", True, (255, 255, 0)
        )
        cheat_rect = cheat_title.get_rect(center=(400, 390))
        self.screen.blit(cheat_title, cheat_rect)

        cheats = [
            "1 - INVINCIBILITY ON/OFF",
            "2 - FREEZE GHOSTS ON/OFF",
            "3 - SPEED BOOST ON/OFF",
        ]

        y = 425

        for cheat in cheats:
            text = self.font.render(
                cheat, True, (0, 255, 150)
            )
            text_rect = text.get_rect(center=(400, y))
            self.screen.blit(text, text_rect)
            y += 35

        # Return to menu
        back_text = self.font.render(
            "PRESS ESC TO RETURN", True, (166, 166, 70)
        )
        back_rect = back_text.get_rect(center=(400, 560))
        self.screen.blit(back_text, back_rect)

    def draw_pause(self) -> None:
        # Semi-transparent dark overlay
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        # PAUSED heading
        heading = self.title_font.render(
            "PAUSED", True, (255, 255, 0)
        )
        heading_rect = heading.get_rect(center=(400, 75))
        self.screen.blit(heading, heading_rect)

        # Pause symbol
        pygame.draw.rect(
            self.screen, (255, 255, 0),
            (370, 250, 15, 60)
        )
        pygame.draw.rect(
            self.screen, (255, 255, 0),
            (415, 250, 15, 60)
        )

        # Resume instruction
        text = self.font.render(
            "Press p to Resume", True, (255, 255, 255)
        )
        self.draw_text(
            "Press ESC to return to Menu",
            245,
            420,
            (166, 166, 70),
        )
        text_rect = text.get_rect(center=(400, 370))
        self.screen.blit(text, text_rect)

    def draw_game_over_or_won(self, won: bool) -> None:
        """Display the game result and final score."""

        if won:
            message = "GAME WON"
            color = (0, 255, 0)
        else:
            message = "GAME OVER"
            color = (255, 0, 0)

        self.draw_text(message, 300, 180, color)

        self.draw_text(
            f"Final Score: {self.engine.score}",
            300, 280, (255, 255, 255)
        )

        self.draw_text(
            "Press ENTER to continue",
            260, 380, (255, 255, 0)
        )

    def run(self) -> None:
        running = True

        while running:
            # 1. Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif self.current_screen == "menu":
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_DOWN:
                            self.selected_option = (
                                self.selected_option + 1
                            ) % 4

                        elif event.key == pygame.K_UP:
                            self.selected_option = (
                                self.selected_option - 1
                            ) % 4

                        elif event.key == pygame.K_RETURN:
                            running = self.activate_menu_option(
                                self.selected_option
                            )

                    elif (
                        event.type == pygame.MOUSEBUTTONDOWN
                        and event.button == 1
                    ):
                        if self.start_rect.collidepoint(event.pos):
                            running = self.activate_menu_option(0)

                        elif self.scores_rect.collidepoint(event.pos):
                            running = self.activate_menu_option(1)

                        elif self.instructions_rect.collidepoint(event.pos):
                            running = self.activate_menu_option(2)

                        elif self.quit_rect.collidepoint(event.pos):
                            running = self.activate_menu_option(3)

                elif self.current_screen == "highscores":
                    if (
                        event.type == pygame.KEYDOWN
                        and event.key == pygame.K_ESCAPE
                    ):
                        self.current_screen = "menu"

                elif self.current_screen == "new_player":
                    if event.type == pygame.KEYDOWN:
                        self.handle_name_input(event)

                elif self.current_screen == "instructions":
                    if (
                        event.type == pygame.KEYDOWN
                        and event.key == pygame.K_ESCAPE
                    ):
                        self.current_screen = "menu"


                elif self.current_screen == "playing":
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.current_screen = "menu"
                            self.is_paused = False

                        elif event.key == pygame.K_p:
                            self.is_paused = not self.is_paused

                            if self.is_paused:
                                self.engine.pause_game()
                            else:
                                self.engine.resume_game()

                        elif not self.is_paused:
                            if event.key in (pygame.K_UP, pygame.K_w):
                                self.engine.set_direction(Direction.NORTH)

                            elif event.key in (pygame.K_DOWN, pygame.K_s):
                                self.engine.set_direction(Direction.SOUTH)

                            elif event.key in (pygame.K_LEFT, pygame.K_a):
                                self.engine.set_direction(Direction.WEST)

                            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                                self.engine.set_direction(Direction.EAST)

                            elif event.key == pygame.K_1:
                                self.engine.toggle_invincible()

                            elif event.key == pygame.K_2:
                                self.engine.toggle_freeze()

                            elif event.key == pygame.K_3:
                                self.engine.toggle_speed()

                elif self.current_screen in ("game_over", "game_won"):
                    if (
                        event.type == pygame.KEYDOWN
                        and event.key == pygame.K_RETURN
                    ):
                        self.final_score = self.engine.score
                        self.player_name = ""
                        self.message = ""
                        self.current_screen = "new_player"

            # 2. Stop immediately if user exits
            if not running:
                break

            # 3. Update game timing
            dt = self.clock.tick(60) / 1000.0

            # 4. Update engine
            if self.current_screen == "playing" and not self.is_paused:
                self.engine.dt_update(dt)

                if self.engine.state == GameState.GAME_OVER:
                    self.current_screen = "game_over"
                elif self.engine.state == GameState.LEVEL_WON:
                    self.engine.continue_game()
                elif self.engine.state == GameState.GAME_WON:
                    self.current_screen = "game_won"

            # 5. Clear window
            self.screen.fill((0, 0, 0))

            # 6. Draw active screen
            if self.current_screen == "menu":
                self.draw_menu()

            elif self.current_screen == "highscores":
                self.draw_highscores()

            elif self.current_screen == "new_player":
                self.draw_name_input()

            elif self.current_screen == "instructions":
                self.draw_instructions()

            elif self.current_screen == "playing":
                self.draw_game()

            elif self.current_screen == "game_over":
                self.draw_game_over_or_won(False)
            elif self.current_screen == "game_won":
                self.draw_game_over_or_won(True)

            # 7. Update display
            pygame.display.update()

        pygame.quit()


if __name__ == "__main__":
    try:
        renderer = Renderer()
        renderer.run()

    except KeyboardInterrupt:
        print("\nProgram interrupted by user (Ctrl+C).")

    finally:
        pygame.quit()
