"""Шрифты и стили интерфейса с корректным fallback на Linux/Windows."""

from __future__ import annotations

import os
import sys
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import ttk


FONT_CANDIDATES = (
    "CN8000A UI",
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


def _bundle_dir() -> Path:
    if getattr(sys, "frozen", False) and getattr(sys, "_MEIPASS", None):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def _fonts_dir() -> Path:
    return _bundle_dir() / "resources" / "fonts"


def register_bundled_fonts(root: tk.Misc) -> str | None:
    """Зарегистрировать TTF из resources/fonts (важно для Linux AppImage)."""
    fonts_dir = _fonts_dir()
    if not fonts_dir.is_dir():
        return None

    registered = False
    for ttf in sorted(fonts_dir.glob("*.ttf")):
        font_id = f"cn8000a::{ttf.stem}"
        try:
            root.tk.call("font", "create", font_id, "-family", "CN8000A UI", "-file", str(ttf))
            registered = True
        except tk.TclError:
            continue

    return "CN8000A UI" if registered else None


def pick_family(root: tk.Misc) -> str:
    bundled = register_bundled_fonts(root)
    if bundled:
        return bundled

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
    if os.name != "nt":
        try:
            root.tk.call("tk", "scaling", 1.0)
        except tk.TclError:
            pass

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
    style.configure("Field.TLabel", font=fonts["base"], foreground="#334e68", anchor="e")
    style.configure("TEntry", font=fonts["entry"], padding=(6, 5))
    style.configure(
        "Accent.TButton",
        font=fonts["button"],
        background="#1e5f9a",
        foreground="white",
        borderwidth=0,
        focusthickness=0,
        padding=(18, 9),
    )
    style.map(
        "Accent.TButton",
        background=[("active", "#1d6fb8"), ("disabled", "#94a3b8")],
        foreground=[("disabled", "#e2e8f0")],
    )

    return fonts
