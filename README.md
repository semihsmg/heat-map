# Keyboard Heat Map

![Windows](https://img.shields.io/badge/platform-Windows-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
[![GitHub Release](https://img.shields.io/github/v/release/semihsmg/heat-map)](https://github.com/semihsmg/heat-map/releases/latest)
![Privacy](https://img.shields.io/badge/privacy-100%25%20local-brightgreen)

A system tray app that visualizes your keyboard usage as a glowing heat map.

![Heat Map Preview](assets/screenshot-heatmap.png)

---

## Download

**[Download Latest Release](https://github.com/semihsmg/heat-map/releases/latest)** ... No installation required, just run the exe!

---

## Quick Start

### Option 1: Standalone Executable (Recommended)

Download `KeyboardHeatMap.exe` from [Releases](https://github.com/semihsmg/heat-map/releases/latest) and run it.

### Option 2: Run from Source

```bash
git clone https://github.com/semihsmg/heat-map.git
cd heat-map
```

**A)** Double-click `run.bat` (auto-installs dependencies & checks for updates)

**B)** Manual install

```bash
pip install -r requirements.txt
pythonw main.pyw
```

---

## Features

| Feature | Description |
|---------|-------------|
| **Heat Map Visualization** | Keys glow brighter based on usage intensity |
| **Top 3 Highlight** | Most used keys shine purple |
| **Top 10 Keys** | See your most pressed keys at a glance |
| **Screenshot Export** | Download your heat map as PNG |
| **Auto-Update** | Check for updates from the tray menu |
| **System Tray** | Runs in background, right-click for menu |
| **Pause/Resume** | Toggle logging anytime |
| **Startup Option** | Auto-launch with Windows |
| **Single Instance** | Prevents duplicate app instances |

---

## Privacy

Your data stays on your machine. Period.

- **100% offline** — No internet connection, no analytics, no telemetry
- **Local storage only** — Everything stored in `%APPDATA%/KeyboardHeatMap/`
- **No keystroke content** — Only counts which keys, not what you typed
- **Aggregated daily totals** — No individual timestamps, just daily summaries
- **You control your data** — Delete the database anytime to reset

---

## Troubleshooting

<details>
<summary><strong>App doesn't start / No tray icon appears</strong></summary>

- Ensure Python 3.8+ is installed
- Run `pip install -r requirements.txt` again
- Try running with `python main.pyw` to see error messages

</details>

<details>
<summary><strong>Heat map shows no data</strong></summary>

- The app only logs keys while running — check it's not paused
- Verify the database exists at `%APPDATA%/KeyboardHeatMap/keystrokes.db`

</details>

<details>
<summary><strong>Keys aren't being captured</strong></summary>

- Some antivirus software blocks keyboard hooks — add an exception
- Run as administrator if issues persist
- Check the tray icon isn't grayed out (paused state)

</details>

<details>
<summary><strong>How do I reset my data?</strong></summary>

Delete the database file:

```
%APPDATA%/KeyboardHeatMap/keystrokes.db
```

</details>

<details>
<summary><strong>Where is my data stored?</strong></summary>

All data is stored locally in `%APPDATA%/KeyboardHeatMap/`. Nothing is transmitted anywhere.

</details>

---

## License

[GNU General Public License v3.0](LICENSE)
