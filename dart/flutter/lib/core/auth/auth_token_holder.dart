/// Синхронный доступ к access token для Dio interceptor.
///
/// Обновляется [AuthSessionNotifier] при save/clear/load.
class AuthTokenHolder {
  AuthTokenHolder._();

  static final AuthTokenHolder instance = AuthTokenHolder._();

  String? accessToken;
}
