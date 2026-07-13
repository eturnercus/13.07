# CN8000A KVM Launcher — исходники

Портативный лаунчер для **ATEN CN8000A** с русским интерфейсом, встроенным Python/Java и иконкой приложения.

## Возможности

1. Окно на русском: **адрес KVM, логин, пароль**.
2. Контекстное меню (ПКМ) и горячие клавиши **Ctrl+C / Ctrl+V / Ctrl+X** в полях ввода.
3. Автоматический логин на CN8000 и скачивание JNLP.
4. Запуск встроенного `javaws` с русской локалью Java.

## Сборка

```bash
cd cn8000a-launcher
chmod +x scripts/*.sh
pip install pillow   # генерация icon.ico при сборке
./scripts/build-appimage.sh
./scripts/build-windows-portable.sh
```

Результаты: `dist/CN8000A-KVM-x86_64.AppImage` и `dist/CN8000A-KVM-Portable-Win64.zip`.

## Файлы

| Файл | Назначение |
|------|------------|
| `launcher.py` | GUI лаунчер |
| `widgets.py` | Поля ввода с ПКМ-меню |
| `cn8000_client.py` | Логин и JNLP |
| `resources/icon.png` | Иконка приложения |
| `resources/java.security.legacy` | Ослабленные TLS/шифры для JRE 8 |

## Ограничения

| Тема | Статус |
|------|--------|
| Python/Java в системе | Не нужны — всё внутри пакета |
| Буфер обмена в Java-вьюере ATEN | Зависит от оригинального клиента ATEN |
| Linux Wayland | Нужен XWayland / X11 |

## Лицензия

MIT — код лаунчера.
