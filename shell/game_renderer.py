import pygame
from engine.grid import Grid
from engine.types import Cell, Direction


class GameRenderer:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font = pygame.font.Font(None, 36)

    def draw_hud(
        self,
        score: int,
        lives: int,
        level: int,
        time_left: int,
    ) -> None:
        values = [
            (f"SCORE: {score}", 20),
            (f"LIVES: {lives}", 220),
            (f"LEVEL: {level}", 420),
            (f"TIME: {time_left}", 600),
        ]

        for text, x in values:
            surface = self.font.render(
                text, True, (255, 255, 0)
            )
            self.screen.blit(surface, (x, 20))

    def draw_maze(self, grid: Grid) -> None:
        cell_size = 25
        offset_x = 50
        offset_y = 100

        for row in range(grid.get_height()):
            for col in range(grid.get_width()):
                cell = Cell(row, col)
                walls = grid.walls_here(cell)

                x = offset_x + col * cell_size
                y = offset_y + row * cell_size
                if walls & Direction.NORTH:
                    pygame.draw.line(
                        self.screen,
                        (0, 100, 255),
                        (x, y),
                        (x + cell_size, y),
                        3,
                    )

                if walls & Direction.EAST:
                    pygame.draw.line(
                        self.screen,
                        (0, 100, 255),
                        (x + cell_size, y),
                        (x + cell_size, y + cell_size),
                        3,
                    )
                if walls & Direction.SOUTH:
                    pygame.draw.line(
                        self.screen,
                        (0, 100, 255),
                        (x, y + cell_size),
                        (x + cell_size, y + cell_size),
                        3,
                    )
                if walls & Direction.WEST:
                    pygame.draw.line(
                        self.screen,
                        (0, 100, 255),
                        (x, y),
                        (x, y + cell_size),
                        3,
                    )

    def draw_pacman(self, row: int, col: int) -> None:
        cell_size = 25
        offset_x = 50
        offset_y = 100
        center_x = offset_x + col * cell_size + cell_size // 2
        center_y = offset_y + row * cell_size + cell_size // 2
        radius = cell_size // 2 - 3
        pygame.draw.circle(
            self.screen,
            (255, 255, 0),
            (center_x, center_y),
            radius,
        )

    def draw_ghosts(
        self,
        ghosts: list[tuple[int, int]],
    ) -> None:
        cell_size = 25
        offset_x = 50
        offset_y = 100

        for row, col in ghosts:
            center_x = offset_x + col * cell_size + cell_size // 2
            center_y = offset_y + row * cell_size + cell_size // 2
            radius = cell_size // 2 - 3
            pygame.draw.circle(
                self.screen,
                (255, 0, 0),
                (center_x, center_y),
                radius,
            )
