import 'dart:async';

import 'package:city_vibe/core/audio/ambient_music.dart';
import 'package:city_vibe/core/auth/logout_providers.dart';
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
class CityVibeApp extends ConsumerStatefulWidget {
  const CityVibeApp({super.key});

  @override
  ConsumerState<CityVibeApp> createState() => _CityVibeAppState();
}

class _CityVibeAppState extends ConsumerState<CityVibeApp>
    with WidgetsBindingObserver {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      unawaited(AmbientMusic.ensurePlaying());
    }
  }

  @override
  Widget build(BuildContext context) {
    final router = ref.watch(appRouterProvider);

    ref.listen<AsyncValue<AppEvent>>(appEventsProvider, (previous, next) {
      next.whenData((event) {
        if (event case AppSessionExpiredEvent(:final reason)) {
          unawaited(_onSessionEnded(ref, router, reason: reason));
          return;
        }
        if (event case AppLoggedOutEvent()) {
          router.go(AppRoutes.login);
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
      case AppLoggedOutEvent():
        break;
      case AppPushEvent():
      case AppTimerEvent():
      case AppAuthSucceededEvent():
        // Заготовки: обработчики добавятся по мере фич.
        break;
    }
  }

  /// 401/403 / BANNED: очистить сессию, сбросить стек навигации, объяснить причину.
  Future<void> _onSessionEnded(
    WidgetRef ref,
    GoRouter router, {
    String? reason,
  }) async {
    await ref.read(appLogoutProvider)(
      notifyServer: true,
      emitLoggedOutEvent: false,
    );
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
