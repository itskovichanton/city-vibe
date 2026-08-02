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

    final session = await ref.read(authSessionStoreProvider).read();
    _syncTokenHolder(session);
    if (session == null) return null;

    final userId = session.userId;
    if (userId != null) {
      // Cold start: всегда свежий профиль с сервера.
      await ref.read(currentUserProvider.notifier).load(
            userId,
            forceRefresh: true,
          );
      final stillLoggedIn = await ref.read(authSessionStoreProvider).read();
      if (stillLoggedIn == null) return null;
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
    if (userId != null) {
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
    AuthTokenHolder.instance.accessToken = session?.accessToken;
  }
}
