"""Snapshot-based terminal viewer. Run: python3 -B ascii_view.py --steps 5.

Only this file is needed for integration; no pygame or installation is required
when the repository's bundled maze-generator wheel is available.
"""

import argparse
import math
from pathlib import Path
import sys
from types import SimpleNamespace

# Keep running this standalone viewer from creating files in engine/ or shell/.
sys.dont_write_bytecode = True

from engine.grid import Grid
from engine.models import Cell, Direction
from engine.snapshot import GameSnapshot


def render_snapshot(snapshot: GameSnapshot, grid: Grid) -> str:
    """Render snapshot contents and grid walls without mutating either.

    Each cell has room for the player, all four ghosts, and its collectible,
    so overlapping actors never hide one another or a super-pacgum.
    """
    cell_width = 6
    canvas = [
        [" "] * (grid.get_width() * (cell_width + 1) + 1)
        for _ in range(grid.get_height() * 2 + 1)
    ]
    for cell in grid.get_all_cells():
        y, x = cell.row * 2, cell.col * (cell_width + 1)
        walls = grid.walls_here(cell)
        for dy in (0, 2):
            for dx in (0, cell_width + 1):
                canvas[y + dy][x + dx] = "+"
        for direction, dy in ((Direction.NORTH, 0), (Direction.SOUTH, 2)):
            if walls & direction:
                canvas[y + dy][x + 1:x + cell_width + 1] = "-" * cell_width
        for direction, dx in ((Direction.WEST, 0), (Direction.EAST, cell_width + 1)):
            if walls & direction:
                canvas[y + 1][x + dx] = "|"
        contents = "P" if cell == snapshot.pacu_position else ""
        contents += "".join(
            str(index) for index, (position, _) in enumerate(snapshot.ghosts, 1)
            if position == cell
        )
        contents += "O" if cell in snapshot.supergums else "." if cell in snapshot.pacgums else ""
        canvas[y + 1][x + 1:x + cell_width + 1] = contents.center(cell_width)

    status = (
        f"Level {snapshot.level} | {snapshot.state.name} | "
        f"Score {snapshot.score} | Lives {snapshot.lives} | "
        f"Pacgums {len(snapshot.pacgums)} | Super-pacgums {len(snapshot.supergums)}"
    )
    ghosts = " | ".join(
        f"{index}: {state.name} at {tuple(position)}"
        for index, (position, state) in enumerate(snapshot.ghosts, 1)
    )
    return "\n".join([status, *("".join(row) for row in canvas), ghosts])


def main() -> None:
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=5, help="updates after the initial frame (default: 5)")
    parser.add_argument("--dt", type=float, default=0.2, help="fixed seconds per update (default: 0.2)")
    parser.add_argument("--config", type=Path, default=root / "config.json")
    args = parser.parse_args()

    # Import the bundled pure-Python wheel directly if it is not installed.
    try:
        import mazegenerator  # noqa: F401
    except ModuleNotFoundError as exc:
        if exc.name != "mazegenerator":
            raise
        wheels = sorted((root / "mazegenerator-00001").glob("mazegenerator-*.whl"))
        if not wheels:
            parser.error("mazegenerator is missing; install the project's dependencies")
        sys.path.insert(0, str(wheels[-1]))

    from engine.gameengine import Engine, MAX_DT
    from shell.config import ConfigLoader

    if args.steps < 0:
        parser.error("--steps must be non-negative")
    if not math.isfinite(args.dt) or not 0 < args.dt <= MAX_DT:
        parser.error(f"--dt must be greater than 0 and at most {MAX_DT}")

    config = ConfigLoader.load_config(str(args.config))
    # The engine expects level_timeout; the existing loader supplies level_max_time.
    settings = SimpleNamespace(**vars(config), level_timeout=config.level_max_time)
    engine = Engine(settings)
    print("P player | 1 2 3 4 ghosts | . pacgum | O super-pacgum | + - | walls")
    for step in range(args.steps + 1):
        if step:
            snapshot = engine.get_snapshot()
            moves = engine.grid.open_neighbors(Cell(*snapshot.pacu_position))
            if moves:
                # Prefer a collectible, then continue forward, then any legal turn.
                direction, _ = min(moves, key=lambda move: (
                    move[1] not in snapshot.pacgums | snapshot.supergums,
                    move[0] != snapshot.pacu_direction,
                ))
                engine.set_direction(direction)
            engine.dt_update(args.dt)
        snapshot = engine.get_snapshot()
        print(f"\nStep {step} | simulation time {step * args.dt:.2f}s | dt {args.dt:g}s")
        print(render_snapshot(snapshot, engine.grid))
        if snapshot.state.name != "PLAYING":
            break


if __name__ == "__main__":
    main()
