
from dataclasses import dataclass
from typing import Tuple, List, FrozenSet

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
