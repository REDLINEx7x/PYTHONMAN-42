"""Pac-Man application entry point."""

import sys

import pygame
from engine.grid import Grid
from engine.gameengine import Engine
from shell.config import ConfigLoader
from shell.renderer import Renderer
from engine.errors import EngineError, GridError, MazeAdapterError


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 pac-man.py config.json")
        return

    config = ConfigLoader.load_config(sys.argv[1])

    try:
        engine = Engine(config)
    except EngineError as e:
        print(f"Error: {e}")

    try:
        renderer = Renderer(config)
        renderer.run()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
    finally:
        pygame.quit()

    


if __name__ == "__main__":
    main()
