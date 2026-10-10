import ctypes
import os
import re
import shutil
import sys
import time
import winreg
from ctypes import wintypes
from pathlib import Path

STEAM_APP_ID = "686060"
GAME_EXE = "Mewgenics.exe"
CONSOLE_LINE = "enable_debugconsole true"
COMPAT_KEY = r"Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"


def _steam_root() -> Path | None:
    for hive, key, value in (
        (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
    ):
        try:
            with winreg.OpenKey(hive, key) as k:
                return Path(winreg.QueryValueEx(k, value)[0])
        except OSError:
            continue
    return None


def find_steam_install() -> Path | None:
    root = _steam_root()
    if not root:
        return None
    libraries = [root]
    vdf = root / "steamapps" / "libraryfolders.vdf"
    if vdf.exists():
        text = vdf.read_text("utf-8", errors="replace")
        libraries += [Path(p.replace("\\\\", "\\")) for p in re.findall(r'"path"\s+"([^"]+)"', text)]
    for lib in libraries:
        manifest = lib / "steamapps" / f"appmanifest_{STEAM_APP_ID}.acf"
        if not manifest.exists():
            continue
        m = re.search(r'"installdir"\s+"([^"]+)"', manifest.read_text("utf-8", errors="replace"))
        if m:
            game = lib / "steamapps" / "common" / m.group(1)
            if (game / "resources.gpak").exists():
                return game
    return None


def is_game_dir(path: Path) -> bool:
    return (path / "resources.gpak").exists() and (path / GAME_EXE).exists()


def config_dirs() -> list[Path]:
    root = Path(os.environ.get("APPDATA", "")) / "Glaiel Games" / "Mewgenics"
    return sorted((p.parent for p in root.glob("*/settings.txt")), key=lambda p: p.stat().st_mtime, reverse=True)


def console_enabled() -> bool:
    dirs = config_dirs()
    return bool(dirs) and all(CONSOLE_LINE in (d / "settings.txt").read_text("utf-8", errors="replace")
                              for d in dirs)


def enable_console() -> list[Path]:
    changed = []
    for d in config_dirs():
        settings = d / "settings.txt"
        text = settings.read_text("utf-8", errors="replace")
        if re.search(r"^enable_debugconsole\s+true\s*$", text, re.M):
            continue
        shutil.copy2(settings, d / f"settings.backup-{time.strftime('%Y%m%d-%H%M%S')}.txt")
        text = re.sub(r"^enable_debugconsole\s+\S+\s*\n?", "", text, flags=re.M)
        settings.write_text(CONSOLE_LINE + "\n" + text, "utf-8")
        changed.append(settings)
    return changed


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except OSError:
        return False


def _game_runs_as_admin_flag(game_dir: Path) -> bool:
    exe = str(game_dir / GAME_EXE).lower()
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            with winreg.OpenKey(hive, COMPAT_KEY) as k:
                i = 0
                while True:
                    name, value, _ = winreg.EnumValue(k, i)
                    if name.lower() == exe and "RUNASADMIN" in str(value).upper():
                        return True
                    i += 1
        except OSError:
            continue
    return False


def _process_elevated(pid: int) -> bool:
    kernel32 = ctypes.windll.kernel32
    advapi32 = ctypes.windll.advapi32
    handle = kernel32.OpenProcess(0x1000, False, pid)
    if not handle:
        return False
    token = wintypes.HANDLE()
    try:
        if not advapi32.OpenProcessToken(handle, 0x0008, ctypes.byref(token)):
            return False
        elevation = wintypes.DWORD()
        size = wintypes.DWORD()
        advapi32.GetTokenInformation(token, 20, ctypes.byref(elevation), 4, ctypes.byref(size))
        return bool(elevation.value)
    finally:
        if token:
            kernel32.CloseHandle(token)
        kernel32.CloseHandle(handle)


def game_needs_admin(game_dir: Path | None, hwnd: int | None) -> bool:
    if hwnd:
        pid = wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if _process_elevated(pid.value):
            return True
    return bool(game_dir) and _game_runs_as_admin_flag(game_dir)


def relaunch_as_admin(script: Path) -> bool:
    params = " ".join(f'"{a}"' for a in [str(script), "--elevated"] + sys.argv[1:])
    rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, str(script.parent), 1)
    return rc > 32


def ui_language() -> str:
    try:
        lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF
    except OSError:
        return "en"
    return "ru" if lang_id == 0x19 else "en"
