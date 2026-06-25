import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import random
import os
from datetime import date, timedelta

APP_DIR = os.path.dirname(os.path.abspath(__file__))


# ──────────────────────────── Тема ────────────────────────────
class DarkTheme:
    BG_DARK = "#1a1a2e"
    BG_MID = "#16213e"
    BG_LIGHT = "#0f3460"
    FG = "#e0e0e0"
    FG_DIM = "#a0a0b0"
    ACCENT = "#e94560"
    ACCENT_HOVER = "#ff6b81"
    SUCCESS = "#2ecc71"
    WARNING = "#f39c12"
    TREE_BG = "#0d1b2a"
    TREE_SEL = "#e94560"
    TREE_FG = "#e0e0e0"
    ENTRY_BG = "#1a1a3e"
    BTN_BG = "#e94560"
    BTN_FG = "#ffffff"
    BORDER = "#2a2a5a"


# ──────────────────────── База данных ────────────────────────
class Database:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(APP_DIR, "freddy_fazbear.db")
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.create_table()

    def create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id TEXT PRIMARY KEY,
                attraction TEXT NOT NULL,
                visitor_name TEXT NOT NULL,
                age INTEGER NOT NULL,
                price REAL NOT NULL,
                ticket_type TEXT NOT NULL,
                purchase_date TEXT NOT NULL
            )
        """)
        self.conn.commit()
        if self.count() == 0:
            self.seed()

    def count(self):
        return self.conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]

    def seed(self):
        attractions = [
            "Караоке с Фредди", "Холм холостяков", "Аттракцион «Звёзды»",
            "Комната Бонни", "Кукольный театр Чика", "Ресторан «Пицца Фрэдди»",
            "Спиральная горка Фокси", "Комната страха", "Водопад Эндорфина",
            "Световое шоу", "Космический полёт", "Карусель мечты"
        ]
        names = [
            "Иван Петров", "Мария Сидорова", "Алексей Козлов", "Анна Морозова",
            "Дмитрий Новиков", "Елена Соколова", "Сергей Лебедев", "Ольга Попова",
            "Никита Волков", "Татьяна Зайцева", "Максим Фёдоров", "Наталья Михайлова",
            "Артём Егоров", "Виктория Белова", "Кирилл Яковлев", "Дарья Кузнецова"
        ]
        for i in range(12):
            att = random.choice(attractions)
            name = random.choice(names)
            age = random.randint(3, 60)
            ticket_type = "Детский" if age < 14 else "Взрослый"
            price = round(random.uniform(150, 999), 2)
            rid = f"АТ-{i:03d}"
            d = date(2025, 1, 1) + timedelta(days=random.randint(0, 364))
            self.conn.execute(
                "INSERT INTO tickets VALUES (?,?,?,?,?,?,?)",
                (rid, att, name, age, price, ticket_type, d.strftime("%d.%m.%Y"))
            )
        self.conn.commit()

    def get_next_id(self):
        rows = self.conn.execute("SELECT id FROM tickets").fetchall()
        nums = []
        for r in rows:
            try:
                nums.append(int(r["id"].split("-")[1]))
            except (IndexError, ValueError):
                pass
        nxt = max(nums) + 1 if nums else 0
        return f"АТ-{nxt:03d}"

    def fetch_all(self):
        return self.conn.execute("SELECT * FROM tickets ORDER BY id").fetchall()

    def add(self, attraction, visitor, age, price, ttype, purchase_date):
        self.conn.execute(
            "INSERT INTO tickets VALUES (?,?,?,?,?,?,?)",
            (self.get_next_id(), attraction, visitor, age, price, ttype, purchase_date)
        )
        self.conn.commit()

    def update(self, tid, attraction, visitor, age, price, ttype, purchase_date):
        self.conn.execute(
            "UPDATE tickets SET attraction=?, visitor_name=?, age=?, price=?, ticket_type=?, purchase_date=? WHERE id=?",
            (attraction, visitor, age, price, ttype, purchase_date, tid)
        )
        self.conn.commit()

    def delete(self, tid):
        self.conn.execute("DELETE FROM tickets WHERE id=?", (tid,))
        self.conn.commit()

    def query(self, sql, params=()):
        return self.conn.execute(sql, params).fetchall()

    def close(self):
        self.conn.close()


# ──────────────────────── Приложение ────────────────────────
class FreddyApp:
    COLUMNS = [
        ("id", "ID"),
        ("attraction", "Аттракцион"),
        ("visitor_name", "Посетитель"),
        ("age", "Возраст"),
        ("price", "Цена"),
        ("ticket_type", "Тип билета"),
        ("purchase_date", "Дата покупки"),
    ]

    def __init__(self, root):
        self.root = root
        self.root.title("Freddy Fazbear — СУБД Парка Аттракционов")
        self.root.geometry("1120x640")
        self.root.minsize(900, 520)
        self.db = Database()
        self.sort_col = None
        self.sort_rev = False
        self.visible_cols = [c[0] for c in self.COLUMNS]

        self._apply_theme()
        self._build_toolbar()
        self._build_filter_bar()
        self._build_statusbar()
        self._build_table()
        self._build_form_panel()
        self.refresh()

    # ─── Тема ───
    def _apply_theme(self):
        T = DarkTheme
        self.root.configure(bg=T.BG_DARK)
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=T.BG_DARK, foreground=T.FG, fieldbackground=T.ENTRY_BG,
                         bordercolor=T.BORDER, font=("Segoe UI", 10))
        style.configure("Treeview", background=T.TREE_BG, foreground=T.TREE_FG,
                         fieldbackground=T.TREE_BG, rowheight=28, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background=T.BG_LIGHT, foreground=T.FG,
                         font=("Segoe UI", 10, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", T.TREE_SEL)],
                   foreground=[("selected", "#ffffff")])
        style.map("Treeview.Heading", background=[("active", T.ACCENT)])

        style.configure("TButton", background=T.BTN_BG, foreground=T.BTN_FG,
                         font=("Segoe UI", 10, "bold"), padding=(12, 6),
                         borderwidth=0, relief="flat")
        style.map("TButton",
                   background=[("active", T.ACCENT_HOVER), ("pressed", "#c0392b")],
                   foreground=[("active", "#ffffff")])

        style.configure("Accent.TButton", background=T.ACCENT, foreground=T.BTN_FG,
                         font=("Segoe UI", 10, "bold"), padding=(14, 7))
        style.map("Accent.TButton",
                   background=[("active", T.ACCENT_HOVER), ("pressed", "#c0392b")])

        style.configure("TLabel", background=T.BG_DARK, foreground=T.FG,
                         font=("Segoe UI", 10))
        style.configure("Header.TLabel", background=T.BG_DARK, foreground=T.ACCENT,
                         font=("Segoe UI", 13, "bold"))
        style.configure("TEntry", fieldbackground=T.ENTRY_BG, foreground=T.FG,
                         insertcolor=T.FG, bordercolor=T.BORDER)
        style.configure("TCombobox", fieldbackground=T.ENTRY_BG, foreground=T.FG,
                         background=T.BG_LIGHT, arrowcolor=T.ACCENT)
        style.map("TCombobox", fieldbackground=[("readonly", T.ENTRY_BG)])

        style.configure("TFrame", background=T.BG_DARK)
        style.configure("Card.TFrame", background=T.BG_MID, relief="ridge", borderwidth=1)

        style.configure("TScrollbar", background=T.BG_MID, troughcolor=T.BG_DARK,
                         arrowcolor=T.ACCENT)

    # ─── Панель инструментов ───
    def _build_toolbar(self):
        T = DarkTheme
        frm = ttk.Frame(self.root, style="Card.TFrame", padding=8)
        frm.pack(fill="x", padx=8, pady=(8, 0))

        ttk.Label(frm, text="🐻 FREDDY FAZBEAR", style="Header.TLabel").pack(side="left")

        btn_frame = ttk.Frame(frm)
        btn_frame.pack(side="right")

        ttk.Button(btn_frame, text="➕ Добавить", command=self.add_record).pack(side="left", padx=3)
        ttk.Button(btn_frame, text="✏️ Изменить", command=self.edit_record).pack(side="left", padx=3)
        ttk.Button(btn_frame, text="🗑️ Удалить", command=self.delete_record).pack(side="left", padx=3)
        ttk.Button(btn_frame, text="ℹ️ О авторе", command=self.show_about).pack(side="left", padx=(12, 3))

        menubtn = ttk.Menubutton(btn_frame, text="📋 Отчёты")
        menubtn.menu = tk.Menu(menubtn, tearoff=0, bg=T.BG_MID, fg=T.FG,
                                activebackground=T.ACCENT, activeforeground="#fff",
                                font=("Segoe UI", 10))
        menubtn["menu"] = menubtn.menu
        self._build_report_menu(menubtn.menu)
        menubtn.pack(side="left", padx=3)

    # ─── Многоуровневое меню отчётов ───
    def _build_report_menu(self, menu):
        report_tree = {
            "1. Финансовые отчёты": [
                ("Общая выручка", self.report_revenue_total),
                ("Выручка по типу билета", self.report_revenue_by_type),
                ("Средний чек", self.report_avg_price),
            ],
            "2. Посещаемость": [
                ("Посетители по типу билета", self.report_by_ticket_type),
                ("Посетители по возрасту", self.report_by_age),
            ],
            "3. Аттракционы": [
                ("Популярность аттракционов", self.report_attraction_popularity),
                ("Загрузка аттракционов", self.report_attraction_load),
                ("Доход по аттракционам", self.report_attraction_revenue),
            ],
            "4. Билеты": [
                ("Продажи по датам", self.report_sales_by_date),
                ("Дорогие билеты", self.report_expensive_tickets),
            ],
            "5. Аналитика": [
                ("Топ-5 посетителей", self.report_top_visitors),
                ("Возрастная статистика", self.report_age_stats),
                ("Ценовой диапазон", self.report_price_range),
            ],
        }
        for cat, items in report_tree.items():
            sub = tk.Menu(menu, tearoff=0, bg=DarkTheme.BG_MID, fg=DarkTheme.FG,
                           activebackground=DarkTheme.ACCENT, activeforeground="#fff",
                           font=("Segoe UI", 10))
            menu.add_cascade(label=cat, menu=sub)
            for label, cmd in items:
                sub.add_command(label=label, command=cmd)

    # ─── Панель фильтрации ───
    def _build_filter_bar(self):
        T = DarkTheme
        frm = ttk.Frame(self.root, style="Card.TFrame", padding=6)
        frm.pack(fill="x", padx=8, pady=(4, 0))

        ttk.Label(frm, text="Показать столбцы:").pack(side="left", padx=(0, 6))

        self.filter_var = tk.StringVar()
        ef = ttk.Entry(frm, textvariable=self.filter_var, width=40)
        ef.pack(side="left", padx=3)
        ef.bind("<Return>", lambda _: self._apply_column_filter())

        col_names = ", ".join(c[1] for c in self.COLUMNS)
        ttk.Label(frm, text=f"Доступны: {col_names}",
                  foreground=DarkTheme.FG_DIM).pack(side="left", padx=8)

        ttk.Button(frm, text="Применить", command=self._apply_column_filter).pack(side="left", padx=3)
        ttk.Button(frm, text="Сброс", command=self._reset_column_filter).pack(side="left", padx=3)

    def _apply_column_filter(self):
        raw = self.filter_var.get().strip()
        if not raw:
            self.visible_cols = [c[0] for c in self.COLUMNS]
        else:
            requested = [s.strip() for s in raw.split(",") if s.strip()]
            self.visible_cols = []
            for cid, heading in self.COLUMNS:
                if heading in requested or cid in requested:
                    self.visible_cols.append(cid)
            if not self.visible_cols:
                self.visible_cols = [c[0] for c in self.COLUMNS]
        self._rebuild_tree()

    def _reset_column_filter(self):
        self.filter_var.set("")
        self.visible_cols = [c[0] for c in self.COLUMNS]
        self._rebuild_tree()

    # ─── Таблица ───
    def _build_table(self):
        T = DarkTheme
        self.table_frame = ttk.Frame(self.root)
        self.table_frame.pack(fill="both", expand=True, padx=8, pady=6)

        self.vsb = ttk.Scrollbar(self.table_frame, orient="vertical")
        self.vsb.pack(side="right", fill="y")

        self.tree = None
        self._rebuild_tree()

    def _rebuild_tree(self):
        if self.tree is not None:
            self.tree.destroy()

        T = DarkTheme
        visible = [c for c in self.COLUMNS if c[0] in self.visible_cols]
        cols = [c[0] for c in visible]

        self.tree = ttk.Treeview(self.table_frame, columns=cols, show="headings",
                                  selectmode="browse")
        self.tree.configure(yscrollcommand=self.vsb.set)
        self.vsb.configure(command=self.tree.yview)
        self.tree.pack(side="left", fill="both", expand=True)

        for cid, heading in visible:
            self.tree.heading(cid, text=heading, anchor="w",
                              command=lambda c=cid: self._sort_by(c))
            w = 70 if cid == "id" else 160 if cid in ("attraction", "visitor_name") else 110 if cid == "purchase_date" else 80
            self.tree.column(cid, width=w, minwidth=50,
                             anchor="center" if cid not in ("attraction", "visitor_name") else "w")

        self.refresh()

    def _sort_by(self, col):
        if self.sort_col == col:
            self.sort_rev = not self.sort_rev
        else:
            self.sort_col = col
            self.sort_rev = False
        self.refresh()

    # ─── Панель формы ───
    def _build_form_panel(self):
        T = DarkTheme
        frm = ttk.Frame(self.root, style="Card.TFrame", padding=8)
        frm.pack(fill="x", padx=8, pady=(0, 8))

        ttk.Label(frm, text="Поиск записи:").pack(side="left", padx=(0, 6))

        self.search_var = tk.StringVar()
        se = ttk.Entry(frm, textvariable=self.search_var, width=50)
        se.pack(side="left", padx=3, fill="x", expand=True)
        se.bind("<Return>", lambda _: self._search_record())

        ttk.Button(frm, text="Найти", command=self._search_record).pack(side="left", padx=3)
        ttk.Button(frm, text="Сброс", command=self._reset_search).pack(side="left", padx=3)

    def _search_record(self):
        q = self.search_var.get().strip().lower()
        if not q:
            self.refresh()
            return
        data = self.db.fetch_all()
        data = [r for r in data if any(q in str(list(r)[i]).lower() for i in range(len(self.COLUMNS)))]
        visible_indices = [i for i, c in enumerate(self.COLUMNS) if c[0] in self.visible_cols]
        self.tree.delete(*self.tree.get_children())
        for row in data:
            filtered_vals = [list(row)[i] for i in visible_indices]
            self.tree.insert("", "end", values=filtered_vals)
        self.count_label.config(text=f"Найдено: {len(data)}")
        self.status_label.config(text=f"Поиск: «{self.search_var.get().strip()}»")

    def _reset_search(self):
        self.search_var.set("")
        self.refresh()

    # ─── Статус-бар ───
    def _build_statusbar(self):
        T = DarkTheme
        frm = ttk.Frame(self.root, style="Card.TFrame", padding=4)
        frm.pack(fill="x", padx=8, pady=(0, 6))
        self.status_label = ttk.Label(frm, text="Готово")
        self.status_label.pack(side="left", padx=8)
        self.count_label = ttk.Label(frm, text="Записей: 0")
        self.count_label.pack(side="right", padx=8)

    # ─── Обновление таблицы ───
    def refresh(self):
        data = self.db.fetch_all()

        # Сортировка
        if self.sort_col:
            idx = next(i for i, c in enumerate(self.COLUMNS) if c[0] == self.sort_col)
            try:
                data = sorted(data, key=lambda r: list(r)[idx], reverse=self.sort_rev)
            except TypeError:
                data = sorted(data, key=lambda r: str(list(r)[idx]), reverse=self.sort_rev)

        visible_indices = [i for i, c in enumerate(self.COLUMNS) if c[0] in self.visible_cols]

        self.tree.delete(*self.tree.get_children())
        for row in data:
            filtered_vals = [list(row)[i] for i in visible_indices]
            self.tree.insert("", "end", values=filtered_vals)

        self.count_label.config(text=f"Записей: {len(data)}")
        self.status_label.config(text="Данные обновлены")

    # ─── CRUD ───
    def add_record(self):
        initial = {"id": self.db.get_next_id(), "purchase_date": date.today().strftime("%d.%m.%Y")}
        d = self._Dialog(self.root, "Добавить запись", self.COLUMNS, initial=initial)
        self.root.wait_window(d.top)
        if d.result:
            try:
                self.db.add(
                    d.result["attraction"], d.result["visitor_name"],
                    d.result["age"], d.result["price"], d.result["ticket_type"],
                    d.result["purchase_date"]
                )
                self.refresh()
                self.status_label.config(text=f"Запись {d.result['id']} добавлена")
            except Exception as e:
                messagebox.showerror("Ошибка БД", f"Не удалось добавить запись:\n{e}")

    def edit_record(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите запись для изменения")
            return
        tree_vals = list(self.tree.item(sel[0], "values"))
        visible_cols = [c for c in self.COLUMNS if c[0] in self.visible_cols]
        id_idx = next((i for i, c in enumerate(visible_cols) if c[0] == "id"), None)
        record_id = tree_vals[id_idx] if id_idx is not None else tree_vals[0]
        rows = self.db.query("SELECT * FROM tickets WHERE id=?", (record_id,))
        if not rows:
            return
        row = rows[0]
        initial = {c[0]: list(row)[i] for i, c in enumerate(self.COLUMNS)}
        d = self._Dialog(self.root, "Изменить запись", self.COLUMNS,
                          initial=initial, edit_mode=True)
        self.root.wait_window(d.top)
        if d.result:
            try:
                self.db.update(
                    d.result["id"], d.result["attraction"], d.result["visitor_name"],
                    d.result["age"], d.result["price"], d.result["ticket_type"],
                    d.result["purchase_date"]
                )
                self.refresh()
                self.status_label.config(text=f"Запись {d.result['id']} обновлена")
            except Exception as e:
                messagebox.showerror("Ошибка БД", f"Не удалось изменить запись:\n{e}")

    def delete_record(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите запись для удаления")
            return
        vals = self.tree.item(sel[0], "values")
        if messagebox.askyesno("Подтверждение", f"Удалить запись {vals[0]}?"):
            try:
                self.db.delete(vals[0])
                self.refresh()
                self.status_label.config(text=f"Запись {vals[0]} удалена")
            except Exception as e:
                messagebox.showerror("Ошибка БД", f"Не удалось удалить запись:\n{e}")

    # ─── Диалог ───
    class _Dialog:
        def __init__(self, parent, title, columns, initial=None, edit_mode=False):
            self.result = None
            self.columns = columns
            T = DarkTheme
            self.top = tk.Toplevel(parent)
            self.top.title(title)
            self.top.geometry("460x370")
            self.top.configure(bg=T.BG_DARK)
            self.top.transient(parent)
            self.top.grab_set()

            frm = ttk.Frame(self.top, padding=20)
            frm.pack(fill="both", expand=True)

            ttk.Label(frm, text=title, style="Header.TLabel").grid(
                row=0, column=0, columnspan=2, pady=(0, 10))

            self.entries = {}
            for i, (cid, heading) in enumerate(columns):
                row = i + 1
                ttk.Label(frm, text=heading + ":").grid(row=row, column=0, padx=6, pady=5, sticky="e")
                val = initial.get(cid, "") if initial else ""
                if cid == "ticket_type":
                    var = tk.StringVar(value=val)
                    w = ttk.Combobox(frm, textvariable=var, width=20, state="readonly",
                                      values=["Детский", "Взрослый"])
                elif cid == "id" and edit_mode:
                    var = tk.StringVar(value=val)
                    w = ttk.Entry(frm, textvariable=var, width=22, state="readonly")
                else:
                    var = tk.StringVar(value=val)
                    w = ttk.Entry(frm, textvariable=var, width=22)
                w.grid(row=row, column=1, padx=6, pady=5)
                self.entries[cid] = var

            def _auto_ticket_type(*_args):
                try:
                    age = int(self.entries["age"].get())
                    if age <= 12:
                        self.entries["ticket_type"].set("Детский")
                    else:
                        self.entries["ticket_type"].set("Взрослый")
                except ValueError:
                    pass

            self.entries["age"].trace_add("write", _auto_ticket_type)
            if not edit_mode:
                _auto_ticket_type()

            err_label = ttk.Label(frm, text="", foreground="#ff6b6b")
            err_label.grid(row=len(columns) + 1, column=0, columnspan=2, pady=(4, 0))
            self._err_label = err_label

            btn_frame = ttk.Frame(frm)
            btn_frame.grid(row=len(columns) + 2, column=0, columnspan=2, pady=14)
            ttk.Button(btn_frame, text="Сохранить", command=self._ok).pack(side="left", padx=8)
            ttk.Button(btn_frame, text="Отмена", command=self.top.destroy).pack(side="left", padx=8)

        def _ok(self):
            vals = {}
            for cid, heading in self.columns:
                v = self.entries[cid].get().strip()
                if not v:
                    self._err_label.config(text=f"Заполните поле «{heading}»")
                    return
                if cid in ("attraction", "visitor_name") and any(ch.isdigit() for ch in v):
                    self._err_label.config(text=f"«{heading}» — только буквы, цифры запрещены")
                    return
                vals[cid] = v

            try:
                vals["age"] = int(vals["age"])
                if vals["age"] < 0 or vals["age"] > 120:
                    self._err_label.config(text="Возраст должен быть от 0 до 120")
                    return
            except ValueError:
                self._err_label.config(text="Возраст — целое число (0–120)")
                return

            if vals["ticket_type"] == "Детский" and vals["age"] > 12:
                self._err_label.config(text="Детский билет: возраст не более 12 лет")
                return
            if vals["ticket_type"] == "Взрослый" and vals["age"] < 13:
                self._err_label.config(text="Взрослый билет: возраст от 13 лет")
                return

            try:
                vals["price"] = float(vals["price"])
                if vals["price"] <= 0:
                    self._err_label.config(text="Цена должна быть больше 0")
                    return
            except ValueError:
                self._err_label.config(text="Цена — число (например: 250.00)")
                return

            try:
                parts = vals["purchase_date"].split(".")
                if len(parts) != 3:
                    raise ValueError
                d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
                purchase = date(y, m, d)
            except (ValueError, IndexError):
                self._err_label.config(text="Дата — формат ДД.ММ.ГГГГ (например: 25.06.2025)")
                return

            if purchase > date.today():
                self._err_label.config(text="Дата покупки не может быть позже сегодня")
                return

            self.result = vals
            self.top.destroy()

    # ─── Отчёты (helper) ───
    def _report_window(self, title, headers, rows):
        T = DarkTheme
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("700x480")
        win.configure(bg=T.BG_DARK)

        ttk.Label(win, text=title, style="Header.TLabel").pack(pady=(12, 6))

        frm = ttk.Frame(win)
        frm.pack(fill="both", expand=True, padx=12, pady=6)
        tree = ttk.Treeview(frm, columns=headers, show="headings", selectmode="none")
        vsb = ttk.Scrollbar(frm, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)
        for h in headers:
            tree.heading(h, text=h)
            tree.column(h, width=140, anchor="center")
        for row in rows:
            tree.insert("", "end", values=row)

        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill="x", padx=12, pady=(0, 10))
        ttk.Button(btn_frame, text="Сохранить в Excel",
                   command=lambda: self._save_excel(title, headers, rows)).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Сохранить в PDF",
                   command=lambda: self._save_pdf(title, headers, rows)).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Закрыть", command=win.destroy).pack(side="right", padx=4)

    def _save_excel(self, title, headers, rows):
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                            filetypes=[("Excel", "*.xlsx")],
                                            title="Сохранить в Excel")
        if not path:
            return
        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = title[:31]
            ws.append(headers)
            for row in rows:
                ws.append([str(v) for v in row])
            for col in ws.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)
            wb.save(path)
            self.status_label.config(text=f"Excel сохранён: {path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить Excel:\n{e}")

    def _save_pdf(self, title, headers, rows):
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                            filetypes=[("PDF", "*.pdf")],
                                            title="Сохранить в PDF")
        if not path:
            return
        try:
            from fpdf import FPDF
            import os
            arial = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "arial.ttf")
            arial_b = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "arialbd.ttf")
            pdf = FPDF(orientation="L", unit="mm", format="A4")
            pdf.add_font("Arial", "", arial, uni=True)
            pdf.add_font("Arial", "B", arial_b, uni=True)
            pdf.add_page()
            pdf.set_font("Arial", size=14)
            pdf.cell(0, 10, title, ln=True, align="C")
            pdf.ln(4)

            num_cols = len(headers)
            page_w = pdf.w - 2 * pdf.l_margin
            col_w = page_w / num_cols

            pdf.set_font("Arial", size=10, style="B")
            for h in headers:
                pdf.cell(col_w, 8, str(h), border=1, align="C")
            pdf.ln()

            pdf.set_font("Arial", size=9)
            for row in rows:
                for val in row:
                    pdf.cell(col_w, 7, str(val), border=1, align="C")
                pdf.ln()

            pdf.output(path)
            self.status_label.config(text=f"PDF сохранён: {path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить PDF:\n{e}")

    def _rows_to_list(self, rows):
        return [list(r) for r in rows]

    # ─── Отчёты ───
    def report_revenue_total(self):
        r = self.db.query("SELECT SUM(price) AS total FROM tickets")
        val = r[0]["total"] or 0
        self._report_window("Общая выручка", ["Метрика", "Значение"],
                            [["Общая выручка", f"{val:,.2f} ₽"]])

    def report_revenue_by_type(self):
        r = self.db.query("SELECT ticket_type, SUM(price) AS total FROM tickets GROUP BY ticket_type")
        rows = self._rows_to_list(r)
        self._report_window("Выручка по типу билета", ["Тип", "Выручка (₽)"],
                            [[x[0], f"{x[1]:,.2f}"] for x in rows])

    def report_avg_price(self):
        r = self.db.query("SELECT AVG(price) AS avg_p FROM tickets")
        val = r[0]["avg_p"] or 0
        self._report_window("Средний чек", ["Метрика", "Значение"],
                            [["Средний чек", f"{val:,.2f} ₽"]])

    def report_by_ticket_type(self):
        r = self.db.query("SELECT ticket_type, COUNT(*) AS cnt FROM tickets GROUP BY ticket_type ORDER BY cnt DESC")
        self._report_window("Посетители по типу билета", ["Тип билета", "Кол-во"],
                            self._rows_to_list(r))

    def report_by_age(self):
        r = self.db.query("""
            SELECT
                CASE
                    WHEN age < 7 THEN '0-6'
                    WHEN age < 14 THEN '7-13'
                    WHEN age < 18 THEN '14-17'
                    WHEN age < 30 THEN '18-29'
                    WHEN age < 50 THEN '30-49'
                    ELSE '50+'
                END AS age_group,
                COUNT(*) AS cnt
            FROM tickets GROUP BY age_group ORDER BY age_group
        """)
        self._report_window("Посетители по возрасту", ["Возрастная группа", "Кол-во"],
                            self._rows_to_list(r))

    def report_attraction_popularity(self):
        r = self.db.query("SELECT attraction, COUNT(*) AS cnt FROM tickets GROUP BY attraction ORDER BY cnt DESC")
        self._report_window("Популярность аттракционов", ["Аттракцион", "Посещений"],
                            self._rows_to_list(r))

    def report_attraction_load(self):
        r = self.db.query("SELECT attraction, COUNT(*) AS cnt, ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM tickets), 1) AS pct FROM tickets GROUP BY attraction ORDER BY cnt DESC")
        self._report_window("Загрузка аттракционов", ["Аттракцион", "Записей", "Доля (%)"],
                            self._rows_to_list(r))

    def report_attraction_revenue(self):
        r = self.db.query("SELECT attraction, SUM(price) AS total FROM tickets GROUP BY attraction ORDER BY total DESC")
        self._report_window("Доход по аттракционам", ["Аттракцион", "Доход (₽)"],
                            [[x[0], f"{x[1]:,.2f}"] for x in self._rows_to_list(r)])

    def report_sales_by_date(self):
        r = self.db.query("SELECT purchase_date, COUNT(*) AS cnt, SUM(price) AS total FROM tickets GROUP BY purchase_date ORDER BY purchase_date DESC")
        self._report_window("Продажи по датам", ["Дата", "Билетов", "Сумма (₽)"],
                            [[x[0], x[1], f"{x[2]:,.2f}"] for x in self._rows_to_list(r)])

    def report_expensive_tickets(self):
        r = self.db.query("SELECT * FROM tickets ORDER BY price DESC LIMIT 5")
        self._report_window("Топ-5 дорогих билетов",
                            ["ID", "Аттракцион", "Посетитель", "Возраст", "Цена", "Тип", "Дата покупки"],
                            self._rows_to_list(r))

    def report_top_visitors(self):
        r = self.db.query("SELECT visitor_name, SUM(price) AS total, COUNT(*) AS visits FROM tickets GROUP BY visitor_name ORDER BY total DESC LIMIT 5")
        self._report_window("Топ-5 посетителей", ["Посетитель", "Сумма (₽)", "Визитов"],
                            [[x[0], f"{x[1]:,.2f}", x[2]] for x in self._rows_to_list(r)])

    def report_age_stats(self):
        r = self.db.query("SELECT MIN(age) AS min_a, MAX(age) AS max_a, ROUND(AVG(age), 1) AS avg_a FROM tickets")
        x = r[0]
        self._report_window("Возрастная статистика", ["Метрика", "Значение"],
                            [["Мин. возраст", x["min_a"]], ["Макс. возраст", x["max_a"]], ["Средний возраст", x["avg_a"]]])

    def report_price_range(self):
        r = self.db.query("SELECT MIN(price) AS min_p, MAX(price) AS max_p, ROUND(AVG(price), 1) AS avg_p FROM tickets")
        x = r[0]
        self._report_window("Ценовой диапазон", ["Метрика", "Значение"],
                            [["Мин. цена", f"{x['min_p']:,.2f} ₽"], ["Макс. цена", f"{x['max_p']:,.2f} ₽"], ["Средняя цена", f"{x['avg_p']:,.2f} ₽"]])

    # ─── О авторе ───
    def show_about(self):
        T = DarkTheme
        win = tk.Toplevel(self.root)
        win.title("О авторе")
        win.geometry("450x380")
        win.configure(bg=T.BG_DARK)
        win.transient(self.root)
        win.grab_set()

        frm = ttk.Frame(win, padding=24)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="🐻 Freddy Fazbear DB", style="Header.TLabel").pack(pady=(0, 12))
        ttk.Label(frm, text="Автор: Кабушко Максим Николаевич",
                  font=("Segoe UI", 11, "bold")).pack(pady=4)
        ttk.Label(frm, text="Группа: ИС-943\nКурс: 2", font=("Segoe UI", 10)).pack(pady=4)

        sep = ttk.Separator(frm, orient="horizontal")
        sep.pack(fill="x", pady=12)

        ttk.Label(frm, text="Использованные библиотеки:",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w")
        libs = ["tkinter — графический интерфейс", "sqlite3 — реляционная БД",
                "random — генерация тестовых данных"]
        for lib in libs:
            ttk.Label(frm, text=f"  • {lib}", font=("Segoe UI", 9),
                      foreground=DarkTheme.FG_DIM).pack(anchor="w")

        ttk.Button(frm, text="Закрыть", command=win.destroy).pack(pady=16)


# ──────────────────────── Запуск ────────────────────────
def main():
    root = tk.Tk()
    FreddyApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
