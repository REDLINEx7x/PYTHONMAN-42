from collections import deque
from engine.types import Cell, Direction
from engine.grid import Grid

def path_finding(grid, start, target):

    if start == target:
        return []
    queue: deque[tuple[Cell, list[Direction]]] = deque()
    queue.append((start, []))
    visited: set[Cell] = {start}

    while queue:

        current_cell, path = queue.popleft()
        if current_cell == target:
            return path

        neighbors = grid.open_neighbors(current_cell)
        for dr, c in neighbors:
            if c in visited:
                continue
            visited.add(c)
            newpath = path + [dr]
            queue.append((c, newpath))
    return []
