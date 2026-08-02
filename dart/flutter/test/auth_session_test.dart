import 'package:city_vibe/core/api/models/auth_models.dart';
import 'package:city_vibe/core/auth/auth_session.dart';
import 'package:flutter_test/flutter_test.dart';

class _MemoryAuthStore implements AuthSessionStore {
  AuthSession? session;

  @override
  Future<void> clear() async {
    session = null;
  }

  @override
  Future<AuthSession?> read() async => session;

  @override
  Future<void> write(AuthSession value) async {
    session = value;
  }
}

void main() {
  group('SecureAuthSessionStore contract', () {
    test('write/read round-trip preserves tokens and user_id', () async {
      final store = _MemoryAuthStore();
      const tokens = AuthTokensDto(
        accessToken: 'access-abc',
        refreshToken: 'refresh-xyz',
        expiresIn: 900,
        userId: 45,
        accountId: 51,
      );

      await store.write(AuthSession.fromTokens(tokens));
      final restored = await store.read();

      expect(restored, isNotNull);
      expect(restored!.accessToken, 'access-abc');
      expect(restored.refreshToken, 'refresh-xyz');
      expect(restored.userId, 45);
      expect(restored.accountId, 51);
      expect(restored.isAuthorized, isTrue);
    });

    test('read returns null without access token', () async {
      final store = _MemoryAuthStore();
      await store.write(
        const AuthSession(
          accessToken: '',
          refreshToken: 'refresh',
          expiresIn: 900,
        ),
      );

      final restored = await store.read();
      expect(restored, isNotNull);
      expect(restored!.isAuthorized, isFalse);
    });
  });
}
