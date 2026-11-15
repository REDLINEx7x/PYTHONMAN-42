
import pygame

from shell.highscores import HighscoreManager


class Renderer:
    def __init__(self, highscore_filename: str = "highscores.json") -> None:
        pygame.init()

        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Pac-Man 42")
        self.clock = pygame.time.Clock()

        self.current_screen = "menu"
        self.player_name = ""
        self.final_score = 0
        self.message = ""

        self.highscore_manager = HighscoreManager(highscore_filename)
        self.highscore_manager.load()

        self.font = pygame.font.Font(None, 36)
        self.title_font = pygame.font.Font(None, 70)
        self.small_font = pygame.font.Font(None, 26)

        self.title = self.title_font.render(
            "PAC-MAN 42", True, (166, 166, 70)
        )
        self.start_game_text = self.font.render(
            "START GAME", True, (212, 212, 184)
        )
        self.high_scores = self.font.render(
            "HIGH SCORES", True, (212, 212, 184)
        )
        self.quit_game = self.font.render(
            "QUIT", True, (212, 212, 184)
        )
        self.instructions_text = self.font.render(
            "INSTRUCTIONS", True, (212, 212, 184)
        )

        self.title_rect = self.title.get_rect(center=(400, 70))
        self.start_rect = self.start_game_text.get_rect(center=(400, 200))
        self.scores_rect = self.high_scores.get_rect(center=(400, 280))
        self.instructions_rect = self.instructions_text.get_rect(
            center=(400, 430)
        )
        self.quit_rect = self.quit_game.get_rect(center=(400, 350))

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
        self.screen.blit(self.start_game_text, self.start_rect)
        self.screen.blit(self.high_scores, self.scores_rect)
        self.screen.blit(self.instructions_text, self.instructions_rect)
        self.screen.blit(self.quit_game, self.quit_rect)

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
        # TEMPORARY TEST:
        # Replace with the real game engine later.
        self.final_score = 2500
        self.player_name = ""
        self.message = ""
        self.current_screen = "new_player"

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

    def run(self) -> None:
        running = True

        while running:
            # 1. Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif self.current_screen == "menu":
                    if (
                        event.type == pygame.MOUSEBUTTONDOWN
                      
                        and event.button == 1
                    ):
                        if self.start_rect.collidepoint(event.pos):
                            self.start_game()

                        elif self.scores_rect.collidepoint(event.pos):
                            self.current_screen = "highscores"
                        elif self.instructions_rect.collidepoint(event.pos):
                            self.current_screen = "instructions"
                        elif self.quit_rect.collidepoint(event.pos):
                            running = False

                elif self.current_screen == "highscores":
                    if (
                        event.type == pygame.KEYDOWN
                        and event.key == pygame.K_ESCAPE
                    ):
                        self.current_screen = "menu"

                elif self.current_screen == "new_player":
                    if event.type == pygame.KEYDOWN:
                        self.handle_name_input(event)


            # 2. Clear window
            self.screen.fill((0, 0, 0))

            # 3. Draw active screen
            if self.current_screen == "menu":
                self.draw_menu()

            elif self.current_screen == "highscores":
                self.draw_highscores()

            elif self.current_screen == "new_player":
                self.draw_name_input()

            # 4. Update window
            pygame.display.update()
            self.clock.tick(60)

        pygame.quit()


if __name__ == "__main__":
    renderer = Renderer()
    renderer.run()
