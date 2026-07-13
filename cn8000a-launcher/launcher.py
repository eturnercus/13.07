#!/usr/bin/env python3
"""Портативный лаунчер KVM для ATEN CN8000A."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from cn8000_client import Cn8000Error, fetch_jnlp, validate_jnlp
from widgets import make_labeled_entry

APP_NAME = "CN8000A KVM"
APP_VERSION = "1.2.0"


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def resources_dir() -> Path:
    return app_root() / "resources"


def config_path() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "cn8000a-launcher" / "profiles.json"


def runtime_dir() -> Path:
    return app_root() / "runtime"


def load_profiles() -> dict:
    path = config_path()
    if not path.exists():
        return {"last_host": "", "last_user": ""}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"last_host": "", "last_user": ""}


def save_profiles(host: str, user: str) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = load_profiles()
    data["last_host"] = host
    data["last_user"] = user
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def find_javaws() -> Path | None:
    bundled = runtime_dir()
    candidates = [
        bundled / "bin" / "javaws",
        bundled / "bin" / "javaws.exe",
        bundled / "bin" / "javaws.cmd",
        bundled / "icedtea-web" / "bin" / "javaws",
        bundled / "icedtea-web" / "bin" / "javaws.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def launch_viewer(jnlp_file: Path) -> None:
    javaws = find_javaws()
    if javaws is None:
        raise FileNotFoundError(
            "Не найден javaws во встроенном runtime. Пересоберите портативный пакет."
        )

    security_override = resources_dir() / "java.security.legacy"
    env = os.environ.copy()
    java_home = javaws.parent.parent
    env["JAVA_HOME"] = str(java_home)
    env["PATH"] = f"{java_home / 'bin'}{os.pathsep}{env.get('PATH', '')}"
    env.setdefault("LANG", "ru_RU.UTF-8")
    env.setdefault("LC_ALL", "ru_RU.UTF-8")

    jvm_opts = [
        "-J-Duser.language=ru",
        "-J-Duser.country=RU",
        "-J-Dfile.encoding=UTF-8",
        "-J-Dawt.useSystemAAFontSettings=on",
        "-J-Djava.awt.datatransfer.SystemClipboardCompatible=true",
    ]
    if security_override.exists():
        jvm_opts.append(f"-J-Djava.security.properties={security_override}")

    cmd = [str(javaws), "-verbose", *jvm_opts, str(jnlp_file)]
    subprocess.Popen(cmd, env=env, cwd=str(app_root()))


def set_window_icon(window: tk.Tk | tk.Toplevel) -> None:
    for name in ("icon-256.png", "icon.png"):
        icon_png = resources_dir() / name
        if icon_png.exists():
            break
    else:
        return
    icon_ico = resources_dir() / "icon.ico"
    try:
        if icon_ico.exists() and os.name == "nt":
            window.iconbitmap(default=str(icon_ico))
        if icon_png.exists():
            image = tk.PhotoImage(file=str(icon_png))
            window.iconphoto(True, image)
            window._icon_image_ref = image  # prevent GC
    except tk.TclError:
        pass


class LauncherApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} — v{APP_VERSION}")
        self.resizable(False, False)
        set_window_icon(self)

        self._setup_style()
        profiles = load_profiles()

        outer = ttk.Frame(self, padding=16)
        outer.grid(row=0, column=0, sticky="nsew")

        header = ttk.Frame(outer)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        ttk.Label(header, text=APP_NAME, style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Портативное подключение к ATEN CN8000A",
            style="Subtitle.TLabel",
        ).pack(anchor="w")

        form = ttk.LabelFrame(outer, text="Параметры подключения", padding=12)
        form.grid(row=1, column=0, sticky="ew")
        form.columnconfigure(1, weight=1)

        self.host_var = tk.StringVar(value=profiles.get("last_host", ""))
        self.user_var = tk.StringVar(value=profiles.get("last_user", ""))
        self.pass_var = tk.StringVar()

        make_labeled_entry(form, "Адрес KVM (IP/хост):", row=0, textvariable=self.host_var)
        make_labeled_entry(form, "Имя пользователя:", row=1, textvariable=self.user_var)
        make_labeled_entry(
            form,
            "Пароль:",
            row=2,
            textvariable=self.pass_var,
            show="•",
        )

        self.status_var = tk.StringVar(value="Готово к подключению")
        ttk.Label(outer, textvariable=self.status_var, style="Status.TLabel").grid(
            row=2, column=0, sticky="w", pady=(10, 6)
        )

        buttons = ttk.Frame(outer)
        buttons.grid(row=3, column=0, sticky="ew")
        buttons.columnconfigure(0, weight=1)

        self.connect_btn = ttk.Button(buttons, text="Подключиться", command=self.on_connect)
        self.connect_btn.grid(row=0, column=0, sticky="ew")

        note = (
            "Используется оригинальный Java-вьюер ATEN (JNLP) со встроенным Java 8.\n"
            "Устаревшие TLS/шифрование включены только для связи с KVM.\n"
            "В полях ввода: ПКМ или Ctrl+C / Ctrl+V для копирования и вставки."
        )
        ttk.Label(outer, text=note, wraplength=380, justify="left", style="Note.TLabel").grid(
            row=4, column=0, sticky="w", pady=(12, 0)
        )

        self.bind("<Return>", lambda _e: self.on_connect())
        self.bind("<Escape>", lambda _e: self.destroy())

    def _setup_style(self) -> None:
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"))
        style.configure("Subtitle.TLabel", font=("Segoe UI", 10), foreground="#555")
        style.configure("Status.TLabel", font=("Segoe UI", 10), foreground="#2f6f3e")
        style.configure("Note.TLabel", font=("Segoe UI", 9), foreground="#666")

    def set_busy(self, busy: bool, message: str) -> None:
        self.status_var.set(message)
        self.connect_btn.configure(state="disabled" if busy else "normal")

    def on_connect(self) -> None:
        host = self.host_var.get().strip()
        user = self.user_var.get().strip()
        password = self.pass_var.get()

        if not host or not user or not password:
            messagebox.showerror(APP_NAME, "Заполните адрес KVM, имя пользователя и пароль.")
            return

        self.set_busy(True, "Подключение к KVM…")
        threading.Thread(
            target=self._connect_worker,
            args=(host, user, password),
            daemon=True,
        ).start()

    def _connect_worker(self, host: str, user: str, password: str) -> None:
        try:
            jnlp_bytes, _info = fetch_jnlp(host, user, password)
            validate_jnlp(jnlp_bytes)

            tmp = Path(tempfile.gettempdir()) / f"cn8000a-{host.replace(':', '_')}.jnlp"
            tmp.write_bytes(jnlp_bytes)

            save_profiles(host, user)
            launch_viewer(tmp)
            self.after(0, lambda: self.set_busy(False, "Вьюер запущен. Можно управлять KVM."))
        except (Cn8000Error, OSError, subprocess.SubprocessError) as exc:
            self.after(
                0,
                lambda: (
                    self.set_busy(False, "Ошибка подключения"),
                    messagebox.showerror(APP_NAME, str(exc)),
                ),
            )


def main() -> int:
    app = LauncherApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
