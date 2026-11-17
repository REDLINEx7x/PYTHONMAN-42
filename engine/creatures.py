import random
from enum import Enum
from engine.models import Cell, Direction
from engine.grid import Grid
from engine.models import Cell, Direction
from engine.bfs import path_finding

RESPAWN_DELAY = 5.0

class Player:
    def __init__(self, start_cell):

        self.start_cell: Cell = start_cell
        self.position: Cell = start_cell
        self.current_direction: Direction | None = None
        self.wanted_direction: Direction | None = None

    def set_next_direction(self, direction):
        if direction is None:
            return
        self. wanted_direction = direction

    def update_position(self, grid):
        wanted = self.wanted_direction
        if wanted is not None and grid.can_move(self.position, wanted):
            self.current_direction = wanted
        current = self.current_direction
        if current is None:
            return
        if grid.can_move(self.position, current):
            self.position = grid.neighbor(self.position, current)
        else:
            self.current_direction = None

    def reset(self):
        self.position  = self.start_cell
        self.current_direction = None
        self.wanted_direction = None


class GhostState(Enum):

    CHASE = 1
    FRIGHTENED = 2
    EATEN = 3


class Ghost:
    def __init__(self, spawn_cell, home_corner):

        self.spawn_cell = spawn_cell
        self.home_corner = home_corner
        self.position = spawn_cell
        self.state = GhostState.CHASE
        self.current_direction = Direction.NORTH
        self.respawn_timer: float = 0.0

    def get_target_cell(self, player_position):

        if self.state == GhostState.CHASE:
            return player_position


    def update_position(self, grid, player_position):

        if self.state == GhostState.EATEN:
            return
        dest = self.get_target_cell(player_position)

        if dest is None:
            self._wander(grid)

        else:
            path = path_finding(grid, self.position, dest)
            if path:
                self.current_direction = path[0]
                self.position = grid.neighbor(self.position, self.current_direction)

    def _wander(self, grid: Grid) -> None:
        """Take one random step, avoiding a U-turn when possible.

        Stays put if the ghost has nowhere to go.
        """
        moves = grid.open_neighbors(self.position)
        if not moves:
            return

        banned = self.current_direction.opposite
        valid_moves = [m for m in moves if m[0] != banned]
        if not valid_moves:
            valid_moves = moves

        chosen_direction, new_cell = random.choice(valid_moves)
        self.current_direction = chosen_direction
        self.position = new_cell

    def change_state(self, new_state):

        self.state = new_state


    def ghost_die(self) -> None:
        self.change_state(GhostState.EATEN)
        self.position = self.home_corner
        self.respawn_timer = RESPAWN_DELAY


    def tick_respawn(self, dt: float) -> None:
        """Advance the respawn countdown by dt seconds.

        Does nothing unless the ghost is eaten. When the countdown
        reaches zero the ghost returns home as a normal ghost.

        Args:
            dt: Seconds elapsed, as given by the engine.
        """
        if self.state != GhostState.EATEN:
            return
        self.respawn_timer = max(0.0, self.respawn_timer - dt)
        if self.respawn_timer == 0.0:
            self.position = self.home_corner
            self.change_state(GhostState.CHASE)


    def reset(self) -> None:
        self.position = self.home_corner
        self.respawn_timer = 0.0
        self.change_state(GhostState.CHASE)

