"""Basic types shared by the whole engine: cells and directions."""

from enum import IntEnum
from typing import NamedTuple


class Cell(NamedTuple):
    """A position in the maze.

    Attributes:
        row: Row index, 0 is the top row and rows grow downward.
        col: Column index, 0 is the leftmost column.
    """

    row: int
    col: int


class Direction(IntEnum):
    """One of the four moves, valued as one wall bit each.

    The values match the usual maze encoding, so a cell's wall mask can
    be tested with a bitwise AND against a direction.
    """

    NORTH = 1
    EAST = 2
    SOUTH = 4
    WEST = 8

    @property
    def row_step(self) -> int:
        """Return the change in row when moving in this direction."""
        return _STEPS[self][0]

    @property
    def col_step(self) -> int:
        """Return the change in column when moving in this direction."""
        return _STEPS[self][1]

    @property
    def opposite(self) -> "Direction":
        """Return the direction pointing the other way."""
        return _OPPOSITES[self]


_STEPS: dict[Direction, tuple[int, int]] = {
    Direction.NORTH: (-1, 0),
    Direction.EAST: (0, 1),
    Direction.SOUTH: (1, 0),
    Direction.WEST: (0, -1),
}

_OPPOSITES: dict[Direction, Direction] = {
    Direction.NORTH: Direction.SOUTH,
    Direction.EAST: Direction.WEST,
    Direction.SOUTH: Direction.NORTH,
    Direction.WEST: Direction.EAST,
}


