import ctypes
import json
import os
import queue
import sys
import threading
from ctypes import wintypes
from pathlib import Path

from PySide6.QtCore import QAbstractNativeEventFilter, QObject, Qt, Signal
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPlainTextEdit, QPushButton,
    QStackedWidget, QVBoxLayout, QWidget,
)

import gamedata
import sender
import snapshots
import system
from i18n import set_language, t

APP_DIR = Path(__file__).resolve().parent
HOTKEY_ID = 0xB00C
VK_F8 = 0x77
WM_HOTKEY = 0x0312

STYLE = """
* { font-family: 'Consolas'; font-size: 13px; color: #d6f5c0; }
QMainWindow, QWidget { background: #0d1a10; }
QLineEdit, QComboBox, QPlainTextEdit, QListWidget {
    background: #0a140c; border: 2px solid #2e5a22; padding: 4px;
    selection-background-color: #46a520; selection-color: #0d1a10;
}
QListWidget::item { padding: 2px; }
QListWidget::item:hover { background: #1c3a22; }
QListWidget#nav { background: #11241a; font-weight: bold; }
QListWidget#nav::item { padding: 8px; border-bottom: 1px solid #1c3a22; }
QListWidget#nav::item:selected { background: #46a520; color: #0d1a10; }
QPushButton { background: #16301d; border: 2px solid #46a520; padding: 6px 10px; }
QPushButton:hover { background: #46a520; color: #0d1a10; }
QPushButton#primary { background: #46a520; color: #0d1a10; font-weight: bold; }
QPushButton#primary:hover { background: #8ce42c; }
QLabel#hint { color: #7fa86a; }
QCheckBox::indicator { width: 14px; height: 14px; border: 2px solid #46a520; background: #0a140c; }
QCheckBox::indicator:checked { background: #8ce42c; }
"""


def settings_file() -> Path:
    return gamedata.app_data_dir() / "settings.json"


def load_settings() -> dict:
    try:
        return json.loads(settings_file().read_text("utf-8-sig"))
    except (OSError, ValueError):
        return {}


def save_settings(data: dict) -> None:
    settings_file().write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")


class Bridge(QObject):
    log = Signal(str)
    hotkey = Signal()


class HotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self, bridge: Bridge):
        super().__init__()
        self.bridge = bridge

    def nativeEventFilter(self, event_type, message):
        if event_type == b"windows_generic_MSG":
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                self.bridge.hotkey.emit()
                return True, 0
        return False, 0


def hint_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("hint")
    label.setWordWrap(True)
    return label


class CatalogTab(QWidget):
    def __init__(self, entries, hint, build, send, extra=None):
        super().__init__()
        self.entries = entries
        self.build = build
        self.send = send
        lay = QVBoxLayout(self)
        top = QHBoxLayout()
        self.search = QLineEdit(placeholderText=t("search"))
        self.group = QComboBox()
        self.group.addItem(t("all_groups"), "")
        for g in sorted({e["group"] for e in entries}):
            self.group.addItem(g, g)
        top.addWidget(self.search, 3)
        top.addWidget(self.group, 1)
        lay.addLayout(top)
        self.list = QListWidget()
        lay.addWidget(self.list, 1)
        if extra is not None:
            lay.addWidget(extra)
        bottom = QHBoxLayout()
        btn = QPushButton(t("send"))
        btn.setObjectName("primary")
        bottom.addWidget(hint_label(hint), 1)
        bottom.addWidget(btn)
        lay.addLayout(bottom)
        self.search.textChanged.connect(self.refill)
        self.group.currentIndexChanged.connect(self.refill)
        self.list.itemDoubleClicked.connect(lambda _: self.fire())
        btn.clicked.connect(self.fire)
        self.refill()

    def refill(self):
        needle = self.search.text().strip().lower()
        group = self.group.currentData()
        self.list.clear()
        for e in self.entries:
            if group and e["group"] != group:
                continue
            text = f"{e['name']}  —  {e['id']}" if e["name"] else e["id"]
            if needle and needle not in text.lower():
                continue
            item = QListWidgetItem(f"{text}   [{e['group']}]")
            item.setData(Qt.UserRole, e["id"])
            self.list.addItem(item)

    def fire(self):
        item = self.list.currentItem()
        if item:
            self.send(self.build(item.data(Qt.UserRole)))


class SavesTab(QWidget):
    def __init__(self, log):
        super().__init__()
        self.log = log
        lay = QVBoxLayout(self)
        lay.addWidget(hint_label(t("saves_hint")))
        row = QHBoxLayout()
        self.label = QLineEdit(placeholderText=t("snap_label"))
        make = QPushButton(t("snap_make"))
        make.setObjectName("primary")
        row.addWidget(self.label, 1)
        row.addWidget(make)
        lay.addLayout(row)
        self.list = QListWidget()
        lay.addWidget(self.list, 1)
        row2 = QHBoxLayout()
        restore = QPushButton(t("snap_restore"))
        delete = QPushButton(t("snap_delete"))
        opendir = QPushButton(t("snap_open"))
        row2.addWidget(restore)
        row2.addWidget(delete)
        row2.addStretch(1)
        row2.addWidget(opendir)
        lay.addLayout(row2)
        make.clicked.connect(self._make)
        restore.clicked.connect(self._restore)
        delete.clicked.connect(self._delete)
        opendir.clicked.connect(lambda: os.startfile(snapshots.snapshots_root()))
        self.refresh()

    def refresh(self):
        self.list.clear()
        for p in snapshots.list_snapshots():
            item = QListWidgetItem(p.name)
            item.setData(Qt.UserRole, str(p))
            self.list.addItem(item)

    def _selected(self):
        item = self.list.currentItem()
        return Path(item.data(Qt.UserRole)) if item else None

    def _make(self):
        try:
            self.log(t("snap_done", snapshots.create(self.label.text()).name))
            self.label.clear()
        except OSError as e:
            self.log(t("snap_failed", e))
        self.refresh()

    def _restore(self):
        snap = self._selected()
        if not snap:
            return
        if sender.find_game_window():
            QMessageBox.warning(self, t("game_running"), t("snap_game_running"))
            return
        if QMessageBox.question(self, t("restore"), t("snap_confirm", snap.name)) != QMessageBox.Yes:
            return
        try:
            snapshots.restore(snap)
            self.log(t("snap_restored", snap.name))
        except OSError as e:
            self.log(t("snap_restore_failed", e))
        self.refresh()

    def _delete(self):
        snap = self._selected()
        if snap and QMessageBox.question(self, t("delete"), t("snap_delete_confirm", snap.name)) == QMessageBox.Yes:
            snapshots.delete(snap)
            self.refresh()


class NavTabs(QWidget):
    def __init__(self):
        super().__init__()
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        self.nav.setFixedWidth(170)
        self.stack = QStackedWidget()
        lay.addWidget(self.nav)
        lay.addWidget(self.stack, 1)
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)

    def add(self, widget, title):
        self.stack.addWidget(widget)
        self.nav.addItem(title)
        if self.nav.currentRow() < 0:
            self.nav.setCurrentRow(0)


class SandboxMenu(QMainWindow):
    def __init__(self, catalog, settings, game_dir):
        super().__init__()
        self.settings = settings
        self.game_dir = game_dir
        self.bridge = Bridge()
        self.bridge.log.connect(self.append_log)
        self.bridge.hotkey.connect(self.toggle_visible)
        self.queue = queue.Queue()
        threading.Thread(target=self._worker, daemon=True).start()

        self.setWindowTitle(t("title"))
        self.resize(860, 680)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, settings.get("on_top", True))
        root = QWidget()
        lay = QVBoxLayout(root)
        lay.addWidget(hint_label(t("fair_note")))
        self.tabs = NavTabs()
        lay.addWidget(self.tabs, 1)
        self._build_tabs(catalog)
        self.log = QPlainTextEdit(readOnly=True)
        self.log.setMaximumHeight(100)
        lay.addWidget(self.log)
        lay.addLayout(self._options_row())
        self.setCentralWidget(root)
        self.append_log(t("welcome"))

    def _enemy_extra(self, buffs):
        self.elite_mod = QComboBox()
        for key, val in (("normal", ""), ("elite", "elite"), ("champion", "champion")):
            self.elite_mod.addItem(t(key), val)
        self.buffs = QListWidget()
        self.buffs.setMaximumHeight(110)
        self.buffs.setFlow(QListWidget.LeftToRight)
        self.buffs.setWrapping(True)
        for b in buffs:
            it = QListWidgetItem(b["id"])
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Unchecked)
            self.buffs.addItem(it)
        box = QWidget()
        el = QVBoxLayout(box)
        el.setContentsMargins(0, 0, 0, 0)
        row = QHBoxLayout()
        row.addWidget(QLabel(t("type")))
        row.addWidget(self.elite_mod)
        row.addWidget(QLabel(t("buffs")), 1)
        el.addLayout(row)
        el.addWidget(self.buffs)
        return box

    def _spawn_command(self, enemy_id):
        buffs = [self.buffs.item(k).text() for k in range(self.buffs.count())
                 if self.buffs.item(k).checkState() == Qt.Checked]
        mod = self.elite_mod.currentData() or ("elite" if buffs else "")
        return " ".join(["spawn", enemy_id] + ([mod] if mod else []) + buffs)

    def _build_tabs(self, c):
        self.tabs.add(CatalogTab(c["enemies"], t("hint_enemies"), self._spawn_command, self.send,
                                 self._enemy_extra(c["elite_buffs"])), t("tab_enemies"))
        self.tabs.add(CatalogTab(c["levels"], t("hint_bosses"), lambda i: f"load {i}", self.send), t("tab_bosses"))
        self.tabs.add(CatalogTab(c["tiles"], t("hint_tiles"), lambda i: f"spawntile {i}", self.send), t("tab_tiles"))
        self.weather_cmd = QComboBox()
        for key, val in (("w_battle", "weather"), ("w_global", "global"),
                         ("w_chapter", "AddChapterWeather"), ("w_house", "house_weather")):
            self.weather_cmd.addItem(t(key), val)
        self.tabs.add(CatalogTab(c["weather"], t("hint_weather"),
                                 lambda i: f"{self.weather_cmd.currentData()} {i}", self.send, self.weather_cmd),
                      t("tab_weather"))
        self.tabs.add(SavesTab(self.append_log), t("tab_saves"))

    def _options_row(self):
        row = QHBoxLayout()
        self.opt_close = QCheckBox(t("close_console"))
        self.opt_close.setChecked(self.settings.get("close_after", True))
        self.opt_top = QCheckBox(t("on_top"))
        self.opt_top.setChecked(self.settings.get("on_top", True))
        self.opt_close.toggled.connect(lambda v: self._set("close_after", v))
        self.opt_top.toggled.connect(self._set_on_top)
        row.addWidget(self.opt_close)
        row.addWidget(self.opt_top)
        row.addStretch(1)
        return row

    def _set(self, key, value):
        self.settings[key] = value
        save_settings(self.settings)

    def _set_on_top(self, value):
        self._set("on_top", value)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, value)
        self.show()

    def append_log(self, text):
        self.log.appendPlainText(text)

    def toggle_visible(self):
        if self.isVisible() and not self.isMinimized():
            self.hide()
        else:
            self.showNormal()
            self.raise_()
            self.activateWindow()

    def send(self, command):
        if command:
            self.queue.put((command, self.opt_close.isChecked()))

    def _worker(self):
        while True:
            command, close_after = self.queue.get()
            hwnd = sender.find_game_window()
            if hwnd and not system.is_admin() and system.game_needs_admin(None, hwnd):
                self.bridge.log.emit(t("need_admin"))
                continue
            try:
                sender.send_command(command, close_after=close_after)
                self.bridge.log.emit(f"> {command}")
            except sender.GameNotFound as e:
                self.bridge.log.emit(t(str(e)))


def resolve_game_dir(settings: dict) -> Path | None:
    candidates = [settings.get("game_dir"), system.find_steam_install()]
    for c in candidates:
        if c and system.is_game_dir(Path(c)):
            path = Path(c)
            break
    else:
        path = None
    while not path:
        chosen = QFileDialog.getExistingDirectory(None, t("pick_dir"))
        if not chosen:
            return None
        if system.is_game_dir(Path(chosen)):
            path = Path(chosen)
    settings["game_dir"] = str(path)
    save_settings(settings)
    return path


def ensure_console(win: SandboxMenu) -> None:
    if not system.config_dirs():
        win.append_log(t("console_missing"))
        return
    if system.console_enabled():
        return
    if QMessageBox.question(win, t("console_title"), t("console_text")) == QMessageBox.Yes:
        system.enable_console()
        win.append_log(t("console_on"))


def pick_language() -> str:
    for i, arg in enumerate(sys.argv[:-1]):
        if arg == "--lang" and sys.argv[i + 1] in ("en", "ru"):
            return sys.argv[i + 1]
    return system.ui_language()


def main():
    lang = pick_language()
    set_language(lang)
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    settings = load_settings()
    game_dir = resolve_game_dir(settings)
    if not game_dir:
        return
    if (not system.is_admin() and "--elevated" not in sys.argv
            and system.game_needs_admin(game_dir, sender.find_game_window())
            and system.relaunch_as_admin(APP_DIR / "main.py")):
        return
    try:
        catalog = gamedata.load_catalog(game_dir, lang)
    except (OSError, ValueError) as e:
        QMessageBox.critical(None, t("error"), t("read_failed", e))
        return
    win = SandboxMenu(catalog, settings, game_dir)
    hotkey_filter = HotkeyFilter(win.bridge)
    app.installNativeEventFilter(hotkey_filter)
    ctypes.windll.user32.RegisterHotKey(None, HOTKEY_ID, 0, VK_F8)
    win.show()
    ensure_console(win)
    code = app.exec()
    ctypes.windll.user32.UnregisterHotKey(None, HOTKEY_ID)
    sys.exit(code)


if __name__ == "__main__":
    main()
