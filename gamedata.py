import csv
import io
import json
import os
import re
import struct
from pathlib import Path

CACHE_VERSION = 1
APP_DATA_NAME = "MewgenicsSandboxMenu"

LEVEL_KINDS = ("house_bosses", "boss", "miniboss", "special")
TILE_EXTRA = ("GrassTile", "TallGrassTile", "TallBrambleTile", "PackedSnowTile", "FloatingGlassTile")
TILE_BASES = {
    "TacticsTile", "SpawnTile", "AddTile", "ChangeTile", "SetTile", "LimitedTile", "IgnoreTile",
    "ReplaceBlankTile", "DamageNeighborTile", "PassiveWhenOnTile", "LockOrientationFaceTile",
    "SpawnOnBattleStartRandomEmptyTile", "RandomDifferentTile", "BlankTile",
}


def app_data_dir() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home())) / APP_DATA_NAME
    base.mkdir(parents=True, exist_ok=True)
    return base


def _read_index(f):
    count = struct.unpack("<I", f.read(4))[0]
    entries = []
    for _ in range(count):
        name_len = struct.unpack("<H", f.read(2))[0]
        name = f.read(name_len).decode("utf-8", "replace")
        size = struct.unpack("<I", f.read(4))[0]
        entries.append((name, size))
    return entries


def read_gpak(gpak_path: Path, want) -> tuple[dict[str, str], list[str]]:
    files = {}
    with open(gpak_path, "rb") as f:
        entries = _read_index(f)
        offset = f.tell()
        for name, size in entries:
            if want(name):
                f.seek(offset)
                files[name] = f.read(size).decode("utf-8-sig", "replace")
            offset += size
    return files, [name for name, _ in entries]


def strip_comments(text: str) -> str:
    out = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == '"':
            j = text.find('"', i + 1)
            j = n if j < 0 else j + 1
            out.append(text[i:j])
            i = j
        elif text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def top_blocks(text: str) -> list[tuple[str, str]]:
    clean = strip_comments(text)
    blocks = []
    depth = 0
    i, n = 0, len(clean)
    start_name = None
    body_start = 0
    while i < n:
        c = clean[i]
        if c == '"':
            j = clean.find('"', i + 1)
            i = n if j < 0 else j + 1
            continue
        if c == "{":
            if depth == 0:
                m = re.search(r"([A-Za-z0-9_\-']+)\s*$", clean[max(0, i - 120):i])
                start_name = m.group(1) if m else None
                body_start = i + 1
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0 and start_name:
                blocks.append((start_name, clean[body_start:i]))
                start_name = None
        i += 1
    return blocks


def field(body: str, key: str) -> str:
    m = re.search(r'(?<![A-Za-z0-9_])' + key + r'\s+"([^"]*)"', body)
    if m:
        return m.group(1)
    m = re.search(r'(?<![A-Za-z0-9_])' + key + r'\s+([A-Za-z0-9_]+)', body)
    return m.group(1) if m else ""


def _merge_csv(table: dict, content: str, lang: str) -> None:
    reader = csv.reader(io.StringIO(content))
    header = next(reader, None)
    if not header:
        return
    col = header.index(lang) if lang in header else 1
    for row in reader:
        if len(row) < 2 or not row[0]:
            continue
        text = row[col] if col < len(row) and row[col].strip() else row[1]
        if text.strip():
            table[row[0]] = text


def load_text(gpak_files: dict, game_dir: Path, lang: str) -> dict:
    table = {}
    for name, content in gpak_files.items():
        if name.startswith("data/text/") and name.endswith(".csv"):
            _merge_csv(table, content, lang)
    if lang != "en":
        disk = game_dir / "data" / "text"
        if disk.is_dir():
            for p in sorted(disk.glob("*.csv")):
                _merge_csv(table, p.read_text("utf-8-sig", errors="replace"), lang)
    return table


def _clean_label(text: str) -> str:
    text = re.sub(r"\[img:[^\]]*\]", "", text)
    text = re.sub(r"\{[^}]*\}", "", text)
    return text.strip()


def _levels(names: list[str]) -> list[dict]:
    result = []
    for name in names:
        if not (name.startswith("levels/") and name.endswith(".lvl")):
            continue
        rel = name[len("levels/"):-len(".lvl")]
        parts = rel.split("/")
        kind = next((k for k in LEVEL_KINDS if k in parts), "")
        if not kind:
            continue
        group = f"{parts[0]} · {kind}" if parts[0] != kind else kind
        label = " / ".join(parts[1:]) if len(parts) > 1 else parts[0]
        result.append({"id": rel, "name": label, "group": group})
    return result


def _tiles(content: str, exe_path: Path) -> list[dict]:
    labels = {}
    for _, body in top_blocks(content):
        m = re.search(r"(?<![A-Za-z_])tile\s+([A-Za-z_]+)", body)
        if m and m.group(1) not in labels:
            labels[m.group(1)] = field(body, "name")
    for extra in TILE_EXTRA:
        labels.setdefault(extra, "")
    try:
        exe = exe_path.read_bytes()
    except OSError:
        return []
    return [
        {"id": cls, "name": label, "group": "tiles"}
        for cls, label in sorted(labels.items())
        if cls not in TILE_BASES and (".?AV" + cls + "@glaiel@@").encode() in exe
    ]


def build_catalog(game_dir: Path, lang: str) -> dict:
    files, names = read_gpak(game_dir / "resources.gpak",
                             lambda n: n.startswith("data/") and n.endswith((".gon", ".csv")))
    text = load_text(files, game_dir, lang)

    def entries(prefix: str, skip=()) -> list[dict]:
        result = []
        for path, content in sorted(files.items()):
            if not (path.startswith(prefix) and path.endswith(".gon")):
                continue
            group = Path(path).stem
            if group in skip:
                continue
            for ident, body in top_blocks(content):
                key = field(body, "name")
                result.append({"id": ident, "name": _clean_label(text.get(key, "")) if key else "", "group": group})
        return result

    buffs = entries("data/elite_buffs.gon") + entries("data/boss_elite_buffs.gon")
    return {
        "enemies": entries("data/characters/", skip=("player_cat", "test_enemies", "rare_cat_tests")),
        "elite_buffs": list({b["id"]: b for b in buffs}.values()),
        "weather": entries("data/weather.gon"),
        "levels": _levels(names),
        "tiles": _tiles(files.get("data/tiles.gon", ""), game_dir / "Mewgenics.exe"),
    }


def load_catalog(game_dir: Path, lang: str) -> dict:
    gpak = game_dir / "resources.gpak"
    stamp = [CACHE_VERSION, lang, str(gpak), gpak.stat().st_size, int(gpak.stat().st_mtime)]
    disk = game_dir / "data" / "text"
    if disk.is_dir():
        stamp.append(max((int(p.stat().st_mtime) for p in disk.glob("*.csv")), default=0))
    cache = app_data_dir() / "catalog.json"
    if cache.exists():
        try:
            data = json.loads(cache.read_text("utf-8"))
            if data.get("stamp") == stamp:
                return data["catalog"]
        except (OSError, ValueError, KeyError):
            pass
    catalog = build_catalog(game_dir, lang)
    cache.write_text(json.dumps({"stamp": stamp, "catalog": catalog}, ensure_ascii=False), "utf-8")
    return catalog
