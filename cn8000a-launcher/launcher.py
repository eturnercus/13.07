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
from ui_theme import apply_theme
from widgets import add_text_context_menu

APP_NAME = "CN8000A KVM"
APP_VERSION = "1.2.1"


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


def load_icon_image(root: tk.Misc) -> tk.PhotoImage | None:
    for name in ("icon-256.png", "icon.png"):
        path = resources_dir() / name
        if path.exists():
            try:
                return tk.PhotoImage(file=str(path))
            except tk.TclError:
                continue
    return None


def set_window_icon(window: tk.Tk | tk.Toplevel) -> None:
    icon_ico = resources_dir() / "icon.ico"
    icon = load_icon_image(window)
    try:
        if icon_ico.exists() and os.name == "nt":
            window.iconbitmap(default=str(icon_ico))
        if icon is not None:
            window.iconphoto(True, icon)
            window._icon_image_ref = icon
    except tk.TclError:
        pass


class LauncherApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.resizable(False, False)
        set_window_icon(self)
        self._fonts = apply_theme(self)

        profiles = load_profiles()
        self.host_var = tk.StringVar(value=profiles.get("last_host", ""))
        self.user_var = tk.StringVar(value=profiles.get("last_user", ""))
        self.pass_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Готово к подключению")
        self._status_style = "Status.TLabel"

        outer = ttk.Frame(self, padding=20)
        outer.grid(row=0, column=0, sticky="nsew")

        self._build_header(outer)
        self._build_form(outer)
        self._build_actions(outer)

        self.bind("<Return>", lambda _e: self.on_connect())
        self.bind("<Escape>", lambda _e: self.destroy())

    def _build_header(self, parent: ttk.Frame) -> None:
        header = ttk.Frame(parent)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))

        icon = load_icon_image(self)
        if icon is not None:
            icon_small = icon.subsample(4, 4) if icon.width() > 64 else icon
            ttk.Label(header, image=icon_small).grid(row=0, column=0, rowspan=2, padx=(0, 12))
            self._header_icon_ref = icon_small

        text = ttk.Frame(header)
        text.grid(row=0, column=1, sticky="w")
        ttk.Label(text, text=APP_NAME, style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            text,
            text="Портативное подключение к ATEN CN8000A",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(2, 0))

    def _build_form(self, parent: ttk.Frame) -> None:
        form = ttk.Frame(parent)
        form.grid(row=1, column=0, sticky="ew")
        form.columnconfigure(1, weight=1)

        self._add_field(form, 0, "Адрес KVM", self.host_var)
        self._add_field(form, 1, "Пользователь", self.user_var)
        self._add_field(form, 2, "Пароль", self.pass_var, show="•")

    def _add_field(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
        *,
        show: str | None = None,
    ) -> ttk.Entry:
        ttk.Label(parent, text=label, style="Field.TLabel").grid(
            row=row, column=0, sticky="e", padx=(0, 12), pady=7
        )
        entry = ttk.Entry(parent, textvariable=variable, width=34, show=show or "")
        entry.grid(row=row, column=1, sticky="ew", pady=7)
        add_text_context_menu(entry)
        return entry

    def _build_actions(self, parent: ttk.Frame) -> None:
        actions = tk.Frame(parent, bg="#f4f6f8")
        actions.grid(row=2, column=0, sticky="ew", pady=(18, 0))
        actions.columnconfigure(0, weight=1)

        self.connect_btn = tk.Button(
            actions,
            text="Подключиться",
            command=self.on_connect,
            font=self._fonts["button"],
            bg="#1e5f9a",
            fg="white",
            activebackground="#1d6fb8",
            activeforeground="white",
            disabledforeground="#d9e2ec",
            relief=tk.FLAT,
            cursor="hand2",
            padx=18,
            pady=8,
            borderwidth=0,
            highlightthickness=0,
        )
        self.connect_btn.grid(row=0, column=0, sticky="ew")

        self.status_label = ttk.Label(actions, textvariable=self.status_var, style=self._status_style)
        self.status_label.grid(row=1, column=0, sticky="w", pady=(10, 0))
        # ttk.Label on tk.Frame needs explicit background via style already set

    def set_busy(self, busy: bool, message: str, *, error: bool = False) -> None:
        self.status_var.set(message)
        self._status_style = "StatusError.TLabel" if error else "Status.TLabel"
        self.status_label.configure(style=self._status_style)
        self.connect_btn.configure(state=tk.DISABLED if busy else tk.NORMAL)

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
            self.after(0, lambda: self.set_busy(False, "Вьюер запущен"))
        except (Cn8000Error, OSError, subprocess.SubprocessError) as exc:
            self.after(
                0,
                lambda: (
                    self.set_busy(False, "Ошибка подключения", error=True),
                    messagebox.showerror(APP_NAME, str(exc)),
                ),
            )


def main() -> int:
    app = LauncherApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
