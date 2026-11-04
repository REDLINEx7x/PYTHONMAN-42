from engine.types import Cell, Direction
from engine.grid import Grid
from enum import Enum
from engine.types import Cell, Direction

class Player:
    def __init__(self, start_cell):

        self.start_cell = start_cell
        self.position = self.start_cell
        self.current_direction = Direction.EAST
        self.next_direction = Direction.EAST
        self.lives = 3

    def set_next_direction(self, direction):

        self. next_direction = self.direction

    def update_position(self, grid):

        if grid.can_move(self.position, self.next_direction):
            self.current_direction = self.next_direction
            self.position = grid.neighbor(self.position, self.current_direction)
        elif grid.can_move(self.position, self.current_direction):
            self.position = grid.neighbor(self.position, self.current_direction)

    def lost_life(self):
        self.lives -= 1
        self.position  = grid.start_cell
        self.Direction = Direction.EAST
        self.next_direction = Direction.EAST

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

    def get_target_cell(self, player_position, ):

        if self.state == GhostState.SCATTER:
            return home_corner
        elif self.state == GhostState.CHASE:
            return player_position
        elif self.state == GhostState.EATEN:
            return self.spawn_cell
        elif self.state == GhostState.FRIGHTENED:
            return None


    #def update_position(self, grid, player_position):

    #    dest = self.get_target_cell(player_position)

    #    if dest == None:
    #        moves = grid.open_neighbors(self.position)
    #        for dr, c in moves:
    #            if current_direction == Direction.NORTH:


