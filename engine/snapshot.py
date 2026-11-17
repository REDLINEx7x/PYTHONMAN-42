
from dataclasses import dataclass
from typing import Tuple, List, FrozenSet
from engine.models import Cell, Direction, GameState
from engine.creatures import GhostState

@dataclass(frozen=True)
class GameSnapshot:
    state: GameState
    score: int
    lives: int
    level: int
    pacu_position: Tuple[int, int]
    pacu_direction: Direction
    ghosts: List[Tuple[Tuple[int, int], GhostState]]
    pacgums: FrozenSet[Tuple[int, int]]
    supergums: FrozenSet[Tuple[int, int]]
