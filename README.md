# CN8000A KVM Launcher

Портативный лаунчер для **ATEN CN8000A** (и совместимых CN8000): подключение к KVM с современных Linux и Windows **без установки Java и Python**.

## Скачать

**Релиз:** [v0.2](https://github.com/eturnercus/KVM-Launcher/releases/tag/v0.2)

| Платформа | Файл | Как запустить |
|-----------|------|---------------|
| **Linux x86_64** | [CN8000A-KVM-x86_64.AppImage](https://github.com/eturnercus/KVM-Launcher/releases/download/v0.2/CN8000A-KVM-x86_64.AppImage) | `chmod +x CN8000A-KVM-x86_64.AppImage && ./CN8000A-KVM-x86_64.AppImage` |
| **Windows x64** | [CN8000A-KVM-Portable-Win64.zip](https://github.com/eturnercus/KVM-Launcher/releases/download/v0.2/CN8000A-KVM-Portable-Win64.zip) | Распаковать → запустить `CN8000A-KVM.exe` |

> **Полностью портативно** — Python, Java 8 и IcedTea-Web уже внутри. Ничего ставить не нужно.

## Быстрый старт

1. Скачайте сборку для своей ОС из [релизов](https://github.com/eturnercus/KVM-Launcher/releases/latest).
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
2. Запустите **`CN8000A-KVM.exe`** (двойной клик).

## Возможности v0.2

- Русский интерфейс, файлы перевода в `i18n/languages/*.json` (UTF-8)
- Портативный Python 3.12 + Java 8 + IcedTea-Web
- Подключение к CN8000A через HTTP/1.0 (совместимость с прошивкой ATEN)
- Таймауты и понятные сообщения об ошибках (логин, пароль, сеть)
- Единый внешний вид на Linux и Windows (шрифты, кнопки)
- Windows: `CN8000A-KVM.exe` вместо `.bat`
- ПКМ и Ctrl+C/V в полях ввода
- Иконка приложения

## Сборка из исходников

Подробности — в [`cn8000a-launcher/README.md`](cn8000a-launcher/README.md).

```bash
cd cn8000a-launcher
./scripts/build-appimage.sh
./scripts/build-windows-portable.sh
```

## Лицензия

MIT — код лаунчера. JRE, IcedTea-Web и `javaclient.jar` с устройства — лицензии соответствующих правообладателей.
