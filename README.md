



# PYTHONMAN-42
import math
from typing import Optional
from engine.types import Cell, Direction
from engine.ghost import GhostState

MAX_DT = 0.1  # Prevents lag spikes from causing tunneling


class Engine:
    # ... previous __init__ and _build_level methods ...

    def update(self, dt: float) -> None:
        """Advance the game engine by dt seconds."""
        # 1. Early return if game is not running
        if self.state != GameState.PLAYING:
            return

        # 2. Cap dt to prevent lag spikes from skipping collisions
        dt = min(dt, MAX_DT)

        # 3. Update global and state timers
        self.level_timer -= dt

        if self.edible_timer > 0:
            self.edible_timer -= dt
            if self.edible_timer <= 0:
                self.edible_timer = 0.0
                # Revert edible ghosts back to CHASE mode
                for ghost in self.ghosts:
                    if ghost.state == GhostState.FRIGHTENED:
                        ghost.change_state(GhostState.CHASE)

        # 4. Accumulate step times
        self.player_accumulator += dt
        self.ghost_accumulator += dt

        # Get level intervals from config
        level_cfg = self.config.levels[self.level - 1]
        player_interval = level_cfg.player_speed
        if self.speed:
            player_interval /= 2.0  # Speed cheat cuts interval in half

        ghost_interval = level_cfg.ghost_speed

        # 5. Move Player & Check Collisions (Check #1)
        while self.player_accumulator >= player_interval:
            self.player_accumulator -= player_interval
            self._move_player()
            self._resolve_eating()
            self._check_collisions()

            # Stop movement loops immediately if life lost or game ended
            if self.state != GameState.PLAYING:
                return

        # 6. Move Ghosts & Check Collisions (Check #2)
        if not self.freeze:
            while self.ghost_accumulator >= ghost_interval:
                self.ghost_accumulator -= ghost_interval
                for ghost in self.ghosts:
                    ghost.update_position(self.grid, self.pacman.position)

                self._check_collisions()

                if self.state != GameState.PLAYING:
                    return

        # 7. Check Timers & Win/Loss Conditions
        if self.level_timer <= 0:
            self.level_timer = 0.0
            self._handle_life_loss()
            return

        if len(self.pacgums) == 0 and len(self.supergums) == 0:
            if self.level >= len(self.config.levels):
                self.state = GameState.GAME_WON
            else:
                self.state = GameState.LEVEL_WON

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _move_player(self) -> None:
        """Try moving player in wanted direction, fallback to current direction."""
        # Check if requested direction is valid in grid
        if self.wanted_direction and self.grid.is_open(self.pacman.position, self.wanted_direction):
            self.pacman.current_direction = self.wanted_direction

        # Move in current direction if possible
        if self.grid.is_open(self.pacman.position, self.pacman.current_direction):
            self.pacman.position = self.grid.neighbor(
                self.pacman.position, self.pacman.current_direction
            )

    def _resolve_eating(self) -> None:
        """Handle pacgum and super-pacgum consumption."""
        pos = self.pacman.position

        if pos in self.pacgums:
            self.pacgums.remove(pos)
            self.score += 10

        elif pos in self.supergums:
            self.supergums.remove(pos)
            self.score += 50
            self.edible_timer = self.config.edible_duration
            for ghost in self.ghosts:
                ghost.change_state(GhostState.FRIGHTENED)

    def _check_collisions(self) -> None:
        """Resolve collisions between Pac-Man and any ghosts in the same cell."""
        for ghost in self.ghosts:
            if ghost.position == self.pacman.position:
                if ghost.state == GhostState.CHASE and not self.invincible:
                    self._handle_life_loss()
                    return  # Stop checking other ghosts on fatal hit
                elif ghost.state == GhostState.FRIGHTENED:
                    ghost.ghost_die()
                    self.score += 200

    def _handle_life_loss(self) -> None:
        """Deduct a life and reset entity positions or trigger game over."""
        if self.invincible:
            return

        self.lives -= 1
        if self.lives <= 0:
            self.state = GameState.GAME_OVER
            return

        # Reset entity positions back to spawn defaults
        self.pacman.position = self.spawn_cell
        self.pacman.current_direction = Direction.NORTH
        self.wanted_direction = None

        for ghost in self.ghosts:
            ghost.position = ghost.spawn_cell
            ghost.state = GhostState.SCATTER
            ghost.current_direction = Direction.NORTH

        # Reset accumulators
        self.player_accumulator = 0.0
        self.ghost_accumulator = 0.0
