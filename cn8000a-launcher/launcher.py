#!/usr/bin/env python3
"""Portable GUI launcher for ATEN CN8000A Java KVM viewer."""

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

APP_NAME = "CN8000A KVM Launcher"
APP_VERSION = "1.1.0"


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


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
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def find_javaws() -> Path | None:
    bundled = runtime_dir()
    candidates = [
        bundled / "bin" / "javaws",
        bundled / "bin" / "javaws.exe",
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
            "Bundled javaws not found. Build the portable package first "
            "(see README: scripts/download-runtime.sh)."
        )

    security_override = app_root() / "resources" / "java.security.legacy"
    env = os.environ.copy()
    java_home = javaws.parent.parent
    env["JAVA_HOME"] = str(java_home)
    env["PATH"] = f"{java_home / 'bin'}{os.pathsep}{env.get('PATH', '')}"

    cmd = [str(javaws), "-verbose"]
    if security_override.exists():
        cmd.append(f"-J-Djava.security.properties={security_override}")
    cmd.append(str(jnlp_file))

    subprocess.Popen(cmd, env=env, cwd=str(app_root()))


class LauncherApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} {APP_VERSION}")
        self.resizable(False, False)

        profiles = load_profiles()

        frame = ttk.Frame(self, padding=12)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="KVM host / IP:").grid(row=0, column=0, sticky="w", pady=4)
        self.host_var = tk.StringVar(value=profiles.get("last_host", ""))
        ttk.Entry(frame, textvariable=self.host_var, width=42).grid(row=0, column=1, pady=4)

        ttk.Label(frame, text="Username:").grid(row=1, column=0, sticky="w", pady=4)
        self.user_var = tk.StringVar(value=profiles.get("last_user", ""))
        ttk.Entry(frame, textvariable=self.user_var, width=42).grid(row=1, column=1, pady=4)

        ttk.Label(frame, text="Password:").grid(row=2, column=0, sticky="w", pady=4)
        self.pass_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.pass_var, show="*", width=42).grid(row=2, column=1, pady=4)

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(frame, textvariable=self.status_var, foreground="#444").grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(8, 4)
        )

        self.connect_btn = ttk.Button(frame, text="Connect", command=self.on_connect)
        self.connect_btn.grid(row=4, column=0, columnspan=2, pady=(4, 0), sticky="ew")

        note = (
            "Uses the original ATEN Java viewer (JNLP) inside a bundled Java 8 runtime.\n"
            "TLS 1.0 / legacy crypto are enabled only for talking to the KVM device."
        )
        ttk.Label(frame, text=note, wraplength=360, justify="left").grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(12, 0)
        )

    def set_busy(self, busy: bool, message: str) -> None:
        self.status_var.set(message)
        self.connect_btn.configure(state="disabled" if busy else "normal")

    def on_connect(self) -> None:
        host = self.host_var.get().strip()
        user = self.user_var.get().strip()
        password = self.pass_var.get()

        if not host or not user or not password:
            messagebox.showerror(APP_NAME, "Please fill in host, username, and password.")
            return

        self.set_busy(True, "Connecting to KVM...")
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
            self.after(0, lambda: self.set_busy(False, f"Viewer launched ({tmp.name})"))
        except (Cn8000Error, OSError, subprocess.SubprocessError) as exc:
            self.after(
                0,
                lambda: (
                    self.set_busy(False, "Connection failed"),
                    messagebox.showerror(APP_NAME, str(exc)),
                ),
            )


def main() -> int:
    app = LauncherApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
