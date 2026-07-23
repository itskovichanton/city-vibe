# CityVibe — Flutter-клиент

Мобильное приложение CityVibe (поиск мест / события).  
Бэкенд живёт в этом же монорепо (`python/api_gateway` и сервисы).

Сейчас: **только вёрстка экрана логина** (+ enable кнопки «Войти» и глаз пароля).

---

## План (как будем делать клиент)

1. **Auth UI** — логин (готово), регистрация, OTP, forgot password по макетам.
2. **API-слой** — `http`/`dio` → только `api-gateway :8080`, модели из OpenAPI `schema/openapi/city-vibe-mobile.json`.
3. **Состояние** — провайдер/репозитории (сессия JWT, профиль).
4. **Навигация** — после логина: home / карта / Милана (NL-поиск).
5. **Фичи** — places/search, milana, профиль — итерациями под дизайн.

Принцип: **сначала пиксель-пёрфект UI по макету → потом логика**.

---

## Структура

```
dart/flutter/
  lib/
    main.dart                 # точка входа
    app.dart                  # MaterialApp
    theme/                    # цвета и ThemeData
    features/auth/presentation/
      login_screen.dart       # экран логина
      widgets/                # поля, кнопка, фон, social
  assets/images/              # референс макета
  README.md                   # этот файл
```

Комментарии в коде — учебные: зачем StatefulWidget, controller, setState, dispose и т.д.

---

## Требования

- Flutter SDK **3.24+** (Dart 3.5+).  
  Если `flutter` не в PATH:

```bash
export PATH="$HOME/development/flutter/bin:$PATH"
# или куда вы установили SDK
flutter doctor
```

- Для Android: Android Studio + SDK, USB debugging на телефоне **или** эмулятор.
- Для быстрого превью UI без телефона: **Chrome** (`flutter run -d chrome`).

---

## Первый запуск (после клона)

Из корня приложения:

```bash
cd dart/flutter

# Если ещё нет папок android/ ios/ web/ — сгенерировать платформы:
flutter create . --project-name city_vibe --org com.cityvibe

flutter pub get
flutter run
```

`flutter create .` в существующем проекте **не затрёт** `lib/` и `pubspec.yaml`, только допишет платформенные папки.

---

## Запуск на Android-устройстве

1. На телефоне: **Настройки → О телефоне → 7 раз по «Номер сборки»** → включить **Режим разработчика**.
2. Включить **Отладка по USB**.
3. Подключить кабель, разрешить отладку на диалоге.
4. Проверить:

```bash
flutter devices
# должен появиться ваш телефон
flutter run -d <device_id>
```

Беспроводная отладка (Android 11+): в режиме разработчика «Беспроводная отладка» → pairing; либо `adb tcpip 5555` + `adb connect IP:5555`.

---

## Если телефона нет

| Вариант | Команда / действие | Когда удобно |
|---------|-------------------|--------------|
| **Эмулятор Android** | Android Studio → Device Manager → Create Virtual Device → Play | близко к реальному Android |
| **Chrome (web)** | `flutter run -d chrome` | быстро смотреть вёрстку |
| **iOS Simulator** (только macOS) | Xcode + `open -a Simulator` → `flutter run` | для iPhone UI |
| **Скрин/hot reload** | после `flutter run` жми `r` в терминале | править UI на лету |

Эмулятор без Android Studio (если SDK уже есть):

```bash
emulator -list-avds
emulator -avd <имя> &
flutter run
```

---

## Что уже сделано на логине

- Фон: ночная «карта» + неон-скайлайн (`CustomPaint`).
- Карточка: email, пароль, «Забыли пароль?», Google/Apple (заглушки).
- **«Войти» enabled** только если email и пароль не пустые (после `trim`).
- **Глаз** показывает/скрывает пароль.
- Нажатие «Войти» → SnackBar-заглушка (без API).

---

## Полезные команды

```bash
flutter analyze          # статический анализ
flutter test             # тесты (пока минимально)
flutter pub outdated     # устаревшие пакеты
```

---

## Связь с бэкендом (позже)

- Gateway: `http://<LAN-IP>:8080` (не `localhost` с телефона — это сам телефон).
- Auth: `POST /auth/login`, … — см. `python/api_gateway/docs/api/auth.md`.
- Для Android emulator → хост-машина: `http://10.0.2.2:8080`.
