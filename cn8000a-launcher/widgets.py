"""Виджеты Tkinter с поддержкой контекстного меню и горячих клавиш."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def _select_all(widget: tk.Widget) -> None:
    widget.select_range(0, tk.END)  # type: ignore[attr-defined]
    widget.icursor(tk.END)  # type: ignore[attr-defined]


def _cut(widget: tk.Widget) -> None:
    try:
        widget.event_generate("<<Cut>>")
    except tk.TclError:
        pass


def _copy(widget: tk.Widget) -> None:
    try:
        widget.event_generate("<<Copy>>")
    except tk.TclError:
        pass


def _paste(widget: tk.Widget) -> None:
    try:
        widget.event_generate("<<Paste>>")
    except tk.TclError:
        try:
            text = widget.winfo_toplevel().clipboard_get()
            if text:
                try:
                    widget.delete("sel.first", "sel.last")  # type: ignore[attr-defined]
                except tk.TclError:
                    pass
                widget.insert(tk.INSERT, text)  # type: ignore[attr-defined]
        except tk.TclError:
            pass


def _bind_clipboard_shortcuts(widget: tk.Widget) -> None:
    widget.bind("<Control-a>", lambda e: (_select_all(widget), "break"))
    widget.bind("<Control-A>", lambda e: (_select_all(widget), "break"))
    widget.bind("<Control-c>", lambda e: (_copy(widget), "break"))
    widget.bind("<Control-C>", lambda e: (_copy(widget), "break"))
    widget.bind("<Control-v>", lambda e: (_paste(widget), "break"))
    widget.bind("<Control-V>", lambda e: (_paste(widget), "break"))
    widget.bind("<Control-x>", lambda e: (_cut(widget), "break"))
    widget.bind("<Control-X>", lambda e: (_cut(widget), "break"))
    widget.bind("<Shift-Insert>", lambda e: (_paste(widget), "break"))
    widget.bind("<Control-Insert>", lambda e: (_copy(widget), "break"))
    widget.bind("<Shift-Delete>", lambda e: (_cut(widget), "break"))


def add_text_context_menu(widget: tk.Widget) -> tk.Menu:
    """ПКМ-меню: Вырезать / Копировать / Вставить / Выделить всё."""
    menu = tk.Menu(widget, tearoff=0)
    menu.add_command(label="Вырезать", command=lambda: _cut(widget))
    menu.add_command(label="Копировать", command=lambda: _copy(widget))
    menu.add_command(label="Вставить", command=lambda: _paste(widget))
    menu.add_separator()
    menu.add_command(label="Выделить всё", command=lambda: _select_all(widget))

    def popup(event: tk.Event) -> str:
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
        return "break"

    widget.bind("<Button-3>", popup)
    widget.bind("<Control-Button-1>", popup)
    _bind_clipboard_shortcuts(widget)
    return menu


def make_labeled_entry(
    parent: ttk.Frame,
    label: str,
    *,
    row: int,
    textvariable: tk.StringVar,
    show: str | None = None,
    width: int = 34,
) -> ttk.Entry:
    ttk.Label(parent, text=label, style="Field.TLabel").grid(
        row=row, column=0, sticky="e", padx=(0, 12), pady=7
    )
    entry = ttk.Entry(parent, textvariable=textvariable, width=width, show=show or "")
    entry.grid(row=row, column=1, sticky="ew", pady=7)
    add_text_context_menu(entry)
    return entry
