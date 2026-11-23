"""Entry point: runs the pipeline end to end, filled in per milestone."""

from pathlib import Path

import yaml

CONFIG = Path(__file__).parent / "config.yaml"


def main() -> None:
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    print("chstorm pipeline: not implemented yet (M1 next). Config sections:", list(cfg))


if __name__ == "__main__":
    main()
