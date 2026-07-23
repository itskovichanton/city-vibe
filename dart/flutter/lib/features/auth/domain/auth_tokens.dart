/// Пример freezed-модели (заготовка под Auth / User).
///
/// После `dart run build_runner build` появятся:
/// - `auth_tokens.freezed.dart` — copyWith, ==, union helpers
/// - `auth_tokens.g.dart` — fromJson / toJson
///
/// Запуск codegen:
///   dart run build_runner build --delete-conflicting-outputs
library;

import 'package:freezed_annotation/freezed_annotation.dart';

part 'auth_tokens.freezed.dart';
part 'auth_tokens.g.dart';

@freezed
abstract class AuthTokens with _$AuthTokens {
  const factory AuthTokens({
    required String accessToken,
    required String refreshToken,
  }) = _AuthTokens;

  factory AuthTokens.fromJson(Map<String, dynamic> json) =>
      _$AuthTokensFromJson(json);
}
