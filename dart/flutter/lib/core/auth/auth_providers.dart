import 'dart:async';

import 'package:city_vibe/core/api/models/auth_models.dart';
import 'package:city_vibe/core/auth/auth_session.dart';
import 'package:city_vibe/core/auth/auth_token_holder.dart';
import 'package:city_vibe/core/auth/session_guard.dart';
import 'package:city_vibe/core/events/app_event.dart';
import 'package:city_vibe/core/events/event_providers.dart';
import 'package:city_vibe/core/user/user_providers.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final authSessionStoreProvider = Provider<AuthSessionStore>((ref) {
  return SecureAuthSessionStore();
});

/// JWT хранятся в [FlutterSecureStorage] (не SharedPreferences).
///
/// Связка access/refresh + user_id — только в secure storage.
final authSessionProvider =
    AsyncNotifierProvider<AuthSessionNotifier, AuthSession?>(
  AuthSessionNotifier.new,
);

/// Подключает [SessionGuard] к шине событий (toast + logout).
final sessionGuardProvider = Provider<void>((ref) {
  SessionGuard.instance.onForceLogout = (reason) {
    ref.read(appEventBusProvider).emit(AppSessionExpiredEvent(reason: reason));
  };
  ref.onDispose(() => SessionGuard.instance.onForceLogout = null);
});

class AuthSessionNotifier extends AsyncNotifier<AuthSession?> {
  @override
  Future<AuthSession?> build() async {
    ref.watch(sessionGuardProvider);

    AuthSession? session;
    try {
      session = await ref
          .read(authSessionStoreProvider)
          .read()
          .timeout(const Duration(seconds: 2), onTimeout: () => null);
    } catch (_) {
      session = null;
    }

    _syncTokenHolder(session);

    if (session == null || !session.isAuthorized) {
      if (session != null && !session.isAuthorized) {
        unawaited(ref.read(authSessionStoreProvider).clear());
        _syncTokenHolder(null);
      }
      return null;
    }

    final userId = session.userId;
    if (userId != null && session.hasAccessToken) {
      // Cold start: кэш сразу, сеть — в фоне (не блокируем auth/router).
      unawaited(
        ref.read(currentUserProvider.notifier).load(
              userId,
              forceRefresh: false,
            ),
      );
    }

    return session;
  }

  /// После login/register verify: сохранить токены и загрузить профиль.
  Future<void> establish(
    AuthTokensDto tokens, {
    bool refreshProfile = true,
  }) async {
    SessionGuard.instance.reset();

    final session = AuthSession.fromTokens(tokens);
    await ref.read(authSessionStoreProvider).write(session);
    _syncTokenHolder(session);
    state = AsyncData(session);

    final userId = session.userId;
    if (userId != null && session.hasAccessToken) {
      await ref.read(currentUserProvider.notifier).load(
            userId,
            forceRefresh: refreshProfile,
          );
      final stillLoggedIn = await ref.read(authSessionStoreProvider).read();
      if (stillLoggedIn == null) {
        state = const AsyncData(null);
      }
    }
  }

  Future<void> clear() async {
    await ref.read(authSessionStoreProvider).clear();
    _syncTokenHolder(null);
    state = const AsyncData(null);
    SessionGuard.instance.reset();
    await ref.read(currentUserProvider.notifier).clear();
  }

  void _syncTokenHolder(AuthSession? session) {
    final token = session?.accessToken;
    AuthTokenHolder.instance.accessToken =
        (token != null && token.isNotEmpty) ? token : null;
  }
}
