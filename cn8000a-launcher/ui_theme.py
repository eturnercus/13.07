"""Шрифты и стили интерфейса с корректным fallback на Linux/Windows."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk


# Шрифты с нормальной поддержкой кириллицы — важен порядок.
FONT_CANDIDATES = (
    "Noto Sans",
    "DejaVu Sans",
    "Ubuntu",
    "Cantarell",
    "Liberation Sans",
    "Segoe UI",
    "Arial",
    "Helvetica",
    "Sans",
)


def pick_family(root: tk.Misc) -> str:
    available = {name.lower(): name for name in tkfont.families(root)}
    for candidate in FONT_CANDIDATES:
        hit = available.get(candidate.lower())
        if hit:
            return hit
    return tkfont.nametofont("TkDefaultFont").actual("family")


def apply_theme(root: tk.Tk) -> dict[str, tuple[str, int, str] | tuple[str, int]]:
    family = pick_family(root)
    fonts = {
        "base": (family, 10),
        "title": (family, 15, "bold"),
        "subtitle": (family, 10),
        "status": (family, 9),
        "note": (family, 9),
        "button": (family, 10, "bold"),
        "entry": (family, 11),
    }

    root.option_add("*Font", fonts["base"])
    root.configure(bg="#f4f6f8")

    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")

    style.configure(".", font=fonts["base"], background="#f4f6f8")
    style.configure("TFrame", background="#f4f6f8")
    style.configure("TLabel", background="#f4f6f8", foreground="#1f2933")
    style.configure("Title.TLabel", font=fonts["title"], foreground="#102a43")
    style.configure("Subtitle.TLabel", font=fonts["subtitle"], foreground="#627d98")
    style.configure("Status.TLabel", font=fonts["status"], foreground="#2f6f3e")
    style.configure("StatusError.TLabel", font=fonts["status"], foreground="#b42318")
    style.configure("Note.TLabel", font=fonts["note"], foreground="#627d98")
    # Без width= — иначе кириллица разъезжается по буквам в ttk.
    style.configure("Field.TLabel", font=fonts["base"], foreground="#334e68", anchor="e")
    style.configure("TEntry", font=fonts["entry"], padding=4)

    return fonts
