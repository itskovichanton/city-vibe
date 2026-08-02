import 'dart:convert';

import 'package:city_vibe/core/api/models/auth_models.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

const _kAccessToken = 'cityvibe.auth.access_token';
const _kRefreshToken = 'cityvibe.auth.refresh_token';
const _kUserId = 'cityvibe.auth.user_id';
const _kAccountId = 'cityvibe.auth.account_id';
const _kExpiresIn = 'cityvibe.auth.expires_in';

/// Активная сессия (JWT + идентификаторы).
class AuthSession {
  const AuthSession({
    required this.accessToken,
    required this.refreshToken,
    required this.expiresIn,
    this.userId,
    this.accountId,
  });

  final String accessToken;
  final String refreshToken;
  final int expiresIn;
  final int? userId;
  final int? accountId;

  factory AuthSession.fromTokens(AuthTokensDto tokens) {
    return AuthSession(
      accessToken: tokens.accessToken,
      refreshToken: tokens.refreshToken,
      expiresIn: tokens.expiresIn,
      userId: tokens.userId,
      accountId: tokens.accountId,
    );
  }

  factory AuthSession.fromJson(Map<String, dynamic> json) {
    return AuthSession(
      accessToken: json['access_token'] as String,
      refreshToken: json['refresh_token'] as String,
      expiresIn: (json['expires_in'] as int?) ?? 900,
      userId: json['user_id'] as int?,
      accountId: json['account_id'] as int?,
    );
  }

  Map<String, dynamic> toJson() => {
        'access_token': accessToken,
        'refresh_token': refreshToken,
        'expires_in': expiresIn,
        'user_id': userId,
        'account_id': accountId,
      };
}

abstract class AuthSessionStore {
  Future<AuthSession?> read();

  Future<void> write(AuthSession session);

  Future<void> clear();
}

class SecureAuthSessionStore implements AuthSessionStore {
  SecureAuthSessionStore([FlutterSecureStorage? storage])
      : _storage = storage ??
            const FlutterSecureStorage(
              aOptions: AndroidOptions(encryptedSharedPreferences: true),
            );

  final FlutterSecureStorage _storage;

  @override
  Future<AuthSession?> read() async {
    final access = await _storage.read(key: _kAccessToken);
    final refresh = await _storage.read(key: _kRefreshToken);
    if (access == null || refresh == null) return null;

    final userIdRaw = await _storage.read(key: _kUserId);
    final accountIdRaw = await _storage.read(key: _kAccountId);
    final expiresRaw = await _storage.read(key: _kExpiresIn);

    return AuthSession(
      accessToken: access,
      refreshToken: refresh,
      expiresIn: int.tryParse(expiresRaw ?? '') ?? 900,
      userId: userIdRaw != null ? int.tryParse(userIdRaw) : null,
      accountId: accountIdRaw != null ? int.tryParse(accountIdRaw) : null,
    );
  }

  @override
  Future<void> write(AuthSession session) async {
    await _storage.write(key: _kAccessToken, value: session.accessToken);
    await _storage.write(key: _kRefreshToken, value: session.refreshToken);
    await _storage.write(
      key: _kExpiresIn,
      value: session.expiresIn.toString(),
    );
    if (session.userId != null) {
      await _storage.write(
        key: _kUserId,
        value: session.userId.toString(),
      );
    } else {
      await _storage.delete(key: _kUserId);
    }
    if (session.accountId != null) {
      await _storage.write(
        key: _kAccountId,
        value: session.accountId.toString(),
      );
    } else {
      await _storage.delete(key: _kAccountId);
    }
  }

  @override
  Future<void> clear() async {
    await _storage.delete(key: _kAccessToken);
    await _storage.delete(key: _kRefreshToken);
    await _storage.delete(key: _kUserId);
    await _storage.delete(key: _kAccountId);
    await _storage.delete(key: _kExpiresIn);
  }
}

/// JSON snapshot для отладки / миграций (не используется в prod path).
String encodeAuthSession(AuthSession session) => jsonEncode(session.toJson());
