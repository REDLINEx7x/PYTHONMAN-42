from engine.types import Cell, Direction
from errors import GridError


class Grid:
    def __init__(self, width: int, height: int, cells: list[list[int]]) -> None:

        if width <= 0 or height <= 0:
            raise GridError("width and height must be positive")

        if len(cells) != height:
            raise GridError("number of rows must equal height")

        for row in cells:
            if len(row) != width:
                raise GridError("every row must have width cells")
            if any(not 0 <= value <= 15 for value in row):
                raise GridError("wall values must be between 0 and 15")

        for r in range(height):
            for c in range(width - 1):
                east_wall = bool(cells[r][c] & Direction.EAST)
                west_wall = bool(cells[r][c + 1] & Direction.WEST)
                if east_wall != west_wall:
                    raise GridError(f"asymmetric wall at row {r}, col {c}")

        for c in range(width):
            for r in range(height - 1):                                 #range(height - 1) stops at the second-to-last row, so r + 1 never goes past the table.
                north_wall = bool(cells[r + 1][c] & Direction.NORTH)
                south_wall = bool(cells[r][c] & Direction.SOUTH)
                if north_wall != south_wall:
                    raise GridError(f"asymmetric wall at row {r}, col {c}")

        self._height = height
        self._width = width
        self._cells = [row[:] for row in cells]

    def get_height(self):
            return self._height

    def get_width(self):
            return self._width

    def in_bounds(self, cell):

        if cell.row < 0 or cell.row > self._height - 1 or cell.col < 0 or cell.col > self._width - 1:
            return False
        return True

    def neighbor(self, cell, direction):

        return Cell(
            cell.row + direction.row_step,
            cell.col + direction.col_step,
        )

    def can_move(self, cell, direction):

        if not self.in_bounds(cell):
            return False
        new_neigbor = self.neighbor(cell, direction)
        if not self.in_bounds(new_neigbor):
            return False
        return not (self._cells[cell.row][cell.col] & direction)

    def open_neighbors(self, cell):

        moves = []
        for direction in Direction:
            if self.can_move(cell, direction):
                dest = self.neighbor(cell, direction)
                moves.append((direction, dest))
        return moves

    def walls_here(self, cell):

        if not self.in_bounds(cell):
            raise GridError()
        return self._cells[cell.row][cell.col]

    def get_corners(self):

        top_left = Cell(0, 0)
        top_right = Cell(0, self._width - 1)
        bottom_left = Cell(self._height - 1, 0)
        bottom_right = Cell(self._height - 1, self._width - 1)
        return [top_left, top_right, bottom_left, bottom_right]

    def get_center(self):

        center_row = self._height // 2
        center_col = self._width // 2
        return Cell(center_row, center_col)

    def get_all_cells(self) -> list[Cell]:
        """Return all cells in the grid in row-major order."""
        all_cells = []
        for row in range(self._height):
            for col in range(self._width):
                all_cells.append(Cell(row, col))
        return all_cells
