import tempfile
import webbrowser
import json
from pathlib import Path
import database


# Full-size keyboard layout definition
# Each row is a list of (key_id, display_label, width_units)
# Width units: 1 = standard key, 1.25, 1.5, 1.75, 2, 2.25, etc.

KEYBOARD_LAYOUT = {
    'main': [
        # Row 0: Function row
        [
            ('Esc', 'Esc', 1),
            ('_gap', '', 0.5),
            ('F1', 'F1', 1), ('F2', 'F2', 1), ('F3', 'F3', 1), ('F4', 'F4', 1),
            ('_gap', '', 0.25),
            ('F5', 'F5', 1), ('F6', 'F6', 1), ('F7', 'F7', 1), ('F8', 'F8', 1),
            ('_gap', '', 0.25),
            ('F9', 'F9', 1), ('F10', 'F10', 1), ('F11', 'F11', 1), ('F12', 'F12', 1),
        ],
        # Row 1: Number row
        [
            ('`', '`', 1), ('1', '1', 1), ('2', '2', 1), ('3', '3', 1), ('4', '4', 1),
            ('5', '5', 1), ('6', '6', 1), ('7', '7', 1), ('8', '8', 1), ('9', '9', 1),
            ('0', '0', 1), ('-', '-', 1), ('=', '=', 1), ('Backspace', 'Backspace', 2),
        ],
        # Row 2: QWERTY row
        [
            ('Tab', 'Tab', 1.5),
            ('q', 'Q', 1), ('w', 'W', 1), ('e', 'E', 1), ('r', 'R', 1), ('t', 'T', 1),
            ('y', 'Y', 1), ('u', 'U', 1), ('i', 'I', 1), ('o', 'O', 1), ('p', 'P', 1),
            ('[', '[', 1), (']', ']', 1), ('\\', '\\', 1.5),
        ],
        # Row 3: Home row
        [
            ('CapsLock', 'Caps', 1.75),
            ('a', 'A', 1), ('s', 'S', 1), ('d', 'D', 1), ('f', 'F', 1), ('g', 'G', 1),
            ('h', 'H', 1), ('j', 'J', 1), ('k', 'K', 1), ('l', 'L', 1),
            (';', ';', 1), ("'", "'", 1), ('Enter', 'Enter', 2.25),
        ],
        # Row 4: Shift row
        [
            ('Shift', 'Shift', 2.25),
            ('z', 'Z', 1), ('x', 'X', 1), ('c', 'C', 1), ('v', 'V', 1), ('b', 'B', 1),
            ('n', 'N', 1), ('m', 'M', 1), (',', ',', 1), ('.', '.', 1), ('/', '/', 1),
            ('Shift_R', 'Shift', 2.75),
        ],
        # Row 5: Bottom row
        [
            ('Ctrl', 'Ctrl', 1.25), ('Win', 'Win', 1.25), ('Alt', 'Alt', 1.25),
            ('Space', 'Space', 6.25),
            ('Alt_R', 'Alt', 1.25), ('Win_R', 'Win', 1.25), ('Menu', 'Menu', 1.25), ('Ctrl_R', 'Ctrl', 1.25),
        ],
    ],
    'nav': [
        # Row 0: Empty (aligns with function row)
        [],
        # Row 1: Insert/Delete cluster
        [('Insert', 'Ins', 1), ('Home', 'Home', 1), ('PageUp', 'PgUp', 1)],
        # Row 2
        [('Delete', 'Del', 1), ('End', 'End', 1), ('PageDown', 'PgDn', 1)],
        # Row 3: Empty
        [],
        # Row 4: Arrow up
        [('_gap', '', 1), ('Up', '\u2191', 1), ('_gap', '', 1)],
        # Row 5: Arrow cluster
        [('Left', '\u2190', 1), ('Down', '\u2193', 1), ('Right', '\u2192', 1)],
    ],
    'numpad': [
        # Row 0: Empty
        [],
        # Row 1
        [('NumLock', 'Num', 1), ('Num/', '/', 1), ('Num*', '*', 1), ('Num-', '-', 1)],
        # Row 2
        [('Num7', '7', 1), ('Num8', '8', 1), ('Num9', '9', 1), ('Num+', '+', 1, 2)],  # + is 2 units tall
        # Row 3
        [('Num4', '4', 1), ('Num5', '5', 1), ('Num6', '6', 1)],
        # Row 4
        [('Num1', '1', 1), ('Num2', '2', 1), ('Num3', '3', 1), ('NumEnter', 'Ent', 1, 2)],  # Enter is 2 units tall
        # Row 5
        [('Num0', '0', 2), ('Num.', '.', 1)],
    ]
}


def generate_html() -> str:
    """Generate the heat map HTML with all-time data."""
    key_counts = database.get_key_counts('all')
    top_keys = key_counts.most_common(10)
    stats = database.get_statistics()

    max_count = max(key_counts.values()) if key_counts else 1

    # Format statistics
    tracking_since = stats['tracking_since'] or 'N/A'
    most_active_day = stats['most_active_day']
    most_active_str = f"{most_active_day[0]} ({most_active_day[1]:,})" if most_active_day else 'N/A'

    # Convert counts to JSON for JavaScript
    counts_json = json.dumps(dict(key_counts))
    top_keys_json = json.dumps(top_keys)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Keyboard Heat Map</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Orbitron:wght@500;700&display=swap" rel="stylesheet">
    <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
    <style>
        :root {{
            --bg-dark: #0a0a0f;
            --bg-keyboard: #1a1a24;
            --key-bg: #2a2a38;
            --key-border: #3a3a4a;
            --key-text: #8888aa;
            --glow-color: #00ffaa;
            --glow-color-mid: #00ddff;
            --glow-color-high: #ff00aa;
            --accent: #00ffaa;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'JetBrains Mono', monospace;
            background: var(--bg-dark);
            min-height: 100vh;
            color: #fff;
            overflow-x: hidden;
        }}

        .background {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background:
                radial-gradient(ellipse at 20% 80%, rgba(0, 255, 170, 0.08) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 20%, rgba(255, 0, 170, 0.06) 0%, transparent 50%),
                radial-gradient(ellipse at 50% 50%, rgba(0, 221, 255, 0.04) 0%, transparent 60%);
            pointer-events: none;
            z-index: -1;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 40px 20px;
        }}

        header {{
            text-align: center;
            margin-bottom: 40px;
        }}

        h1 {{
            font-family: 'Orbitron', sans-serif;
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--glow-color), var(--glow-color-mid), var(--glow-color-high));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 40px rgba(0, 255, 170, 0.3);
            letter-spacing: 4px;
            margin-bottom: 10px;
        }}

        .subtitle {{
            color: var(--key-text);
            font-size: 0.9rem;
            letter-spacing: 2px;
        }}

        .stats-section {{
            display: flex;
            justify-content: center;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: var(--key-bg);
            border: 1px solid var(--key-border);
            border-radius: 8px;
            padding: 14px 20px;
            width: fit-content;
            white-space: nowrap;
            text-align: center;
            box-shadow:
                0 4px 0 #1a1a24,
                0 6px 10px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
        }}

        .stat-card:hover {{
            transform: translateY(-2px);
            box-shadow:
                0 6px 0 #1a1a24,
                0 8px 15px rgba(0, 0, 0, 0.4);
        }}

        .stat-value {{
            font-family: 'Orbitron', sans-serif;
            font-size: 1.4rem;
            font-weight: 700;
            color: var(--accent);
            text-shadow: 0 0 15px rgba(0, 255, 170, 0.3);
        }}

        .stat-label {{
            color: var(--key-text);
            font-size: 0.75rem;
            letter-spacing: 0.5px;
            margin-top: 6px;
        }}

        .keyboard-container {{
            display: flex;
            justify-content: center;
            margin-bottom: 30px;
        }}

        .keyboard {{
            background: var(--bg-keyboard);
            border-radius: 16px;
            padding: 20px;
            display: flex;
            gap: 20px;
            box-shadow:
                0 20px 60px rgba(0, 0, 0, 0.5),
                inset 0 1px 0 rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}

        .keyboard-section {{
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}

        .keyboard-row {{
            display: flex;
            gap: 4px;
            height: 48px;
        }}

        .key {{
            background: var(--key-bg);
            border: 1px solid var(--key-border);
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.7rem;
            font-weight: 600;
            color: var(--key-text);
            position: relative;
            transition: all 0.3s ease;
            box-shadow:
                0 4px 0 #1a1a24,
                0 6px 10px rgba(0, 0, 0, 0.3);
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
        }}

        .key:hover {{
            transform: translateY(-2px);
            box-shadow:
                0 6px 0 #1a1a24,
                0 8px 15px rgba(0, 0, 0, 0.4);
        }}

        .key.glow-1 {{
            background: linear-gradient(180deg, #2a3a38 0%, #2a2a38 100%);
            border-color: rgba(0, 255, 170, 0.3);
            color: rgba(0, 255, 170, 0.8);
            box-shadow:
                0 4px 0 #1a2a28,
                0 6px 10px rgba(0, 0, 0, 0.3),
                0 0 15px rgba(0, 255, 170, 0.1);
        }}

        .key.glow-2 {{
            background: linear-gradient(180deg, #2a4a45 0%, #2a3a38 100%);
            border-color: rgba(0, 255, 170, 0.5);
            color: rgba(0, 255, 170, 0.9);
            box-shadow:
                0 4px 0 #1a3a35,
                0 6px 10px rgba(0, 0, 0, 0.3),
                0 0 20px rgba(0, 255, 170, 0.2);
        }}

        .key.glow-3 {{
            background: linear-gradient(180deg, #2a5a52 0%, #2a4a45 100%);
            border-color: rgba(0, 221, 255, 0.5);
            color: #00ffaa;
            box-shadow:
                0 4px 0 #1a4a42,
                0 6px 10px rgba(0, 0, 0, 0.3),
                0 0 25px rgba(0, 255, 170, 0.3);
        }}

        .key.glow-4 {{
            background: linear-gradient(180deg, #2a6a5f 0%, #2a5a52 100%);
            border-color: rgba(0, 221, 255, 0.7);
            color: #00ffdd;
            text-shadow: 0 0 10px rgba(0, 255, 170, 0.5);
            box-shadow:
                0 4px 0 #1a5a4f,
                0 6px 10px rgba(0, 0, 0, 0.3),
                0 0 30px rgba(0, 221, 255, 0.3);
        }}

        .key.glow-5 {{
            background: linear-gradient(180deg, #3a7a6f 0%, #2a6a5f 100%);
            border-color: rgba(0, 221, 255, 0.9);
            color: #00ffff;
            text-shadow: 0 0 15px rgba(0, 221, 255, 0.7);
            box-shadow:
                0 4px 0 #2a6a5f,
                0 6px 10px rgba(0, 0, 0, 0.3),
                0 0 35px rgba(0, 221, 255, 0.4);
        }}

        .key.glow-max {{
            background: linear-gradient(180deg, #5a4a6a 0%, #4a3a5a 100%);
            border-color: rgba(255, 0, 170, 0.9);
            color: #ff44dd;
            text-shadow: 0 0 20px rgba(255, 0, 170, 0.8);
            box-shadow:
                0 4px 0 #3a2a4a,
                0 6px 10px rgba(0, 0, 0, 0.3),
                0 0 40px rgba(255, 0, 170, 0.5);
            animation: pulse 2s ease-in-out infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ box-shadow: 0 4px 0 #3a2a4a, 0 6px 10px rgba(0, 0, 0, 0.3), 0 0 40px rgba(255, 0, 170, 0.5); }}
            50% {{ box-shadow: 0 4px 0 #3a2a4a, 0 6px 10px rgba(0, 0, 0, 0.3), 0 0 60px rgba(255, 0, 170, 0.7); }}
        }}

        .key-count {{
            position: absolute;
            bottom: 2px;
            right: 4px;
            font-size: 0.5rem;
            opacity: 0.7;
        }}

        .top-keys-section {{
            text-align: center;
        }}

        .top-keys-title {{
            font-family: 'Orbitron', sans-serif;
            font-size: 0.75rem;
            color: var(--key-text);
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 16px;
        }}

        .top-keys-list {{
            display: flex;
            justify-content: center;
            gap: 12px;
            flex-wrap: wrap;
        }}

        .top-key-card {{
            background: var(--key-bg);
            border: 1px solid var(--key-border);
            border-radius: 8px;
            padding: 12px 16px;
            min-width: 90px;
            text-align: center;
            box-shadow:
                0 4px 0 #1a1a24,
                0 6px 10px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
        }}

        .top-key-card:hover {{
            transform: translateY(-2px);
            box-shadow:
                0 6px 0 #1a1a24,
                0 8px 15px rgba(0, 0, 0, 0.4);
        }}

        .top-key-card.glow-1 {{
            background: linear-gradient(180deg, #2a3a38 0%, #2a2a38 100%);
            border-color: rgba(0, 255, 170, 0.3);
            box-shadow: 0 4px 0 #1a2a28, 0 6px 10px rgba(0, 0, 0, 0.3), 0 0 15px rgba(0, 255, 170, 0.1);
        }}

        .top-key-card.glow-2 {{
            background: linear-gradient(180deg, #2a4a45 0%, #2a3a38 100%);
            border-color: rgba(0, 255, 170, 0.5);
            box-shadow: 0 4px 0 #1a3a35, 0 6px 10px rgba(0, 0, 0, 0.3), 0 0 20px rgba(0, 255, 170, 0.2);
        }}

        .top-key-card.glow-3 {{
            background: linear-gradient(180deg, #2a5a52 0%, #2a4a45 100%);
            border-color: rgba(0, 221, 255, 0.5);
            box-shadow: 0 4px 0 #1a4a42, 0 6px 10px rgba(0, 0, 0, 0.3), 0 0 25px rgba(0, 255, 170, 0.3);
        }}

        .top-key-card.glow-4 {{
            background: linear-gradient(180deg, #2a6a5f 0%, #2a5a52 100%);
            border-color: rgba(0, 221, 255, 0.7);
            box-shadow: 0 4px 0 #1a5a4f, 0 6px 10px rgba(0, 0, 0, 0.3), 0 0 30px rgba(0, 221, 255, 0.3);
        }}

        .top-key-card.glow-5 {{
            background: linear-gradient(180deg, #3a7a6f 0%, #2a6a5f 100%);
            border-color: rgba(0, 221, 255, 0.9);
            box-shadow: 0 4px 0 #2a6a5f, 0 6px 10px rgba(0, 0, 0, 0.3), 0 0 35px rgba(0, 221, 255, 0.4);
        }}

        .top-key-card.glow-max {{
            background: linear-gradient(180deg, #5a4a6a 0%, #4a3a5a 100%);
            border-color: rgba(255, 0, 170, 0.9);
            box-shadow: 0 4px 0 #3a2a4a, 0 6px 10px rgba(0, 0, 0, 0.3), 0 0 40px rgba(255, 0, 170, 0.5);
            animation: pulse 2s ease-in-out infinite;
        }}

        .top-key-header {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            margin-bottom: 4px;
        }}

        .top-key-rank {{
            font-family: 'Orbitron', sans-serif;
            font-size: 0.65rem;
            color: var(--key-text);
        }}

        .top-key-name {{
            font-weight: 700;
            font-size: 1rem;
            color: #fff;
        }}

        .top-key-count {{
            font-family: 'Orbitron', sans-serif;
            font-size: 0.8rem;
            color: var(--accent);
        }}

        .download-section {{
            display: flex;
            justify-content: center;
            margin: 30px 0;
        }}

        .download-btn {{
            display: flex;
            align-items: center;
            gap: 8px;
            background: var(--key-bg);
            border: 1px solid var(--key-border);
            border-radius: 8px;
            padding: 12px 24px;
            color: var(--key-text);
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            box-shadow:
                0 4px 0 #1a1a24,
                0 6px 10px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
        }}

        .download-btn:hover {{
            transform: translateY(-2px);
            color: var(--accent);
            border-color: rgba(0, 255, 170, 0.3);
            box-shadow:
                0 6px 0 #1a1a24,
                0 8px 15px rgba(0, 0, 0, 0.4),
                0 0 15px rgba(0, 255, 170, 0.1);
        }}

        .download-btn:active {{
            transform: translateY(2px);
            box-shadow:
                0 2px 0 #1a1a24,
                0 4px 8px rgba(0, 0, 0, 0.3);
        }}

        .download-btn:disabled {{
            opacity: 0.6;
            cursor: not-allowed;
        }}

        .download-btn svg {{
            width: 18px;
            height: 18px;
        }}

        .footer {{
            text-align: center;
            margin-top: 50px;
            color: var(--key-text);
            font-size: 0.75rem;
        }}

        .footer-link {{
            color: var(--key-text);
            text-decoration: none;
            transition: color 0.3s ease;
        }}

        .footer-link:hover {{
            color: var(--accent);
        }}
    </style>
</head>
<body>
    <div class="background"></div>
    <div class="container">
        <header>
            <h1>KEYBOARD HEAT MAP</h1>
            <p class="subtitle">Your typing patterns visualized</p>
        </header>

        <div class="stats-section">
            <div class="stat-card">
                <div class="stat-value">{stats['total_keystrokes']:,}</div>
                <div class="stat-label">Total Keystrokes</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['keys_per_day']:,}</div>
                <div class="stat-label">Keys per Day</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['keys_per_hour']:,}</div>
                <div class="stat-label">Keys per Hour</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{tracking_since}</div>
                <div class="stat-label">Tracking Since</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['days_tracked']}</div>
                <div class="stat-label">Days Tracked</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{most_active_str}</div>
                <div class="stat-label">Most Active Day</div>
            </div>
        </div>

        <div class="keyboard-container">
            <div class="keyboard">
                <div class="keyboard-section" id="main-section"></div>
                <div class="keyboard-section" id="nav-section"></div>
                <div class="keyboard-section" id="numpad-section"></div>
            </div>
        </div>

        <div class="download-section" id="download-section">
            <button class="download-btn" id="download-btn" onclick="downloadScreenshot()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                Download
            </button>
        </div>

        <div class="top-keys-section">
            <div class="top-keys-title">Top 10 Keys</div>
            <div class="top-keys-list" id="top-keys-list"></div>
        </div>

        <footer class="footer">
            <a href="https://github.com/semihsmg/heat-map" target="_blank" class="footer-link">
                <svg height="16" width="16" viewBox="0 0 16 16" fill="currentColor" style="vertical-align: middle; margin-right: 6px;">
                    <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path>
                </svg>
                semihsmg/heat-map
            </a>
        </footer>
    </div>

    <script>
        const keyCounts = {counts_json};
        const topKeys = {top_keys_json};
        const maxCount = {max_count};

        const keyboardLayout = {{
            main: [
                [
                    ['Esc', 'Esc', 1],
                    ['_gap', '', 0.5],
                    ['F1', 'F1', 1], ['F2', 'F2', 1], ['F3', 'F3', 1], ['F4', 'F4', 1],
                    ['_gap', '', 0.25],
                    ['F5', 'F5', 1], ['F6', 'F6', 1], ['F7', 'F7', 1], ['F8', 'F8', 1],
                    ['_gap', '', 0.25],
                    ['F9', 'F9', 1], ['F10', 'F10', 1], ['F11', 'F11', 1], ['F12', 'F12', 1],
                ],
                [
                    ['`', '`', 1], ['1', '1', 1], ['2', '2', 1], ['3', '3', 1], ['4', '4', 1],
                    ['5', '5', 1], ['6', '6', 1], ['7', '7', 1], ['8', '8', 1], ['9', '9', 1],
                    ['0', '0', 1], ['-', '-', 1], ['=', '=', 1], ['Backspace', 'Backspace', 2],
                ],
                [
                    ['Tab', 'Tab', 1.5],
                    ['q', 'Q', 1], ['w', 'W', 1], ['e', 'E', 1], ['r', 'R', 1], ['t', 'T', 1],
                    ['y', 'Y', 1], ['u', 'U', 1], ['i', 'I', 1], ['o', 'O', 1], ['p', 'P', 1],
                    ['[', '[', 1], [']', ']', 1], ['\\\\', '\\\\', 1.5],
                ],
                [
                    ['CapsLock', 'Caps', 1.75],
                    ['a', 'A', 1], ['s', 'S', 1], ['d', 'D', 1], ['f', 'F', 1], ['g', 'G', 1],
                    ['h', 'H', 1], ['j', 'J', 1], ['k', 'K', 1], ['l', 'L', 1],
                    [';', ';', 1], ["'", "'", 1], ['Enter', 'Enter', 2.25],
                ],
                [
                    ['Shift', 'Shift', 2.25],
                    ['z', 'Z', 1], ['x', 'X', 1], ['c', 'C', 1], ['v', 'V', 1], ['b', 'B', 1],
                    ['n', 'N', 1], ['m', 'M', 1], [',', ',', 1], ['.', '.', 1], ['/', '/', 1],
                    ['Shift_R', 'Shift', 2.75],
                ],
                [
                    ['Ctrl', 'Ctrl', 1.25], ['Win', 'Win', 1.25], ['Alt', 'Alt', 1.25],
                    ['Space', 'Space', 6.25],
                    ['Alt_R', 'Alt', 1.25], ['Win_R', 'Win', 1.25], ['Menu', 'Menu', 1.25], ['Ctrl_R', 'Ctrl', 1.25],
                ],
            ],
            nav: [
                [],
                [['Insert', 'Ins', 1], ['Home', 'Home', 1], ['PageUp', 'PgUp', 1]],
                [['Delete', 'Del', 1], ['End', 'End', 1], ['PageDown', 'PgDn', 1]],
                [],
                [['_gap', '', 1], ['Up', '\u2191', 1], ['_gap', '', 1]],
                [['Left', '\u2190', 1], ['Down', '\u2193', 1], ['Right', '\u2192', 1]],
            ],
            numpad: [
                [],
                [['NumLock', 'Num', 1], ['Num/', '/', 1], ['Num*', '*', 1], ['Num-', '-', 1]],
                [['Num7', '7', 1], ['Num8', '8', 1], ['Num9', '9', 1], ['Num+', '+', 1, 2]],
                [['Num4', '4', 1], ['Num5', '5', 1], ['Num6', '6', 1]],
                [['Num1', '1', 1], ['Num2', '2', 1], ['Num3', '3', 1], ['NumEnter', 'Ent', 1, 2]],
                [['Num0', '0', 2], ['Num.', '.', 1]],
            ]
        }};

        function getGlowClass(count) {{
            if (count === 0) return '';
            const ratio = count / maxCount;
            if (ratio >= 0.9) return 'glow-max';
            if (ratio >= 0.7) return 'glow-5';
            if (ratio >= 0.5) return 'glow-4';
            if (ratio >= 0.3) return 'glow-3';
            if (ratio >= 0.15) return 'glow-2';
            return 'glow-1';
        }}

        function renderKeyboard(section, layout) {{
            const container = document.getElementById(section + '-section');
            container.innerHTML = '';

            layout.forEach((row, rowIndex) => {{
                if (row.length === 0) {{
                    const emptyRow = document.createElement('div');
                    emptyRow.className = 'keyboard-row';
                    emptyRow.innerHTML = '<div style="height: 48px;"></div>';
                    container.appendChild(emptyRow);
                    return;
                }}

                const rowDiv = document.createElement('div');
                rowDiv.className = 'keyboard-row';

                row.forEach(keyDef => {{
                    const [keyId, label, width, height] = keyDef;

                    if (keyId === '_gap') {{
                        const gap = document.createElement('div');
                        gap.style.width = (width * 48) + 'px';
                        rowDiv.appendChild(gap);
                        return;
                    }}

                    const keyDiv = document.createElement('div');
                    keyDiv.className = 'key';
                    keyDiv.style.width = (width * 48 + (width - 1) * 4) + 'px';

                    if (height && height > 1) {{
                        keyDiv.style.height = (height * 48 + (height - 1) * 4) + 'px';
                        keyDiv.style.position = 'absolute';
                        keyDiv.style.marginLeft = (row.indexOf(keyDef) * 52) + 'px';
                    }}

                    const count = keyCounts[keyId] || keyCounts[keyId.toLowerCase()] || 0;
                    const glowClass = getGlowClass(count);
                    if (glowClass) keyDiv.classList.add(glowClass);

                    keyDiv.innerHTML = label;
                    if (count > 0) {{
                        keyDiv.innerHTML += '<span class="key-count">' + count.toLocaleString() + '</span>';
                    }}

                    keyDiv.title = keyId + ': ' + count.toLocaleString() + ' presses';
                    rowDiv.appendChild(keyDiv);
                }});

                container.appendChild(rowDiv);
            }});
        }}

        function renderTopKeys() {{
            const container = document.getElementById('top-keys-list');
            container.innerHTML = '';

            if (topKeys.length === 0) {{
                container.innerHTML = '<p style="color: var(--key-text);">No data yet</p>';
                return;
            }}

            topKeys.forEach((item, index) => {{
                const [key, count] = item;
                const glowClass = getGlowClass(count);

                // Capitalize single letter keys
                const displayKey = key.length === 1 && key.match(/[a-z]/i) ? key.toUpperCase() : key;

                const card = document.createElement('div');
                card.className = 'top-key-card' + (glowClass ? ' ' + glowClass : '');
                card.innerHTML = `
                    <div class="top-key-header">
                        <span class="top-key-rank">#${{index + 1}}</span>
                        <span class="top-key-name">${{displayKey}}</span>
                    </div>
                    <div class="top-key-count">${{count.toLocaleString()}}</div>
                `;
                container.appendChild(card);
            }});
        }}

        // Render everything
        renderKeyboard('main', keyboardLayout.main);
        renderKeyboard('nav', keyboardLayout.nav);
        renderKeyboard('numpad', keyboardLayout.numpad);
        renderTopKeys();

        // Download screenshot with watermark
        async function downloadScreenshot() {{
            const btn = document.getElementById('download-btn');
            const downloadSection = document.getElementById('download-section');
            const container = document.querySelector('.container');

            btn.disabled = true;
            btn.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                Capturing...
            `;

            // Hide download button for clean screenshot
            downloadSection.style.display = 'none';

            try {{
                // Clone the container and position at 0,0 to fix html2canvas centering issues
                const clone = container.cloneNode(true);
                clone.style.position = 'absolute';
                clone.style.left = '0';
                clone.style.top = '0';
                clone.style.margin = '0';
                clone.style.padding = '80px';
                clone.style.zIndex = '-9999';
                // Apply background gradient directly to clone
                clone.style.background = 'radial-gradient(ellipse at 20% 80%, rgba(0, 255, 170, 0.08) 0%, transparent 50%), radial-gradient(ellipse at 80% 20%, rgba(255, 0, 170, 0.06) 0%, transparent 50%), radial-gradient(ellipse at 50% 50%, rgba(0, 221, 255, 0.04) 0%, transparent 60%), #0a0a0f';
                document.body.appendChild(clone);

                // Hide download button in clone
                const cloneDownloadSection = clone.querySelector('#download-section');
                if (cloneDownloadSection) cloneDownloadSection.style.display = 'none';

                const canvas = await html2canvas(clone, {{
                    backgroundColor: '#0a0a0f',
                    scale: 2,
                    useCORS: true,
                    allowTaint: true,
                    foreignObjectRendering: true
                }});

                // Remove clone
                document.body.removeChild(clone);

                // Download the image with timestamp
                const now = new Date();
                const timestamp = now.toISOString().slice(0, 19).replace('T', '_').replace(/:/g, '-');
                const a = document.createElement('a');
                a.href = canvas.toDataURL('image/png');
                a.download = `keyboard-heatmap-${{timestamp}}.png`;
                a.click();
            }} catch (error) {{
                console.error('Download failed:', error);
            }} finally {{
                // Restore download button
                downloadSection.style.display = 'flex';
                btn.disabled = false;
                btn.innerHTML = `
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="7 10 12 15 17 10"></polyline>
                        <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                    Download
                `;
            }}
        }}
    </script>
</body>
</html>'''

    return html


def generate_report() -> Path:
    """Generate the heat map report and return the file path."""
    html = generate_html()

    temp_dir = Path(tempfile.gettempdir())
    report_path = temp_dir / 'keyboard_heatmap.html'

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html)

    return report_path


def open_report():
    """Generate and open the heat map report in the default browser."""
    report_path = generate_report()
    webbrowser.open(f'file:///{report_path}')
