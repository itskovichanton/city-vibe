import 'package:city_vibe/core/auth/auth_providers.dart';
import 'package:city_vibe/core/events/app_event.dart';
import 'package:city_vibe/core/events/event_providers.dart';
import 'package:city_vibe/core/milana/milana_providers.dart';
import 'package:city_vibe/features/onboarding/onboarding_providers.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Очищает сессию и пользовательские данные.
///
/// JWT — secure storage; профиль — SharedPreferences.
/// Справочники городов (SQLite) и категории (API-кэш в памяти) не трогаем.
typedef AppLogoutFn = Future<void> Function({
  bool notifyServer,
  bool emitLoggedOutEvent,
});

final appLogoutProvider = Provider<AppLogoutFn>((ref) {
  return ({
    bool notifyServer = true,
    bool emitLoggedOutEvent = true,
  }) async {
    await ref
        .read(authSessionProvider.notifier)
        .clear(notifyServer: notifyServer);
    await ref.read(milanaWelcomeCompletedProvider.notifier).reset();
    try {
      final repo = await ref.read(milanaRepositoryProvider.future);
      await repo.clear();
    } catch (_) {}
    ref.invalidate(milanaAccountProvider);
    ref.invalidate(milanaRepositoryProvider);
    if (emitLoggedOutEvent) {
      ref.read(appEventBusProvider).emit(const AppLoggedOutEvent());
    }
  };
});
