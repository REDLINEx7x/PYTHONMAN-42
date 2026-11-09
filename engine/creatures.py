import random
from enum import Enum
from engine.types import Cell, Direction
from engine.grid import Grid
from engine.types import Cell, Direction
from engine.bfs import path_finding

class Player:
    def __init__(self, start_cell):

        self.start_cell = start_cell
        self.position = self.start_cell
        self.current_direction = Direction.EAST
        self.wanted_direction = Direction.EAST
        self.lives = 3

    def set_next_direction(self, direction):

        self. wanted_direction = self.direction

    def update_position(self, grid):

        if grid.can_move(self.position, self.wanted_direction):
            self.current_direction = self.wanted_direction
            self.position = grid.neighbor(self.position, self.current_direction)
        elif grid.can_move(self.position, self.current_direction):
            self.position = grid.neighbor(self.position, self.current_direction)

    def lost_life(self):
        self.lives -= 1
        self.position  = grid.start_cell
        self.Direction = Direction.EAST
        self.wanted_direction = Direction.EAST

    def is_dead(self):
        return self.lives <= 0

class GhostState(Enum):

    SCATTER = 1
    CHASE = 2
    FRIGHTENED = 3
    EATEN = 4

class Ghost:
    def __init__(self, spawn_cell, home_corner):

        self.spawn_cell = spawn_cell
        self.home_corner = home_corner
        self.position = spawn_cell
        self.state = GhostState.SCATTER
        self.current_direction = Direction.NORTH

    def get_target_cell(self, player_position):

        if self.state == GhostState.SCATTER:
            return self.home_corner
        elif self.state == GhostState.CHASE:
            return player_position
        elif self.state == GhostState.EATEN:
            return self.spawn_cell
        elif self.state == GhostState.FRIGHTENED:
            return None


    def update_position(self, grid, player_position):

        dest = self.get_target_cell(player_position)

        if dest is None:
            moves = grid.open_neighbors(self.position)
            banned_direction = self.current_direction.opposite

            if len(moves) > 1:
                valid_moves = [m for m in moves if [0] != banned_direction]
            else:
                valid_moves = moves

            chosen_direction, new_cell = random.choice(valid_moves)
            self.current_direction = chosen_direction
            self.position = new_cell

        else:
            path = path_finding(grid, self.position, dest)
            if path:
                self.current_direction = path[0]
                self.position = grid.neighbor(self.position, self.current_direction)

        if self.state == GhostState.EATEN and self.position == self.spawn_cell:
            self.state = GhostState.SCATTER

    def change_state(self, new_state):

        if self.state == GhostState.EATEN:
            return
        else:
            self.state = new_state


    def ghost_die(self):

        self.state = GhostState.EATEN

    def check_respawn(self):

        if self.state == GhostState.EATEN and self.position == self.spawn_cell:
            self.state = GhostState.SCATTER
            return True
        return False

