import random
from enum import Enum
from typing import NamedTuple
from engine.models import Cell, GameState
from engine.creatures import Player, Ghost, GhostState
from engine.snapshot import GameSnapshot
from engine.grid import Grid
from engine.adapter import _generate_grid


MAX_DT = 0.2
PLAYER_INTERVAL = 0.15
GHOST_INTERVAL = 0.2
GHOST_EDIBLE_INTERVAL = 0.3
SPEED_FACTOR = 0.5
EDIBLE_DURATION = 5.0
POINTS_PACGUM = 10
POINTS_SUPERGUM = 50
POINTS_GHOST = 200


class GameState(Enum):

    PLAYING = 1
    PAUSED = 2
    LEVEL_WON = 3
    GAME_WON = 4
    GAME_OVER = 5

class LevelData(NamedTuple):

    grid: Grid
    player: Player
    ghosts: list[Ghost]
    pacgums: set[Cell]
    supergums: set[Cell]

class Engine:
    def __init__(self, config,) -> None:
        self.config = config

        if self.config.lives < 1:
            raise ValueError("Cannot start game with 0 lives!")
        if len(self.config.levels) == 0:
            raise ValueError("Config must have at least one level!")

        self._rng = random.Random()
        self.score: int = 0
        self.level: int = 1
        self.lives: int = config.lives
        self.state = GameState.PLAYING

        data = self._build_level(self.level)
        self.grid: Grid = data.grid
        self.pacu: Player = data.player
        self.ghosts: list[Ghost] = data.ghosts
        self.pacgums: set[Cell] = data.pacgums
        self.supergums: set[Cell] = data.supergums

        self.level_timer: float = config.level_timeout
        self.edible_timer: float = 0.0
        self.player_accumulator: float = 0.0
        self.ghost_accumulator: float = 0.0
        self.speed: bool = False
        self.freeze: bool = False
        self.invincible: bool = False


    def _build_level(self, level: int) -> LevelData:

        level_config = self.config.levels[level - 1]
        if level == 1:
            seed = self.config.seed
        else:
            seed = self._rng.randrange(2**32)
        grid = _generate_grid(level_config.width, level_config.height, seed)
        player = Player(grid.get_center())
        corners = grid.get_corners()
        ghosts = [Ghost(spawn_cell=c, home_corner=c) for c in corners]

        pacgums: set[Cell] = set()
        supergums: set[Cell] = set()
        for cell in grid.get_all_cells():
            if cell == player.start_cell:
                continue
            if cell in corners:
                supergums.add(cell)
            elif len(grid.open_neighbors(cell)) > 0:
                pacgums.add(cell)

        return LevelData(grid, player, ghosts, pacgums, supergums)

    def _load_level(self, level: int) -> None:

        data = self._build_level(level)
        self.level = level
        self.grid = data.grid
        self.pacu = data.player
        self.ghosts = data.ghosts
        self.pacgums = data.pacgums
        self.supergums = data.supergums
        self.level_timer = self.config.level_timeout
        self.edible_timer = 0.0
        self.player_accumulator = 0.0
        self.ghost_accumulator = 0.0
        self.state = GameState.PLAYING


    def dt_update(self, dt):

        if dt <= 0:
            return
        if self.state != GameState.PLAYING:
            return
        dt = min(dt, MAX_DT)
        self.level_timer = max(0.0, self.level_timer - dt)
        self.edible_timer = max(0.0, self.edible_timer - dt)
        for ghost in self.ghosts:
            ghost.tick_respawn(dt)
        self.player_accumulator += dt
        self.ghost_accumulator += dt
        player_interval = PLAYER_INTERVAL
        if self.speed:
            player_interval *= SPEED_FACTOR
        ghost_interval = GHOST_INTERVAL
        if self.edible_timer > 0:
            ghost_interval = GHOST_EDIBLE_INTERVAL

        while (self.state == GameState.PLAYING
            and self.player_accumulator >= player_interval):
            self.player_accumulator -= player_interval
            self._move_player()
        if self.state != GameState.PLAYING:
            return

        if self.freeze:
            self.ghost_accumulator = 0.0
        while (self.state == GameState.PLAYING
            and self.ghost_accumulator >= ghost_interval):
            self.ghost_accumulator -= ghost_interval
            self._move_ghosts()
        if self.state != GameState.PLAYING:
            return

        if self.edible_timer <= 0:
            for ghost in self.ghosts:
                if ghost.state == GhostState.FRIGHTENED:
                    ghost.change_state(GhostState.CHASE)

        if self._check_win():
            return
        if self.level_timer <= 0:
            self._lose_life()


    def _move_player(self):

        self.pacu.update_position(self.grid)
        if self.pacu.position in self.pacgums:
            self.pacgums.remove(self.pacu.position)
            self.score += POINTS_PACGUM
        if self.pacu.position in self.supergums:
            self.supergums.remove(self.pacu.position)
            self.score += POINTS_SUPERGUM
            self.edible_timer = EDIBLE_DURATION
            for ghost in self.ghosts:
                if ghost.state != GhostState.EATEN:
                    ghost.change_state(GhostState.FRIGHTENED)
        #for ghost in self.ghosts:
        #    if ghost.position == self.pacu.position:
        if self._check_win():
            return
        self._handle_collisions()


    def _move_ghosts(self) -> None:
        for ghost in self.ghosts:
            ghost.update_position(self.grid, self.pacu.position)
            if self._handle_collisions():
                return


    def _handle_collisions(self) -> bool:

        here = [g for g in self.ghosts if g.position == self.pacu.position]
        for ghost in here:
            if ghost.state == GhostState.FRIGHTENED:
                ghost.ghost_die()
                self.score += POINTS_GHOST
        if self.invincible:
            return False
        for ghost in here:
            if ghost.state == GhostState.CHASE:
                self._lose_life()
                return True
        return False


    def _lose_life(self) -> None:
        self.lives -= 1
        if self.lives <= 0:
            self.state = GameState.GAME_OVER
            return
        self.pacu.reset()
        for ghost in self.ghosts:
            ghost.reset()
        self.edible_timer = 0.0
        self.level_timer = self.config.level_timeout
        self.player_accumulator = 0.0
        self.ghost_accumulator = 0.0


    def _check_win(self) -> bool:
        if self.pacgums or self.supergums:
            return False
        if self.level == len(self.config.levels):
            self.state = GameState.GAME_WON
        else:
            self.state = GameState.LEVEL_WON
        return True


    def continue_game(self) -> None:
        if self.state == GameState.LEVEL_WON:
            self._load_level(self.level + 1)


    def get_snapshot(self):

        ghosts_data = [(g.position, g.state) for g in self.ghosts]
        return GameSnapshot(state=self.state,
                            score=self.score,
                            lives=self.lives,
                            level=self.level,
                            pacu_position=self.pacu.position,
                            pacu_direction=self.pacu.current_direction,
                            ghosts=ghosts_data,
                            pacgums=frozenset(self.pacgums),
                            supergums=frozenset(self.supergums))

    def set_direction(self, direction):
        if self.pacu and self.state == GameState.PLAYING:
            self.pacu.wanted_direction = direction

    def toggle_invincible(self):
        self.invincible = not self.invincible

    def toggle_freeze(self):
        self.freeze = not self.freeze

    def toggle_speed(self):
        self.speed = not self.speed

    def pause_game(self):
        if self.state == GameState.PLAYING:
            self.state = GameState.PAUSED

    def resume_game(self):
        if self.state == GameState.PAUSED:
            self.state = GameState.PLAYING
