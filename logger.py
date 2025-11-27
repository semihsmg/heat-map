from pynput import keyboard
from typing import Callable, Optional
import database


class KeyLogger:
    """Handles keyboard event capture and logging."""

    def __init__(self):
        self.listener: Optional[keyboard.Listener] = None
        self.paused = False
        self.on_key_logged: Optional[Callable[[str], None]] = None

    def _parse_key(self, key) -> str:
        """Parse a pynput key object into a readable string."""
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

        # Handle numpad and other special cases
        if '<' in key_str and '>' in key_str:
            # Virtual key codes like <65437>
            vk_code = key_str.strip('<>')
            if vk_code.isdigit():
                vk = int(vk_code)
                # Common numpad virtual key codes
                numpad_map = {
                    96: 'Num0', 97: 'Num1', 98: 'Num2', 99: 'Num3',
                    100: 'Num4', 101: 'Num5', 102: 'Num6', 103: 'Num7',
                    104: 'Num8', 105: 'Num9',
                    106: 'Num*', 107: 'Num+', 109: 'Num-',
                    110: 'Num.', 111: 'Num/',
                }
                return numpad_map.get(vk, f'Key{vk}')

        return key_str

    def _on_release(self, key):
        """Handle key release event."""
        if self.paused:
            return

        key_name = self._parse_key(key)
        database.log_key(key_name)

        if self.on_key_logged:
            self.on_key_logged(key_name)

    def start(self):
        """Start the keyboard listener."""
        if self.listener is None or not self.listener.running:
            self.listener = keyboard.Listener(on_release=self._on_release)
            self.listener.start()

    def stop(self):
        """Stop the keyboard listener."""
        if self.listener and self.listener.running:
            self.listener.stop()
            self.listener = None

    def pause(self):
        """Pause logging (listener keeps running but ignores events)."""
        self.paused = True

    def resume(self):
        """Resume logging."""
        self.paused = False

    def toggle_pause(self) -> bool:
        """Toggle pause state. Returns new paused state."""
        self.paused = not self.paused
        return self.paused

    @property
    def is_paused(self) -> bool:
        """Check if logging is paused."""
        return self.paused
