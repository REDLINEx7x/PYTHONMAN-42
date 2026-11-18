"""Standalone snapshot viewer: python3 -B pygame_view.py --steps 5 --dt 0.2.

The demo stays open after its updates. Use --play for keyboard control,
or --headless for a finite smoke run without a display.
"""

import argparse
import math
import os
from pathlib import Path
import sys
from types import SimpleNamespace

sys.dont_write_bytecode = True


def draw_snapshot(screen, snapshot, grid, font, footer):
    """Draw walls from the grid and all gameplay contents from a snapshot."""
    import pygame
    from engine.models import Direction

    screen.fill((12, 15, 26))
    size = min((screen.get_width() - 40) // grid.get_width(),
               (screen.get_height() - 120) // grid.get_height())
    left = (screen.get_width() - size * grid.get_width()) // 2
    top = 70

    def center(cell):
        row, col = cell
        return left + col * size + size // 2, top + row * size + size // 2

    for cell in grid.get_all_cells():
        x, y = left + cell.col * size, top + cell.row * size
        edges = (
            (Direction.NORTH, (x, y), (x + size, y)),
            (Direction.EAST, (x + size, y), (x + size, y + size)),
            (Direction.SOUTH, (x, y + size), (x + size, y + size)),
            (Direction.WEST, (x, y), (x, y + size)),
        )
        for direction, start, end in edges:
            if grid.walls_here(cell) & direction:
                pygame.draw.line(screen, (55, 105, 255), start, end, 2)
    for cell in snapshot.pacgums:
        pygame.draw.circle(screen, (255, 221, 172), center(cell), max(2, size // 14))
    for cell in snapshot.supergums:
        pygame.draw.circle(screen, (255, 245, 220), center(cell), max(4, size // 5), 2)

    radius = max(3, size // 3)
    pygame.draw.circle(screen, (255, 222, 35), center(snapshot.pacu_position), radius)
    colors = ((255, 80, 90), (255, 153, 211), (70, 224, 235), (255, 169, 65))
    for index, (cell, state) in enumerate(snapshot.ghosts):
        x, y = center(cell)
        color = (70, 90, 240) if state.name == "FRIGHTENED" else colors[index % 4]
        if state.name != "EATEN":
            pygame.draw.circle(screen, color, (x, y - 2), radius)
            pygame.draw.rect(screen, color, (x - radius, y - 2, radius * 2, radius))
        for dx in (-radius // 3, radius // 3):
            pygame.draw.circle(screen, (255, 255, 255), (x + dx, y - 3), max(2, radius // 4))
            pygame.draw.circle(screen, (15, 20, 55), (x + dx, y - 3), 1)

    lines = (
        (f"Score {snapshot.score}    Lives {snapshot.lives}    Level {snapshot.level}    {snapshot.state.name}", 15),
        (f"Pacgums {len(snapshot.pacgums)}    Super-pacgums {len(snapshot.supergums)}", 40),
        (footer, screen.get_height() - 32),
    )
    for text, y in lines:
        screen.blit(font.render(text, True, (235, 238, 250)), (20, y))


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=5)
    parser.add_argument("--dt", type=float, default=0.2)
    parser.add_argument("--play", action="store_true", help="play with arrows or WASD instead of the demo")
    parser.add_argument("--headless", action="store_true", help="run demo and exit without a window")
    parser.add_argument("--config", type=Path, default=root / "config.json")
    args = parser.parse_args()
    if args.steps < 0 or not math.isfinite(args.dt) or not 0 < args.dt <= 0.2:
        parser.error("use --steps >= 0 and 0 < --dt <= 0.2 (engine timestep limit)")
    if args.headless and args.play:
        parser.error("--headless is only available for the finite demo")
    if args.headless:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    try:
        import pygame
    except ModuleNotFoundError:
        parser.error("pygame is missing; install pygame-ce in your Python environment")
    try:
        import mazegenerator  # noqa: F401
    except ModuleNotFoundError as exc:
        if exc.name != "mazegenerator":
            raise
        wheels = sorted((root / "mazegenerator-00001").glob("mazegenerator-*.whl"))
        if not wheels:
            parser.error("install the project's mazegenerator dependency")
        sys.path.insert(0, str(wheels[-1]))
    from engine.gameengine import Engine
    from engine.models import Cell, Direction
    from shell.config import ConfigLoader

    settings = dict(vars(ConfigLoader.load_config(str(args.config))))
    settings.setdefault("level_timeout", settings.get("level_max_time", 90))
    engine = Engine(SimpleNamespace(**settings))
    pygame.display.init()
    pygame.font.init()
    try:
        screen = pygame.display.set_mode((800, 660))
        pygame.display.set_caption("Pac-Man snapshot viewer")
        font = pygame.font.Font(None, 24)
        keys = {pygame.K_UP: Direction.NORTH, pygame.K_w: Direction.NORTH,
                pygame.K_RIGHT: Direction.EAST, pygame.K_d: Direction.EAST,
                pygame.K_DOWN: Direction.SOUTH, pygame.K_s: Direction.SOUTH,
                pygame.K_LEFT: Direction.WEST, pygame.K_a: Direction.WEST}
        clock = pygame.time.Clock()
        elapsed, step, running = 0.0, 0, True
        snapshot = engine.get_snapshot()
        while running:
            elapsed += args.dt if args.headless else clock.tick(60) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif args.play and event.key in keys:
                        engine.set_direction(keys[event.key])
                    elif args.play and event.key == pygame.K_RETURN:
                        engine.continue_game()
            if not running:
                break
            while elapsed >= args.dt and (args.play or step < args.steps):
                elapsed -= args.dt
                snapshot = engine.get_snapshot()
                if snapshot.state.name != "PLAYING":
                    break
                if not args.play:
                    moves = engine.grid.open_neighbors(Cell(*snapshot.pacu_position))
                    if moves:
                        direction, _ = min(moves, key=lambda move: (
                            move[1] not in snapshot.pacgums | snapshot.supergums,
                            move[0] != snapshot.pacu_direction))
                        engine.set_direction(direction)
                engine.dt_update(args.dt)
                step += 1
            # Avoid banking time while stopped or waiting for the next level.
            elapsed = min(elapsed, args.dt)
            snapshot = engine.get_snapshot()
            footer = ("Arrows / WASD: move | Enter: next level | Esc: quit" if args.play
                      else f"Demo {step}/{args.steps} | dt {args.dt:g}s | Esc: quit")
            draw_snapshot(screen, snapshot, engine.grid, font, footer)
            pygame.display.flip()
            if args.headless and (step >= args.steps or snapshot.state.name != "PLAYING"):
                running = False
        print(f"Steps {step} | Score {snapshot.score} | Lives {snapshot.lives} | {snapshot.state.name}")
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
