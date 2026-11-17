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


#if __name__ == "__main__":
#    # 1. Test valid generation
#    grid1 = generate_maze(width=15, height=11, seed=42)
#    print(f"Generated Grid with {len(grid1.get_all_cells())} cells")
#    print(f"Centre: {grid1.get_center()} | Corners: {grid1.get_corners()}")

#    # 2. Test determinism (same seed -> identical cells)
#    grid2 = generate_maze(width=15, height=11, seed=42)
#    assert grid1.get_all_cells() == grid2.get_all_cells(), "Determinism check failed!"
#    print("Determinism check: PASSED")

#    # 3. Test error handling (seed <= 0 should raise MazeAdapterError)
#    try:
#        generate_maze(width=15, height=11, seed=0)
#        print("Error handling check: FAILED")
#    except MazeAdapterError as err:
#        print(f"Error handling check: PASSED ({err})")
