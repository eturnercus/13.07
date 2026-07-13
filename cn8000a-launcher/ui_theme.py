"""Шрифты и стили интерфейса с корректным fallback на Linux/Windows."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk


FONT_CANDIDATES = (
    "Segoe UI",
    "Ubuntu",
    "Cantarell",
    "Noto Sans",
    "DejaVu Sans",
    "Liberation Sans",
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
    style.configure("Field.TLabel", font=fonts["base"], foreground="#334e68", width=16, anchor="e")
    style.configure("TEntry", font=fonts["entry"], padding=4)
    style.configure("Accent.TButton", font=fonts["button"], padding=(16, 8))
    style.map(
        "Accent.TButton",
        background=[("active", "#1d6fb8"), ("!disabled", "#1e5f9a")],
        foreground=[("!disabled", "white")],
    )

    return fonts
