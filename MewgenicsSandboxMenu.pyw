import ctypes
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.chdir(HERE)
sys.path.insert(0, str(HERE))


def ensure_pyside6() -> bool:
    try:
        import PySide6  # noqa: F401
        return True
    except ImportError:
        pass
    ok = ctypes.windll.user32.MessageBoxW(
        None,
        "PySide6 is not installed. Install it now? (one-time download, ~200 MB)",
        "Mewgenics Sandbox Menu",
        0x24,
    )
    if ok != 6:
        return False
    python = Path(sys.executable).with_name("python.exe")
    result = subprocess.run([str(python), "-m", "pip", "install", "-r", str(HERE / "requirements.txt")])
    return result.returncode == 0


if __name__ == "__main__":
    if ensure_pyside6():
        import main
        main.main()
