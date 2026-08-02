import 'package:city_vibe/core/api/models/user_models.dart';
import 'package:city_vibe/core/network/api_exception.dart';

/// Принудительный выход: refresh исчерпан, BANNED и т.п.
///
/// HTTP 401 обрабатывается в Dio [createDio] (refresh → retry → logout).
/// Callback регистрируется из [sessionGuardProvider] при старте приложения.
class SessionGuard {
  SessionGuard._();

  static final SessionGuard instance = SessionGuard._();

  void Function(String reason)? onForceLogout;

  bool _inProgress = false;

  /// Сброс после успешного входа (чтобы следующий kick снова сработал).
  void reset() {
    _inProgress = false;
  }

  void forceLogout(String reason) {
    if (_inProgress) return;
    _inProgress = true;
    onForceLogout?.call(reason);
  }

  /// Любой HTTP 401 — принудительный logout (базовое правило клиента).
  void handleUnauthorized([ApiException? error]) {
    forceLogout(
      messageForAuthHttpError(
        error ?? ApiException(message: '', statusCode: 401),
      ),
    );
  }

  void handleAuthHttpError(ApiException error) {
    if (error.statusCode == 401) {
      handleUnauthorized(error);
    } else if (error.statusCode == 403) {
      forceLogout(messageForAuthHttpError(error));
    }
  }

  void rejectIfBanned(UserProfile user) {
    if (user.status.isBanned) {
      forceLogout(
        'Ваш аккаунт заблокирован. Обратитесь в поддержку.',
      );
      throw StateError('user_banned');
    }
  }

  static String messageForAuthHttpError(ApiException error) {
    final msg = error.message.trim();
    if (msg.isNotEmpty && msg != 'Ошибка сервера') return msg;
    return switch (error.statusCode) {
      401 => 'Сессия истекла. Войдите снова.',
      403 => 'Доступ запрещён. Войдите снова.',
      _ => 'Требуется повторный вход.',
    };
  }
}
