import pygame


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
