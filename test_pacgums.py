import sys
import unittest
from contextlib import nullcontext
from types import ModuleType
from unittest.mock import Mock, patch

# These unit tests supply their own grids. The optional maze generator must
# still be importable while the engine imports its adapter.
try:
    import mazegenerator
except ModuleNotFoundError as error:
    if error.name != "mazegenerator":
        raise
    mazegenerator = ModuleType("mazegenerator")
    mazegenerator.MazeGenerator = Mock(
        side_effect=AssertionError("Tests must supply a deterministic grid")
    )
    maze_import = patch.dict(sys.modules, {"mazegenerator": mazegenerator})
else:
    maze_import = nullcontext()

from engine.creatures import Ghost, GhostState
with maze_import:
    from engine.gameengine import (
        Engine,
        GameState,
        EDIBLE_DURATION,
        PLAYER_INTERVAL,
        GHOST_INTERVAL,
        GHOST_EDIBLE_INTERVAL,
        MAX_DT,
    )
from engine.grid import Grid
from engine.models import Cell, Direction
from shell.config import Config, LevelConfig


START = Cell(2, 2)
TARGET = Cell(2, 3)
SPARE = Cell(4, 4)


class PacgumTests(unittest.TestCase):
    def make_engine(self, grid=None, levels=1):
        if grid is None:
            grid = Grid(5, 5, [[0] * 5 for _ in range(5)])

        config = Config(
            levels=[
                LevelConfig(grid.get_width(), grid.get_height())
                for _ in range(levels)
            ]
        )
        with patch("engine.gameengine._generate_grid", return_value=grid):
            return Engine(config)

    def arena(self, kind="pacgums", levels=1):
        engine = self.make_engine(levels=levels)
        engine.ghosts = []
        engine.pacgums = {SPARE}
        engine.supergums = set()
        getattr(engine, kind).add(TARGET)
        engine.set_direction(Direction.EAST)
        return engine

    def ghost(self, engine, position=Cell(0, 0),
              state=GhostState.CHASE):
        ghost = Ghost(position, Cell(0, 0))
        ghost.change_state(state)
        engine.ghosts.append(ghost)
        return ghost

    def test_initial_placement(self):
        engine = self.make_engine()
        cells = {
            Cell(row, col)
            for row in range(5)
            for col in range(5)
        }
        corners = set(engine.grid.get_corners())

        self.assertEqual(engine.supergums, corners)
        self.assertEqual(engine.pacgums, cells - corners - {START})
        self.assertTrue(engine.pacgums.isdisjoint(engine.supergums))
        self.assertNotIn(START, engine.pacgums | engine.supergums)
        self.assertEqual(engine.score, 0)
        self.assertEqual(engine.edible_timer, 0)

    def test_unreachable_cells_receive_no_gums(self):
        # Only the center and its eastern neighbor are connected.
        grid = Grid(3, 3, [
            [15, 15, 15],
            [15, 13, 7],
            [15, 15, 15],
        ])
        engine = self.make_engine(grid)

        self.assertEqual(engine.pacu.position, Cell(1, 1))
        self.assertEqual(engine.pacgums, {Cell(1, 2)})
        self.assertEqual(engine.supergums, set())

    def test_narrow_grid_deduplicates_corners_and_excludes_spawn(self):
        for width, height in ((1, 2), (2, 1), (1, 3), (3, 1)):
            with self.subTest(width=width, height=height):
                grid = Grid(
                    width, height,
                    [[0] * width for _ in range(height)],
                )
                engine = self.make_engine(grid)
                corners = set(grid.get_corners())
                spawn = engine.pacu.start_cell
                cells = set(grid.get_all_cells())

                self.assertEqual(engine.supergums, corners - {spawn})
                self.assertEqual(engine.pacgums, cells - corners - {spawn})
                self.assertNotIn(spawn, engine.supergums)

    def test_collection_scores_configured_points_once(self):
        for kind, field in (
            ("pacgums", "points_per_pacgum"),
            ("supergums", "points_per_super_pacgum"),
        ):
            for points in (0, 1, 37, 10**9):
                with self.subTest(kind=kind, points=points):
                    engine = self.arena(kind)
                    setattr(engine.config, field, points)
                    engine.score = 123
                    engine.dt_update(PLAYER_INTERVAL)

                    self.assertEqual(engine.pacu.position, TARGET)
                    self.assertNotIn(TARGET, getattr(engine, kind))
                    self.assertEqual(engine.score, 123 + points)

                    # Leave and revisit the consumed cell.
                    engine.set_direction(Direction.WEST)
                    engine.dt_update(PLAYER_INTERVAL)
                    engine.set_direction(Direction.EAST)
                    engine.dt_update(PLAYER_INTERVAL)

                    self.assertEqual(engine.score, 123 + points)
                    self.assertEqual(engine.pacgums, {SPARE})
                    self.assertEqual(engine.supergums, set())

    def test_empty_cell_does_not_score_or_start_power(self):
        engine = self.arena()
        engine.pacgums = {SPARE}
        engine.dt_update(PLAYER_INTERVAL)

        self.assertEqual(engine.score, 0)
        self.assertEqual(engine.edible_timer, 0)

    def test_blocked_move_does_not_collect_remote_gum(self):
        engine = self.arena()
        engine.grid = Grid(5, 5, [[15] * 5 for _ in range(5)])
        engine.dt_update(PLAYER_INTERVAL)

        self.assertEqual(engine.pacu.position, START)
        self.assertIn(TARGET, engine.pacgums)
        self.assertEqual(engine.score, 0)

    def test_stationary_player_collects_current_cell_only_once(self):
        for kind in ("pacgums", "supergums"):
            with self.subTest(kind=kind):
                engine = self.arena(kind)
                getattr(engine, kind).remove(TARGET)
                getattr(engine, kind).add(START)
                engine.pacu.wanted_direction = None

                engine.dt_update(PLAYER_INTERVAL)
                score = engine.score
                engine.dt_update(PLAYER_INTERVAL)

                self.assertNotIn(START, getattr(engine, kind))
                self.assertEqual(engine.score, score)

    def test_overlapping_sets_collect_both_once(self):
        # Defensive case: generated levels normally keep these disjoint.
        engine = self.arena()
        engine.supergums.add(TARGET)
        engine.dt_update(PLAYER_INTERVAL)

        self.assertNotIn(TARGET, engine.pacgums | engine.supergums)
        self.assertEqual(
            engine.score,
            engine.config.points_per_pacgum
            + engine.config.points_per_super_pacgum,
        )
        self.assertEqual(engine.edible_timer, EDIBLE_DURATION)

    def test_supergum_frightens_active_ghosts_but_preserves_eaten(self):
        engine = self.arena("supergums")
        ghosts = [
            self.ghost(engine, state=state)
            for state in GhostState
        ]
        eaten = ghosts[2]
        eaten.respawn_timer = 2.0

        engine.dt_update(PLAYER_INTERVAL)

        self.assertEqual(ghosts[0].state, GhostState.FRIGHTENED)
        self.assertEqual(ghosts[1].state, GhostState.FRIGHTENED)
        self.assertEqual(eaten.state, GhostState.EATEN)
        self.assertAlmostEqual(eaten.respawn_timer, 2 - PLAYER_INTERVAL)
        self.assertEqual(engine.edible_timer, EDIBLE_DURATION)

    def test_second_supergum_refreshes_duration_instead_of_stacking(self):
        engine = self.arena("supergums")
        second = Cell(2, 4)
        engine.supergums.add(second)

        engine.dt_update(PLAYER_INTERVAL)
        engine.edible_timer = 0.01
        engine.dt_update(PLAYER_INTERVAL)

        self.assertEqual(engine.edible_timer, EDIBLE_DURATION)
        self.assertEqual(
            engine.score, 2 * engine.config.points_per_super_pacgum
        )

    def test_normal_gum_does_not_refresh_power(self):
        engine = self.arena()
        engine.edible_timer = 2.0
        ghost = self.ghost(engine, state=GhostState.FRIGHTENED)

        engine.dt_update(PLAYER_INTERVAL)

        self.assertAlmostEqual(engine.edible_timer, 2 - PLAYER_INTERVAL)
        self.assertEqual(ghost.state, GhostState.FRIGHTENED)

    def test_timer_expiration_and_clamping(self):
        for remaining, dt in ((0.1, 0.1), (0.05, 0.1)):
            with self.subTest(remaining=remaining, dt=dt):
                engine = self.arena()
                engine.edible_timer = remaining
                ghost = self.ghost(engine, state=GhostState.FRIGHTENED)
                eaten = self.ghost(engine, state=GhostState.EATEN)
                eaten.respawn_timer = 3

                engine.dt_update(dt)

                self.assertEqual(engine.edible_timer, 0)
                self.assertEqual(ghost.state, GhostState.CHASE)
                self.assertEqual(eaten.state, GhostState.EATEN)

    def test_large_dt_is_capped(self):
        engine = self.arena()
        engine.edible_timer = 2
        engine.dt_update(100)

        self.assertAlmostEqual(engine.edible_timer, 2 - MAX_DT)
        self.assertEqual(engine.pacu.position, TARGET)
        self.assertEqual(engine.score, engine.config.points_per_pacgum)

    def test_nonpositive_dt_and_inactive_states_do_nothing(self):
        cases = [(GameState.PLAYING, 0), (GameState.PLAYING, -1)]
        cases += [
            (state, 0.2)
            for state in GameState
            if state != GameState.PLAYING
        ]
        for state, dt in cases:
            with self.subTest(state=state, dt=dt):
                engine = self.arena("supergums")
                engine.state = state
                engine.edible_timer = 2
                before = engine.get_snapshot()

                engine.dt_update(dt)

                self.assertEqual(engine.get_snapshot(), before)
                self.assertEqual(engine.edible_timer, 2)

    def test_pause_and_resume_preserve_collection(self):
        engine = self.arena("supergums")
        engine.pause_game()
        engine.dt_update(PLAYER_INTERVAL)
        self.assertIn(TARGET, engine.supergums)

        engine.resume_game()
        engine.dt_update(PLAYER_INTERVAL)
        self.assertNotIn(TARGET, engine.supergums)
        self.assertEqual(engine.edible_timer, EDIBLE_DURATION)

    def test_supergum_is_applied_before_collision(self):
        engine = self.arena("supergums")
        ghost = self.ghost(engine, TARGET)
        engine.dt_update(PLAYER_INTERVAL)

        self.assertEqual(engine.lives, 3)
        self.assertEqual(ghost.state, GhostState.EATEN)
        self.assertEqual(
            engine.score,
            engine.config.points_per_super_pacgum
            + engine.config.points_per_ghost,
        )

    def test_multiple_ghosts_award_points_once_each(self):
        engine = self.arena("supergums")
        ghosts = [self.ghost(engine, TARGET) for _ in range(3)]
        engine.dt_update(PLAYER_INTERVAL)

        expected = (
            engine.config.points_per_super_pacgum
            + 3 * engine.config.points_per_ghost
        )
        self.assertEqual(engine.score, expected)
        self.assertTrue(all(g.state == GhostState.EATEN for g in ghosts))

        engine._handle_collisions()
        self.assertEqual(engine.score, expected)

    def test_normal_gum_scores_before_lethal_collision(self):
        engine = self.arena()
        self.ghost(engine, TARGET)
        engine.dt_update(PLAYER_INTERVAL)

        self.assertEqual(engine.lives, 2)
        self.assertEqual(engine.score, engine.config.points_per_pacgum)
        self.assertNotIn(TARGET, engine.pacgums)
        self.assertEqual(engine.pacu.position, START)

    def test_expired_power_does_not_allow_eating_ghost(self):
        # Regression expectation: power is inactive at timer == 0.
        # May fail with the current ordering inside dt_update().
        engine = self.arena()
        engine.edible_timer = PLAYER_INTERVAL
        self.ghost(engine, TARGET, GhostState.FRIGHTENED)

        engine.dt_update(PLAYER_INTERVAL)

        self.assertEqual(engine.lives, 2)
        self.assertEqual(engine.score, engine.config.points_per_pacgum)

    def test_ghost_movement_uses_power_interval(self):
        for timer, interval in (
            (0, GHOST_INTERVAL),
            (2, GHOST_EDIBLE_INTERVAL),
        ):
            with self.subTest(timer=timer):
                engine = self.arena()
                engine.pacu.wanted_direction = None
                engine.edible_timer = timer
                engine.ghost_accumulator = interval - 0.02

                with patch.object(engine, "_move_ghosts") as move:
                    engine.dt_update(0.01)
                    move.assert_not_called()
                    engine.dt_update(0.011)
                    move.assert_called_once()

    def test_freeze_does_not_prevent_supergum_collection(self):
        engine = self.arena("supergums")
        ghost = self.ghost(engine)
        engine.freeze = True

        with patch.object(engine, "_move_ghosts") as move:
            engine.dt_update(PLAYER_INTERVAL)
            move.assert_not_called()

        self.assertEqual(ghost.state, GhostState.FRIGHTENED)
        self.assertEqual(engine.edible_timer, EDIBLE_DURATION)

    def test_speed_collects_each_cell_crossed(self):
        engine = self.arena()
        engine.pacgums.add(Cell(2, 4))
        engine.speed = True
        engine.dt_update(PLAYER_INTERVAL)

        self.assertEqual(engine.pacu.position, Cell(2, 4))
        self.assertEqual(engine.score, 2 * engine.config.points_per_pacgum)
        self.assertEqual(engine.pacgums, {SPARE})

    def test_either_remaining_gum_type_prevents_win(self):
        for kind in ("pacgums", "supergums"):
            with self.subTest(kind=kind):
                engine = self.arena()
                engine.pacgums = set()
                engine.supergums = set()
                getattr(engine, kind).add(SPARE)

                self.assertFalse(engine._check_win())
                self.assertEqual(engine.state, GameState.PLAYING)

    def test_last_gum_completes_level_or_game(self):
        for levels, expected in (
            (1, GameState.GAME_WON),
            (2, GameState.LEVEL_WON),
        ):
            for kind in ("pacgums", "supergums"):
                with self.subTest(levels=levels, kind=kind):
                    engine = self.arena(kind, levels=levels)
                    engine.pacgums.discard(SPARE)
                    engine.dt_update(PLAYER_INTERVAL)

                    self.assertEqual(engine.state, expected)
                    self.assertFalse(engine.pacgums | engine.supergums)

    def test_last_gum_win_takes_priority_over_collision_and_timeout(self):
        # Documents the current engine's explicit win-first behavior.
        for kind in ("pacgums", "supergums"):
            with self.subTest(kind=kind):
                engine = self.arena(kind)
                engine.pacgums.discard(SPARE)
                engine.level_timer = PLAYER_INTERVAL
                self.ghost(engine, TARGET)
                engine.dt_update(PLAYER_INTERVAL)

                field = (
                    "points_per_pacgum" if kind == "pacgums"
                    else "points_per_super_pacgum"
                )
                self.assertEqual(engine.state, GameState.GAME_WON)
                self.assertEqual(engine.lives, 3)
                self.assertEqual(engine.score, getattr(engine.config, field))

    def test_empty_board_wins_on_update(self):
        engine = self.arena()
        engine.pacgums.clear()
        engine.supergums.clear()
        engine.dt_update(0.01)
        self.assertEqual(engine.state, GameState.GAME_WON)

    def test_life_loss_preserves_consumed_gums_and_score(self):
        engine = self.arena("supergums")
        engine.dt_update(PLAYER_INTERVAL)
        before = engine.get_snapshot()

        engine._lose_life()

        self.assertEqual(engine.score, before.score)
        self.assertEqual(engine.pacgums, set(before.pacgums))
        self.assertEqual(engine.supergums, set(before.supergums))
        self.assertEqual(engine.edible_timer, 0)
        self.assertEqual(engine.lives, before.lives - 1)

    def test_next_level_repopulates_gums_and_resets_power(self):
        engine = self.arena("supergums", levels=2)
        engine.pacgums.clear()
        engine.dt_update(PLAYER_INTERVAL)
        score = engine.score
        fresh = self.make_engine(levels=2)

        with patch(
            "engine.gameengine._generate_grid", return_value=fresh.grid
        ):
            engine.continue_game()

        self.assertEqual(engine.level, 2)
        self.assertEqual(engine.state, GameState.PLAYING)
        self.assertEqual(engine.score, score)
        self.assertEqual(engine.lives, 3)
        self.assertEqual(engine.edible_timer, 0)
        self.assertEqual(engine.pacgums, fresh.pacgums)
        self.assertEqual(engine.supergums, fresh.supergums)
        self.assertTrue(
            all(g.state == GhostState.CHASE for g in engine.ghosts)
        )

    def test_snapshot_gums_are_immutable_independent_copies(self):
        for kind in ("pacgums", "supergums"):
            with self.subTest(kind=kind):
                engine = self.arena(kind)
                before = engine.get_snapshot()
                frozen = getattr(before, kind)

                self.assertIsInstance(frozen, frozenset)
                with self.assertRaises(AttributeError):
                    frozen.remove(TARGET)

                engine.dt_update(PLAYER_INTERVAL)

                self.assertIn(TARGET, frozen)
                self.assertNotIn(
                    TARGET, getattr(engine.get_snapshot(), kind)
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
