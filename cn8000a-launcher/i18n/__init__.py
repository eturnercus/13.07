"""Загрузка строк интерфейса из UTF-8 JSON-файлов."""

from __future__ import annotations

import json
import os
from pathlib import Path


class I18n:
    def __init__(self, lang_dir: Path, lang: str | None = None) -> None:
        self.lang_dir = lang_dir
        self.lang = self._resolve_lang(lang)
        self._strings = self._load(self.lang)

    @staticmethod
    def _resolve_lang(explicit: str | None) -> str:
        if explicit:
            return explicit.split(".")[0].lower().replace("_", "-")
        for key in ("CN8000A_LANG", "LANG"):
            value = os.environ.get(key, "")
            if value:
                return value.split(".")[0].lower().replace("_", "-")
        return "ru"

    def _load(self, lang: str) -> dict[str, str]:
        path = self.lang_dir / f"{lang}.json"
        if not path.exists():
            path = self.lang_dir / "ru.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return {str(k): str(v) for k, v in data.items()}

    def t(self, key: str, **kwargs: str) -> str:
        template = self._strings.get(key, key)
        if kwargs:
            try:
                return template.format(**kwargs)
            except KeyError:
                return template
        return template

    @property
    def java_locale(self) -> tuple[str, str]:
        if self.lang.startswith("en"):
            return "en", "US"
        return "ru", "RU"
