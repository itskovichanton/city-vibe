# CityVibe — Flutter-клиент

Мобильное приложение CityVibe (поиск мест / события).  
Бэкенд живёт в этом же монорепо (`python/api_gateway` и сервисы).

Сейчас: **только вёрстка экрана логина** (+ enable кнопки «Войти» и глаз пароля).

---

## План (как будем делать клиент)

1. **Auth UI** — логин (готово), регистрация, OTP, forgot password по макетам.
2. **API-слой** — `dio` → только `api-gateway :8080`, модели `freezed` + `json_serializable`.
3. **Состояние** — `Riverpod` (+ codegen `riverpod_generator`).
4. **Навигация** — `go_router` (сейчас `/login`).
5. **Фичи** — places/search, milana, профиль — feature-first.

Стек: **Riverpod + freezed + go_router + dio + feature-first**  
(+ secure_storage, talker_dio_logger, cached_network_image, svg, connectivity).

Принцип: **сначала пиксель-пёрфект UI по макету → потом логика**.

---

## Структура

```
dart/flutter/lib/
  main.dart
  app.dart                      # ProviderScope + MaterialApp.router
  core/
    router/app_router.dart      # go_router
    network/dio_client.dart     # Dio + logger
  theme/
  features/
    auth/
      domain/                   # freezed-модели
      data/                     # (скоро) API/репозитории
      presentation/             # экраны + виджеты
```

Codegen после изменений моделей/провайдеров:

```bash
dart run build_runner build --delete-conflicting-outputs
```

---

## Запуск на Android-телефоне (когда подключил)

1. На телефоне: **Настройки → О телефоне → 7× «Номер сборки»** → **Режим разработчика**.
2. Включить **Отладка по USB** (и при необходимости «Установка через USB»).
3. Кабель → на телефоне **Разрешить отладку по USB**.
4. На Mac:

```bash
export PATH="$HOME/development/flutter/bin:$HOME/Library/Android/sdk/platform-tools:$PATH"
adb devices
# должно быть: <serial>   device

cd /Users/itskovich/IdeaProjects/city-vibe/dart/flutter
flutter devices
flutter run -d <serial_или_имя>
```

Если `unauthorized` — сними/воткни кабель и снова подтверди RSA-ключ на телефоне.  
Если устройства нет в списке — поставь драйверы OEM / на Samsung включи «Отладка по умолчанию».

**Сеть к бэкенду с телефона:** не `localhost`, а IP Mac в Wi‑Fi, например `http://192.168.1.10:8080`  
(телефон и Mac в одной сети; gateway слушает `0.0.0.0:8080`).

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
