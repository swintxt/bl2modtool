import json
import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import datetime

APP_NAME = "Borderlands 2 Mod Editor"
ROOT = Path.home() / "Borderlands2ModEditor"
ROOT.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = ROOT / "mod_profile.json"
BACKUP_DIR = ROOT / "backups"

# Starter catalog only. These are editable profile entries, not a parsed list
# of every entity shipped in the game.
DEFAULT_CATALOG = [
    {"type": "Карта", "name": "Southern Shelf", "key": "map.southern_shelf",
     "stats": {"уровень рекомендованный": 5, "масштаб врагов": 1.0}},
    {"type": "Карта", "name": "Three Horns - Divide", "key": "map.three_horns_divide",
     "stats": {"уровень рекомендованный": 8, "масштаб врагов": 1.0}},
    {"type": "Квест", "name": "The Road to Sanctuary", "key": "quest.road_to_sanctuary",
     "stats": {"награда XP": 120, "награда денег": 50}},
    {"type": "Квест", "name": "Best Minion Ever", "key": "quest.best_minion_ever",
     "stats": {"награда XP": 800, "награда денег": 250}},
    {"type": "Враг", "name": "Bandit", "key": "enemy.bandit",
     "stats": {"здоровье": 100, "урон": 10, "скорость": 1.0, "уровень": 5}},
    {"type": "Враг", "name": "Badass Psycho", "key": "enemy.badass_psycho",
     "stats": {"здоровье": 1200, "урон": 75, "скорость": 1.1, "уровень": 15}},
]

def load_profile():
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("entries"), list):
                return data
        except Exception:
            pass
    return {"schema_version": 1, "game_path": "", "entries": DEFAULT_CATALOG}

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1000x680")
        self.minsize(820, 560)
        self.profile = load_profile()
        self.selected_entry = None
        self._build_ui()
        self._refresh_list()
        self.path_var.set(self.profile.get("game_path", ""))

    def _build_ui(self):
        outer = ttk.Frame(self, padding=12)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text=APP_NAME, font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(
            outer,
            text="Редактор профиля модификаций • безопасное хранение изменений отдельно от игровых файлов",
            foreground="#555"
        ).pack(anchor="w", pady=(2, 12))

        pathrow = ttk.Frame(outer)
        pathrow.pack(fill="x", pady=(0, 10))
        ttk.Label(pathrow, text="Папка игры:").pack(side="left")
        self.path_var = tk.StringVar()
        ttk.Entry(pathrow, textvariable=self.path_var).pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(pathrow, text="Выбрать…", command=self.choose_game).pack(side="left")
        ttk.Button(pathrow, text="Проверить", command=self.validate_game).pack(side="left", padx=(6, 0))

        body = ttk.Panedwindow(outer, orient="horizontal")
        body.pack(fill="both", expand=True)

        left = ttk.Frame(body, padding=(0, 0, 10, 0))
        right = ttk.Frame(body, padding=(10, 0, 0, 0))
        body.add(left, weight=1)
        body.add(right, weight=2)

        filterrow = ttk.Frame(left)
        filterrow.pack(fill="x", pady=(0, 6))
        ttk.Label(filterrow, text="Тип:").pack(side="left")
        self.filter_var = tk.StringVar(value="Все")
        combo = ttk.Combobox(filterrow, textvariable=self.filter_var,
                             values=["Все", "Карта", "Квест", "Враг"], state="readonly", width=12)
        combo.pack(side="left", padx=6)
        combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_list())

        self.listbox = tk.Listbox(left, activestyle="dotbox", exportselection=False)
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        actions = ttk.Frame(left)
        actions.pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text="Добавить запись", command=self.add_entry).pack(side="left")
        ttk.Button(actions, text="Удалить", command=self.delete_entry).pack(side="left", padx=6)

        ttk.Label(right, text="Характеристики выбранной записи", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(right, text="Изменения сохраняются в профиль редактора, а не напрямую в игровых пакетах.",
                  foreground="#8a4b08", wraplength=500).pack(anchor="w", pady=(4, 10))

        form = ttk.Frame(right)
        form.pack(fill="x")
        ttk.Label(form, text="Название:").grid(row=0, column=0, sticky="w", pady=4)
        self.name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.name_var).grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Label(form, text="Тип:").grid(row=1, column=0, sticky="w", pady=4)
        self.type_var = tk.StringVar()
        ttk.Combobox(form, textvariable=self.type_var, values=["Карта", "Квест", "Враг"],
                     state="readonly").grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Label(form, text="Ключ записи:").grid(row=2, column=0, sticky="w", pady=4)
        self.key_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.key_var).grid(row=2, column=1, sticky="ew", pady=4)
        form.columnconfigure(1, weight=1)

        ttk.Label(right, text="Параметры (числовые значения)").pack(anchor="w", pady=(12, 4))
        self.stats_frame = ttk.Frame(right)
        self.stats_frame.pack(fill="x")
        self.stat_vars = {}
        self.stats_hint = ttk.Label(right, text="Выбери запись слева, чтобы редактировать параметры.",
                                    foreground="#555")
        self.stats_hint.pack(anchor="w", pady=(8, 0))

        bottom = ttk.Frame(right)
        bottom.pack(fill="x", side="bottom", pady=(14, 0))
        ttk.Button(bottom, text="Сохранить запись", command=self.save_entry).pack(side="left")
        ttk.Button(bottom, text="Сохранить профиль", command=self.save_profile).pack(side="left", padx=6)
        ttk.Button(bottom, text="Откатить профиль", command=self.rollback_profile).pack(side="left")
        ttk.Button(bottom, text="Экспорт JSON…", command=self.export_profile).pack(side="right")

        self.status_var = tk.StringVar(value="Готово. Выбери папку игры и запись каталога.")
        ttk.Label(outer, textvariable=self.status_var, relief="sunken", anchor="w").pack(fill="x", pady=(10, 0))

    def _refresh_list(self, select_index=None):
        self.listbox.delete(0, tk.END)
        filter_type = self.filter_var.get()
        self.visible_entries = []
        for entry in self.profile["entries"]:
            if filter_type != "Все" and entry.get("type") != filter_type:
                continue
            self.visible_entries.append(entry)
            self.listbox.insert(tk.END, f'[{entry.get("type","?")}] {entry.get("name","Без названия")}')
        if select_index is not None and 0 <= select_index < len(self.visible_entries):
            self.listbox.selection_set(select_index)
            self.listbox.event_generate("<<ListboxSelect>>")

    def on_select(self, _event=None):
        selection = self.listbox.curselection()
        if not selection:
            return
        self.selected_entry = self.visible_entries[selection[0]]
        entry = self.selected_entry
        self.name_var.set(entry.get("name", ""))
        self.type_var.set(entry.get("type", "Враг"))
        self.key_var.set(entry.get("key", ""))
        for child in self.stats_frame.winfo_children():
            child.destroy()
        self.stat_vars = {}
        stats = entry.get("stats", {})
        for row, (key, value) in enumerate(stats.items()):
            ttk.Label(self.stats_frame, text=key + ":").grid(row=row, column=0, sticky="w", pady=3)
            var = tk.StringVar(value=str(value))
            ttk.Entry(self.stats_frame, textvariable=var, width=22).grid(row=row, column=1, sticky="ew", pady=3)
            self.stat_vars[key] = var
        self.stats_frame.columnconfigure(1, weight=1)
        self.stats_hint.config(text=f"Ключ: {entry.get('key','')} • параметров: {len(stats)}")

    def choose_game(self):
        path = filedialog.askdirectory(title="Выбери папку Borderlands 2")
        if path:
            self.path_var.set(path)
            self.profile["game_path"] = path
            self.validate_game()

    def validate_game(self):
        raw = self.path_var.get().strip()
        if not raw or not Path(raw).is_dir():
            messagebox.showwarning("Папка не найдена", "Выбери существующую папку игры.")
            return
        p = Path(raw)
        candidates = [
            p / "WillowGame" / "CookedPCConsole",
            p / "Binaries" / "Win32",
            p / "Borderlands2.exe",
            p / "Launcher.exe",
        ]
        found = [str(x) for x in candidates if x.exists()]
        self.profile["game_path"] = str(p)
        if found:
            self.status_var.set("Папка существует; найдены возможные признаки установки. Это не подтверждает совместимость форматов.")
            messagebox.showinfo("Папка проверена", "Папка существует.\nНайдены:\n" + "\n".join(found) +
                                "\n\nПроверка не определяет автоматически оригинал это или переиздание.")
        else:
            self.status_var.set("Папка существует, но ожидаемые признаки установки не найдены.")
            messagebox.showwarning("Не удалось подтвердить игру",
                                   "Папка существует, но стандартные признаки установки не найдены. "
                                   "Можно продолжить, если структура нестандартная.")

    def add_entry(self):
        entry = {"type": "Враг", "name": "Новая запись", "key": "custom.new_entry", "stats": {"здоровье": 100}}
        self.profile["entries"].append(entry)
        self.filter_var.set("Все")
        self._refresh_list(len(self.profile["entries"]) - 1)
        self.status_var.set("Добавлена пользовательская запись.")

    def delete_entry(self):
        if not self.selected_entry:
            messagebox.showinfo("Нет выбора", "Сначала выбери запись.")
            return
        if messagebox.askyesno("Удалить запись", f"Удалить «{self.selected_entry.get('name')}» из профиля?"):
            self.profile["entries"].remove(self.selected_entry)
            self.selected_entry = None
            self._refresh_list()
            self.status_var.set("Запись удалена из профиля.")

    def save_entry(self):
        if not self.selected_entry:
            messagebox.showinfo("Нет выбора", "Сначала выбери запись слева.")
            return
        try:
            stats = {}
            for key, var in self.stat_vars.items():
                value = var.get().strip()
                number = float(value)
                stats[key] = int(number) if number.is_integer() else number
        except ValueError:
            messagebox.showerror("Неверное значение", "Параметры должны быть числами.")
            return
        self.selected_entry["name"] = self.name_var.get().strip() or "Без названия"
        self.selected_entry["type"] = self.type_var.get() or "Враг"
        self.selected_entry["key"] = self.key_var.get().strip() or "custom.unnamed"
        self.selected_entry["stats"] = stats
        idx = next((i for i, x in enumerate(self.visible_entries) if x is self.selected_entry), 0)
        self._refresh_list(idx)
        self.status_var.set("Запись обновлена в памяти. Нажми «Сохранить профиль», чтобы записать на диск.")

    def save_profile(self):
        self.profile["game_path"] = self.path_var.get().strip()
        save_json(CONFIG_FILE, self.profile)
        self.status_var.set(f"Профиль сохранён: {CONFIG_FILE}")
        messagebox.showinfo("Сохранено", f"Профиль сохранён:\n{CONFIG_FILE}\n\nИгровые файлы не изменялись.")

    def rollback_profile(self):
        if not CONFIG_FILE.exists():
            messagebox.showinfo("Нет сохранения", "Сохранённого профиля пока нет.")
            return
        if not messagebox.askyesno("Откатить профиль",
                                   "Вернуть каталог и параметры к последнему сохранённому профилю на диске?\n"
                                   "Несохранённые изменения будут потеряны. Игровые файлы не затрагиваются."):
            return
        self.profile = load_profile()
        self.path_var.set(self.profile.get("game_path", ""))
        self.selected_entry = None
        self._refresh_list()
        self.status_var.set("Профиль восстановлен из последнего сохранения.")

    def export_profile(self):
        target = filedialog.asksaveasfilename(title="Экспорт профиля", defaultextension=".json",
                                              filetypes=[("JSON profile", "*.json")],
                                              initialfile="borderlands2_mod_profile.json")
        if target:
            self.profile["game_path"] = self.path_var.get().strip()
            save_json(Path(target), self.profile)
            self.status_var.set(f"Экспортировано: {target}")

if __name__ == "__main__":
    App().mainloop()
