/// Глобальный роутер приложения (go_router + Riverpod).
library;

import 'package:city_vibe/core/app/app_bootstrap_screen.dart';
import 'package:city_vibe/core/auth/auth_providers.dart';
import 'package:city_vibe/core/user/user_providers.dart';
import 'package:city_vibe/core/api/models/user_models.dart';
import 'package:city_vibe/features/auth/presentation/forgot_password_screen.dart';
import 'package:city_vibe/features/auth/presentation/login_screen.dart';
import 'package:city_vibe/features/auth/presentation/otp_verify_screen.dart';
import 'package:city_vibe/features/auth/presentation/register_screen.dart';
import 'package:city_vibe/features/home/presentation/home_screen.dart';
import 'package:city_vibe/features/onboarding/milana_welcome_pending.dart';
import 'package:city_vibe/features/onboarding/presentation/milana_greeting_screen.dart';
import 'package:city_vibe/features/onboarding/presentation/onboarding_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

/// Имена маршрутов — лучше строки-константы, чем «магические» литералы в UI.
abstract final class AppRoutes {
  static const bootstrap = '/';
  static const login = '/login';
  static const register = '/register';
  static const registerOtp = '/register/otp';
  static const forgotPassword = '/forgot-password';
  static const onboarding = '/onboarding';
  static const milanaGreeting = '/milana-greeting';
  static const home = '/home';
}

bool _isPublicAuthRoute(String location) {
  return location == AppRoutes.login ||
      location == AppRoutes.register ||
      location == AppRoutes.registerOtp ||
      location == AppRoutes.forgotPassword;
}

bool _isAuthorizedShellRoute(String location) {
  return location == AppRoutes.onboarding ||
      location == AppRoutes.milanaGreeting ||
      location == AppRoutes.home;
}

String _authorizedDestination({
  required UserProfile? user,
  required bool welcomePending,
}) {
  if (user != null && !user.onboardingCompleted) {
    return AppRoutes.onboarding;
  }
  if (welcomePending) {
    return AppRoutes.milanaGreeting;
  }
  return AppRoutes.home;
}

final appRouterProvider = Provider<GoRouter>((ref) {
  final refresh = ValueNotifier<int>(0);
  ref.listen(authSessionProvider, (_, __) => refresh.value++);
  ref.listen(currentUserProvider, (_, __) => refresh.value++);
  ref.listen(milanaWelcomeCompletedProvider, (_, __) => refresh.value++);
  ref.onDispose(refresh.dispose);

  return GoRouter(
    initialLocation: AppRoutes.bootstrap,
    refreshListenable: refresh,
    redirect: (context, state) {
      final auth = ref.read(authSessionProvider);
      final location = state.matchedLocation;
      final userAsync = ref.read(currentUserProvider);
      final user = userAsync.valueOrNull;
      final welcomePending = ref.read(milanaWelcomePendingProvider);

      // Cold start: secure storage + локальный профиль — splash, не login.
      if (auth.isLoading) {
        return location == AppRoutes.bootstrap ? null : AppRoutes.bootstrap;
      }

      final session = auth.valueOrNull;

      if (session == null) {
        if (location == AppRoutes.bootstrap) {
          return AppRoutes.login;
        }
        return _isPublicAuthRoute(location) ? null : AppRoutes.login;
      }

      if (user == null && userAsync.isLoading) {
        return location == AppRoutes.bootstrap ? null : AppRoutes.bootstrap;
      }

      final authorizedDest = _authorizedDestination(
        user: user,
        welcomePending: welcomePending,
      );

      if (location == AppRoutes.bootstrap ||
          _isPublicAuthRoute(location)) {
        return authorizedDest;
      }

      if (user != null && !user.onboardingCompleted) {
        if (location != AppRoutes.onboarding) return AppRoutes.onboarding;
        return null;
      }

      if (welcomePending) {
        if (location != AppRoutes.milanaGreeting) {
          return AppRoutes.milanaGreeting;
        }
        return null;
      }

      if (location == AppRoutes.onboarding ||
          location == AppRoutes.milanaGreeting) {
        return AppRoutes.home;
      }

      if (!_isAuthorizedShellRoute(location)) {
        return AppRoutes.home;
      }

      return null;
    },
    routes: [
      GoRoute(
        path: AppRoutes.bootstrap,
        name: 'bootstrap',
        builder: (context, state) => const AppBootstrapScreen(),
      ),
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
              body: Center(
                child: Text(
                  'Нет данных challenge — вернитесь к регистрации',
                ),
              ),
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
      GoRoute(
        path: AppRoutes.onboarding,
        name: 'onboarding',
        builder: (context, state) => const OnboardingScreen(),
      ),
      GoRoute(
        path: AppRoutes.milanaGreeting,
        name: 'milanaGreeting',
        builder: (context, state) => const MilanaGreetingScreen(),
      ),
      GoRoute(
        path: AppRoutes.home,
        name: 'home',
        builder: (context, state) => const HomeScreen(),
      ),
    ],
    errorBuilder: (context, state) => Scaffold(
      body: Center(child: Text('Страница не найдена: ${state.uri}')),
    ),
  );
});
