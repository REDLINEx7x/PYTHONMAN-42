from enum import Enum
from engine.grid import Grid
from engine.creatures import Player, Ghost
from engine.bfs import path_finding


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
        self.pacu = None
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


    #def _update(slef, dt):


    #    if self.state == GameState.PAUESED or self.state == GameState.GAME_WON or self.state == GameState.LEVEL_WON or self.state ==GameState.GAME_OVER:
    #        return
    #    if self.level_timer > 0:
    #        slef.level_timer -= dt
    #    if self.eaten_timer > 0:
    #        self.timer -= dt
    #    self.player_accumulator += dt
    #    self.ghost_accumulator += dt
    #    current_level_config = self.config.levels[self.level - 1]
    #    player_interval = current_level_config.player_speed
    #    ghost_interval = current_level_config.ghost_speed

