"""Build a clean pygbag package without including local development files."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
STAGE = Path(tempfile.gettempdir()) / "free-snake-game"
OUTPUT = ROOT / "build" / "web"


def customize_web_shell(generated: Path) -> None:
    index_path = generated / "index.html"
    html = index_path.read_text(encoding="utf-8")
    splash = (ROOT / "web" / "splash.html").read_text(encoding="utf-8").strip()

    if "</head>" not in html or "<body>" not in html:
        raise RuntimeError("pygbag template is missing expected head/body markers")

    html = html.replace(
        "</head>",
        '    <meta name="theme-color" content="#2e9e60">\n'
        '    <link rel="stylesheet" href="shell.css">\n</head>',
        1,
    )
    html = html.replace("<body>", f"<body>\n{splash}", 1)
    index_path.write_text(html, encoding="utf-8")
    shutil.copy2(ROOT / "web" / "shell.css", generated / "shell.css")


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

    customize_web_shell(generated)
    shutil.copytree(generated, OUTPUT)
    shutil.copy2(ROOT / "CNAME", OUTPUT / "CNAME")
    (OUTPUT / ".nojekyll").touch()
    shutil.rmtree(STAGE, ignore_errors=True)
    print(f"Web build ready at {OUTPUT}")


if __name__ == "__main__":
    main()
