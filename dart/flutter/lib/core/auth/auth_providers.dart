import 'dart:async';

import 'package:city_vibe/core/api/api_providers.dart';
import 'package:city_vibe/core/api/models/auth_models.dart';
import 'package:city_vibe/core/auth/auth_session.dart';
import 'package:city_vibe/core/auth/auth_token_coordinator.dart';
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

/// Подключает [SessionGuard] и [AuthTokenCoordinator] к Riverpod.
final sessionGuardProvider = Provider<void>((ref) {
  SessionGuard.instance.onForceLogout = (reason) {
    ref.read(appEventBusProvider).emit(AppSessionExpiredEvent(reason: reason));
  };

  final coordinator = AuthTokenCoordinator.instance;
  coordinator.persistTokens =
      (AuthTokensDto tokens, {bool loadProfile = true, bool forceRefreshProfile = true}) {
    return ref.read(authSessionProvider.notifier).persistTokens(
          tokens,
          loadProfile: loadProfile,
          forceRefreshProfile: forceRefreshProfile,
        );
  };
  coordinator.tryRefreshSession = () {
    return ref.read(authSessionProvider.notifier).refreshPersistedTokens();
  };

  ref.onDispose(() {
    SessionGuard.instance.onForceLogout = null;
    coordinator.persistTokens = null;
    coordinator.tryRefreshSession = null;
  });
});

class AuthSessionNotifier extends AsyncNotifier<AuthSession?> {
  @override
  Future<AuthSession?> build() async {
    ref.watch(sessionGuardProvider);

    AuthSession? session;
    try {
      session = await ref.read(authSessionStoreProvider).read();
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
      await ref.read(currentUserProvider.notifier).load(
            userId,
            forceRefresh: false,
          );
    }

    return session;
  }

  /// Сохранить JWT из любого auth-ответа с [AuthTokensDto]:
  /// - `POST /auth/register/verify`
  /// - `POST /auth/login/verify`
  /// - `POST /auth/token/refresh`
  /// - `POST /auth/social/google`
  Future<void> persistTokens(
    AuthTokensDto tokens, {
    bool loadProfile = true,
    bool forceRefreshProfile = true,
    bool resetSessionGuard = true,
  }) async {
    if (resetSessionGuard) {
      SessionGuard.instance.reset();
    }

    final session = AuthSession.fromTokens(tokens);
    await ref.read(authSessionStoreProvider).write(session);
    _syncTokenHolder(session);
    state = AsyncData(session);

    final userId = session.userId;
    if (loadProfile && userId != null && session.hasAccessToken) {
      await ref.read(currentUserProvider.notifier).load(
            userId,
            forceRefresh: forceRefreshProfile,
          );
    }
  }

  /// После OTP verify / social login.
  Future<void> establish(
    AuthTokensDto tokens, {
    bool refreshProfile = true,
  }) {
    return persistTokens(
      tokens,
      forceRefreshProfile: refreshProfile,
    );
  }

  /// `POST /auth/token/refresh` — ротация refresh + запись в secure storage.
  Future<bool> refreshPersistedTokens() async {
    final session =
        state.valueOrNull ?? await ref.read(authSessionStoreProvider).read();
    if (session == null || !session.hasRefreshToken) {
      return false;
    }

    try {
      final tokens = await ref.read(authClientProvider).refreshToken(
            refreshToken: session.refreshToken,
          );
      await persistTokens(
        tokens,
        loadProfile: false,
        forceRefreshProfile: false,
        resetSessionGuard: false,
      );
      return true;
    } catch (_) {
      return false;
    }
  }

  /// Стереть JWT и профиль локально. Для UI используй [appLogoutProvider].
  Future<void> clear({bool notifyServer = true}) async {
    final session =
        state.valueOrNull ?? await ref.read(authSessionStoreProvider).read();
    final refresh = session?.refreshToken;
    if (notifyServer && refresh != null && refresh.isNotEmpty) {
      try {
        await ref.read(authClientProvider).logout(refreshToken: refresh);
      } catch (_) {
        // Локально всё равно чистим.
      }
    }

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
