import 'package:city_vibe/core/api/models/auth_models.dart';

/// Мост Dio ↔ Riverpod: обновление JWT без прямой зависимости от [Ref].
///
/// Callbacks регистрируются из [sessionGuardProvider] при старте приложения.
class AuthTokenCoordinator {
  AuthTokenCoordinator._();

  static final AuthTokenCoordinator instance = AuthTokenCoordinator._();

  /// `POST /auth/token/refresh` + secure storage.
  Future<bool> Function()? tryRefreshSession;

  /// Сохранить пару access/refresh из любого auth-ответа с [AuthTokensDto].
  Future<void> Function(
    AuthTokensDto tokens, {
    bool loadProfile,
    bool forceRefreshProfile,
  })? persistTokens;
}
