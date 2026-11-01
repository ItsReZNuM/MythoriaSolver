"""
Generate modern vector-style icons using PIL supersampling.
Produces clean, crisp 64x64 PNG icons and a multi-resolution .ico file.
"""
from pathlib import Path
from PIL import Image, ImageDraw

ASSETS_DIR = Path(__file__).parent
ICONS_DIR = ASSETS_DIR / "icons"
ICONS_DIR.mkdir(parents=True, exist_ok=True)

SCALE = 4  # Draw at 256x256, scale to 64x64
SIZE_HIGH = 64 * SCALE
SIZE_TARGET = (64, 64)

WHITE = (255, 255, 255, 255)
CYAN = (56, 189, 248, 255)
GREEN = (34, 197, 94, 255)
RED = (239, 68, 68, 255)
GRAY = (148, 163, 184, 255)
GOLD = (245, 158, 11, 255)


def new_canvas():
    return Image.new("RGBA", (SIZE_HIGH, SIZE_HIGH), (0, 0, 0, 0))


def save_icon(img: Image.Image, name: str):
    resized = img.resize(SIZE_TARGET, Image.Resampling.LANCZOS)
    out_path = ICONS_DIR / f"{name}.png"
    resized.save(out_path, format="PNG")
    return resized


# 1. Dashboard (Layout Grid / Gauge)
def make_dashboard(color=WHITE):
    im = new_canvas()
    d = ImageDraw.Draw(im)
    w = 16
    # 4 rounded rectangles
    d.rounded_rectangle([32, 32, 112, 112], radius=16, fill=color)
    d.rounded_rectangle([144, 32, 224, 112], radius=16, fill=color)
    d.rounded_rectangle([32, 144, 112, 224], radius=16, fill=color)
    d.rounded_rectangle([144, 144, 224, 224], radius=16, fill=color)
    return im


# 2. Settings (Gear)
def make_settings(color=WHITE):
    im = new_canvas()
    d = ImageDraw.Draw(im)
    center = 128
    # Outer gear teeth
    d.ellipse([48, 48, 208, 208], outline=color, width=28)
    import math
    for i in range(8):
        angle = i * (math.pi / 4)
        x1 = center + 80 * math.cos(angle)
        y1 = center + 80 * math.sin(angle)
        x2 = center + 116 * math.cos(angle)
        y2 = center + 116 * math.sin(angle)
        d.line([(x1, y1), (x2, y2)], fill=color, width=32)
    # Inner hole
    d.ellipse([92, 92, 164, 164], fill=(0, 0, 0, 0))
    d.ellipse([96, 96, 160, 160], outline=color, width=12)
    return im


# 3. Solvers (Puzzle / Brain)
def make_solvers(color=WHITE):
    im = new_canvas()
    d = ImageDraw.Draw(im)
    # Modern puzzle piece outline / fill
    d.rounded_rectangle([48, 48, 208, 208], radius=24, outline=color, width=20)
    d.ellipse([104, 24, 152, 72], fill=color)
    d.ellipse([184, 104, 232, 152], fill=color)
    d.ellipse([104, 184, 152, 232], fill=(0, 0, 0, 0), outline=color, width=16)
    return im


# 4. Stealth (Shield)
def make_stealth(color=WHITE):
    im = new_canvas()
    d = ImageDraw.Draw(im)
    pts = [
        (128, 28),
        (216, 60),
        (208, 156),
        (128, 232),
        (48, 156),
        (40, 60),
    ]
    d.polygon(pts, outline=color, fill=None)
    # Draw thick outline
    d.line(pts + [pts[0]], fill=color, width=20, joint="curve")
    # Inner check or line
    d.line([(128, 70), (128, 190)], fill=color, width=16)
    return im


# 5. Tabchi (Megaphone)
def make_tabchi(color=WHITE):
    im = new_canvas()
    d = ImageDraw.Draw(im)
    # Horn polygon
    horn = [(56, 100), (140, 72), (188, 44), (188, 212), (140, 184), (56, 156)]
    d.polygon(horn, fill=color)
    # Handle
    d.rounded_rectangle([80, 156, 116, 220], radius=12, fill=color)
    # Sound waves
    d.arc([196, 76, 244, 180], -60, 60, fill=color, width=18)
    return im


# 6. Stats / Chart
def make_stats(color=WHITE):
    im = new_canvas()
    d = ImageDraw.Draw(im)
    # Axes
    d.line([(40, 36), (40, 220), (228, 220)], fill=color, width=18)
    # Bars
    d.rounded_rectangle([60, 140, 96, 212], radius=8, fill=color)
    d.rounded_rectangle([112, 92, 148, 212], radius=8, fill=color)
    d.rounded_rectangle([164, 48, 200, 212], radius=8, fill=color)
    return im


# 7. Play (Triangle)
def make_play(color=GREEN):
    im = new_canvas()
    d = ImageDraw.Draw(im)
    pts = [(72, 44), (208, 128), (72, 212)]
    d.polygon(pts, fill=color)
    return im


# 8. Stop (Square)
def make_stop(color=RED):
    im = new_canvas()
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([52, 52, 204, 204], radius=24, fill=color)
    return im


# 9. Save (Floppy disk)
def make_save(color=WHITE):
    im = new_canvas()
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([44, 44, 212, 212], radius=20, outline=color, width=18)
    d.rounded_rectangle([76, 44, 180, 110], radius=8, fill=color)
    d.rounded_rectangle([68, 140, 188, 212], radius=8, outline=color, width=14)
    return im


# 10. Refresh / Auto-detect
def make_refresh(color=WHITE):
    im = new_canvas()
    d = ImageDraw.Draw(im)
    d.arc([48, 48, 208, 208], 30, 300, fill=color, width=20)
    # Arrow head
    d.polygon([(190, 60), (226, 96), (170, 114)], fill=color)
    return im


# 11. Folder / Browse
def make_folder(color=WHITE):
    im = new_canvas()
    d = ImageDraw.Draw(im)
    # Tab
    d.rounded_rectangle([44, 60, 120, 100], radius=10, fill=color)
    # Body
    d.rounded_rectangle([44, 88, 212, 204], radius=16, fill=color)
    return im


# 12. Plus (Add)
def make_plus(color=WHITE):
    im = new_canvas()
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([112, 44, 144, 212], radius=12, fill=color)
    d.rounded_rectangle([44, 112, 212, 144], radius=12, fill=color)
    return im


# 13. Trash (Delete)
def make_trash(color=WHITE):
    im = new_canvas()
    d = ImageDraw.Draw(im)
    # Lid
    d.rounded_rectangle([48, 56, 208, 80], radius=8, fill=color)
    d.rounded_rectangle([104, 36, 152, 60], radius=6, fill=color)
    # Can
    pts = [(64, 88), (76, 216), (180, 216), (192, 88)]
    d.polygon(pts, fill=color)
    # Inner stripes
    d.line([(108, 110), (108, 194)], fill=(20, 20, 24, 255), width=10)
    d.line([(148, 110), (148, 194)], fill=(20, 20, 24, 255), width=10)
    return im


# 14. Bolt / Test
def make_bolt(color=GOLD):
    im = new_canvas()
    d = ImageDraw.Draw(im)
    pts = [(148, 24), (64, 136), (124, 136), (108, 232), (192, 120), (132, 120)]
    d.polygon(pts, fill=color)
    return im


# 15. Checkmark
def make_check(color=GREEN):
    im = new_canvas()
    d = ImageDraw.Draw(im)
    pts = [(52, 132), (104, 188), (204, 68)]
    d.line(pts, fill=color, width=28, joint="curve")
    return im


# 16. App Logo (Lightning Diamond)
def make_app_logo():
    im = new_canvas()
    d = ImageDraw.Draw(im)
    # Hexagon / diamond background
    bg_pts = [(128, 16), (228, 72), (228, 184), (128, 240), (28, 184), (28, 72)]
    d.polygon(bg_pts, fill=(30, 41, 59, 255), outline=(56, 189, 248, 255))
    d.line(bg_pts + [bg_pts[0]], fill=(56, 189, 248, 255), width=14, joint="curve")
    # Lightning bolt inside
    bolt = [(144, 48), (76, 140), (128, 140), (112, 216), (180, 116), (128, 116)]
    d.polygon(bolt, fill=(245, 158, 11, 255))
    return im


def generate_all():
    generators = {
        "dashboard": make_dashboard,
        "settings": make_settings,
        "solvers": make_solvers,
        "stealth": make_stealth,
        "tabchi": make_tabchi,
        "stats": make_stats,
        "play": make_play,
        "stop": make_stop,
        "save": make_save,
        "refresh": make_refresh,
        "folder": make_folder,
        "plus": make_plus,
        "trash": make_trash,
        "bolt": make_bolt,
        "check": make_check,
    }

    for name, gen in generators.items():
        img = gen(WHITE)
        save_icon(img, name)
        # Also accent variant
        if name in ("dashboard", "settings", "solvers", "stealth", "tabchi", "stats"):
            img_cyan = gen(CYAN)
            save_icon(img_cyan, f"{name}_active")

    # Generate app logo & ico
    app_img = make_app_logo()
    app_png = app_img.resize((128, 128), Image.Resampling.LANCZOS)
    app_png.save(ASSETS_DIR / "app_icon.png", format="PNG")

    # Save multi-size .ico
    ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    ico_imgs = [app_img.resize(s, Image.Resampling.LANCZOS) for s in ico_sizes]
    ico_imgs[0].save(
        ASSETS_DIR / "app_icon.ico",
        format="ICO",
        sizes=ico_sizes,
        append_images=ico_imgs[1:],
    )
    print("All icons successfully generated in assets/!")


if __name__ == "__main__":
    generate_all()
