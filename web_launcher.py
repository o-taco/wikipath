"""Standalone entry point for the web app (used by PyInstaller)."""
import multiprocessing
import sys
import threading
import time
import webbrowser

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def open_browser() -> None:
    time.sleep(1.5)
    webbrowser.open("http://localhost:8000")


def main() -> None:
    multiprocessing.freeze_support()

    import uvicorn
    from web.app import app

    print("WikiPath Finder -> http://localhost:8000")
    print("Press Ctrl+C to stop.\n")

    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")


if __name__ == "__main__":
    main()
