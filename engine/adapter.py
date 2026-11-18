from mazegenerator import MazeGenerator
from engine.errors import MazeAdapterError
from engine.grid import Grid


def _generate_grid(width: int, height: int, seed: int) -> Grid:
    #if width <= 0 or height <= 0 or seed <= 0:
    #    raise MazeAdapterError(f"Invalid maze params ({width}x{height}, seed={seed})")

    try:
        maze_gen = MazeGenerator(
            size=(width, height),
            entry_cell=(0, 0),
            exit_cell=(width - 1, height - 1),
            perfect=False,
            seed=seed,
        )
        cells = [list(row) for row in maze_gen.maze]
        return Grid(width=width, height=height, cells=cells)
    except Exception as exc:
        raise MazeAdapterError(f"Maze failed ({width}x{height}, seed={seed}")


