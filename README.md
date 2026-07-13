# CN8000A KVM Launcher

Портативный лаунчер для **ATEN CN8000A** (и совместимых CN8000): подключение к KVM с современных Linux и Windows **без установки Java**.

Старый Java-клиент ATEN не работает на новых ОС из‑за TLS 1.0, MD5/SHA1 и отсутствия Java Web Start. Этот проект упаковывает оригинальный ATEN viewer в портативное приложение со встроенным Java 8.

## Скачать

**Последний релиз:** [v1.0.0](https://github.com/eturnercus/13.07/releases/tag/v1.0.0)

| Платформа | Файл | Как запустить |
|-----------|------|---------------|
| **Linux x86_64** | [CN8000A-KVM-x86_64.AppImage](https://github.com/eturnercus/13.07/releases/download/v1.0.0/CN8000A-KVM-x86_64.AppImage) | `chmod +x CN8000A-KVM-x86_64.AppImage && ./CN8000A-KVM-x86_64.AppImage` |
| **Windows x64** | [CN8000A-KVM-Portable-Win64.zip](https://github.com/eturnercus/13.07/releases/download/v1.0.0/CN8000A-KVM-Portable-Win64.zip) | Распаковать → запустить `CN8000A-KVM.bat` |

> Установка не нужна: скачали, распаковали (или сделали AppImage исполняемым) — и запускаете.

## Быстрый старт

1. Скачайте сборку для своей ОС из [релизов](https://github.com/eturnercus/13.07/releases/latest).
2. Запустите приложение.
3. Введите **IP/хост**, **логин** и **пароль** от KVM.
4. Нажмите **Connect** — откроется оригинальный Java viewer ATEN.

### Linux

```bash
chmod +x CN8000A-KVM-x86_64.AppImage
./CN8000A-KVM-x86_64.AppImage
```

На Wayland нужен **XWayland** (Java Swing).

### Windows

1. Распакуйте `CN8000A-KVM-Portable-Win64.zip`.
2. Убедитесь, что установлен **Python 3** с модулем **tkinter** (идёт с [python.org](https://www.python.org/downloads/)).
3. Запустите `CN8000A-KVM.bat`.

Java в систему ставить не нужно — JRE 8 уже внутри пакета.

## Что внутри

```
Ваш ПК                         CN8000A
┌──────────────┐   TLS 1.0    ┌─────────────┐
│ GUI лаунчер  │ ───────────► │ Web-интерфейс│
│      │       │              └──────┬──────┘
│      ▼       │                     │
│ Скачать JNLP │ ◄───────────────────┘
│      │       │
│      ▼       │
│ Java 8 +     │
│ IcedTea-Web  │ ──► ATEN Java KVM Viewer
└──────────────┘
```

- Логин и скачивание JNLP — автоматически (старая и новая прошивка CN8000).
- Встроенный **Temurin JRE 8** + **IcedTea-Web 1.8.8**.
- Ослабленные крипто-настройки — **только** внутри портативного runtime, не в системе.

## Ограничения

| | |
|---|---|
| Нативный клиент без Java | Нет — видеопоток в проприетарном `javaclient.jar` ATEN |
| Размер | ~80–120 МБ |
| Linux Wayland | Нужен XWayland / X11 |
| Безопасность | TLS 1.0 включается только для связи с KVM |

## Сборка из исходников

Подробности — в [`cn8000a-launcher/README.md`](cn8000a-launcher/README.md).

```bash
cd cn8000a-launcher
./scripts/build-appimage.sh          # Linux AppImage
./scripts/build-windows-portable.sh  # Windows ZIP (можно собирать на Linux)
```

## Структура репозитория

```
.
├── README.md                 ← эта страница
└── cn8000a-launcher/         ← исходники и скрипты сборки
    ├── launcher.py           ← GUI
    ├── cn8000_client.py      ← логин / JNLP
    └── scripts/              ← сборка AppImage и Windows ZIP
```

## Лицензия

MIT — код лаунчера. JRE, IcedTea-Web и `javaclient.jar` с устройства — лицензии соответствующих правообладателей.
