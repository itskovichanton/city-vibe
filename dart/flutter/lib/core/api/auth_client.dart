import 'package:city_vibe/core/api/models/auth_models.dart';
import 'package:city_vibe/core/network/api_http.dart';

/// Auth-методы gateway (`/auth/*`). Без Dio — только через [ApiHttp].
class AuthClient {
  AuthClient(this._http);

  final ApiHttp _http;

  Future<Challenge> register(RegisterRequest body) {
    return _http.post(
      '/auth/register',
      body: body.toJson(),
      parse: (data) => Challenge.fromJson(Map<String, dynamic>.from(data as Map)),
    );
  }

  Future<AuthTokensDto> registerVerify(VerifyRequest body) {
    return _http.post(
      '/auth/register/verify',
      body: body.toJson(),
      parse: (data) =>
          AuthTokensDto.fromJson(Map<String, dynamic>.from(data as Map)),
    );
  }

  Future<Challenge> login(LoginRequest body) {
    return _http.post(
      '/auth/login',
      body: body.toJson(),
      parse: (data) => Challenge.fromJson(Map<String, dynamic>.from(data as Map)),
    );
  }

  Future<AuthTokensDto> loginVerify(VerifyRequest body) {
    return _http.post(
      '/auth/login/verify',
      body: body.toJson(),
      parse: (data) =>
          AuthTokensDto.fromJson(Map<String, dynamic>.from(data as Map)),
    );
  }

  Future<Challenge> resendOtp({required String challengeId}) {
    return _http.post(
      '/auth/otp/resend',
      body: {'challenge_id': challengeId},
      parse: (data) => Challenge.fromJson(Map<String, dynamic>.from(data as Map)),
    );
  }

  Future<Challenge> forgotPassword(ForgotPasswordRequest body) {
    return _http.post(
      '/auth/password/forgot',
      body: body.toJson(),
      parse: (data) => Challenge.fromJson(Map<String, dynamic>.from(data as Map)),
    );
  }

  Future<ResetTokenDto> forgotVerify(VerifyRequest body) {
    return _http.post(
      '/auth/password/forgot/verify',
      body: body.toJson(),
      parse: (data) =>
          ResetTokenDto.fromJson(Map<String, dynamic>.from(data as Map)),
    );
  }

  Future<void> resetPassword(ResetPasswordRequest body) {
    return _http.post(
      '/auth/password/reset',
      body: body.toJson(),
      parse: (_) {},
    );
  }

  Future<AuthTokensDto> refreshToken({required String refreshToken}) {
    return _http.post(
      '/auth/token/refresh',
      body: {'refresh_token': refreshToken},
      parse: (data) =>
          AuthTokensDto.fromJson(Map<String, dynamic>.from(data as Map)),
    );
  }

  Future<void> logout({required String refreshToken}) {
    return _http.post(
      '/auth/logout',
      body: {'refresh_token': refreshToken},
      parse: (_) {},
    );
  }

  Future<AuthTokensDto> socialGoogle({required String idToken}) {
    return _http.post(
      '/auth/social/google',
      body: {'id_token': idToken},
      parse: (data) =>
          AuthTokensDto.fromJson(Map<String, dynamic>.from(data as Map)),
    );
  }
}
