import 'package:city_vibe/core/api/models/user_models.dart';
import 'package:city_vibe/core/auth/session_guard.dart';
import 'package:city_vibe/core/network/api_exception.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('SessionGuard.messageForAuthHttpError', () {
    test('401 default message', () {
      final msg = SessionGuard.messageForAuthHttpError(
        ApiException(message: '', statusCode: 401),
      );
      expect(msg, contains('Сессия истекла'));
    });

    test('403 default message', () {
      final msg = SessionGuard.messageForAuthHttpError(
        ApiException(message: '', statusCode: 403),
      );
      expect(msg, contains('Доступ запрещён'));
    });

    test('uses server message when present', () {
      final msg = SessionGuard.messageForAuthHttpError(
        ApiException(message: 'invalid_token', statusCode: 401),
      );
      expect(msg, 'invalid_token');
    });
  });

  group('SessionGuard.rejectIfBanned', () {
    test('throws and calls forceLogout for BANNED user', () {
      SessionGuard.instance.reset();
      String? reason;
      SessionGuard.instance.onForceLogout = (r) => reason = r;

      const banned = UserProfile(
        id: 1,
        name: 'X',
        status: UserStatus.banned,
      );

      expect(
        () => SessionGuard.instance.rejectIfBanned(banned),
        throwsA(isA<StateError>()),
      );
      expect(reason, contains('заблокирован'));

      SessionGuard.instance.onForceLogout = null;
      SessionGuard.instance.reset();
    });

    test('active user passes', () {
      SessionGuard.instance.reset();
      var called = false;
      SessionGuard.instance.onForceLogout = (_) => called = true;

      const active = UserProfile(id: 1, name: 'Ok');
      SessionGuard.instance.rejectIfBanned(active);
      expect(called, isFalse);

      SessionGuard.instance.onForceLogout = null;
    });
  });

  group('SessionGuard.handleUnauthorized', () {
    test('401 triggers forceLogout once', () {
      SessionGuard.instance.reset();
      final reasons = <String>[];
      SessionGuard.instance.onForceLogout = reasons.add;

      SessionGuard.instance.handleUnauthorized(
        ApiException(message: 'expired', statusCode: 401),
      );
      SessionGuard.instance.handleUnauthorized(
        ApiException(message: 'expired', statusCode: 401),
      );

      expect(reasons, hasLength(1));
      SessionGuard.instance.onForceLogout = null;
      SessionGuard.instance.reset();
    });
  });

  group('SessionGuard.handleAuthHttpError', () {
    test('401 triggers forceLogout once', () {
      SessionGuard.instance.reset();
      final reasons = <String>[];
      SessionGuard.instance.onForceLogout = reasons.add;

      SessionGuard.instance.handleAuthHttpError(
        ApiException(message: 'expired', statusCode: 401),
      );
      SessionGuard.instance.handleAuthHttpError(
        ApiException(message: 'expired', statusCode: 401),
      );

      expect(reasons, hasLength(1));
      SessionGuard.instance.onForceLogout = null;
      SessionGuard.instance.reset();
    });
  });
}
