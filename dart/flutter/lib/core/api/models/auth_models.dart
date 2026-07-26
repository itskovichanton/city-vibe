/// Auth DTO по OpenAPI `city-vibe-mobile.json`.
library;

class RegisterRequest {
  const RegisterRequest({
    required this.name,
    required this.identifier,
    required this.password,
    required this.cityId,
    required this.acceptTerms,
    this.birthdate,
  });

  final String name;
  final String identifier;
  final String password;
  final int cityId;
  final bool acceptTerms;

  /// `YYYY-MM-DD` или null.
  final String? birthdate;

  Map<String, dynamic> toJson() => {
        'name': name,
        'identifier': identifier,
        'password': password,
        'city_id': cityId,
        'accept_terms': acceptTerms,
        if (birthdate != null) 'birthdate': birthdate,
      };
}

class LoginRequest {
  const LoginRequest({
    required this.identifier,
    required this.password,
  });

  final String identifier;
  final String password;

  Map<String, dynamic> toJson() => {
        'identifier': identifier,
        'password': password,
      };
}

class VerifyRequest {
  const VerifyRequest({
    required this.challengeId,
    required this.code,
  });

  final String challengeId;
  final String code;

  Map<String, dynamic> toJson() => {
        'challenge_id': challengeId,
        'code': code,
      };
}

class Challenge {
  const Challenge({
    required this.challengeId,
    required this.channel,
    required this.destinationMasked,
    this.expiresIn = 300,
  });

  final String challengeId;
  final String channel;
  final String destinationMasked;
  final int expiresIn;

  factory Challenge.fromJson(Map<String, dynamic> json) {
    return Challenge(
      challengeId: json['challenge_id'] as String,
      channel: json['channel'] as String,
      destinationMasked: json['destination_masked'] as String,
      expiresIn: (json['expires_in'] as int?) ?? 300,
    );
  }
}

class AuthTokensDto {
  const AuthTokensDto({
    required this.accessToken,
    required this.refreshToken,
    required this.expiresIn,
    this.tokenType = 'Bearer',
    this.userId,
    this.accountId,
  });

  final String accessToken;
  final String refreshToken;
  final String tokenType;
  final int expiresIn;
  final int? userId;
  final int? accountId;

  factory AuthTokensDto.fromJson(Map<String, dynamic> json) {
    return AuthTokensDto(
      accessToken: json['access_token'] as String,
      refreshToken: json['refresh_token'] as String,
      tokenType: (json['token_type'] as String?) ?? 'Bearer',
      expiresIn: json['expires_in'] as int,
      userId: json['user_id'] as int?,
      accountId: json['account_id'] as int?,
    );
  }
}
