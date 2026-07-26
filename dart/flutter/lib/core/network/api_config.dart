import 'package:flutter/foundation.dart';

/// Конфиг доступа к **api-gateway** (единственная точка входа для mobile).
///
/// Телефон и Mac в одной Wi‑Fi → LAN IP Mac. Переопределение:
/// `flutter run --dart-define=API_BASE_URL=http://x.x.x.x:8080`
abstract final class ApiConfig {
  /// IP Mac в домашней сети (см. `ipconfig getifaddr en0`).
  static const lanHost = '192.168.1.12';
  static const port = 8080;

  static const _fromDefine = String.fromEnvironment('API_BASE_URL');

  /// Базовый URL gateway.
  static String get baseUrl {
    if (_fromDefine.isNotEmpty) return _fromDefine;

    if (kIsWeb) {
      return 'http://127.0.0.1:$port';
    }

    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
      case TargetPlatform.iOS:
        // Реальный телефон/планшет в той же Wi‑Fi, что и Mac.
        return 'http://$lanHost:$port';
      case TargetPlatform.macOS:
      case TargetPlatform.windows:
      case TargetPlatform.linux:
      case TargetPlatform.fuchsia:
        return 'http://127.0.0.1:$port';
    }
  }
}
