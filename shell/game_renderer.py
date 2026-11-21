import pygame
from engine.grid import Grid
from engine.models import Cell, Direction
from pathlib import Path
from engine.creatures import GhostState


class GameRenderer:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.offset_x = 0
        self.offset_y = 0
        self.font = pygame.font.Font(None, 36)
        self.cell_size = 25
        self.mouth_animation_speed = 200

        self.ghost_previous_positions = {}
        self.ghost_target_positions = {}
        self.ghost_move_starts = {}

        self.ghost_previous_positions = {}
        self.ghost_target_positions = {}
        self.ghost_move_starts = {}

        self.wall_color = (35, 75, 220)
        self.wall_highlight = (100, 160, 255)
        self.wall_thickness = 5
        sprite_path = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "sprites"
        )

        self.pacman_sprite = pygame.image.load(
            str(sprite_path / "pacman.png")
        ).convert_alpha()
        self.ghost_sprites = [
            pygame.image.load(
                str(sprite_path / filename)
            ).convert_alpha()
            for filename in (
                "ghost_red.png",
                "ghost_pink.png",
                "ghost_cyan.png",
                "ghost_orange.png",
            )
        ]
        self.pacman_closed_sprite = pygame.image.load(
            str(sprite_path / "pacman_closed.png")
        ).convert_alpha()
        self.frightened_sprite = pygame.image.load(
            str(sprite_path / "ghost_frightened.png")
        ).convert_alpha()

        self.eaten_sprite = pygame.image.load(
            str(sprite_path / "ghost_eaten.png")
        ).convert_alpha()

    def draw_hud(
        self,
        score: int,
        lives: int,
        level: int,
        time_left: int,
        status: str = "PLAYING",
    ) -> None:
        screen_width = self.screen.get_width()

        margin = 30
        gap = 12
        box_height = 70
        box_width = (screen_width - 2 * margin - 4 * gap) // 5

        values = [
            ("SCORE", f"{score:06d}"),
            ("LIVES", str(lives)),
            ("LEVEL", f"{level:02d}"),
            ("TIME", f"{max(0, time_left):03d}s"),
            ("STATUS", status),
        ]

        label_font = pygame.font.Font(None, 25)
        value_font = pygame.font.Font(None, 35)

        for index, (label, value) in enumerate(values):
            x = margin + index * (box_width + gap)
            y = 20

            rect = pygame.Rect(x, y, box_width, box_height)

            pygame.draw.rect(
                self.screen,
                (25, 36, 64),
                rect,
            )

            pygame.draw.rect(
                self.screen,
                (75, 126, 255),
                rect,
                3,
            )

            pygame.draw.rect(
                self.screen,
                (125, 175, 255),
                (x + 5, y + 5, box_width - 10, 2),
            )

            label_surface = label_font.render(
                label, True, (158, 196, 255)
            )
            value_surface = value_font.render(
                value, True, (255, 216, 75)
            )

            label_rect = label_surface.get_rect(
                center=(rect.centerx, y + 20)
            )
            value_rect = value_surface.get_rect(
                center=(rect.centerx, y + 48)
            )

            self.screen.blit(label_surface, label_rect)
            self.screen.blit(value_surface, value_rect)

    def draw_maze(self, grid: Grid) -> None:
        screen_width, screen_height = self.screen.get_size()

        self.grid_height = grid.get_height()
        self.grid_width = grid.get_width()

        margin = 30
        gap = 12
        box_width = (
            screen_width - 2 * margin - 4 * gap
        ) // 5

        # Fixed maze area under LIVES, LEVEL, TIME
        self.maze_box_x = margin + box_width + gap
        self.maze_box_y = 125
        self.maze_box_width = 3 * box_width + 2 * gap
        self.maze_box_height = max(
            1, screen_height - self.maze_box_y - 90
        )

        # Cells fill the entire fixed maze area
        self.cell_width = (
            self.maze_box_width / self.grid_width
        )
        self.cell_height = (
            self.maze_box_height / self.grid_height
        )

        self.offset_x = self.maze_box_x
        self.offset_y = self.maze_box_y

        self.cell_size = max(
            1,
            int(min(self.cell_width, self.cell_height)),
        )

        thickness = max(
            1,
            min(
                self.wall_thickness,
                int(min(self.cell_width, self.cell_height) / 5),
            ),
        )
        highlight = max(1, thickness // 3)

        for row in range(self.grid_height):
            for col in range(self.grid_width):
                cell = Cell(row, col)
                walls = grid.walls_here(cell)

                x1 = self.offset_x + round(
                    col * self.cell_width
                )
                x2 = self.offset_x + round(
                    (col + 1) * self.cell_width
                )
                y1 = self.offset_y + round(
                    row * self.cell_height
                )
                y2 = self.offset_y + round(
                    (row + 1) * self.cell_height
                )

                width = x2 - x1
                height = y2 - y1

                if walls & Direction.NORTH:
                    pygame.draw.rect(
                        self.screen,
                        self.wall_color,
                        (x1, y1, width, thickness),
                    )
                    pygame.draw.rect(
                        self.screen,
                        self.wall_highlight,
                        (x1, y1, width, highlight),
                    )

                if walls & Direction.EAST:
                    pygame.draw.rect(
                        self.screen,
                        self.wall_color,
                        (x2 - thickness, y1, thickness, height),
                    )
                    pygame.draw.rect(
                        self.screen,
                        self.wall_highlight,
                        (x2 - highlight, y1, highlight, height),
                    )

                if walls & Direction.SOUTH:
                    pygame.draw.rect(
                        self.screen,
                        self.wall_color,
                        (x1, y2 - thickness, width, thickness),
                    )
                    pygame.draw.rect(
                        self.screen,
                        self.wall_highlight,
                        (x1, y2 - highlight, width, highlight),
                    )

                if walls & Direction.WEST:
                    pygame.draw.rect(
                        self.screen,
                        self.wall_color,
                        (x1, y1, thickness, height),
                    )
                    pygame.draw.rect(
                        self.screen,
                        self.wall_highlight,
                        (x1, y1, highlight, height),
                    )

    def reset_movement_animation(self) -> None:

        self.ghost_previous_positions.clear()
        self.ghost_target_positions.clear()
        self.ghost_move_starts.clear()

    def draw_pacman(
        self,
        row: float,
        col: float,
        direction: Direction,
    ) -> None:
        animation_frame = (
            pygame.time.get_ticks()
            // self.mouth_animation_speed
        ) % 2

        image = (
            self.pacman_sprite
            if animation_frame == 0
            else self.pacman_closed_sprite
        )

        angles = {
            Direction.EAST: 0,
            Direction.WEST: 180,
            Direction.NORTH: 90,
            Direction.SOUTH: 270,
        }

        sprite_size = max(
            1,
            int(min(self.cell_width, self.cell_height)) - 4,
        )

        sprite = pygame.transform.scale(
            image,
            (sprite_size, sprite_size),
        )

        sprite = pygame.transform.rotate(
            sprite,
            angles.get(direction, 0),
        )

        center_x = self.offset_x + round(
            (col + 0.5) * self.cell_width
        )
        center_y = self.offset_y + round(
            (row + 0.5) * self.cell_height
        )

        rect = sprite.get_rect(
            center=(center_x, center_y)
        )

        self.screen.blit(sprite, rect)

    def draw_ghosts(
        self,
        ghosts,
        edible_timer: float,
        move_interval: float,
    ) -> None:
        sprite_size = max(
            1,
            int(min(self.cell_width, self.cell_height)) - 4,
        )

        now = pygame.time.get_ticks()

        for index, (position, state) in enumerate(ghosts):
            normal_sprite = self.ghost_sprites[
                index % len(self.ghost_sprites)
            ]

            if state == GhostState.EATEN:
                image = self.eaten_sprite

            elif state == GhostState.FRIGHTENED:
                if 0 < edible_timer <= 2.0:
                    flash_frame = (now // 200) % 2

                    image = (
                        self.frightened_sprite
                        if flash_frame == 0
                        else normal_sprite
                    )
                else:
                    image = self.frightened_sprite

            else:
                image = normal_sprite

            sprite = pygame.transform.scale(
                image,
                (sprite_size, sprite_size),
            )

            # Current position from the engine
            current_position = (position.row, position.col)

            # Initialize animation for this ghost
            if index not in self.ghost_target_positions:
                self.ghost_previous_positions[index] = current_position
                self.ghost_target_positions[index] = current_position
                self.ghost_move_starts[index] = now

            # Detect when the ghost changes tile
            elif current_position != self.ghost_target_positions[index]:
                previous = self.ghost_target_positions[index]

                distance = (
                    abs(current_position[0] - previous[0])
                    + abs(current_position[1] - previous[1])
                )

                if distance > 1:
                    # Teleport or respawn: move instantly
                    self.ghost_previous_positions[index] = current_position
                else:
                    # Normal movement: animate one tile
                    self.ghost_previous_positions[index] = previous

                self.ghost_target_positions[index] = current_position
                self.ghost_move_starts[index] = now

            # Calculate animation progress
            elapsed = (
                now - self.ghost_move_starts[index]
            ) / 1000.0

            progress = min(1.0, elapsed / move_interval)

            previous_row, previous_col = (
                self.ghost_previous_positions[index]
            )

            target_row, target_col = (
                self.ghost_target_positions[index]
            )

            # Interpolate between two tiles
            smooth_row = previous_row + (
                target_row - previous_row
            ) * progress

            smooth_col = previous_col + (
                target_col - previous_col
            ) * progress

            # Convert interpolated tile coordinates to pixels
            center_x = self.offset_x + round(
                (smooth_col + 0.5) * self.cell_width
            )

            center_y = self.offset_y + round(
                (smooth_row + 0.5) * self.cell_height
            )

            rect = sprite.get_rect(
                center=(center_x, center_y)
            )

            self.screen.blit(sprite, rect)
        
    def draw_supergums(
        self,
        supergums: frozenset[tuple[int, int]],
    ) -> None:

        for row, col in supergums:
            center_x = self.offset_x + round(
                (col + 0.5) * self.cell_width
            )
            center_y = self.offset_y + round(
                (row + 0.5) * self.cell_height
            )
            pygame.draw.circle(
                self.screen,
                (255, 255, 255),
                (center_x, center_y),
                7,
            )

    def draw_pacgums(
        self,
        pacgums: frozenset[tuple[int, int]],
    ) -> None:
        for row, col in pacgums:
            center_x = self.offset_x + round(
                (col + 0.5) * self.cell_width
            )
            center_y = self.offset_y + round(
                (row + 0.5) * self.cell_height
            )

            pygame.draw.circle(
                self.screen,
                (255, 255, 255),
                (center_x, center_y),
                3,
            )

    def draw_controls_bar(self) -> None:
        # Position below the maze
        bar_width = min(520, self.maze_box_width)
        bar_height = 36

        x = self.maze_box_x + (
            self.maze_box_width - bar_width
        ) // 2
        y = (
            self.maze_box_y
            + self.maze_box_height
            + 18
        )

        bar = pygame.Rect(
            x, y, bar_width, bar_height
        )

        # HUD-style background and border
        pygame.draw.rect(
            self.screen, (25, 36, 64), bar
        )
        pygame.draw.rect(
            self.screen, (75, 126, 255), bar, 2
        )
        pygame.draw.rect(
            self.screen,
            (125, 175, 255),
            (x + 5, y + 4, bar_width - 10, 1),
        )

        font = pygame.font.Font(None, 22)

        # Small keyboard shortcuts
        controls = [
            ("P", "PAUSE"),
            ("ESC", "RETURN TO MENU"),
        ]

        centers = [
            x + bar_width // 4,
            x + 3 * bar_width // 4,
        ]

        for (key, label), center_x in zip(
            controls, centers
        ):
            key_surface = font.render(
                f"[{key}]", True, (255, 216, 75)
            )
            label_surface = font.render(
                label, True, (230, 235, 255)
            )

            total_width = (
                key_surface.get_width()
                + 8
                + label_surface.get_width()
            )

            start_x = center_x - total_width // 2

            self.screen.blit(
                key_surface,
                (
                    start_x,
                    y + (bar_height - key_surface.get_height()) // 2,
                ),
            )
            self.screen.blit(
                label_surface,
                (
                    start_x + key_surface.get_width() + 8,
                    y + (bar_height - label_surface.get_height()) // 2,
                ),
            )

    def draw_ghost_panel(self, ghosts) -> None:
        screen_width, _ = self.screen.get_size()

        # Same dimensions and alignment as SCORE
        margin = 30
        gap = 12
        panel_width = (
            screen_width - 2 * margin - 4 * gap
        ) // 5

        panel_height = self.maze_box_height // 2

        x = margin
        y = self.maze_box_y

        panel = pygame.Rect(x, y, panel_width, panel_height)

        # Same design as SCORE box
        pygame.draw.rect(
            self.screen, (25, 36, 64), panel
        )
        pygame.draw.rect(
            self.screen, (75, 126, 255), panel, 3
        )
        pygame.draw.rect(
            self.screen,
            (125, 175, 255),
            (x + 5, y + 5, panel_width - 10, 2),
        )

        title_font = pygame.font.Font(None, 36)
        name_font = pygame.font.Font(None, 32)
        state_font = pygame.font.Font(None, 26)

        title = title_font.render(
            "GHOST RADAR", True, (255, 216, 75)
        )
        self.screen.blit(
            title,
            title.get_rect(center=(panel.centerx, y + 25)),
        )

        names = ("RED", "PINK", "CYAN", "ORANGE")

        # Distribute ghosts vertically inside the panel
        content_top = y + 55
        content_height = max(1, panel_height - 65)
        row_spacing = content_height / 4

        for index, (_, state) in enumerate(ghosts):
            if index >= len(names):
                break

            row_y = int(
                content_top + (index + 0.5) * row_spacing - 23
            )
            if state == GhostState.FRIGHTENED:
                sprite = self.frightened_sprite
                state_color = (100, 190, 255)
            elif state == GhostState.EATEN:
                sprite = self.eaten_sprite
                state_color = (200, 200, 200)
            else:
                sprite = self.ghost_sprites[index]
                state_color = (255, 180, 90)

            sprite = pygame.transform.scale(
                sprite, (42, 42)
            )
            self.screen.blit(sprite, (x + 18, row_y))

            name = name_font.render(
                names[index], True, (255, 255, 255)
            )
            status = state_font.render(
                state.name, True, state_color
            )

            self.screen.blit(name, (x + 75, row_y))
            self.screen.blit(status, (x + 75, row_y + 26))

    def draw_cheat_panel(
        self,
        invincible: bool,
        freeze: bool,
        speed: bool,
    ) -> None:
        screen_width, _ = self.screen.get_size()

        # Same dimensions and alignment as STATUS
        margin = 30
        gap = 12
        panel_width = (
            screen_width - 2 * margin - 4 * gap
        ) // 5

        panel_height = self.maze_box_height // 2

        x = margin + 4 * (panel_width + gap)
        y = self.maze_box_y

        panel = pygame.Rect(x, y, panel_width, panel_height)

        # Same design as SCORE box
        pygame.draw.rect(
            self.screen, (25, 36, 64), panel
        )
        pygame.draw.rect(
            self.screen, (75, 126, 255), panel, 3
        )
        pygame.draw.rect(
            self.screen,
            (125, 175, 255),
            (x + 5, y + 5, panel_width - 10, 2),
        )

        title_font = pygame.font.Font(None, 36)
        name_font = pygame.font.Font(None, 29)
        state_font = pygame.font.Font(None, 25)

        title = title_font.render(
            "POWER PANEL", True, (255, 216, 75)
        )
        self.screen.blit(
            title,
            title.get_rect(center=(panel.centerx, y + 25)),
        )

        cheats = [
            ("1", "INVINCIBLE", invincible),
            ("2", "FREEZE GHOSTS", freeze),
            ("3", "SPEED BOOST", speed),
        ]

        # Distribute cheats vertically inside the panel
        content_top = y + 55
        content_height = max(1, panel_height - 65)
        row_spacing = content_height / 3

        for index, (key, name, active) in enumerate(cheats):
            row_y = int(
                content_top + (index + 0.5) * row_spacing - 23
            )
            key_rect = pygame.Rect(
                x + 15, row_y, 40, 40
            )
            pygame.draw.rect(
                self.screen, (52, 71, 108), key_rect
            )
            pygame.draw.rect(
                self.screen, (107, 145, 255), key_rect, 2
            )

            key_surface = name_font.render(
                key, True, (255, 255, 255)
            )

            self.screen.blit(
                key_surface,
                key_surface.get_rect(center=key_rect.center),
            )

            name_surface = name_font.render(
                name, True, (255, 255, 255)
            )

            status_text = "ACTIVE" if active else "OFF"
            status_color = (
                (73, 229, 139)
                if active
                else (135, 144, 163)
            )

            status_surface = state_font.render(
                status_text, True, status_color
            )
            self.screen.blit(
                name_surface, (x + 70, row_y)
            )
            self.screen.blit(
                status_surface, (x + 70, row_y + 27)
            )

    def calculate_cell_size(self, grid: Grid) -> int:
        screen_width, screen_height = self.screen.get_size()

        # Reserve space for the interface
        side_panel_width = 250
        top_hud_height = 110
        bottom_panel_height = 90
        margin = 30

        available_width = (
            screen_width - 2 * side_panel_width - 2 * margin
        )

        available_height = (
            screen_height - top_hud_height
            - bottom_panel_height - 2 * margin
        )

        cell_width = available_width // grid.get_width()
        cell_height = available_height // grid.get_height()

        return max(1, min(cell_width, cell_height))
