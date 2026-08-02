import 'package:city_vibe/app.dart';
import 'package:city_vibe/core/app/app_identity.dart';
import 'package:city_vibe/core/audio/ambient_music.dart';
import 'package:city_vibe/core/device/device_capability.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Точка входа Flutter-приложения.
///
/// `main()` всегда вызывается первой. Здесь принято:
/// 1) гарантировать инициализацию биндингов Flutter,
/// 2) настроить системный UI (status bar),
/// 3) вызвать runApp(...) с корневым виджетом.
Future<void> main() async {
  // Нужен, если до runApp есть async-инициализация / SystemChrome.
  WidgetsFlutterBinding.ensureInitialized();

  // Слабый телефон? Нужно до UI, чтобы фичи читали флаг синхронно.
  await DeviceCapability.init();

  // User-Agent для всех HTTP (версия из pubspec / native package info).
  await AppIdentity.init();

  // Светлые иконки status bar — под тёмный фон макета.
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
      statusBarBrightness: Brightness.dark,
    ),
  );

  // Только портрет — поворот экрана не меняет ориентацию UI.
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
  ]);

  // Фоновый lo-fi при запуске (не блокируем UI, если аудио не поднялось).
  AmbientMusic.start().ignore();

  runApp(const ProviderScope(child: CityVibeApp()));
}
