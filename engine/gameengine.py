from enum import Enum
from engine.grid import Grid
from engine.creatures import Player, Ghost
from engine.bfs import path_finding

PLAYER_INTERVAL = 0.15
GHOST_INTERVAL = 0.2
class GameState(Enum):

    PLAYING = 1
    PAUESED = 2
    LEVEL_WON = 3
    GAME_WON = 4
    GAME_OVER = 5


class Engine:
    def __init__(self, config):
        self.config = config

        if self.config.lives < 1:
            raise ValueError("Cannot start game with 0 lives!")
        if len(self.config.levels) == 0:
            raise ValueError("Config must have at least one level!")

        self.score = 0
        self.level = 1
        self.lives = self.config.lives
        self.state = GameState.PLAYING
        self.grid = None
        self.pacu: Player = None
        self.ghosts = []
        self.pacgums = set()
        self.supergums = set()
        self.level_timer = 0.0
        self.eaten_timer = 0.0
        self.player_accumulator = 0.0
        self.ghost_accumulator = 0.0
        self.speed = False
        self.freeze = False
        self.invincible = False

        self._build_level()


    def _update(slef, dt):

        if self.state != GameState.PLAYING:
            return
        dt = min(dt, 0.2)
        if self.level_timer > 0:
            slef.level_timer -= dt
        if self.eaten_timer > 0:
            self.timer -= dt
        self.player_accumulator += dt
        self.ghost_accumulator += dt
        current_level_config = self.config.levels[self.level - 1]
        current_player_interval = PLAYER_INTERVAL
        current_ghost_interval = GHOST_INTERVAL
        while self.player_accumulator >= current_player_interval:
            self.player_accumulator -= current_player_interval




    def _move_player(self):

        if self.grid.can_move(self.pacu.position, self.pacu.wanted_direction):
            self.pacu.current_direction = self.pacu.wanted_direction
        if self.grid.can_move(self.pacu.position, self.pacu.current_direction):
            self.player.position = self.grid.neighbor(self.pacu.position, self.pacu.current_direction)
        else:
            self.pacu.current_direction = None
        if self.pacu.position in self.pacgums:
            self.pacgums.remove(self.pacu.position)
            self.score += 10
        if self.pacu.position in self.supergums:
            self.supergums.remove(self.pacu.position)
            self.score += 50
            self.edible_timer = 5.0
            for ghost in self.ghosts:
                if ghost.state != GhostState.EATEN:
                    ghost.change_state(GhostState.FRIGHTENED)
        for ghost in self.ghosts:
            if ghost.position == self.pacu.position:
                self._handle_collision(ghost)


    def _build_level(self):

        current_level_config = self.config.level[self.level - 1]
        self.grid = maze_bank()

        centre_cell = self.grid.get_centre()
        if len(grid.open_neighbors(centre_cell)) > 0:
            self.pacu.start_cell = centre_cell
        corners = self.grid.get_corners()
        self.ghosts = [Ghost(spawn_cell=corner, home_corner=corner) for corner in corners]

        all_cells = self.grid.get_all_cells()

        for cell in all_cells:
            if cell == self.pacu.start_cell:
                continue
            if cell in corners:
                self.supergums.add(cell)
            if len(grid.open_neighbors(centre_cell)) > 0:
                self.pacgums.add(cell)

        self.level_timer = self.config.level_timeout
        self.eaten_timer = 0.0
        self.player_accumulator = 0.0
        self.ghost_accumulator - 0.0

#Verify reachability of pacgums

