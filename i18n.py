STRINGS = {
    "title": ("Mewgenics Sandbox Menu", "Mewgenics Sandbox Menu"),
    "search": ("Search by name or ID…", "Поиск по названию или ID…"),
    "all_groups": ("All groups", "Все группы"),
    "send": ("Send to game", "Отправить в игру"),
    "tab_enemies": ("Enemies", "Враги"),
    "tab_bosses": ("Bosses & levels", "Боссы и уровни"),
    "tab_tiles": ("Tiles", "Тайлы"),
    "tab_weather": ("Weather", "Погода"),
    "tab_saves": ("Save snapshots", "Снимки сохранений"),
    "hint_enemies": ("In combat: the enemy appears on a random free tile.",
                     "Бой: враг появится на случайной свободной клетке."),
    "hint_bosses": ("In combat: loads this arena with its enemies (load).",
                    "Бой: загружает эту арену с её врагами (load)."),
    "hint_tiles": ("In combat: places a tile on the field (spawntile).",
                   "Бой: ставит тайл на поле (spawntile)."),
    "hint_weather": ("Choose where to apply the weather.", "Выбери, куда применить погоду."),
    "type": ("Type:", "Тип:"),
    "normal": ("Normal", "Обычный"),
    "elite": ("Elite", "Элитный"),
    "champion": ("Champion", "Чемпион"),
    "buffs": ("Elite buffs (tick any):", "Баффы элиты (отметь галочками):"),
    "w_battle": ("This battle (weather)", "В этом бою (weather)"),
    "w_global": ("Whole battle, global (global)", "Глобально в бою (global)"),
    "w_chapter": ("Rest of the chapter (AddChapterWeather)", "На главу (AddChapterWeather)"),
    "w_house": ("House (house_weather)", "В доме (house_weather)"),
    "saves_hint": ("A snapshot copies all your save files. Restore only while the game is closed — "
                   "your current saves are snapshotted as 'before-restore' first.",
                   "Снимок копирует все сохранения. Откатывать можно только при закрытой игре — "
                   "текущие сохранения сначала тоже сохраняются снимком «before-restore»."),
    "snap_label": ("Snapshot label, e.g. before boss", "Подпись снимка, например: до босса"),
    "snap_make": ("Take snapshot", "Сделать снимок"),
    "snap_restore": ("Restore selected", "Откатить к выбранному"),
    "snap_delete": ("Delete snapshot", "Удалить снимок"),
    "snap_open": ("Open folder", "Открыть папку"),
    "snap_done": ("Snapshot saved: {0}", "Снимок сохранён: {0}"),
    "snap_failed": ("! Snapshot failed: {0}", "! Не удалось сделать снимок: {0}"),
    "snap_game_running": ("Close Mewgenics before restoring, otherwise the game overwrites the files.",
                          "Закрой Mewgenics перед откатом — иначе игра перезапишет файлы."),
    "snap_confirm": ("Replace your saves with snapshot '{0}'?", "Заменить сохранения снимком «{0}»?"),
    "snap_restored": ("Saves restored to: {0}", "Сохранения откатены к: {0}"),
    "snap_restore_failed": ("! Restore failed: {0}", "! Откат не удался: {0}"),
    "snap_delete_confirm": ("Delete snapshot '{0}'?", "Удалить снимок «{0}»?"),
    "game_running": ("Game is running", "Игра запущена"),
    "restore": ("Restore", "Откат"),
    "delete": ("Delete", "Удалить"),
    "close_console": ("Close console after each command", "Закрывать консоль после команды"),
    "on_top": ("Always on top", "Поверх окон"),
    "welcome": ("F8 shows/hides this window. Commands work in the house, on the map and in combat.",
                "F8 — показать/спрятать окно. Команды работают в доме, на карте и в бою."),
    "game_not_found": ("! Mewgenics window not found — start the game first.",
                       "! Окно Mewgenics не найдено — сначала запусти игру."),
    "focus_failed": ("! Could not switch to the game window.", "! Не удалось переключиться на окно игры."),
    "pick_dir": ("Mewgenics folder (the one with resources.gpak)", "Папка Mewgenics (где resources.gpak)"),
    "error": ("Error", "Ошибка"),
    "read_failed": ("Could not read the game data:\n{0}", "Не удалось прочитать данные игры:\n{0}"),
    "console_title": ("Enable the debug console?", "Включить консоль разработчика?"),
    "console_text": ("This menu uses Mewgenics' built-in developer console. It is off by default.\n\n"
                     "Enable it now? The line 'enable_debugconsole true' is added to settings.txt "
                     "(a backup is made). Restart the game afterwards.",
                     "Меню работает через встроенную консоль разработчика Mewgenics, по умолчанию она выключена.\n\n"
                     "Включить? В settings.txt добавится строка 'enable_debugconsole true' (с резервной копией). "
                     "После этого перезапусти игру."),
    "console_on": ("Debug console enabled — restart Mewgenics if it is running.",
                   "Консоль включена — перезапусти Mewgenics, если игра запущена."),
    "console_missing": ("! settings.txt not found — launch Mewgenics once, close it, then reopen this menu.",
                        "! settings.txt не найден — запусти Mewgenics один раз, закрой и открой меню снова."),
    "need_admin": ("! The game runs as administrator, so this menu needs admin rights too. Restart the menu as admin.",
                   "! Игра запущена от администратора — меню тоже нужно запустить от администратора."),
    "fair_note": ("Sandbox edition: spawns and arena tweaks only — no god mode, auto-win or free loot.",
                  "Песочница: только спавн и настройки арены — без бессмертия, автопобеды и бесплатных предметов."),
}

_lang = "en"


def set_language(lang: str) -> None:
    global _lang
    _lang = "ru" if lang == "ru" else "en"


def language() -> str:
    return _lang


def t(key: str, *args) -> str:
    en, ru = STRINGS[key]
    text = ru if _lang == "ru" else en
    return text.format(*args) if args else text
