import os
import tkinter as tk
from tkinter import simpledialog, messagebox

from PIL import Image, ImageDraw, ImageFont, ImageTk


CARD_WIDTH = 430          # ширина карточки в пикселях
MAGIC_COLOR = "#010203"   # цвет, который станет прозрачным для окна


# -----------------------------
# Мок-данные (потом заменишь на API)
# -----------------------------
MOCK_DATA = {
    "nickname": "SteelSeal",
    "clan": "TEST",
    "position": "PVP",
    "mode": "МИР КОРАБЛЕЙ",
    "rating": 88,
    "battles": 5321,
    "winrate": 61.4,
    "avg_damage": 72500,
    "avg_frags": 1.08,
    "avg_xp": 1450,
    "max_frags": 6,
}


def fetch_player_data(nickname):
    """Позже сюда вставишь вызов API. Пока мок."""
    return {**MOCK_DATA, "nickname": nickname or MOCK_DATA["nickname"]}


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
# Раскладки под каждый фон.
# Координаты в долях от ширины/высоты карточки: (x, y, size)
# -----------------------------
LAYOUTS = {
    "gold": {
        "file": "templates/Silver.png",
        "name":     (0.500, 0.098, 32),
        "clan":     (0.500, 0.140, 15),
        "rating":   (0.300, 0.320, 62),
        "position": (0.300, 0.408, 19),
        "mode":     (0.500, 0.452, 22),
        "stats": [
            (0.257, 0.685), (0.742, 0.685),
            (0.257, 0.775), (0.742, 0.775),
            (0.257, 0.868), (0.742, 0.868),
        ],
        "stat_value_size": 24,
        "stat_label_size": 24,
        "text":  (240, 226, 170, 255),
        "accent": (255, 216, 120, 255),
    },
    "blue": {
        "file": "templates/UCL.png",
        "name":     (0.630, 0.082, 28),
        "clan":     (0.630, 0.138, 14),
        "rating":   (0.160, 0.100, 50),
        "position": (0.160, 0.172, 15),
        "mode":     (0.500, 0.478, 22),
        "stats": [
            (0.190, 0.775), (0.500, 0.775), (0.815, 0.775),
            (0.190, 0.908), (0.500, 0.908), (0.815, 0.908),
        ],
        "stat_value_size": 22,
        "stat_label_size": 11,
        "text":  (235, 222, 175, 255),
        "accent": (255, 216, 120, 255),
    },
}


def stat_items(data):
    return [
        ("PAC",   f"{int(data.get('battles', 0)):,}"),
        ("DRI",   f"{float(data.get('winrate', 0)):.1f}%"),
        ("SHO",  f"{int(data.get('avg_damage', 0)):,}"),
        ("DEF", f"{float(data.get('avg_frags', 0)):.2f}"),
        ("PAS",  f"{int(data.get('avg_xp', 0)):,}"),
        ("PHY",  f"{int(data.get('max_frags', 0))}"),
    ]


# -----------------------------
# Загрузка фона: убираем белый фон вокруг карточки,
# чтобы окно было именно формы карточки
# -----------------------------
def load_card_background(path):
    img = Image.open(path).convert("RGBA")

    pixels = img.getdata()
    cleaned = []
    for r, g, b, a in pixels:
        if r > 240 and g > 240 and b > 240:
            cleaned.append((r, g, b, 0))
        else:
            cleaned.append((r, g, b, a))
    img.putdata(cleaned)

    alpha = img.split()[-1]
    bbox = alpha.getbbox()
    if bbox:
        img = img.crop(bbox)

    return img


def draw_centered(draw, cx, cy, text, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text((cx - w / 2 - bbox[0], cy - h / 2 - bbox[1]), text, font=font, fill=fill)


# -----------------------------
# Рендер карточки
# -----------------------------
def render_card(data, theme):
    layout = LAYOUTS[theme]
    path = layout["file"]

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Не найден фон карточки: {path}. "
            "Сохрани сгенерированные картинки рядом со скриптом."
        )

    base = load_card_background(path)

    width = CARD_WIDTH
    height = int(base.height * CARD_WIDTH / base.width)
    base = base.resize((width, height), Image.LANCZOS)

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    text_color = layout["text"]
    accent = layout["accent"]

    # Рейтинг
    x, y, size = layout["rating"]
    draw_centered(draw, x * width, y * height, str(data.get("rating", "--")),
                  get_font(size), accent)

    # Позиция / режим
    x, y, size = layout["position"]
    draw_centered(draw, x * width, y * height, data.get("position", "PVP"),
                  get_font(size), text_color)

    # Ник
    x, y, size = layout["name"]
    draw_centered(draw, x * width, y * height, data.get("nickname", "PLAYER"),
                  get_font(size), accent)

    # Клан
    x, y, size = layout["clan"]
    clan = data.get("clan")
    draw_centered(draw, x * width, y * height, f"[{clan}]" if clan else "",
                  get_font(size, bold=False), text_color)

    # Подпись по центру
    x, y, size = layout["mode"]
    draw_centered(draw, x * width, y * height, data.get("mode", ""),
                  get_font(size, bold=False), text_color)

    # Статы
    items = stat_items(data)
    for (cx, cy), (label, value) in zip(layout["stats"], items):
        px = cx * width
        py = cy * height

        draw_centered(draw, px, py - 12, value,
                      get_font(layout["stat_value_size"]), accent)
        draw_centered(draw, px, py + 16, label,
                      get_font(layout["stat_label_size"], bold=False), text_color)

    card = Image.alpha_composite(base, overlay)

    # Кладём карточку на "магический" цвет, который окно сделает прозрачным
    out = Image.new("RGBA", (width, height), (1, 2, 3, 255))
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

        # Прозрачность окна по форме карточки (работает на Windows)
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
        self.bind_all("1", lambda e: self.set_theme("gold"))
        self.bind_all("2", lambda e: self.set_theme("blue"))
        self.bind_all("r", lambda e: self.refresh())
        self.bind_all("R", lambda e: self.refresh())
        self.bind_all("n", lambda e: self.ask_nickname())
        self.bind_all("N", lambda e: self.ask_nickname())

        self._drag_x = 0
        self._drag_y = 0

        self.refresh()

    def set_theme(self, theme):
        self.theme = theme
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