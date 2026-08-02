import 'dart:async';

import 'package:city_vibe/core/auth/auth_providers.dart';
import 'package:city_vibe/core/events/app_event.dart';
import 'package:city_vibe/core/events/event_providers.dart';
import 'package:city_vibe/core/router/app_router.dart';
import 'package:city_vibe/theme/app_theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

/// Корневой виджет приложения.
///
/// [ProviderScope] создаётся в `main.dart`.
/// [MaterialApp.router] + [GoRouter] — декларативные маршруты.
/// Здесь же глобальная подписка на [appEventsProvider] (ошибки, пуши, …).
class CityVibeApp extends ConsumerWidget {
  const CityVibeApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);

    ref.listen<AsyncValue<AppEvent>>(appEventsProvider, (previous, next) {
      next.whenData((event) {
        if (event case AppSessionExpiredEvent(:final reason)) {
          unawaited(_forcedLogout(ref, router, reason));
          return;
        }
        _onAppEvent(ref, router, event);
      });
    });

    return MaterialApp.router(
      title: 'CityVibe',
      debugShowCheckedModeBanner: false,
      theme: buildAppTheme(),
      routerConfig: router,
      scaffoldMessengerKey: rootScaffoldMessengerKey,
    );
  }

  /// Центральная реакция UI на шину. Расширяй по мере появления сценариев.
  void _onAppEvent(WidgetRef ref, GoRouter router, AppEvent event) {
    final messenger = rootScaffoldMessengerKey.currentState;
    switch (event) {
      case AppErrorEvent(:final message):
        messenger?.showSnackBar(
          SnackBar(content: Text(message), backgroundColor: Colors.red.shade800),
        );
      case AppInfoEvent(:final message):
        messenger?.showSnackBar(SnackBar(content: Text(message)));
      case AppSessionExpiredEvent():
        break;
      case AppPushEvent():
      case AppTimerEvent():
      case AppAuthSucceededEvent():
        // Заготовки: обработчики добавятся по мере фич.
        break;
    }
  }

  /// 401/403 / BANNED: очистить сессию, сбросить стек навигации, объяснить причину.
  Future<void> _forcedLogout(
    WidgetRef ref,
    GoRouter router,
    String? reason,
  ) async {
    await ref.read(authSessionProvider.notifier).clear();
    router.go(AppRoutes.login);
    final text = reason?.trim();
    if (text != null && text.isNotEmpty) {
      rootScaffoldMessengerKey.currentState?.showSnackBar(
        SnackBar(
          content: Text(text),
          backgroundColor: Colors.red.shade800,
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }
}

/// Глобальный [ScaffoldMessenger] — snackbar из шины без BuildContext экрана.
final rootScaffoldMessengerKey = GlobalKey<ScaffoldMessengerState>();
