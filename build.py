"""Build script. Produces wikipath.exe and wikipath-web.exe in dist/."""

import argparse
import subprocess
import sys


def run(args: list[str]) -> None:
    print(f"\n$ {' '.join(args)}\n")
    subprocess.run(args, check=True)


# Packages excluded to avoid conflicts and reduce output size.
_EXCLUDES: list[str] = [
    "PyQt5", "PySide2", "PySide6",
    "matplotlib", "numpy", "scipy", "pandas",
    "IPython", "ipykernel", "ipywidgets",
    "tkinter", "_tkinter",
    "zmq", "tornado",
    "PIL", "Pillow",
    "cv2", "sklearn", "tensorflow", "torch",
    "notebook", "jupyter", "nbformat",
    "sphinx", "docutils",
    "black", "pylint", "flake8", "mypy",
    "pytest",
]


def _exclude_flags() -> list[str]:
    flags: list[str] = []
    for mod in _EXCLUDES:
        flags += ["--exclude-module", mod]
    return flags


def build_cli(onefile: bool) -> None:
    print("=" * 50)
    print("Building CLI executable (wikipath.exe) ...")
    print("=" * 50)
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "wikipath",
        "--collect-all", "httpx",
        "--collect-all", "anyio",
        "--hidden-import", "click",
        "--hidden-import", "wiki_path.api_client",
        "--hidden-import", "wiki_path.bfs",
        "--hidden-import", "wiki_path.path_utils",
        "--hidden-import", "wiki_path.filters",
        *_exclude_flags(),
        "--noconfirm",
        "--clean",
        "cli.py",
    ]
    if onefile:
        cmd.insert(3, "--onefile")
    run(cmd)


def build_web(onefile: bool) -> None:
    print("=" * 50)
    print("Building web executable (wikipath-web.exe) ...")
    print("=" * 50)
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "wikipath-web",
        "--collect-all", "uvicorn",
        "--collect-all", "httpx",
        "--collect-all", "anyio",
        "--collect-all", "fastapi",
        "--collect-all", "starlette",
        "--hidden-import", "pydantic",
        "--hidden-import", "wiki_path.api_client",
        "--hidden-import", "wiki_path.bfs",
        "--hidden-import", "wiki_path.path_utils",
        "--hidden-import", "wiki_path.filters",
        *_exclude_flags(),
        "--noconfirm",
        "--clean",
        "web_launcher.py",
    ]
    if onefile:
        cmd.insert(3, "--onefile")
    run(cmd)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build WikiPath Finder executables")
    parser.add_argument("--cli", action="store_true", help="Build CLI exe only")
    parser.add_argument("--web", action="store_true", help="Build web exe only")
    parser.add_argument("--onefile", action="store_true", help="Build single-file exe.")
    args = parser.parse_args()

    build_both = not args.cli and not args.web

    if args.cli or build_both:
        build_cli(args.onefile)

    if args.web or build_both:
        build_web(args.onefile)

    mode = "onefile" if args.onefile else "onedir"
    print("\n" + "=" * 50)
    print(f"Done! ({mode} mode)")
    print("Executables are in the  dist/  folder.")
    if not args.onefile:
        print("  dist/wikipath/wikipath.exe")
        print("  dist/wikipath-web/wikipath-web.exe")
    else:
        print("  dist/wikipath.exe")
        print("  dist/wikipath-web.exe")
    print("=" * 50)


if __name__ == "__main__":
    main()
