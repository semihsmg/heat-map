from pynput import keyboard
from typing import Callable, Optional
from collections import Counter
import threading
import database


class KeyLogger:
    """Handles keyboard event capture and logging with buffered writes."""

    FLUSH_INTERVAL = 30  # seconds

    def __init__(self):
        self.listener: Optional[keyboard.Listener] = None
        self.paused = False
        self.buffer = Counter()
        self.buffer_lock = threading.Lock()
        self.flush_timer: Optional[threading.Timer] = None
        self.on_key_logged: Optional[Callable[[str], None]] = None

    def _parse_key(self, key) -> str:
        """Parse a pynput key object into a readable string."""
        # Numpad virtual key codes (check first before char)
        numpad_map = {
            96: 'Num0', 97: 'Num1', 98: 'Num2', 99: 'Num3',
            100: 'Num4', 101: 'Num5', 102: 'Num6', 103: 'Num7',
            104: 'Num8', 105: 'Num9',
            106: 'Num*', 107: 'Num+', 109: 'Num-',
            110: 'Num.', 111: 'Num/',
        }

        # Check virtual key code first for numpad keys
        if hasattr(key, 'vk') and key.vk is not None:
            if key.vk in numpad_map:
                return numpad_map[key.vk]

        try:
            # Regular character keys
            if hasattr(key, 'char') and key.char is not None:
                return key.char.lower()
        except AttributeError:
            pass

        # Special keys
        key_str = str(key)

        # Handle Key.xxx format
        if key_str.startswith('Key.'):
            key_name = key_str[4:]  # Remove 'Key.' prefix

            # Map common key names to display names
            key_mapping = {
                'space': 'Space',
                'enter': 'Enter',
                'backspace': 'Backspace',
                'tab': 'Tab',
                'shift': 'Shift',
                'shift_r': 'Shift',
                'ctrl': 'Ctrl',
                'ctrl_l': 'Ctrl',
                'ctrl_r': 'Ctrl',
                'alt': 'Alt',
                'alt_l': 'Alt',
                'alt_r': 'Alt',
                'alt_gr': 'AltGr',
                'caps_lock': 'CapsLock',
                'esc': 'Esc',
                'delete': 'Delete',
                'insert': 'Insert',
                'home': 'Home',
                'end': 'End',
                'page_up': 'PageUp',
                'page_down': 'PageDown',
                'up': 'Up',
                'down': 'Down',
                'left': 'Left',
                'right': 'Right',
                'print_screen': 'PrtSc',
                'scroll_lock': 'ScrLk',
                'pause': 'Pause',
                'num_lock': 'NumLock',
                'menu': 'Menu',
                'cmd': 'Win',
                'cmd_l': 'Win',
                'cmd_r': 'Win',
                # Function keys
                'f1': 'F1', 'f2': 'F2', 'f3': 'F3', 'f4': 'F4',
                'f5': 'F5', 'f6': 'F6', 'f7': 'F7', 'f8': 'F8',
                'f9': 'F9', 'f10': 'F10', 'f11': 'F11', 'f12': 'F12',
                # Media keys
                'media_play_pause': 'Play/Pause',
                'media_next': 'Next',
                'media_previous': 'Previous',
                'media_volume_up': 'VolUp',
                'media_volume_down': 'VolDown',
                'media_volume_mute': 'Mute',
            }

            return key_mapping.get(key_name, key_name.title())

        # Handle numpad and other special cases via string format
        if '<' in key_str and '>' in key_str:
            # Virtual key codes like <65437>
            vk_code = key_str.strip('<>')
            if vk_code.isdigit():
                vk = int(vk_code)
                if vk in numpad_map:
                    return numpad_map[vk]
                return f'Key{vk}'

        return key_str

    def _on_release(self, key):
        """Handle key release event."""
        if self.paused:
            return

        key_name = self._parse_key(key)

        with self.buffer_lock:
            self.buffer[key_name] += 1

        if self.on_key_logged:
            self.on_key_logged(key_name)

    def _schedule_flush(self):
        """Schedule the next buffer flush."""
        if self.flush_timer:
            self.flush_timer.cancel()

        self.flush_timer = threading.Timer(self.FLUSH_INTERVAL, self._auto_flush)
        self.flush_timer.daemon = True
        self.flush_timer.start()

    def _auto_flush(self):
        """Automatically flush buffer and reschedule."""
        self.flush()
        self._schedule_flush()

    def flush(self):
        """Flush the buffer to database."""
        with self.buffer_lock:
            if self.buffer:
                database.flush_counts(self.buffer.copy())
                self.buffer.clear()

    def start(self):
        """Start the keyboard listener and flush timer."""
        if self.listener is None or not self.listener.running:
            self.listener = keyboard.Listener(on_release=self._on_release)
            self.listener.start()
            self._schedule_flush()

    def stop(self):
        """Stop the keyboard listener and flush remaining buffer."""
        if self.flush_timer:
            self.flush_timer.cancel()
            self.flush_timer = None

        self.flush()  # Flush any remaining keystrokes

        if self.listener and self.listener.running:
            self.listener.stop()
            self.listener = None

    def pause(self):
        """Pause logging and flush buffer."""
        self.paused = True
        self.flush()

    def resume(self):
        """Resume logging."""
        self.paused = False

    def toggle_pause(self) -> bool:
        """Toggle pause state. Returns new paused state."""
        if self.paused:
            self.resume()
        else:
            self.pause()
        return self.paused

    @property
    def is_paused(self) -> bool:
        """Check if logging is paused."""
        return self.paused
