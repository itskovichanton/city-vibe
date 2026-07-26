import 'package:city_vibe/core/router/app_router.dart';
import 'package:city_vibe/theme/app_theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Корневой виджет приложения.
///
/// [ProviderScope] создаётся в `main.dart`.
/// [MaterialApp.router] + [GoRouter] — декларативные маршруты.
class CityVibeApp extends StatelessWidget {
  const CityVibeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'CityVibe',
      debugShowCheckedModeBanner: false,
      theme: buildAppTheme(),
      routerConfig: appRouter,
    );
  }
}
