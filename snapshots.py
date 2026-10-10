import os
import shutil
import time
from pathlib import Path

import gamedata


def saves_dir() -> Path | None:
    root = Path(os.environ.get("APPDATA", "")) / "Glaiel Games" / "Mewgenics"
    found = sorted(root.glob("*/saves"), key=lambda p: p.stat().st_mtime, reverse=True)
    return found[0] if found else None


def snapshots_root() -> Path:
    root = gamedata.app_data_dir() / "snapshots"
    root.mkdir(parents=True, exist_ok=True)
    return root


def list_snapshots() -> list[Path]:
    return sorted((p for p in snapshots_root().iterdir() if p.is_dir()), key=lambda p: p.name, reverse=True)


def _safe(label: str) -> str:
    keep = "".join(ch if ch.isalnum() or ch in " -_" else "_" for ch in label).strip()
    return keep[:40]


def create(label: str = "") -> Path:
    src = saves_dir()
    if not src:
        raise FileNotFoundError("saves folder not found")
    name = time.strftime("%Y-%m-%d %H-%M-%S")
    if label.strip():
        name += " " + _safe(label)
    dst = snapshots_root() / name
    shutil.copytree(src, dst)
    return dst


def restore(snapshot: Path) -> None:
    dst = saves_dir()
    if not dst:
        raise FileNotFoundError("saves folder not found")
    create("before-restore")
    tmp = dst.with_name("saves_restoring")
    if tmp.exists():
        shutil.rmtree(tmp)
    shutil.copytree(snapshot, tmp)
    shutil.rmtree(dst)
    tmp.rename(dst)


def delete(snapshot: Path) -> None:
    shutil.rmtree(snapshot)
