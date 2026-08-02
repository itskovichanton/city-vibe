import 'package:city_vibe/core/api/models/user_models.dart';
import 'package:city_vibe/core/network/api_exception.dart';

/// Принудительный выход: 401/403, BANNED и т.п.
///
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

  void handleAuthHttpError(ApiException error) {
    final code = error.statusCode;
    if (code == 401 || code == 403) {
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
