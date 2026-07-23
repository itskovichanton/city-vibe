import 'package:city_vibe/app.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Точка входа Flutter-приложения.
///
/// `main()` всегда вызывается первой. Здесь принято:
/// 1) гарантировать инициализацию биндингов Flutter,
/// 2) настроить системный UI (status bar),
/// 3) вызвать runApp(...) с корневым виджетом.
Future<void> main() async {
  // Нужен, если до runApp есть async-инициализация / SystemChrome.
  WidgetsFlutterBinding.ensureInitialized();

  // Светлые иконки status bar — под тёмный фон макета.
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
      statusBarBrightness: Brightness.dark,
    ),
  );

  runApp(const CityVibeApp());
}
