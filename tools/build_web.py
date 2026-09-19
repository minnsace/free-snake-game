"""Build a clean pygbag package without including local development files."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
STAGE = Path(tempfile.gettempdir()) / "free-snake-game"
OUTPUT = ROOT / "build" / "web"


def main() -> None:
    shutil.rmtree(STAGE, ignore_errors=True)
    shutil.rmtree(OUTPUT, ignore_errors=True)
    STAGE.mkdir(parents=True)

    shutil.copy2(ROOT / "main.py", STAGE / "main.py")
    shutil.copy2(ROOT / "pygbag.ini", STAGE / "pygbag.ini")
    shutil.copytree(ROOT / "game", STAGE / "game", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    subprocess.run(
        [
            sys.executable,
            "-m",
            "pygbag",
            "--build",
            "--ume_block",
            "0",
            "--title",
            "Free Snake Game",
            str(STAGE),
        ],
        check=True,
    )

    generated = STAGE / "build" / "web"
    if not (generated / "index.html").is_file():
        raise RuntimeError("pygbag did not produce index.html")

    shutil.copytree(generated, OUTPUT)
    shutil.copy2(ROOT / "CNAME", OUTPUT / "CNAME")
    (OUTPUT / ".nojekyll").touch()
    shutil.rmtree(STAGE, ignore_errors=True)
    print(f"Web build ready at {OUTPUT}")


if __name__ == "__main__":
    main()
