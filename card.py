import os
import tkinter as tk
from tkinter import simpledialog, messagebox
from collections import deque

from PIL import Image, ImageDraw, ImageFont, ImageTk


CARD_WIDTH = 430
MAGIC_COLOR = "#010203"


# -----------------------------
# Мок-данные (заглушки, позже подставишь API)
# -----------------------------
MOCK_DATA = {
    "nickname": "SteelSeal",
    "clan": "TEST",
    "position": "GK",
    "mode": "random",
    "rating": 88,
    "pac": 88,
    "sho": 79,
    "pas": 74,
    "dri": 91,
    "def": 67,
    "phy": 82,
}


def fetch_player_data(nickname):
    """Позже сюда встанет вызов API. Пока заглушка."""
    return {**MOCK_DATA, "nickname": nickname or MOCK_DATA["nickname"]}


# -----------------------------
# Темы: координаты в долях ширины/высоты карточки.
# rating/position — anchor "ls" (левый край, базовая линия НА линии-заглушке),
# остальные — "mm" (по центру точки).
# -----------------------------
THEMES = {
    "white": {
        "file": "templates/Icon.png",
        "rating":   (0.229, 0.237),
        "position": (0.229, 0.303),
        "name":     (0.500, 0.580),
        "clan":     (0.500, 0.612),
        "mode":     (0.500, 0.858),
        "stats_rows": [0.692, 0.752, 0.812],
        "label_x": (0.368, 0.728),
        "value_dx": -0.095,
        "draw_labels": False,   # аббревиатуры уже напечатаны на фоне
        "text":  (135, 115, 35, 255),
        "accent": (135, 115, 35, 255),
    },
    "gold": {
        "file": "templates/Gold.png",
        "rating":   (0.180, 0.260),
        "position": (0.180, 0.360),
        "name":     (0.500, 0.545),
        "clan":     (0.500, 0.578),
        "mode":     (0.500, 0.610),
        "stats_rows": [0.665, 0.720, 0.775],
        "label_x": (0.368, 0.728),
        "value_dx": -0.095,
        "draw_labels": True,    # фон пустой — печатаем PAC/SHO/... сами
        "text":  (60, 40, 10, 255),
        "accent": (50, 30, 5, 255),
    },
    "silver": {
        "file": "templates/Silver.png",
        "rating":   (0.283, 0.300),
        "position": (0.283, 0.362),
        "name":     (0.500, 0.545),
        "clan":     (0.500, 0.578),
        "mode":     (0.500, 0.800),
        "stats_rows": [0.665, 0.720, 0.775],
        "label_x": (0.368, 0.728),
        "value_dx": -0.095,
        "draw_labels": True,
        "text":  (40, 40, 40, 255),
        "accent": (20, 20, 20, 255),
    },
    "bronze": {
        "file": "templates/Bronze.png",
        "rating":   (0.283, 0.300),
        "position": (0.283, 0.362),
        "name":     (0.500, 0.545),
        "clan":     (0.500, 0.578),
        "mode":     (0.500, 0.800),
        "stats_rows": [0.665, 0.720, 0.775],
        "label_x": (0.368, 0.728),
        "value_dx": -0.095,
        "draw_labels": True,
        "text":  (70, 35, 15, 255),
        "accent": (55, 25, 10, 255),
    },
    "blue": {
        "file": "templates/UCL.png",
        "rating":   (0.213, 0.333),
        "position": (0.213, 0.428),
        "name":     (0.500, 0.555),
        "clan":     (0.500, 0.588),
        "mode":     (0.500, 0.820),
        "stats_rows": [0.665, 0.725, 0.785],
        "label_x": (0.387, 0.733),
        "value_dx": -0.105,
        "draw_labels": False,   # на фоне напечатаны VEL/TIR/... — не дублируем
        "text":  (225, 235, 250, 255),
        "accent": (240, 245, 255, 255),
    },
}

THEME_ORDER = ["white", "gold", "silver", "bronze", "blue"]

SIZES = {
    "rating": 40,
    "position": 18,
    "name": 26,
    "clan": 13,
    "mode": 11,
    "value": 20,
    "label": 15,
}

STAT_ORDER = [("PAC", "pac"), ("SHO", "sho"), ("PAS", "pas"),
              ("DRI", "dri"), ("DEF", "def"), ("PHY", "phy")]


# -----------------------------
# Шрифты
# -----------------------------
BOLD_CANDIDATES = [
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]
REG_CANDIDATES = [
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]

_font_cache = {}


def get_font(size, bold=True):
    key = (size, bold)
    if key in _font_cache:
        return _font_cache[key]

    for path in (BOLD_CANDIDATES if bold else REG_CANDIDATES):
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, size)
                _font_cache[key] = font
                return font
            except Exception:
                continue

    font = ImageFont.load_default()
    _font_cache[key] = font
    return font


# -----------------------------
# Фон: flood-fill от углов убирает внешнюю подложку,
# чтобы окно повторяло форму карточки
# -----------------------------
_bg_cache = {}


def _remove_outer_background(img, tol=14):
    img = img.convert("RGBA")
    w, h = img.size
    px = img.load()

    base = px[0, 0]
    visited = bytearray(w * h)
    dq = deque()

    seeds = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    for sx, sy in seeds:
        if not visited[sy * w + sx]:
            visited[sy * w + sx] = 1
            dq.append((sx, sy))

    def close(c):
        return (abs(c[0] - base[0]) <= tol and
                abs(c[1] - base[1]) <= tol and
                abs(c[2] - base[2]) <= tol)

    while dq:
        x, y = dq.popleft()
        px[x, y] = (px[x, y][0], px[x, y][1], px[x, y][2], 0)

        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not visited[ny * w + nx]:
                if close(px[nx, ny]):
                    visited[ny * w + nx] = 1
                    dq.append((nx, ny))

    return img


def get_background(theme_key):
    if theme_key in _bg_cache:
        return _bg_cache[theme_key]

    path = THEMES[theme_key]["file"]
    if not os.path.exists(path):
        raise FileNotFoundError(f"Не найден фон карточки: {path}")

    img = _remove_outer_background(Image.open(path))

    bbox = img.split()[-1].getbbox()
    if bbox:
        img = img.crop(bbox)

    width = CARD_WIDTH
    height = int(img.height * CARD_WIDTH / img.width)
    img = img.resize((width, height), Image.LANCZOS)

    _bg_cache[theme_key] = img
    return img


# -----------------------------
# Рендер
# -----------------------------
def render_card(data, theme_key):
    theme = THEMES[theme_key]
    base = get_background(theme_key)
    w, h = base.size
    scale = w / 430.0

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    text = theme["text"]
    accent = theme["accent"]

    # Верхний блок: ВЫРАВНИВАНИЕ ПО ЛЕВОМУ КРАЮ (anchor "ls"),
    # текст стоит НА линиях-заглушках, как на карточках
    rx, ry = theme["rating"]
    d.text((rx * w, ry * h), str(data.get("rating", "--")),
           font=get_font(int(SIZES["rating"] * scale)),
           fill=accent, anchor="ls")

    px_, py_ = theme["position"]
    d.text((px_ * w, py_ * h), data.get("position", "PVP"),
           font=get_font(int(SIZES["position"] * scale), bold=False),
           fill=text, anchor="ls")

    # Ник и клан — классика FUT: над разделителем
    nx, ny = theme["name"]
    d.text((nx * w, ny * h), data.get("nickname", "PLAYER"),
           font=get_font(int(SIZES["name"] * scale)),
           fill=accent, anchor="mm")

    clan = data.get("clan")
    if clan:
        cx, cy = theme["clan"]
        d.text((cx * w, cy * h), f"[{clan}]",
               font=get_font(int(SIZES["clan"] * scale), bold=False),
               fill=text, anchor="mm")

    # Подпись внизу (над короткой линией)
    mx, my = theme["mode"]
    d.text((mx * w, my * h), data.get("mode", ""),
           font=get_font(int(SIZES["mode"] * scale), bold=False),
           fill=text, anchor="mm")

    # Статы: значение слева от аббревиатуры
    lx = theme["label_x"]
    rows = theme["stats_rows"]
    dx = theme["value_dx"]

    for i, (lab, key) in enumerate(STAT_ORDER):
        col = 0 if i < 3 else 1
        row = i % 3

        x_lab = lx[col]
        vy = rows[row] * h

        d.text(((x_lab + dx) * w, vy), str(int(data.get(key, 0))),
               font=get_font(int(SIZES["value"] * scale)),
               fill=accent, anchor="mm")

        if theme["draw_labels"]:
            d.text((x_lab * w, vy), lab,
                   font=get_font(int(SIZES["label"] * scale), bold=False),
                   fill=text, anchor="mm")

    card = Image.alpha_composite(base, overlay)

    out = Image.new("RGBA", (w, h), (1, 2, 3, 255))
    out = Image.alpha_composite(out, card)
    return out.convert("RGB")


# -----------------------------
# Окно-виджет
# -----------------------------
class FifaCardWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg=MAGIC_COLOR)

        try:
            self.attributes("-transparentcolor", MAGIC_COLOR)
        except Exception:
            pass

        self.theme = "gold"
        self.nickname = MOCK_DATA["nickname"]

        self.photo = None
        self.label = tk.Label(self, bd=0, highlightthickness=0, bg=MAGIC_COLOR)
        self.label.pack()

        self.label.bind("<ButtonPress-1>", self._start_drag)
        self.label.bind("<B1-Motion>", self._on_drag)

        self.bind_all("<Escape>", lambda e: self.destroy())
        self.bind_all("<Button-3>", lambda e: self.destroy())

        for i, key in enumerate(THEME_ORDER, start=1):
            self.bind_all(str(i), lambda e, k=key: self.set_theme(k))

        self.bind_all("r", lambda e: self.refresh())
        self.bind_all("R", lambda e: self.refresh())
        self.bind_all("n", lambda e: self.ask_nickname())
        self.bind_all("N", lambda e: self.ask_nickname())

        self._drag_x = 0
        self._drag_y = 0

        self.refresh()

    def set_theme(self, theme_key):
        self.theme = theme_key
        self.refresh()

    def ask_nickname(self):
        nickname = simpledialog.askstring("Никнейм", "Введи ник игрока:", parent=self)
        if nickname:
            self.nickname = nickname.strip()
            self.refresh()

    def refresh(self):
        try:
            data = fetch_player_data(self.nickname)
            image = render_card(data, self.theme)
        except Exception as e:
            messagebox.showerror("Ошибка карточки", str(e))
            self.destroy()
            return

        self.photo = ImageTk.PhotoImage(image)
        self.label.configure(image=self.photo)
        self.geometry(f"{image.width}x{image.height}")

    def _start_drag(self, event):
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()

    def _on_drag(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.geometry(f"+{x}+{y}")


if __name__ == "__main__":
    FifaCardWindow().mainloop()