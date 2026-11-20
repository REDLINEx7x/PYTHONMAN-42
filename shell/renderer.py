
import pygame
from shell.highscores import HighscoreManager
from shell.config import Config
from shell.game_renderer import GameRenderer
from mazegenerator import MazeGenerator
from engine.grid import Grid
from engine.gameengine import Engine
from engine.models import Direction
from engine.gameengine import GameState
from pathlib import Path


class Renderer:
    def __init__(self, config: Config) -> None:
        # Initialize pygame
        pygame.init()
        self.is_paused = False
        self.selected_option = 0

        # Configuration
        self.config = config
        self.podium_icons = [
            pygame.image.load("assets/medals/crown.png"),
            pygame.image.load("assets/medals/silver.png"),
            pygame.image.load("assets/medals/bronze.png"),
        ]

        self.screen = pygame.display.set_mode(
                (0, 0),
                pygame.FULLSCREEN,
                )
        background_dir = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "backgrounds"
        )

        self.backgrounds = {}

        for screen_name in (
            "menu",
            "highscores",
            "instructions",
            "playing",
            "game_over",
            "game_won",
            "new_player",
        ):
            path = background_dir / f"{screen_name}.png"

            if path.is_file():
                image = pygame.image.load(str(path)).convert()
                self.backgrounds[screen_name] = pygame.transform.smoothscale(
                    image,
                    self.screen.get_size(),
                )
        self.screen_width, self.screen_height = (
            self.screen.get_size()
        )
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

        # Draw maze
        self.game_renderer.draw_maze(self.engine.grid)

        # Draw collectibles
        self.game_renderer.draw_pacgums(snapshot.pacgums)
        self.game_renderer.draw_supergums(snapshot.supergums)

        # Draw Pac-Man
        self.game_renderer.draw_pacman(
            start_row,
            start_col,
            snapshot.pacu_direction,
        )

        # Draw ghosts
        self.game_renderer.draw_ghosts(
            snapshot.ghosts,
            self.engine.edible_timer,
        )

        # Left panel: Ghost Radar
        self.game_renderer.draw_ghost_panel(
            snapshot.ghosts,
        )

        # Right panel: Power Panel
        self.game_renderer.draw_cheat_panel(
            invincible=self.engine.invincible,
            freeze=self.engine.freeze,
            speed=self.engine.speed,
        )

        # Top HUD
        self.game_renderer.draw_hud(
            score=snapshot.score,
            lives=snapshot.lives,
            level=snapshot.level,
            time_left=int(self.engine.level_timer),
            status=snapshot.state.name,
        )

        # Bottom controls bar: P / ESC
        self.game_renderer.draw_controls_bar()

        # Pause overlay must be drawn last
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

    def draw_background(self) -> None:
        background = self.backgrounds.get(self.current_screen)

        if background is not None:
            self.screen.blit(background, (0, 0))
        else:
            self.screen.fill((8, 12, 24))

    def draw_menu(self) -> None:
        screen_width, screen_height = self.screen.get_size()

        # self.screen.fill((8, 12, 24))

        title_font = pygame.font.Font(None, 88)
        subtitle_font = pygame.font.Font(None, 27)
        menu_font = pygame.font.Font(None, 36)
        footer_font = pygame.font.Font(None, 23)

        title = title_font.render(
            "PYTHONMAN-42", True, (255, 216, 75)
        )
        title_rect = title.get_rect(
            center=(screen_width // 2, screen_height // 5)
        )
        self.screen.blit(title, title_rect)

        subtitle = subtitle_font.render(
            "A CLASSIC ARCADE ADVENTURE",
            True,
            (133, 169, 255),
        )
        self.screen.blit(
            subtitle,
            subtitle.get_rect(
                center=(screen_width // 2, title_rect.bottom + 20)
            ),
        )

        # Decorative Pac-Man
        pacman = pygame.transform.scale(
            self.game_renderer.pacman_sprite,
            (95, 95),
        )
        self.screen.blit(
            pacman,
            pacman.get_rect(
                center=(screen_width // 2 - 115, screen_height // 3)
            ),
        )

        for index in range(3):
            pygame.draw.circle(
                self.screen,
                (255, 255, 255),
                (
                    screen_width // 2 - 30 + index * 40,
                    screen_height // 3,
                ),
                5,
            )

        ghost = pygame.transform.scale(
            self.game_renderer.ghost_sprites[0],
            (85, 85),
        )
        self.screen.blit(
            ghost,
            ghost.get_rect(
                center=(screen_width // 2 + 150, screen_height // 3)
            ),
        )

        # Menu container
        menu_width = min(460, screen_width - 60)
        item_height = 62
        item_gap = 12
        padding = 22

        menu_height = (
            4 * item_height + 3 * item_gap + 2 * padding
        )

        menu_x = (screen_width - menu_width) // 2
        menu_y = int(screen_height * 0.45)

        container = pygame.Rect(
            menu_x, menu_y, menu_width, menu_height
        )

        pygame.draw.rect(
            self.screen, (25, 36, 64), container
        )
        pygame.draw.rect(
            self.screen, (75, 126, 255), container, 3
        )
        pygame.draw.rect(
            self.screen,
            (125, 175, 255),
            (menu_x + 5, menu_y + 5, menu_width - 10, 2),
        )

        options = [
            "START GAME",
            "HIGH SCORES",
            "INSTRUCTIONS",
            "QUIT GAME",
        ]

        # Save actual visible button rectangles
        self.menu_rects = []

        for index, option in enumerate(options):
            item_rect = pygame.Rect(
                menu_x + padding,
                menu_y + padding + index * (item_height + item_gap),
                menu_width - 2 * padding,
                item_height,
            )

            self.menu_rects.append(item_rect)

            selected = index == self.selected_option

            background = (
                (49, 75, 136) if selected else (17, 27, 50)
            )
            border = (
                (255, 216, 75) if selected else (69, 101, 162)
            )
            text_color = (
                (255, 216, 75) if selected else (230, 235, 255)
            )

            pygame.draw.rect(
                self.screen, background, item_rect
            )
            pygame.draw.rect(
                self.screen, border, item_rect, 2
            )

            text = menu_font.render(
                option, True, text_color
            )
            self.screen.blit(
                text,
                text.get_rect(center=item_rect.center),
            )

            if selected:
                arrow = menu_font.render(
                    ">", True, (255, 216, 75)
                )
                self.screen.blit(
                    arrow,
                    (
                        item_rect.x + 15,
                        item_rect.centery
                        - arrow.get_height() // 2,
                    ),
                )

        footer = footer_font.render(
            "UP / DOWN - NAVIGATE    ENTER - SELECT",
            True,
            (132, 149, 188),
        )
        self.screen.blit(
            footer,
            footer.get_rect(
                center=(screen_width // 2, screen_height - 160)
            ),
        )

    def draw_highscores(self) -> None:
        screen_width, screen_height = self.screen.get_size()

        # Actual saved scores, highest first
        scores = sorted(
            self.highscore_manager.scores,
            key=lambda entry: int(entry["score"]),
            reverse=True,
        )[:10]

        # Colors
        gold = (255, 216, 75)
        silver = (201, 213, 233)
        bronze = (243, 173, 118)
        blue = (75, 126, 255)
        white = (235, 240, 255)

        # Fonts
        title_font = pygame.font.Font(None, 68)
        subtitle_font = pygame.font.Font(None, 25)
        name_font = pygame.font.Font(None, 27)
        score_font = pygame.font.Font(None, 29)
        rank_font = pygame.font.Font(None, 55)
        section_font = pygame.font.Font(None, 28)
        row_font = pygame.font.Font(None, 25)
        footer_font = pygame.font.Font(None, 24)

        # Main title
        title = title_font.render(
            "HALL OF FAME", True, gold
        )
        title_rect = title.get_rect(
            center=(screen_width // 2, 65)
        )
        self.screen.blit(title, title_rect)

        subtitle = subtitle_font.render(
            "THE LEGENDS OF PYTHONMAN-42",
            True,
            (133, 169, 255),
        )
        self.screen.blit(
            subtitle,
            subtitle.get_rect(
                center=(screen_width // 2, 110)
            ),
        )

        # Main leaderboard container
        board_width = min(850, screen_width - 60)
        board_height = min(650, screen_height - 210)

        board = pygame.Rect(
            (screen_width - board_width) // 2,
            145,
            board_width,
            board_height,
        )

        pygame.draw.rect(
            self.screen, (25, 36, 64), board
        )
        pygame.draw.rect(
            self.screen, blue, board, 3
        )
        pygame.draw.rect(
            self.screen,
            (125, 175, 255),
            (board.x + 5, board.y + 5, board.width - 10, 2),
        )

        if not scores:
            empty_font = pygame.font.Font(None, 40)
            empty = empty_font.render(
                "NO CHAMPIONS YET", True, gold
            )
            self.screen.blit(
                empty,
                empty.get_rect(center=board.center),
            )

        else:
            # Top three podium positions:
            # 2nd on left, 1st in center, 3rd on right
            podium_order = [
                (1, silver, 105),
                (0, gold, 150),
                (2, bronze, 75),
            ]

            podium_area_top = board.y + 35
            podium_bottom = board.y + 265

            column_width = board.width // 3

            for column, (score_index, color, height) in enumerate(
                podium_order
            ):
                if score_index >= len(scores):
                    continue

                entry = scores[score_index]

                center_x = (
                    board.x
                    + column * column_width
                    + column_width // 2
                )

                podium_width = column_width - 24

                podium_rect = pygame.Rect(
                    center_x - podium_width // 2,
                    podium_bottom - height,
                    podium_width,
                    height,
                )

                # Podium background
                podium_color = (
                    (81, 68, 34)
                    if score_index == 0
                    else (38, 57, 85)
                    if score_index == 1
                    else (68, 51, 43)
                )

                # Rounded top corners, square bottom corners
                pygame.draw.rect(
                    self.screen,
                    podium_color,
                    podium_rect,
                    border_top_left_radius=25,
                    border_top_right_radius=25,
                    border_bottom_left_radius=0,
                    border_bottom_right_radius=0,
                )

                # Rounded podium border
                pygame.draw.rect(
                    self.screen,
                    color,
                    podium_rect,
                    2,
                    border_top_left_radius=25,
                    border_top_right_radius=25,
                    border_bottom_left_radius=0,
                    border_bottom_right_radius=0,
                )
                # Rank number
                rank = rank_font.render(
                    str(score_index + 1),
                    True,
                    color,
                )
                self.screen.blit(
                    rank,
                    rank.get_rect(center=podium_rect.center),
                )

                # First place stays at the top.
                # Second and third place move closer to their podiums.
                if score_index == 0:
                    name_y = podium_area_top + 30
                    score_y = podium_area_top + 65
                else:
                    name_y = podium_rect.top - 55
                    score_y = podium_rect.top - 25

                # Player name
                player_name = name_font.render(
                    str(entry["name"])[:16].upper(),
                    True,
                    color,
                )
                self.screen.blit(
                    player_name,
                    player_name.get_rect(
                        center=(center_x, name_y)
                    ),
                )

                # Player score
                player_score = score_font.render(
                    f'{int(entry["score"]):,}',
                    True,
                    white,
                )
                self.screen.blit(
                    player_score,
                    player_score.get_rect(
                        center=(center_x, score_y)
                    ),
                )
                # Crown for 1st, medals for 2nd and 3rd
                icon = pygame.transform.smoothscale(
                    self.podium_icons[score_index],
                    (52, 52),
                )

                # Position icons above each player's name
                if score_index == 0:
                    icon_y = podium_area_top - 5
                else:
                    icon_y = podium_rect.top - 95

                icon_rect = icon.get_rect(
                    center=(center_x, icon_y)
                )
                self.screen.blit(icon, icon_rect)
            # Other legends section
            other_scores = scores[3:]

            section_y = podium_bottom + 35

            section_title = section_font.render(
                "OTHER LEGENDS", True, (143, 169, 223)
            )
            self.screen.blit(
                section_title,
                (
                    board.x + 35,
                    section_y,
                ),
            )

            pygame.draw.line(
                self.screen,
                (69, 101, 162),
                (board.x + 30, section_y + 35),
                (board.right - 30, section_y + 35),
                2,
            )

            # Automatically fit remaining players
            rows_top = section_y + 48
            rows_bottom = board.bottom - 20

            if other_scores:
                available_height = max(
                    1, rows_bottom - rows_top
                )
                row_height = min(
                    40,
                    available_height // len(other_scores),
                )

                for index, entry in enumerate(
                    other_scores, start=4
                ):
                    y = rows_top + (index - 4) * row_height

                    row_rect = pygame.Rect(
                        board.x + 30,
                        y,
                        board.width - 60,
                        max(1, row_height - 4),
                    )

                    pygame.draw.rect(
                        self.screen,
                        (17, 27, 50),
                        row_rect,
                    )

                    rank_text = row_font.render(
                        f"{index:02d}",
                        True,
                        white,
                    )
                    name_text = row_font.render(
                        str(entry["name"])[:20].upper(),
                        True,
                        white,
                    )
                    score_text = row_font.render(
                        f'{int(entry["score"]):,}',
                        True,
                        white,
                    )

                    text_y = (
                        row_rect.centery
                        - rank_text.get_height() // 2
                    )

                    self.screen.blit(
                        rank_text,
                        (row_rect.x + 15, text_y),
                    )
                    self.screen.blit(
                        name_text,
                        (row_rect.x + 85, text_y),
                    )
                    self.screen.blit(
                        score_text,
                        (
                            row_rect.right
                            - score_text.get_width()
                            - 15,
                            text_y,
                        ),
                    )

        # Bottom ESC instruction
        footer = footer_font.render(
            "[ESC]  BACK TO MENU",
            True,
            gold,
        )
        self.screen.blit(
            footer,
            footer.get_rect(
                center=(
                    screen_width // 2,
                    screen_height - 160,
                )
            ),
        )

    def draw_name_input(self) -> None:
        """Draw the arcade-style player name entry screen."""

        screen_width, screen_height = self.screen.get_size()

        gold = (255, 216, 75)
        blue = (75, 126, 255)
        white = (230, 235, 255)
        muted = (143, 169, 223)

        title_font = pygame.font.Font(None, 58)
        subtitle_font = pygame.font.Font(None, 23)
        label_font = pygame.font.Font(None, 27)
        score_font = pygame.font.Font(None, 80)
        input_font = pygame.font.Font(None, 35)
        button_font = pygame.font.Font(None, 28)
        message_font = pygame.font.Font(None, 24)

        # Main centered panel
        panel_width = min(580, screen_width - 40)
        panel_height = min(550, screen_height - 40)

        panel = pygame.Rect(
            (screen_width - panel_width) // 2,
            (screen_height - panel_height) // 2,
            panel_width,
            panel_height,
        )

        # Dark translucent background
        overlay = pygame.Surface(
            (panel_width, panel_height),
            pygame.SRCALPHA,
        )
        overlay.fill((8, 13, 28, 235))
        self.screen.blit(overlay, panel.topleft)

        pygame.draw.rect(
            self.screen,
            blue,
            panel,
            3,
            border_radius=12,
        )

        # Decorative top line
        pygame.draw.line(
            self.screen,
            (125, 175, 255),
            (panel.x + 30, panel.y + 18),
            (panel.right - 30, panel.y + 18),
            2,
        )

        # Player icon
        icon_x = panel.centerx
        icon_y = panel.y + 65

        pygame.draw.circle(
            self.screen,
            gold,
            (icon_x, icon_y - 10),
            14,
        )
        pygame.draw.arc(
            self.screen,
            gold,
            pygame.Rect(
                icon_x - 28,
                icon_y + 5,
                56,
                38,
            ),
            0,
            3.14159,
            5,
        )

        # Main heading
        heading = title_font.render(
            "ENTER YOUR NAME",
            True,
            gold,
        )
        self.screen.blit(
            heading,
            heading.get_rect(
                center=(panel.centerx, panel.y + 145)
            ),
        )

        subtitle = subtitle_font.render(
            "YOUR SCORE DESERVES A PLACE IN HISTORY",
            True,
            muted,
        )
        self.screen.blit(
            subtitle,
            subtitle.get_rect(
                center=(panel.centerx, panel.y + 183)
            ),
        )

        # Separator
        pygame.draw.line(
            self.screen,
            (69, 101, 162),
            (panel.x + 45, panel.y + 208),
            (panel.right - 45, panel.y + 208),
            2,
        )

        # Final score label
        score_label = label_font.render(
            "FINAL SCORE",
            True,
            white,
        )
        self.screen.blit(
            score_label,
            score_label.get_rect(
                center=(panel.centerx, panel.y + 242)
            ),
        )

        # Score value
        score = score_font.render(
            str(self.final_score),
            True,
            gold,
        )
        self.screen.blit(
            score,
            score.get_rect(
                center=(panel.centerx, panel.y + 295)
            ),
        )

        # Player name label
        input_width = min(420, panel_width - 60)
        input_x = panel.centerx - input_width // 2

        name_label = label_font.render(
            "PLAYER NAME",
            True,
            white,
        )
        self.screen.blit(
            name_label,
            (input_x, panel.y + 340),
        )

        # Name input box
        input_rect = pygame.Rect(
            input_x,
            panel.y + 370,
            input_width,
            55,
        )

        pygame.draw.rect(
            self.screen,
            (17, 27, 50),
            input_rect,
            border_radius=7,
        )
        pygame.draw.rect(
            self.screen,
            (117, 160, 255),
            input_rect,
            2,
            border_radius=7,
        )

        # Player name
        name_text = input_font.render(
            self.player_name,
            True,
            gold,
        )
        self.screen.blit(
            name_text,
            (
                input_rect.x + 15,
                input_rect.centery - name_text.get_height() // 2,
            ),
        )

        # Input cursor
        cursor_x = input_rect.x + 17 + name_text.get_width()

        if cursor_x < input_rect.right - 12:
            pygame.draw.line(
                self.screen,
                gold,
                (cursor_x, input_rect.y + 12),
                (cursor_x, input_rect.bottom - 12),
                2,
            )

        # Save button
        button = pygame.Rect(
            panel.centerx - 165,
            panel.y + 445,
            330,
            45,
        )

        pygame.draw.rect(
            self.screen,
            (24, 41, 77),
            button,
            border_radius=7,
        )
        pygame.draw.rect(
            self.screen,
            blue,
            button,
            2,
            border_radius=7,
        )

        button_text = button_font.render(
            "[ ENTER ]  SAVE SCORE",
            True,
            gold,
        )
        self.screen.blit(
            button_text,
            button_text.get_rect(center=button.center),
        )

        # Return instruction
        return_text = message_font.render(
            "[ ESC ]  RETURN TO MENU",
            True,
            muted,
        )
        self.screen.blit(
            return_text,
            return_text.get_rect(
                center=(panel.centerx, panel.y + 515)
            ),
        )

        # Validation / error message
        if self.message:
            message_surface = message_font.render(
                self.message,
                True,
                (255, 100, 100),
            )
            self.screen.blit(
                message_surface,
                message_surface.get_rect(
                    center=(panel.centerx, panel.bottom + 22)
                ),
            )

    def start_game(self) -> None:
        self.engine = Engine(self.config)
        self.current_screen = "playing"
        self.is_paused = False
        self.player_name = ""
        self.message = ""

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
        """Draw the improved arcade mission briefing screen."""

        screen_width, screen_height = self.screen.get_size()

        gold = (255, 216, 75)
        blue = (75, 126, 255)
        white = (230, 235, 255)
        muted = (143, 169, 223)
        panel_color = (25, 36, 64)
        inner_color = (17, 27, 50)

        green = (96, 232, 165)
        ice_blue = (128, 201, 255)

        title_font = pygame.font.Font(None, 68)
        subtitle_font = pygame.font.Font(None, 25)
        section_font = pygame.font.Font(None, 31)
        body_font = pygame.font.Font(None, 25)
        small_font = pygame.font.Font(None, 23)
        key_font = pygame.font.Font(None, 28)

        # Main heading
        title = title_font.render("MISSION BRIEFING", True, gold)
        self.screen.blit(
            title,
            title.get_rect(center=(screen_width // 2, 60)),
        )

        subtitle = subtitle_font.render(
            "WELCOME TO PYTHONMAN-42",
            True,
            (133, 169, 255),
        )
        self.screen.blit(
            subtitle,
            subtitle.get_rect(center=(screen_width // 2, 105)),
        )

        # Compact main container
        panel_width = min(850, screen_width - 60)
        panel_height = 545

        panel = pygame.Rect(
            (screen_width - panel_width) // 2,
            145,
            panel_width,
            panel_height,
        )

        pygame.draw.rect(self.screen, panel_color, panel)
        pygame.draw.rect(self.screen, blue, panel, 3)

        pygame.draw.rect(
            self.screen,
            (125, 175, 255),
            (panel.x + 5, panel.y + 5, panel.width - 10, 2),
        )

        left = panel.x + 35
        right = panel.right - 35

        mission_y = panel.y + 25

        pacman = pygame.transform.scale(
            self.game_renderer.pacman_sprite,
            (65, 65),
        )
        self.screen.blit(
            pacman,
            pacman.get_rect(center=(left + 35, mission_y + 45)),
        )

        mission_title = section_font.render(
            "YOUR MISSION", True, gold
        )
        self.screen.blit(
            mission_title,
            (left + 90, mission_y + 3),
        )

        mission_lines = [
            "Collect Pac-Gums to earn points and clear the maze.",
            "Avoid ghosts, or eat Super Pac-Gums to fight back!",
            "Complete all levels to win the game.",
        ]

        for index, line in enumerate(mission_lines):
            text = body_font.render(line, True, white)
            self.screen.blit(
                text,
                (left + 90, mission_y + 35 + index * 24),
            )

        # Decorative ghost and Super Pac-Gum
        ghost = pygame.transform.scale(
            self.game_renderer.ghost_sprites[0],
            (42, 42),
        )
        self.screen.blit(
            ghost,
            ghost.get_rect(center=(right - 25, mission_y + 20)),
        )

        pygame.draw.circle(
            self.screen,
            gold,
            (right - 25, mission_y + 76),
            8,
        )

        pygame.draw.line(
            self.screen,
            (69, 101, 162),
            (left, mission_y + 112),
            (right, mission_y + 112),
            2,
        )

        movement_y = mission_y + 130

        movement_title = section_font.render(
            "MOVEMENT CONTROLS", True, gold
        )
        self.screen.blit(
            movement_title,
            (left, movement_y),
        )

        key_size = 43
        key_gap = 6

        def draw_key(label: str, center_x: int, y: int) -> None:
            rect = pygame.Rect(
                center_x - key_size // 2,
                y,
                key_size,
                key_size,
            )

            pygame.draw.rect(
                self.screen,
                (49, 75, 136),
                rect,
                border_radius=6,
            )
            pygame.draw.rect(
                self.screen,
                (117, 160, 255),
                rect,
                2,
                border_radius=6,
            )

            key_text = key_font.render(label, True, white)
            self.screen.blit(
                key_text,
                key_text.get_rect(center=rect.center),
            )

        # Arrow keys
        arrows_x = panel.centerx - 160
        keyboard_y = movement_y + 55

        arrow_title = small_font.render(
            "ARROW KEYS", True, muted
        )
        self.screen.blit(
            arrow_title,
            arrow_title.get_rect(
                center=(arrows_x, keyboard_y - 20)
            ),
        )

        draw_key("^", arrows_x, keyboard_y)

        for index, label in enumerate(("<", "v", ">")):
            draw_key(
                label,
                arrows_x + (index - 1) * (key_size + key_gap),
                keyboard_y + key_size + key_gap,
            )

        # WASD keys
        wasd_x = panel.centerx + 160

        wasd_title = small_font.render(
            "WASD", True, muted
        )
        self.screen.blit(
            wasd_title,
            wasd_title.get_rect(
                center=(wasd_x, keyboard_y - 20)
            ),
        )

        draw_key("W", wasd_x, keyboard_y)

        for index, label in enumerate(("A", "S", "D")):
            draw_key(
                label,
                wasd_x + (index - 1) * (key_size + key_gap),
                keyboard_y + key_size + key_gap,
            )

        pygame.draw.line(
            self.screen,
            (69, 101, 162),
            (left, movement_y + 160),
            (right, movement_y + 160),
            2,
        )

        cards_y = movement_y + 178
        card_gap = 18
        card_width = (panel_width - 70 - card_gap) // 2
        card_height = 145

        pause_card = pygame.Rect(
            left, cards_y, card_width, card_height
        )

        abilities_card = pygame.Rect(
            left + card_width + card_gap,
            cards_y,
            card_width,
            card_height,
        )

        for card in (pause_card, abilities_card):
            pygame.draw.rect(
                self.screen,
                inner_color,
                card,
                border_radius=8,
            )
            pygame.draw.rect(
                self.screen,
                (69, 101, 162),
                card,
                2,
                border_radius=8,
            )

        # Game controls
        pause_title = section_font.render(
            "GAME CONTROLS", True, gold
        )
        self.screen.blit(
            pause_title,
            (pause_card.x + 20, pause_card.y + 18),
        )

        pause_lines = [
            "[P]    Pause / Resume",
            "[ESC]  Return to Main Menu",
        ]

        for index, line in enumerate(pause_lines):
            text = body_font.render(line, True, white)
            self.screen.blit(
                text,
                (pause_card.x + 20, pause_card.y + 65 + index * 35),
            )

        # Special abilities
        abilities_title = section_font.render(
            "SPECIAL ABILITIES", True, gold
        )
        self.screen.blit(
            abilities_title,
            (abilities_card.x + 20, abilities_card.y + 18),
        )

        abilities = [
            ("[1]  Invincibility ON/OFF", green),
            ("[2]  Freeze Ghosts ON/OFF", ice_blue),
            ("[3]  Speed Boost ON/OFF", gold),
        ]

        for index, (label, color) in enumerate(abilities):
            text = body_font.render(label, True, color)
            self.screen.blit(
                text,
                (
                    abilities_card.x + 20,
                    abilities_card.y + 62 + index * 28,
                ),
            )

        footer = small_font.render(
            "[ESC]  BACK TO MENU", True, gold
        )
        self.screen.blit(
            footer,
            footer.get_rect(
                center=(screen_width // 2, screen_height - 160)
            ),
        )

    def draw_pause(self) -> None:
        screen_width, screen_height = self.screen.get_size()

        # Dark transparent overlay covering the screen
        overlay = pygame.Surface(
            (screen_width, screen_height),
            pygame.SRCALPHA,
        )
        overlay.fill((0, 0, 0, 165))
        self.screen.blit(overlay, (0, 0))

        # Centered pause panel
        panel_width = min(460, screen_width - 40)
        panel_height = min(300, screen_height - 40)

        panel = pygame.Rect(
            (screen_width - panel_width) // 2,
            (screen_height - panel_height) // 2,
            panel_width,
            panel_height,
        )

        pygame.draw.rect(
            self.screen, (25, 36, 64), panel
        )
        pygame.draw.rect(
            self.screen, (75, 126, 255), panel, 3
        )
        pygame.draw.rect(
            self.screen,
            (125, 175, 255),
            (
                panel.x + 5,
                panel.y + 5,
                panel.width - 10,
                2,
            ),
        )

        # Fonts
        title_font = pygame.font.Font(None, 52)
        icon_font = pygame.font.Font(None, 65)
        text_font = pygame.font.Font(None, 28)

        # PAUSED title
        title = title_font.render(
            "PAUSED", True, (255, 216, 75)
        )
        self.screen.blit(
            title,
            title.get_rect(
                center=(panel.centerx, panel.y + 55)
            ),
        )

        # Pause symbol
        icon = icon_font.render(
            "II", True, (255, 216, 75)
        )
        self.screen.blit(
            icon,
            icon.get_rect(
                center=(panel.centerx, panel.y + 125)
            ),
        )

        # Resume instruction
        resume = text_font.render(
            "Press P to Resume",
            True,
            (255, 255, 255),
        )
        self.screen.blit(
            resume,
            resume.get_rect(
                center=(panel.centerx, panel.y + 195)
            ),
        )

        # Return instruction
        return_text = text_font.render(
            "Press ESC to Return to Menu",
            True,
            (255, 216, 75),
        )
        self.screen.blit(
            return_text,
            return_text.get_rect(
                center=(panel.centerx, panel.y + 240)
            ),
        )

    def draw_game_over_or_won(self, won: bool) -> None:
        """Display a centered arcade-style game result screen."""

        screen_width, screen_height = self.screen.get_size()

        gold = (255, 216, 75)
        white = (230, 235, 255)
        muted = (143, 169, 223)

        if won:
            message = "GAME WON"
            subtitle = "THE MAZE IS YOURS!"
            accent = (62, 220, 154)
            button_color = (21, 45, 42)
        else:
            message = "GAME OVER"
            subtitle = "THE MAZE WINS THIS ROUND"
            accent = (255, 89, 107)
            button_color = (38, 26, 44)

        title_font = pygame.font.Font(None, 75)
        subtitle_font = pygame.font.Font(None, 27)
        label_font = pygame.font.Font(None, 29)
        score_font = pygame.font.Font(None, 90)
        button_font = pygame.font.Font(None, 29)

        # Main result panel
        panel_width = min(550, screen_width - 40)
        panel_height = min(440, screen_height - 60)

        panel = pygame.Rect(
            (screen_width - panel_width) // 2,
            (screen_height - panel_height) // 2,
            panel_width,
            panel_height,
        )

        # Dark translucent panel
        overlay = pygame.Surface(
            (panel_width, panel_height),
            pygame.SRCALPHA,
        )
        overlay.fill((8, 13, 28, 235))
        self.screen.blit(overlay, panel.topleft)

        pygame.draw.rect(
            self.screen,
            accent,
            panel,
            3,
            border_radius=12,
        )

        # Decorative top line
        pygame.draw.line(
            self.screen,
            accent,
            (panel.x + 30, panel.y + 18),
            (panel.right - 30, panel.y + 18),
            2,
        )

        # Result icon (drawn with Pygame)
        icon_y = panel.y + 75

        if won:
            # Gold trophy cup
            cup = pygame.Rect(panel.centerx - 25, icon_y - 20, 50, 35)
            pygame.draw.rect(
                self.screen, gold, cup, border_radius=6
            )
            pygame.draw.rect(
                self.screen,
                gold,
                (panel.centerx - 5, icon_y + 15, 10, 17),
            )
            pygame.draw.rect(
                self.screen,
                gold,
                (panel.centerx - 24, icon_y + 32, 48, 7),
                border_radius=3,
            )
        else:
            # Red ghost-like icon
            pygame.draw.circle(
                self.screen,
                accent,
                (panel.centerx, icon_y),
                26,
            )
            pygame.draw.rect(
                self.screen,
                accent,
                (panel.centerx - 26, icon_y, 52, 25),
            )

            for offset in (-17, 0, 17):
                pygame.draw.circle(
                    self.screen,
                    (8, 13, 28),
                    (panel.centerx + offset, icon_y + 24),
                    8,
                )

            for offset in (-10, 10):
                pygame.draw.circle(
                    self.screen,
                    white,
                    (panel.centerx + offset, icon_y - 3),
                    5,
                )

        # Main title
        title = title_font.render(message, True, accent)
        self.screen.blit(
            title,
            title.get_rect(
                center=(panel.centerx, panel.y + 155)
            ),
        )

        # Subtitle
        subtitle_text = subtitle_font.render(
            subtitle, True, muted
        )
        self.screen.blit(
            subtitle_text,
            subtitle_text.get_rect(
                center=(panel.centerx, panel.y + 195)
            ),
        )

        # Separator
        pygame.draw.line(
            self.screen,
            (69, 101, 162),
            (panel.x + 45, panel.y + 225),
            (panel.right - 45, panel.y + 225),
            2,
        )

        # Final score label
        score_label = label_font.render(
            "FINAL SCORE", True, white
        )
        self.screen.blit(
            score_label,
            score_label.get_rect(
                center=(panel.centerx, panel.y + 260)
            ),
        )

        # Final score value
        score = score_font.render(
            str(self.engine.score), True, gold
        )
        self.screen.blit(
            score,
            score.get_rect(
                center=(panel.centerx, panel.y + 315)
            ),
        )

        # Continue button
        button = pygame.Rect(
            panel.centerx - 165,
            panel.y + 360,
            330,
            52,
        )

        pygame.draw.rect(
            self.screen,
            button_color,
            button,
            border_radius=8,
        )
        pygame.draw.rect(
            self.screen,
            accent,
            button,
            2,
            border_radius=8,
        )

        button_text = button_font.render(
            "[ ENTER ]  CONTINUE", True, gold
        )
        self.screen.blit(
            button_text,
            button_text.get_rect(center=button.center),
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
                        if event.key == pygame.K_ESCAPE:
                            running = False

                        elif event.key == pygame.K_DOWN:
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

                    elif event.type == pygame.MOUSEMOTION:
                        for index, rect in enumerate(
                            getattr(self, "menu_rects", [])
                        ):
                            if rect.collidepoint(event.pos):
                                self.selected_option = index
                                break

                    elif (
                        event.type == pygame.MOUSEBUTTONDOWN
                        and event.button == 1
                    ):
                        for index, rect in enumerate(
                            getattr(self, "menu_rects", [])
                        ):
                            if rect.collidepoint(event.pos):
                                self.selected_option = index
                                running = self.activate_menu_option(index)
                                break

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
                                self.engine.set_direction(
                                    Direction.NORTH
                                )

                            elif event.key in (pygame.K_DOWN, pygame.K_s):
                                self.engine.set_direction(
                                    Direction.SOUTH
                                )

                            elif event.key in (pygame.K_LEFT, pygame.K_a):
                                self.engine.set_direction(
                                    Direction.WEST
                                )

                            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                                self.engine.set_direction(
                                    Direction.EAST
                                )

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
            # self.screen.fill((0, 0, 0))
            self.draw_background()

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
