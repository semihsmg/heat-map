import sys
import os
import winreg
import threading
import tempfile
import atexit
import subprocess
from pathlib import Path

import pystray
from pystray import MenuItem as Item

import database
import logger
import report
import icons


# Single instance lock
LOCK_FILE = Path(tempfile.gettempdir()) / 'keyboard_heatmap.lock'


def is_process_running(pid: int) -> bool:
    """Check if a process with given PID is running (Windows)."""
    import ctypes
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    STILL_ACTIVE = 259

    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if handle == 0:
        return False

    exit_code = ctypes.c_ulong()
    result = kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
    kernel32.CloseHandle(handle)

    if result == 0:
        return False
    return exit_code.value == STILL_ACTIVE


def check_single_instance() -> bool:
    """Check if another instance is already running. Returns True if this is the only instance."""
    if LOCK_FILE.exists():
        try:
            pid = int(LOCK_FILE.read_text().strip())
            if is_process_running(pid):
                return False  # Another instance is running
        except (ValueError, OSError):
            pass  # Invalid lock file, we can take over

    # Create/update lock file with our PID
    LOCK_FILE.write_text(str(os.getpid()))
    atexit.register(remove_lock_file)
    return True


def remove_lock_file():
    """Remove the lock file on exit."""
    try:
        LOCK_FILE.unlink(missing_ok=True)
    except Exception:
        pass


class KeyboardHeatMapApp:
    """Main application class for the Keyboard Heat Map system tray app."""

    APP_NAME = "KeyboardHeatMap"
    STARTUP_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"

    def __init__(self):
        self.key_logger = logger.KeyLogger()
        self.icon: pystray.Icon = None
        self._setup_app()

    def _setup_app(self):
        """Initialize the application."""
        # Initialize database
        database.init_db()

        # Create the system tray icon
        self.icon = pystray.Icon(
            self.APP_NAME,
            icons.get_active_icon(),
            "Keyboard Heat Map",
            menu=self._create_menu()
        )

        # Update tooltip with today's count periodically
        self._update_tooltip()

    def _create_menu(self) -> pystray.Menu:
        """Create the system tray context menu."""
        return pystray.Menu(
            Item(
                'Open Heat Map',
                lambda icon, item: self._open_heatmap(),
                default=True
            ),
            pystray.Menu.SEPARATOR,
            Item(
                'Pause' if not self.key_logger.is_paused else 'Resume',
                self._toggle_pause
            ),
            pystray.Menu.SEPARATOR,
            Item(
                'Check for Updates',
                self._check_for_updates
            ),
            Item(
                'Run at Startup',
                self._toggle_startup,
                checked=lambda item: self._is_startup_enabled()
            ),
            pystray.Menu.SEPARATOR,
            Item('Exit', self._exit_app)
        )

    def _toggle_pause(self, icon, item):
        """Toggle pause/resume logging."""
        is_paused = self.key_logger.toggle_pause()

        # Update icon
        if is_paused:
            self.icon.icon = icons.get_paused_icon()
            self._notify("Logging Paused", "Keyboard logging has been paused.")
        else:
            self.icon.icon = icons.get_active_icon()
            self._notify("Logging Resumed", "Keyboard logging has been resumed.")

        # Refresh menu to update text
        self.icon.menu = self._create_menu()

    def _open_heatmap(self):
        """Open the heat map in the browser."""
        self.key_logger.flush()  # Ensure latest data is saved
        report.open_report()

    def _toggle_startup(self, icon, item):
        """Toggle run at startup setting."""
        if self._is_startup_enabled():
            self._remove_from_startup()
            self._notify("Startup Disabled", "App will not run at Windows startup.")
        else:
            self._add_to_startup()
            self._notify("Startup Enabled", "App will run at Windows startup.")

    def _is_startup_enabled(self) -> bool:
        """Check if app is set to run at startup."""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.STARTUP_REG_PATH,
                0,
                winreg.KEY_READ
            )
            try:
                winreg.QueryValueEx(key, self.APP_NAME)
                return True
            except FileNotFoundError:
                return False
            finally:
                winreg.CloseKey(key)
        except Exception:
            return False

    def _add_to_startup(self):
        """Add app to Windows startup."""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.STARTUP_REG_PATH,
                0,
                winreg.KEY_SET_VALUE
            )
            # Get the path to this script
            script_path = os.path.abspath(sys.argv[0])
            pythonw_path = sys.executable.replace('python.exe', 'pythonw.exe')
            startup_cmd = f'"{pythonw_path}" "{script_path}"'

            winreg.SetValueEx(key, self.APP_NAME, 0, winreg.REG_SZ, startup_cmd)
            winreg.CloseKey(key)
        except Exception as e:
            self._notify("Error", f"Could not enable startup: {e}")

    def _remove_from_startup(self):
        """Remove app from Windows startup."""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.STARTUP_REG_PATH,
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.DeleteValue(key, self.APP_NAME)
            winreg.CloseKey(key)
        except Exception:
            pass  # Already removed or doesn't exist

    def _check_for_updates(self, icon, item):
        """Check for updates via git pull and restart if updated."""
        try:
            # Get the app directory
            app_dir = Path(__file__).parent

            # Run git pull --ff-only
            result = subprocess.run(
                ['git', 'pull', '--ff-only'],
                cwd=app_dir,
                capture_output=True,
                text=True
            )

            output = result.stdout + result.stderr

            if 'Already up to date' in output:
                self._notify("No Updates", "You're running the latest version.")
            elif result.returncode == 0:
                # Updates were pulled, restart the app
                self._notify("Updated!", "Restarting to apply updates...")

                # Give notification time to show
                threading.Event().wait(1)

                # Start new instance
                script_path = os.path.abspath(sys.argv[0])
                pythonw_path = sys.executable.replace('python.exe', 'pythonw.exe')
                subprocess.Popen([pythonw_path, script_path])

                # Exit current instance
                self._exit_app(icon, item)
            else:
                self._notify("Update Failed", f"Could not update: {output[:100]}")

        except FileNotFoundError:
            self._notify("Git Not Found", "Git is not installed or not in PATH.")
        except Exception as e:
            self._notify("Update Error", str(e)[:100])

    def _update_tooltip(self):
        """Update the tooltip with today's keystroke count."""
        def update():
            while self.icon and self.icon.visible:
                try:
                    count = database.get_today_count()
                    status = " (Paused)" if self.key_logger.is_paused else ""
                    self.icon.title = f"Keyboard Heat Map{status}\nToday: {count:,} keys"
                except Exception:
                    pass
                # Update every 30 seconds
                threading.Event().wait(30)

        tooltip_thread = threading.Thread(target=update, daemon=True)
        tooltip_thread.start()

    def _notify(self, title: str, message: str):
        """Show a system notification."""
        try:
            self.icon.notify(message, title)
        except Exception:
            pass  # Notifications might not be supported

    def _exit_app(self, icon, item):
        """Exit the application."""
        self.key_logger.stop()
        self.icon.stop()

    def run(self):
        """Start the application."""
        # Start the key logger
        self.key_logger.start()

        # Run the system tray icon (blocks)
        self.icon.run()


def main():
    """Entry point."""
    if not check_single_instance():
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            0,
            "Another instance of Keyboard Heat Map is already running.",
            "Keyboard Heat Map",
            0x40  # MB_ICONINFORMATION
        )
        sys.exit(1)

    app = KeyboardHeatMapApp()
    app.run()


if __name__ == '__main__':
    main()
