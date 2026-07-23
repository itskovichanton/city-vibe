/// Глобальный роутер приложения (go_router).
///
/// Зачем отдельный файл:
/// - один источник правды для путей (`/login`, `/home`…);
/// - позже сюда добавим redirect: «нет JWT → /login»;
/// - deep links и web-URL совпадают с mobile-путями.
library;

import 'package:city_vibe/features/auth/presentation/login_screen.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// Имена маршрутов — лучше строки-константы, чем «магические» литералы в UI.
abstract final class AppRoutes {
  static const login = '/login';
  // Дальше: home, places, milana…
}

/// Создаём роутер один раз (не внутри build — иначе потеряется стек на rebuild).
final GoRouter appRouter = GoRouter(
  initialLocation: AppRoutes.login,
  routes: [
    GoRoute(
      path: AppRoutes.login,
      name: 'login',
      builder: (context, state) => const LoginScreen(),
    ),
  ],
  // Красивая заглушка, если путь не найден (особенно на web).
  errorBuilder: (context, state) => Scaffold(
    body: Center(child: Text('Страница не найдена: ${state.uri}')),
  ),
);
