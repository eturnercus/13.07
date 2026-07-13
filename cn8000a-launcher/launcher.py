#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
from i18n import I18n
from ui_theme import apply_theme
from widgets import add_text_context_menu

APP_VERSION = "0.1"
LABEL_COLUMN_MINSIZE = 132


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def resources_dir() -> Path:
    return app_root() / "resources"


def i18n_dir() -> Path:
    return app_root() / "i18n" / "languages"


def config_path() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "cn8000a-launcher" / "profiles.json"


def runtime_dir() -> Path:
    return app_root() / "runtime"


def load_profiles() -> dict:
    path = config_path()
    if not path.exists():
        return {"last_host": "", "last_user": "", "language": ""}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"last_host": "", "last_user": "", "language": ""}


def save_profiles(host: str, user: str, language: str) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = load_profiles()
    data["last_host"] = host
    data["last_user"] = user
    data["language"] = language
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


def format_error(i18n: I18n, exc: BaseException) -> str:
    if isinstance(exc, Cn8000Error):
        return i18n.t(exc.code, **exc.params)
    return str(exc)


class LauncherApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        profiles = load_profiles()
        saved_lang = profiles.get("language") or None
        self.i18n = I18n(i18n_dir(), saved_lang)

        self.title(self.i18n.t("app.title"))
        self.resizable(False, False)
        set_window_icon(self)
        self._fonts = apply_theme(self)

        self.host_var = tk.StringVar(value=profiles.get("last_host", ""))
        self.user_var = tk.StringVar(value=profiles.get("last_user", ""))
        self.pass_var = tk.StringVar()
        self.status_var = tk.StringVar(value=self.i18n.t("status.ready"))
        self._status_style = "Status.TLabel"

        outer = ttk.Frame(self, padding=20)
        outer.grid(row=0, column=0, sticky="nsew")

        self._build_header(outer)
        self._build_form(outer)
        self._build_actions(outer)
        self._build_footer(outer)

        self.bind("<Return>", lambda _e: self.on_connect())
        self.bind("<Escape>", lambda _e: self.destroy())

    def _build_header(self, parent: ttk.Frame) -> None:
        header = ttk.Frame(parent)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))

        icon = load_icon_image(self)
        if icon is not None:
            icon_small = icon.subsample(4, 4) if icon.width() > 64 else icon
            ttk.Label(header, image=icon_small).grid(row=0, column=0, rowspan=2, padx=(0, 12))
            self._header_icon_ref = icon_small

        text = ttk.Frame(header)
        text.grid(row=0, column=1, sticky="w")
        ttk.Label(text, text=self.i18n.t("app.title"), style="Title.TLabel").pack(anchor="w")
        ttk.Label(text, text=self.i18n.t("app.subtitle"), style="Subtitle.TLabel").pack(
            anchor="w", pady=(2, 0)
        )

    def _build_form(self, parent: ttk.Frame) -> None:
        form = ttk.Frame(parent)
        form.grid(row=1, column=0, sticky="ew")
        form.columnconfigure(0, minsize=LABEL_COLUMN_MINSIZE)
        form.columnconfigure(1, weight=1)

        self._add_field(form, 0, self.i18n.t("field.host"), self.host_var)
        self._add_field(form, 1, self.i18n.t("field.user"), self.user_var)
        self._add_field(form, 2, self.i18n.t("field.password"), self.pass_var, show="*")

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
        entry = ttk.Entry(parent, textvariable=variable, width=32, show=show or "")
        entry.grid(row=row, column=1, sticky="ew", pady=7)
        add_text_context_menu(entry, self.i18n)
        return entry

    def _build_actions(self, parent: ttk.Frame) -> None:
        actions = tk.Frame(parent, bg="#f4f6f8")
        actions.grid(row=2, column=0, sticky="ew", pady=(16, 0))
        actions.columnconfigure(0, weight=1)

        self.connect_btn = tk.Button(
            actions,
            text=self.i18n.t("button.connect"),
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

    def _build_footer(self, parent: ttk.Frame) -> None:
        footer = ttk.Frame(parent)
        footer.grid(row=3, column=0, sticky="ew", pady=(14, 0))
        for idx, key in enumerate(("footer.line1", "footer.line2", "footer.line3"), start=0):
            ttk.Label(
                footer,
                text=self.i18n.t(key),
                style="Note.TLabel",
                wraplength=400,
                justify="left",
            ).grid(row=idx, column=0, sticky="w", pady=(0, 3))

    def set_busy(self, busy: bool, message_key: str, *, error: bool = False) -> None:
        self.status_var.set(self.i18n.t(message_key))
        self._status_style = "StatusError.TLabel" if error else "Status.TLabel"
        self.status_label.configure(style=self._status_style)
        self.connect_btn.configure(state=tk.DISABLED if busy else tk.NORMAL)

    def on_connect(self) -> None:
        host = self.host_var.get().strip()
        user = self.user_var.get().strip()
        password = self.pass_var.get()

        if not host or not user or not password:
            messagebox.showerror(self.i18n.t("app.title"), self.i18n.t("error.fill_fields"))
            return

        self.set_busy(True, "status.connecting")
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

            save_profiles(host, user, self.i18n.lang)
            launch_viewer(tmp, self.i18n)
            self.after(0, lambda: self.set_busy(False, "status.launched"))
        except Exception as exc:
            msg = format_error(self.i18n, exc) if isinstance(exc, Cn8000Error) else str(exc)
            self.after(
                0,
                lambda m=msg: (
                    self.set_busy(False, "status.error", error=True),
                    messagebox.showerror(self.i18n.t("app.title"), m),
                ),
            )


def launch_viewer(jnlp_file: Path, i18n: I18n) -> None:
    javaws = find_javaws()
    if javaws is None:
        raise FileNotFoundError(i18n.t("error.javaws_missing"))

    security_override = resources_dir() / "java.security.legacy"
    env = os.environ.copy()
    java_home = javaws.parent.parent
    env["JAVA_HOME"] = str(java_home)
    env["PATH"] = f"{java_home / 'bin'}{os.pathsep}{env.get('PATH', '')}"

    lang, country = i18n.java_locale
    env["LANG"] = f"{lang}_{country}.UTF-8"
    env["LC_ALL"] = f"{lang}_{country}.UTF-8"

    jvm_opts = [
        f"-J-Duser.language={lang}",
        f"-J-Duser.country={country}",
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


def main() -> int:
    app = LauncherApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
