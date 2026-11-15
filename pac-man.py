"""Pac-Man application entry point."""

import sys

import pygame

from shell.config import ConfigLoader
from shell.renderer import Renderer


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 pac-man.py config.json")
        return

    config = ConfigLoader.load_config(sys.argv[1])

    try:
        renderer = Renderer(config)
        renderer.run()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()