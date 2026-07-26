/// Глобальный роутер приложения (go_router).
///
/// Зачем отдельный файл:
/// - один источник правды для путей (`/login`, `/home`…);
/// - позже сюда добавим redirect: «нет JWT → /login»;
/// - deep links и web-URL совпадают с mobile-путями.
library;

import 'package:city_vibe/features/auth/presentation/forgot_password_screen.dart';
import 'package:city_vibe/features/auth/presentation/login_screen.dart';
import 'package:city_vibe/features/auth/presentation/otp_verify_screen.dart';
import 'package:city_vibe/features/auth/presentation/register_screen.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// Имена маршрутов — лучше строки-константы, чем «магические» литералы в UI.
abstract final class AppRoutes {
  static const login = '/login';
  static const register = '/register';
  static const registerOtp = '/register/otp';
  static const forgotPassword = '/forgot-password';
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
    GoRoute(
      path: AppRoutes.register,
      name: 'register',
      builder: (context, state) => const RegisterScreen(),
    ),
    GoRoute(
      path: AppRoutes.registerOtp,
      name: 'registerOtp',
      builder: (context, state) {
        final args = state.extra;
        if (args is! OtpVerifyArgs) {
          return const Scaffold(
            body: Center(child: Text('Нет данных challenge — вернитесь к регистрации')),
          );
        }
        return OtpVerifyScreen(args: args);
      },
    ),
    GoRoute(
      path: AppRoutes.forgotPassword,
      name: 'forgotPassword',
      builder: (context, state) => const ForgotPasswordScreen(),
    ),
  ],
  // Красивая заглушка, если путь не найден (особенно на web).
  errorBuilder: (context, state) => Scaffold(
    body: Center(child: Text('Страница не найдена: ${state.uri}')),
  ),
);
