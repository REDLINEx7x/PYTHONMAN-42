class EngineError(Exception):
    """Base exception for all errors raised by the Pacu game engine."""


class GridError(EngineError):
    """Raised when grid dimensions, wall values, or symmetry are invalid."""


class MazeAdapterError(EngineError):
    """Raised when maze generation or raw table validation fails."""
