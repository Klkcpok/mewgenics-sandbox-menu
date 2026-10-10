import ctypes
import time
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008
SW_RESTORE = 9
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

SC_GRAVE = 0x29
SC_ENTER = 0x1C
SC_ESC = 0x01
SC_BACKSPACE = 0x0E
SC_LCTRL = 0x1D
SC_A = 0x1E

ULONG_PTR = ctypes.c_size_t


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]


user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


class GameNotFound(Exception):
    pass


def _process_name(pid):
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(1024)
        size = wintypes.DWORD(1024)
        if kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
            return buf.value.rsplit("\\", 1)[-1].lower()
        return ""
    finally:
        kernel32.CloseHandle(handle)


def find_game_window(exe_name="mewgenics.exe"):
    found = []

    def callback(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if _process_name(pid.value) == exe_name:
            found.append(hwnd)
            return False
        return True

    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return found[0] if found else None


def _send(inputs):
    arr = (INPUT * len(inputs))(*inputs)
    user32.SendInput(len(inputs), arr, ctypes.sizeof(INPUT))


def _scan(code, up=False):
    flags = KEYEVENTF_SCANCODE | (KEYEVENTF_KEYUP if up else 0)
    return INPUT(type=INPUT_KEYBOARD, u=_INPUTUNION(ki=KEYBDINPUT(0, code, flags, 0, 0)))


def _uni(ch, up=False):
    flags = KEYEVENTF_UNICODE | (KEYEVENTF_KEYUP if up else 0)
    return INPUT(type=INPUT_KEYBOARD, u=_INPUTUNION(ki=KEYBDINPUT(0, ord(ch), flags, 0, 0)))


def tap(code, delay=0.03):
    _send([_scan(code)])
    time.sleep(delay)
    _send([_scan(code, up=True)])
    time.sleep(delay)


def type_text(text, delay=0.004):
    for ch in text:
        _send([_uni(ch), _uni(ch, up=True)])
        time.sleep(delay)


def focus(hwnd, timeout=1.5):
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    _send([_scan(0x38), _scan(0x38, up=True)])
    user32.SetForegroundWindow(hwnd)
    end = time.time() + timeout
    while time.time() < end:
        if user32.GetForegroundWindow() == hwnd:
            return True
        time.sleep(0.03)
    return False


user32.GetKeyboardLayout.restype = ctypes.c_void_p
user32.LoadKeyboardLayoutW.restype = ctypes.c_void_p
user32.PostMessageW.argtypes = (wintypes.HWND, wintypes.UINT, wintypes.WPARAM, ctypes.c_void_p)
WM_INPUTLANGCHANGEREQUEST = 0x0050
EN_US = "00000409"


def current_layout(hwnd):
    return user32.GetKeyboardLayout(user32.GetWindowThreadProcessId(hwnd, None))


def set_layout(hwnd, hkl, timeout=1.0):
    user32.PostMessageW(hwnd, WM_INPUTLANGCHANGEREQUEST, 0, hkl)
    end = time.time() + timeout
    while time.time() < end:
        if (current_layout(hwnd) or 0) & 0xFFFF == (hkl or 0) & 0xFFFF:
            return True
        time.sleep(0.03)
    return False


def send_command(command, open_console=True, close_after=True, settle=0.25):
    hwnd = find_game_window()
    if not hwnd:
        raise GameNotFound("game_not_found")
    if not focus(hwnd):
        raise GameNotFound("focus_failed")
    previous = current_layout(hwnd)
    english = user32.LoadKeyboardLayoutW(EN_US, 0)
    if (previous or 0) & 0xFFFF != 0x0409:
        set_layout(hwnd, english)
    try:
        _type_command(command, open_console, close_after, settle)
    finally:
        if previous and (previous & 0xFFFF) != 0x0409:
            set_layout(hwnd, previous)
    return hwnd


def _type_command(command, open_console, close_after, settle):
    time.sleep(settle)
    if open_console:
        tap(SC_GRAVE)
        time.sleep(settle)
        tap(SC_BACKSPACE)
    type_text(command)
    time.sleep(0.05)
    tap(SC_ENTER)
    if close_after:
        time.sleep(settle)
        tap(SC_ESC)
