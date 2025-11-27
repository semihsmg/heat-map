# Keyboard Heat Map

![Windows](https://img.shields.io/badge/platform-Windows-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)

A system tray app that visualizes your keyboard usage as a glowing heat map.

![Heat Map Preview](assets/screenshot-heatmap.png)

---

## Quick Start

```bash
git clone https://github.com/yourusername/heat-map.git
cd heat-map
pip install -r requirements.txt
pythonw main.pyw
```

---

## Features

| Feature | Description |
|---------|-------------|
| **Heat Map Visualization** | Keys glow brighter based on usage intensity |
| **Time Filters** | View Today, This Week, This Month, or All Time |
| **Top 10 Keys** | Bar chart of your most pressed keys |
| **System Tray** | Runs in background, right-click for menu |
| **Pause/Resume** | Toggle logging anytime |
| **Startup Option** | Auto-launch with Windows |

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
- Try selecting "All Time" instead of "Today"

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
