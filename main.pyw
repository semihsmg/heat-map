import sys
import os
import winreg
import threading
import tempfile
import atexit
import subprocess
import json
import urllib.request
from pathlib import Path

import pystray
from pystray import MenuItem as Item

import database
import logger
import report
import icons

__version__ = "0.7.0"
GITHUB_REPO = "semihsmg/heat-map"

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
        """Check for updates and apply them."""
        # Run in background thread to not block UI
        threading.Thread(target=self._do_update_check, args=(icon, item), daemon=True).start()

    def _do_update_check(self, icon, item):
        """Perform the actual update check."""
        try:
            if getattr(sys, 'frozen', False):
                # Running as exe - use GitHub Releases
                self._check_github_release(icon, item)
            else:
                # Running from source - use git pull
                self._check_git_update(icon, item)
        except Exception as e:
            self._notify("Update Error", str(e)[:100])

    def _check_git_update(self, icon, item):
        """Check for updates via git pull (for development)."""
        try:
            app_dir = Path(__file__).parent
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
                self._notify("Updated!", "Restarting to apply updates...")
                threading.Event().wait(1)
                script_path = os.path.abspath(sys.argv[0])
                pythonw_path = sys.executable.replace('python.exe', 'pythonw.exe')
                subprocess.Popen([pythonw_path, script_path])
                self._exit_app(icon, item)
            else:
                self._notify("Update Failed", f"Could not update: {output[:100]}")
        except FileNotFoundError:
            self._notify("Git Not Found", "Git is not installed or not in PATH.")

    def _check_github_release(self, icon, item):
        """Check GitHub releases for updates (for exe)."""
        try:
            # Get latest release from GitHub API
            api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'KeyboardHeatMap'})
            with urllib.request.urlopen(req, timeout=10) as response:
                release = json.loads(response.read().decode())

            latest_version = release['tag_name'].lstrip('v')
            current_version = __version__

            # Compare versions
            if self._compare_versions(latest_version, current_version) <= 0:
                self._notify("No Updates", f"You're running the latest version (v{current_version}).")
                return

            # Find exe asset
            exe_asset = None
            for asset in release.get('assets', []):
                if asset['name'].endswith('.exe'):
                    exe_asset = asset
                    break

            if not exe_asset:
                self._notify("Update Error", "No executable found in latest release.")
                return

            self._notify("Updating...", f"Downloading v{latest_version}...")

            # Download new exe to temp
            download_url = exe_asset['browser_download_url']
            temp_dir = Path(tempfile.gettempdir())
            new_exe_path = temp_dir / f"KeyboardHeatMap_v{latest_version}.exe"

            req = urllib.request.Request(download_url, headers={'User-Agent': 'KeyboardHeatMap'})
            with urllib.request.urlopen(req, timeout=60) as response:
                with open(new_exe_path, 'wb') as f:
                    f.write(response.read())

            # Create batch script to replace exe and restart
            current_exe = Path(sys.executable)
            batch_path = temp_dir / "update_heatmap.bat"

            batch_content = f'''@echo off
timeout /t 2 /nobreak >nul
copy /y "{new_exe_path}" "{current_exe}"
del "{new_exe_path}"
start "" "{current_exe}"
del "%~f0"
'''
            with open(batch_path, 'w') as f:
                f.write(batch_content)

            self._notify("Updated!", f"Restarting with v{latest_version}...")
            threading.Event().wait(1)

            # Run batch script and exit
            subprocess.Popen(['cmd', '/c', str(batch_path)], creationflags=subprocess.CREATE_NO_WINDOW)
            self._exit_app(icon, item)

        except urllib.error.URLError as e:
            self._notify("Network Error", "Could not connect to GitHub.")
        except json.JSONDecodeError:
            self._notify("Update Error", "Invalid response from GitHub.")

    def _compare_versions(self, v1: str, v2: str) -> int:
        """Compare two version strings. Returns >0 if v1 > v2, <0 if v1 < v2, 0 if equal."""
        def parse(v):
            return [int(x) for x in v.split('.')]
        p1, p2 = parse(v1), parse(v2)
        for a, b in zip(p1, p2):
            if a != b:
                return a - b
        return len(p1) - len(p2)

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
