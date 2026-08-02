/// События приложения для шины [AppEventBus].
///
/// Добавляй новые типы сюда (sealed) — UI подписывается через `ref.listen`
/// / `StreamProvider` и реагирует без прямой связки эмиттера с экраном.
sealed class AppEvent {
  const AppEvent();
}

/// Глобальная ошибка, которую стоит показать пользователю (snackbar / dialog).
final class AppErrorEvent extends AppEvent {
  const AppErrorEvent({
    required this.message,
    this.code,
    this.fatal = false,
  });

  final String message;
  final String? code;
  final bool fatal;
}

/// Успешное/информационное сообщение для UI.
final class AppInfoEvent extends AppEvent {
  const AppInfoEvent(this.message);

  final String message;
}

/// Push / remote notification (заготовка под FCM).
final class AppPushEvent extends AppEvent {
  const AppPushEvent({
    required this.title,
    this.body,
    this.data = const {},
  });

  final String title;
  final String? body;
  final Map<String, dynamic> data;
}

/// Тик таймера / периодическое событие (например, refresh OTP countdown).
final class AppTimerEvent extends AppEvent {
  const AppTimerEvent({
    required this.name,
    this.payload,
  });

  final String name;
  final Object? payload;
}

/// Сессия завершена (401 / BANNED / refresh expired) — навигация на login.
final class AppSessionExpiredEvent extends AppEvent {
  const AppSessionExpiredEvent({this.reason});

  final String? reason;
}

/// Явный выход пользователя — навигация на login без сообщения об ошибке.
final class AppLoggedOutEvent extends AppEvent {
  const AppLoggedOutEvent();
}

/// Пользователь успешно залогинился / зарегистрировался.
final class AppAuthSucceededEvent extends AppEvent {
  const AppAuthSucceededEvent({
    required this.userId,
    this.isNewUser = false,
  });

  final int userId;
  final bool isNewUser;
}
