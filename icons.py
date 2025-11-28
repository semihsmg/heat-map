from PIL import Image, ImageDraw
from pathlib import Path


def create_keyboard_icon(size: int = 64, active: bool = True) -> Image.Image:
    """
    Create a simple keyboard icon.

    Args:
        size: Icon size in pixels
        active: If True, icon is colored; if False, icon is grayed out
    """
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Colors
    if active:
        bg_color = (26, 26, 36, 255)       # Dark background
        key_color = (0, 255, 170, 255)     # Accent green
        border_color = (0, 200, 140, 255)  # Slightly darker accent
    else:
        bg_color = (40, 40, 40, 255)       # Gray background
        key_color = (100, 100, 100, 255)   # Gray keys
        border_color = (80, 80, 80, 255)   # Gray border

    # Keyboard body (rounded rectangle)
    margin = size // 8
    body_rect = [margin, margin + size // 6, size - margin, size - margin]
    draw.rounded_rectangle(body_rect, radius=size // 12, fill=bg_color, outline=border_color, width=2)

    # Draw key grid
    key_margin = margin + size // 12
    key_area_width = size - 2 * key_margin
    key_area_height = (size - margin - size // 6 - margin) - size // 8

    key_start_y = margin + size // 6 + size // 16

    # Three rows of keys
    rows = 3
    cols = 4
    key_w = key_area_width // cols - 2
    key_h = key_area_height // rows - 2

    for row in range(rows):
        for col in range(cols):
            x = key_margin + col * (key_w + 2)
            y = key_start_y + row * (key_h + 2)
            draw.rounded_rectangle(
                [x, y, x + key_w, y + key_h],
                radius=2,
                fill=key_color
            )

    return img


def get_active_icon() -> Image.Image:
    """Get the active (recording) tray icon."""
    return create_gradient_icon(128)


def get_paused_icon() -> Image.Image:
    """Get the paused (not recording) tray icon."""
    # Create gradient icon and convert to grayscale
    img = create_gradient_icon(128)
    # Convert to grayscale while preserving alpha
    gray = img.convert('LA').convert('RGBA')
    return gray


def create_gradient_icon(size: int = 256) -> Image.Image:
    """
    Create a keyboard icon with gradient colors (teal → cyan → magenta).
    Used for the application exe icon.
    """
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background
    bg_color = (26, 26, 36, 255)
    border_color = (58, 58, 74, 255)

    # Gradient colors (teal → cyan → magenta)
    colors = [
        (0, 255, 170),    # Teal (top-left)
        (0, 221, 255),    # Cyan (middle)
        (255, 0, 170),    # Magenta (bottom-right)
    ]

    # Keyboard body - 1.5:1 aspect ratio (subtle keyboard shape)
    kb_width = size
    kb_height = int(size / 1.5)
    kb_top = (size - kb_height) // 2  # Center vertically

    body_rect = [0, kb_top, size - 1, kb_top + kb_height - 1]
    draw.rounded_rectangle(body_rect, radius=size // 16, fill=bg_color, outline=border_color, width=max(2, size // 64))

    # Draw key grid with gradient
    rows = 3
    cols = 5
    gap = size // 32

    # Calculate key sizes based on available space with minimal padding
    padding = size // 24
    avail_width = size - 2 * padding
    avail_height = kb_height - 2 * padding

    key_w = (avail_width - (cols - 1) * gap) // cols
    key_h = (avail_height - (rows - 1) * gap) // rows

    # Calculate total grid size and center it
    total_width = cols * key_w + (cols - 1) * gap
    total_height = rows * key_h + (rows - 1) * gap
    start_x = (size - total_width) // 2
    start_y = kb_top + (kb_height - total_height) // 2

    for row in range(rows):
        for col in range(cols):
            # Calculate gradient position (0 to 1)
            t = (row * cols + col) / (rows * cols - 1)

            # Interpolate color
            if t < 0.5:
                t2 = t * 2
                r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * t2)
                g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * t2)
                b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * t2)
            else:
                t2 = (t - 0.5) * 2
                r = int(colors[1][0] + (colors[2][0] - colors[1][0]) * t2)
                g = int(colors[1][1] + (colors[2][1] - colors[1][1]) * t2)
                b = int(colors[1][2] + (colors[2][2] - colors[1][2]) * t2)

            key_color = (r, g, b, 255)

            x = start_x + col * (key_w + gap)
            y = start_y + row * (key_h + gap)
            draw.rounded_rectangle(
                [x, y, x + key_w, y + key_h],
                radius=max(2, size // 32),
                fill=key_color
            )

    return img


def generate_ico_file():
    """Generate the .ico file for the application."""
    # Create 256px icon (max size for ICO format)
    icon = create_gradient_icon(256)

    # Save as ico with explicit size
    ico_path = Path(__file__).parent / 'assets' / 'icon.ico'
    icon.save(ico_path, format='ICO', sizes=[(256, 256)])
    print(f"Icon saved to {ico_path}")
    return ico_path


if __name__ == '__main__':
    generate_ico_file()
