# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "toml-rs>=0.3.13",
# ]
# ///

import sys
from pathlib import Path

import toml_rs


def main(pyproject: Path) -> None:
    data = toml_rs.loads(pyproject.read_text(encoding="utf-8"))
    data["project"]["name"] += "-cuda"
    data["project"]["description"] += " with CUDA support"

    for override in data["tool"]["scikit-build"]["overrides"]:
        if override["if"]["platform-system"] in ["win32", "linux"]:
            override["cmake"]["define"]["ENABLE_CUDA"] = "ON"

    pyproject.write_text(toml_rs.dumps(data, pretty=False), encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
