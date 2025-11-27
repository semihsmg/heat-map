from PIL import Image, ImageDraw


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
    return create_keyboard_icon(64, active=True)


def get_paused_icon() -> Image.Image:
    """Get the paused (not recording) tray icon."""
    return create_keyboard_icon(64, active=False)
