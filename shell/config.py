
"""Configuration models and robust JSON loading for Pac-Man."""

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LevelConfig:
    """Dimensions of a game level."""

    width: int = 15
    height: int = 11


@dataclass
class Config:
    """Validated game settings with safe fallback values."""

    highscore_filename: str = "highscores.json"
    lives: int = 3
    points_per_pacgum: int = 10
    points_per_super_pacgum: int = 50
    points_per_ghost: int = 200
    pacgum: int = 42
    seed: int = 42
    level_max_time: int = 90
    levels: list[LevelConfig] = field(
        default_factory=lambda: [
            LevelConfig(15, 11),
            LevelConfig(15, 13),
            LevelConfig(17, 13),
            LevelConfig(17, 15),
            LevelConfig(19, 15),
            LevelConfig(19, 17),
            LevelConfig(21, 17),
            LevelConfig(21, 19),
            LevelConfig(23, 19),
            LevelConfig(25, 21),
        ]
    )


class ConfigLoader:
    """Read, validate, and normalize a Pac-Man configuration file."""

    @staticmethod
    def load(filename: str) -> dict[str, Any]:
        """Load a JSON object, ignoring full lines beginning with #."""
        try:
            with open(filename, "r", encoding="utf-8") as file:
                lines = [
                    line for line in file
                    if not line.lstrip().startswith("#")
                ]

            data: Any = json.loads("".join(lines))

            if not isinstance(data, dict):
                print("Warning: Config must be a JSON object. Using defaults.")
                return {}

            return data

        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            print(f"Warning: Cannot load {filename}: {error}. Using defaults.")
            return {}

    @staticmethod
    def parse(data: dict[str, Any]) -> Config:
        """Validate known settings and retain defaults for invalid values."""
        config = Config()

        numeric_fields = (
            ("lives", 1),
            ("points_per_pacgum", 0),
            ("points_per_super_pacgum", 0),
            ("points_per_ghost", 0),
            ("pacgum", 0),
            ("level_max_time", 1),
        )

        for name, minimum in numeric_fields:
            if name not in data:
                continue

            value = data[name]

            if type(value) is int and value >= minimum:
                setattr(config, name, value)
            else:
                print(f"Warning: Invalid {name}. Using default.")

        if "seed" in data:
            seed = data["seed"]

            if type(seed) is int:
                config.seed = seed
            else:
                print("Warning: Invalid seed. Using default.")

        if "highscore_filename" in data:
            filename = data["highscore_filename"]

            if isinstance(filename, str) and filename.strip():
                config.highscore_filename = filename
            else:
                print("Warning: Invalid highscore_filename. Using default.")

        if "level" in data:
            levels = data["level"]

            if not isinstance(levels, list) or not levels:
                print("Warning: Invalid level list. Using defaults.")
            else:
                valid_levels: list[LevelConfig] = []

                for index, level in enumerate(levels, start=1):
                    if not isinstance(level, dict):
                        print(
                            f"Warning: Invalid level {index}. Using default."
                        )
                        valid_levels.append(LevelConfig())
                        continue

                    width = level.get("width")
                    height = level.get("height")

                    if (
                        type(width) is not int
                        or type(height) is not int
                        or width <= 0
                        or height <= 0
                    ):
                        print(
                            f"Warning: Invalid dimensions for level {index}. "
                            "Using default."
                        )
                        valid_levels.append(LevelConfig())
                        continue

                    valid_levels.append(LevelConfig(width, height))

                config.levels = valid_levels

        return config

    @staticmethod
    def load_config(filename: str) -> Config:
        """Read a file and return validated settings."""
        return ConfigLoader.parse(ConfigLoader.load(filename))
