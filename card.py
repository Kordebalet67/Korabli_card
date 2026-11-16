import customtkinter as ctk
from tkinter import simpledialog


# -----------------------------
# Мок-данные для демонстрации
# -----------------------------
MOCK_DATA = {
    "nickname": "SteelSeal",
    "clan": "TEST",
    "subtitle": "Мир кораблей • PVP",
    "mode": "PVP",
    "rating": 88,
    "battles": 5321,
    "winrate": 61.4,
    "avg_damage": 72500,
    "avg_frags": 1.08,
    "avg_xp": 1450,
    "max_frags": 6,
}


# -----------------------------
# Вспомогательные функции
# -----------------------------
def calculate_rating(data):
    """
    Простой синтетический рейтинг, если нет WN8/PR.
    Можно потом заменить на реальный WN8 или Personal Rating.
    """
    battles = int(data.get("battles", 0))
    if battles == 0:
        return 50

    winrate = float(data.get("winrate", 50))
    avg_damage = float(data.get("avg_damage", 0))
    avg_frags = float(data.get("avg_frags", 0))
    avg_xp = float(data.get("avg_xp", 0))

    score = 30

    # Бонус за винрейт
    score += max(0, min(30, (winrate - 45) * 2.0))

    # Бонус за средний урон
    score += max(0, min(25, avg_damage / 3500))

    # Бонус за фраги
    score += max(0, min(10, avg_frags * 6))

    # Бонус за опыт
    score += max(0, min(5, avg_xp / 500))

    return int(max(1, min(99, score)))


def rating_color(rating):
    """
    Цвет карточки/рейтинга в стиле разных уровней.
    """
    if rating >= 90:
        return "#fbbf24"  # золотой
    if rating >= 80:
        return "#a78bfa"  # фиолетовый
    if rating >= 70:
        return "#38bdf8"  # синий
    if rating >= 60:
        return "#34d399"  # зелёный
    return "#9ca3af"      # серый


def fetch_player_data(nickname):
    """
    Пока возвращаем мок-данные.

    Потом здесь будет вызов API:
    1. найти аккаунт по нику
    2. получить account_id
    3. получить статистику
    4. вернуть словарь для карточки
    """
    return {
        **MOCK_DATA,
        "nickname": nickname or MOCK_DATA["nickname"],
    }


# -----------------------------
# Виджет-карточка
# -----------------------------
class PlayerCard(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Убираем рамку окна
        self.overrideredirect(True)

        # Поверх всех окон
        self.attributes("-topmost", True)

        # Размер и позиция окна
        self.geometry("430x660+140+80")

        # Цвет фона окна.
        # Если хочешь прозрачность на Windows, можно оставить этот же цвет
        # и задать -transparentcolor ниже.
        self.configure(fg_color="#05070f")

        # Опциональная прозрачность фона на Windows.
        # Если будут артефакты — просто убери этот try-блок.
        try:
            self.attributes("-transparentcolor", "#05070f")
        except Exception:
            pass

        self.current_nickname = MOCK_DATA["nickname"]

        # Основная карточка
        self.card = ctk.CTkFrame(
            self,
            corner_radius=30,
            fg_color="#0b1220",
            border_width=2,
            border_color="#d4af37",
        )
        self.card.pack(fill="both", expand=True, padx=18, pady=18)

        self._drag_x = 0
        self._drag_y = 0

        # Показываем данные
        self.show_data(fetch_player_data(self.current_nickname))

        # Управление
        self.bind_all("<Escape>", lambda e: self.destroy())
        self.bind_all("<Button-3>", lambda e: self.destroy())  # ПКМ закрыть
        self.bind_all("r", lambda e: self.refresh())
        self.bind_all("R", lambda e: self.refresh())
        self.bind_all("n", lambda e: self.ask_nickname())
        self.bind_all("N", lambda e: self.ask_nickname())

    def refresh(self):
        data = fetch_player_data(self.current_nickname)
        self.show_data(data)

    def ask_nickname(self):
        nickname = simpledialog.askstring(
            "Никнейм",
            "Введи ник игрока:",
            parent=self,
        )

        if nickname:
            self.current_nickname = nickname.strip()
            self.refresh()

    def show_data(self, data):
        # Очищаем старое содержимое карточки
        for child in self.card.winfo_children():
            child.destroy()

        rating = int(data.get("rating") or calculate_rating(data))
        color = rating_color(rating)

        # -----------------------------
        # Верхняя часть: рейтинг + ник
        # -----------------------------
        header = ctk.CTkFrame(self.card, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(22, 10))

        # Левый блок с рейтингом
        rating_box = ctk.CTkFrame(
            header,
            fg_color=color,
            corner_radius=22,
            width=125,
        )
        rating_box.pack(side="left", fill="y", padx=(0, 16))
        rating_box.pack_propagate(False)

        ctk.CTkLabel(
            rating_box,
            text=str(rating),
            font=ctk.CTkFont(size=52, weight="bold"),
            text_color="#081018",
        ).pack(pady=(18, 0))

        ctk.CTkLabel(
            rating_box,
            text="OVR",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#081018",
        ).pack()

        ctk.CTkLabel(
            rating_box,
            text=data.get("mode", "PVP"),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#081018",
        ).pack(pady=(0, 16))

        # Правый блок с ником и кланом
        info_box = ctk.CTkFrame(header, fg_color="transparent")
        info_box.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            info_box,
            text=data.get("nickname", "PLAYER"),
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color="#e5e7eb",
            anchor="w",
        ).pack(fill="x")

        clan = data.get("clan")
        clan_text = f"[{clan}]" if clan else "Без клана"

        ctk.CTkLabel(
            info_box,
            text=clan_text,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#d4af37",
            anchor="w",
        ).pack(fill="x", pady=(2, 8))

        ctk.CTkLabel(
            info_box,
            text=data.get("subtitle", "Мир кораблей"),
            font=ctk.CTkFont(size=13),
            text_color="#94a3b8",
            anchor="w",
        ).pack(fill="x")

        # Разделитель
        line = ctk.CTkFrame(
            self.card,
            height=2,
            fg_color="#d4af37",
        )
        line.pack(fill="x", padx=22, pady=(0, 10))

        # -----------------------------
        # Статы
        # -----------------------------
        stats_grid = ctk.CTkFrame(self.card, fg_color="transparent")
        stats_grid.pack(fill="both", expand=True, padx=18, pady=(0, 8))

        for row in range(3):
            stats_grid.rowconfigure(row, weight=1)
        for col in range(2):
            stats_grid.columnconfigure(col, weight=1)

        items = [
            ("БОИ", f"{int(data.get('battles', 0)):,}"),
            ("ПОБЕДЫ", f"{float(data.get('winrate', 0)):.1f}%"),
            ("СР. УРОН", f"{int(data.get('avg_damage', 0)):,}"),
            ("СР. ФРАГИ", f"{float(data.get('avg_frags', 0)):.2f}"),
            ("СР. ОПЫТ", f"{int(data.get('avg_xp', 0)):,}"),
            ("МАКС. ФРАГИ", f"{int(data.get('max_frags', 0))}"),
        ]

        for index, (title, value) in enumerate(items):
            row, col = divmod(index, 2)

            cell = ctk.CTkFrame(
                stats_grid,
                corner_radius=18,
                fg_color="#111827",
                border_width=1,
                border_color="#1f2937",
            )
            cell.grid(
                row=row,
                column=col,
                sticky="nsew",
                padx=7,
                pady=7,
            )

            ctk.CTkLabel(
                cell,
                text=title,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#94a3b8",
            ).pack(pady=(14, 0))

            ctk.CTkLabel(
                cell,
                text=value,
                font=ctk.CTkFont(size=24, weight="bold"),
                text_color="#f9fafb",
            ).pack(pady=(0, 14))

        # -----------------------------
        # Низ карточки
        # -----------------------------
        footer = ctk.CTkLabel(
            self.card,
            text="N — ник • R — обновить • ПКМ/Esc — закрыть",
            font=ctk.CTkFont(size=11),
            text_color="#64748b",
        )
        footer.pack(pady=(0, 16))

        # Делаем карточку перетаскиваемой
        self._make_draggable(self.card)

    def _make_draggable(self, widget):
        widget.bind("<ButtonPress-1>", self._start_drag)
        widget.bind("<B1-Motion>", self._on_drag)

        for child in widget.winfo_children():
            self._make_draggable(child)

    def _start_drag(self, event):
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()

    def _on_drag(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.geometry(f"+{x}+{y}")


if __name__ == "__main__":
    app = PlayerCard()
    app.mainloop()