"""Виджеты Tkinter с поддержкой контекстного меню и горячих клавиш."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from i18n import I18n


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
    """Вставка напрямую из буфера — без event_generate, чтобы не дублировать текст."""
    try:
        text = widget.winfo_toplevel().clipboard_get()
    except tk.TclError:
        return
    if not text:
        return
    try:
        widget.delete("sel.first", "sel.last")  # type: ignore[attr-defined]
    except tk.TclError:
        pass
    widget.insert(tk.INSERT, text)  # type: ignore[attr-defined]


def _bind_shortcut(widget: tk.Widget, sequence: str, action) -> None:
    def handler(_event: tk.Event) -> str:
        action()
        return "break"

    widget.bind(sequence, handler)


def _bind_clipboard_shortcuts(widget: tk.Widget) -> None:
    shortcuts = {
        "<Control-a>": lambda: _select_all(widget),
        "<Control-A>": lambda: _select_all(widget),
        "<Control-c>": lambda: _copy(widget),
        "<Control-C>": lambda: _copy(widget),
        "<Control-v>": lambda: _paste(widget),
        "<Control-V>": lambda: _paste(widget),
        "<Control-x>": lambda: _cut(widget),
        "<Control-X>": lambda: _cut(widget),
        "<Shift-Insert>": lambda: _paste(widget),
        "<Control-Insert>": lambda: _copy(widget),
        "<Shift-Delete>": lambda: _cut(widget),
    }
    for sequence, action in shortcuts.items():
        _bind_shortcut(widget, sequence, action)


def add_text_context_menu(widget: tk.Widget, i18n: I18n) -> tk.Menu:
    menu = tk.Menu(widget, tearoff=0)
    menu.add_command(label=i18n.t("menu.cut"), command=lambda: _cut(widget))
    menu.add_command(label=i18n.t("menu.copy"), command=lambda: _copy(widget))
    menu.add_command(label=i18n.t("menu.paste"), command=lambda: _paste(widget))
    menu.add_separator()
    menu.add_command(label=i18n.t("menu.select_all"), command=lambda: _select_all(widget))

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
