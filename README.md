# CN8000A KVM Launcher

Портативный лаунчер для **ATEN CN8000A** (и совместимых CN8000): подключение к KVM с современных Linux и Windows **без установки Java и Python**.

## Скачать

**Последний релиз:** [v1.2.1](https://github.com/eturnercus/13.07/releases/tag/v1.2.1)

| Платформа | Файл | Как запустить |
|-----------|------|---------------|
| **Linux x86_64** | [CN8000A-KVM-x86_64.AppImage](https://github.com/eturnercus/13.07/releases/download/v1.2.1/CN8000A-KVM-x86_64.AppImage) | `chmod +x CN8000A-KVM-x86_64.AppImage && ./CN8000A-KVM-x86_64.AppImage` |
| **Windows x64** | [CN8000A-KVM-Portable-Win64.zip](https://github.com/eturnercus/13.07/releases/download/v1.2.1/CN8000A-KVM-Portable-Win64.zip) | Распаковать → запустить `CN8000A-KVM.bat` |

> **Полностью портативно** — Python, Java 8 и IcedTea-Web уже внутри. Ничего ставить не нужно.

## Быстрый старт

1. Скачайте сборку для своей ОС из [релизов](https://github.com/eturnercus/13.07/releases/latest).
2. Запустите приложение.
3. Введите **IP/хост**, **логин** и **пароль** от KVM.
4. Нажмите **Подключиться** — откроется оригинальный Java-вьюер ATEN.

### Linux

```bash
chmod +x CN8000A-KVM-x86_64.AppImage
./CN8000A-KVM-x86_64.AppImage
```

На Wayland нужен **XWayland** (Java Swing).

### Windows

1. Распакуйте `CN8000A-KVM-Portable-Win64.zip`.
2. Запустите `CN8000A-KVM.bat`.

Python и Java в систему ставить не нужно — всё уже внутри архива.

## Что нового в v1.2.1

- Нормальные **пропорциональные шрифты** на Linux и Windows (без «печатной машинки»)
- Чище **вёрстка**: иконка, выровненные поля, одна кнопка, без лишнего текста внизу
- ПКМ и Ctrl+C/V в полях ввода по-прежнему работают

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
- Встроенный **Python 3.12**, **Temurin JRE 8** + **IcedTea-Web 1.8.8**.
- Ослабленные крипто-настройки — **только** внутри портативного runtime.

## Ограничения

| | |
|---|---|
| Нативный клиент без Java | Нет — видеопоток в проприетарном `javaclient.jar` ATEN |
| Буфер обмена в Java-вьюере | Управляется оригинальным клиентом ATEN; в лаунчере — ПКМ и Ctrl+C/V |
| Размер | ~70–80 МБ |
| Linux Wayland | Нужен XWayland / X11 |

## Сборка из исходников

Подробности — в [`cn8000a-launcher/README.md`](cn8000a-launcher/README.md).

```bash
cd cn8000a-launcher
pip install pillow   # для иконки .ico
./scripts/build-appimage.sh
./scripts/build-windows-portable.sh
```

## Лицензия

MIT — код лаунчера. JRE, IcedTea-Web и `javaclient.jar` с устройства — лицензии соответствующих правообладателей.
