"""Persistent highscore management for Pac-Man."""
import json


class HighscoreManager:
    """Manage player highscores."""

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.scores: list[dict[str, str | int]] = []

    def sort_score(self, name: str, score: int) -> None:
        self.scores.append({
            "name": name,
            "score": score
        })

        self.scores.sort(
            key=lambda entry: entry["score"],
            reverse=True
        )

        self.scores = self.scores[:10]

    def add(self, name: str, score: int) -> None:
        if (
            not isinstance(name, str)
            or len(name) > 10
            or not name.replace(" ", "").isalnum()
        ):
            raise ValueError(
                "Name must contain at most 10 \
alphanumeric characters or spaces"
            )

        if type(score) is not int or score < 0:
            raise ValueError("Score must be a non-negative integer")

        self.sort_score(name, score)

    def load(self) -> None:
        """Load highscores from the file."""
        self.scores = []
        try:
            with open(self.filename, "r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, list):
                print("Warning: Invalid highscore format. Expected a list.")
                return

            for entry in data:
                if not isinstance(entry, dict):
                    print("Warning: Invalid entry. Skipping.")
                    continue
                try:
                    self.add(entry["name"], entry["score"])
                except (ValueError, KeyError):
                    print("Warning: Invalid highscore entry. Skipping.")

        except (OSError, json.JSONDecodeError, UnicodeError) as error:
            print(f"Warning: Cannot load highscores: {error}")

    def save(self) -> None:
        """Save highscores to the file."""
        try:
            with open(self.filename, "w", encoding="utf-8") as file:
                json.dump(self.scores, file, indent=4)
        except OSError as error:
            print(f"Warning: Cannot save highscores: {error}")


if __name__ == "__main__":
    manager = HighscoreManager("highscores.json")

    manager.add("Hicham", 100)
    manager.add("Ghost", 2000)
    manager.save()

    new_manager = HighscoreManager("highscores.json")
    new_manager.load()

    print(new_manager.scores)
