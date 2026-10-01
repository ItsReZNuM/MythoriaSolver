import time
import logging
import ctypes
import pyperclip
from config import config

# ── Patch PyAutoGUI Keyboard Mapping on Windows ──────────────────────
try:
    import pyautogui
    import pyautogui._pyautogui_win as pw

    for i, c in enumerate("abcdefghijklmnopqrstuvwxyz"):
        pw.keyboardMapping[c] = 0x41 + i
        pw.keyboardMapping[c.upper()] = 0x41 + i + 0x100
    for i in range(10):
        pw.keyboardMapping[str(i)] = 0x30 + i
    pw.keyboardMapping["enter"] = 0x0D
    pw.keyboardMapping["return"] = 0x0D
    pw.keyboardMapping["t"] = 0x54
    pw.keyboardMapping["v"] = 0x56
    pw.keyboardMapping["c"] = 0x43
    pw.keyboardMapping["ctrl"] = 0x11
    pw.keyboardMapping["space"] = 0x20
    pw.keyboardMapping["escape"] = 0x1B
    pw.keyboardMapping["-"] = 0xBD
    pw.keyboardMapping["/"] = 0xBF
except Exception:
    pass

try:
    import win32gui
    import win32process
    import win32api
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

logger = logging.getLogger("AnswerSender")

user32 = ctypes.windll.user32 if hasattr(ctypes, "windll") else None

KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004

# Virtual Key (VK) codes and Hardware Scan codes:
# Key 'T':       VK 0x54, Scan 0x14
# Key 'Enter':   VK 0x0D, Scan 0x1C
# Key 'Ctrl':    VK 0x11, Scan 0x1D
# Key 'V':       VK 0x56, Scan 0x2F
# Key 'Escape':  VK 0x1B, Scan 0x01
VK_T = 0x54
SCAN_T = 0x14

VK_RETURN = 0x0D
SCAN_RETURN = 0x1C

VK_CONTROL = 0x11
SCAN_LCONTROL = 0x1D

VK_V = 0x56
SCAN_V = 0x2F


def _press_key(vk: int, scancode: int, hold: float = 0.04):
    """
    Press and release a key sending both Virtual Key code and Hardware Scan code.
    Uses keybd_event which is 100% reliable across 32/64-bit Windows and immune
    to keyboard layout changes (Persian, English, etc.).
    """
    if not user32:
        return
    user32.keybd_event(vk, scancode, 0, 0)
    time.sleep(hold)
    user32.keybd_event(vk, scancode, KEYEVENTF_KEYUP, 0)


def _send_paste(text: str):
    """
    Copy text to Windows clipboard and send physical Ctrl+V.
    """
    if not user32:
        return
    pyperclip.copy(text)
    time.sleep(0.02)
    # Ctrl down
    user32.keybd_event(VK_CONTROL, SCAN_LCONTROL, 0, 0)
    time.sleep(0.03)
    # V down
    user32.keybd_event(VK_V, SCAN_V, 0, 0)
    time.sleep(0.05)
    # V up
    user32.keybd_event(VK_V, SCAN_V, KEYEVENTF_KEYUP, 0)
    time.sleep(0.03)
    # Ctrl up
    user32.keybd_event(VK_CONTROL, SCAN_LCONTROL, KEYEVENTF_KEYUP, 0)


def _send_unicode_text(text: str, interval: float = 0.01):
    """
    Type text directly character-by-character using Windows Unicode events.
    Completely independent of active keyboard layout.
    """
    if not user32:
        return
    for char in text:
        code = ord(char)
        user32.keybd_event(0, code, KEYEVENTF_UNICODE, 0)
        user32.keybd_event(0, code, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0)
        if interval > 0:
            time.sleep(interval)


class AnswerSender:
    """
    Simulates keyboard input to send answers directly into Minecraft chat.
    Uses native Windows keybd_event with both Virtual Key and Hardware Scan codes,
    guaranteeing reliable typing regardless of keyboard layout (Persian/English).
    """

    def __init__(
        self,
        cooldown: float = config.SEND_COOLDOWN,
        require_focus: bool = config.REQUIRE_FOCUS,
        dry_run: bool = config.DRY_RUN,
        send_method: str = config.SEND_METHOD,
        post_open_chat_delay: float = 0.35,
        post_type_delay: float = 0.15,
    ):
        self.cooldown = cooldown
        self.require_focus = require_focus
        self.dry_run = dry_run
        self.send_method = send_method
        self.post_open_chat_delay = max(0.20, post_open_chat_delay)
        self.post_type_delay = max(0.08, post_type_delay)
        self.last_send_time: float = 0.0

    def is_minecraft_focused(self) -> bool:
        """Check if the active foreground window is Minecraft."""
        if not HAS_WIN32:
            return True

        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return False

            title = win32gui.GetWindowText(hwnd).lower()
            if config.WINDOW_TITLE_KEYWORD.lower() in title:
                return True

            # Also verify if foreground process is javaw.exe / java.exe
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                handle = win32api.OpenProcess(
                    win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid
                )
                if handle:
                    proc_name = win32process.GetModuleFileNameEx(handle, 0).lower()
                    win32api.CloseHandle(handle)
                    if "javaw.exe" in proc_name or "java.exe" in proc_name:
                        return True
            except Exception:
                pass

        except Exception as e:
            logger.warning(f"Error checking window focus: {e}")

        return False

    def wait_cooldown(self) -> float:
        """Wait if needed until the server cooldown elapses. Returns wait time."""
        elapsed = time.time() - self.last_send_time
        remaining = self.cooldown - elapsed
        if remaining > 0:
            time.sleep(remaining)
            return remaining
        return 0.0

    def send_chat_message(self, message: str, force: bool = False) -> bool:
        """
        Open Minecraft chat with key 'T' (VK 0x54 + Scan 0x14),
        write or paste the message, and hit 'Enter' (VK 0x0D + Scan 0x1C).
        """
        clean_msg = message.strip()
        if not clean_msg:
            return False

        # 1. Enforce Cooldown
        self.wait_cooldown()

        # 2. Focus Verification
        if self.require_focus and not force:
            if not self.is_minecraft_focused():
                logger.warning(
                    f"Blocked sending '{clean_msg}': Minecraft window is not currently focused."
                )
                return False

        if self.dry_run:
            logger.info(f"[DRY-RUN] Would type in chat: '{clean_msg}'")
            self.last_send_time = time.time()
            return True

        try:
            # 3. Open chat: press key 'T' (VK_T + SCAN_T)
            _press_key(VK_T, SCAN_T, hold=0.04)
            # Give Minecraft Fabric/TLauncher enough time to open ChatScreen GUI
            time.sleep(self.post_open_chat_delay)

            # 4. Type or Paste message
            if self.send_method == "paste":
                _send_paste(clean_msg)
            else:
                _send_unicode_text(clean_msg, interval=0.01)

            time.sleep(self.post_type_delay)

            # 5. Submit message: press key 'Enter' (VK_RETURN + SCAN_RETURN)
            _press_key(VK_RETURN, SCAN_RETURN, hold=0.04)
            self.last_send_time = time.time()
            logger.info(f"Sent message to chat: '{clean_msg}'")
            return True

        except Exception as e:
            logger.error(f"Failed to send chat message: {e}")
            return False
