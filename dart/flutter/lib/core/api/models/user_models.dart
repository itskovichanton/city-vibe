/// User DTO по OpenAPI `UserOut`.
library;

import 'package:city_vibe/core/api/models/auth_models.dart';
import 'package:city_vibe/core/network/media_url_resolver.dart';

/// Статус пользователя (`Status` на бэкенде).
enum UserStatus {
  active,
  banned;

  bool get isBanned => this == UserStatus.banned;

  bool get isActive => this == UserStatus.active;

  String get apiValue => switch (this) {
        UserStatus.active => 'ACTIVE',
        UserStatus.banned => 'BANNED',
      };

  static UserStatus fromApi(String? raw) {
    return switch (raw?.toUpperCase()) {
      'BANNED' => UserStatus.banned,
      _ => UserStatus.active,
    };
  }

  /// Gateway иногда отдаёт `status` как int (Python Enum auto): 1=ACTIVE, 2=BANNED.
  static UserStatus fromJson(dynamic raw) {
    if (raw is int) {
      return raw == 2 ? UserStatus.banned : UserStatus.active;
    }
    return fromApi(raw?.toString());
  }
}

class UserProfile {
  const UserProfile({
    required this.id,
    required this.name,
    this.status = UserStatus.active,
    this.gender = Gender.male,
    this.age,
    this.shortBio = '',
    this.longBio = '',
    this.role = 'REGULAR',
    this.favoriteCategories = const [],
    this.favoriteProductCategories = const [],
    this.onboardingCompleted = false,
    this.deleted = false,
    this.cityId,
    this.birthdate,
    this.avatarUrl,
    this.authAccountId,
  });

  final int id;
  final String name;
  final UserStatus status;
  final Gender gender;
  final int? age;
  final String shortBio;
  final String longBio;
  final String role;
  final List<String> favoriteCategories;
  final List<String> favoriteProductCategories;
  final bool onboardingCompleted;
  final bool deleted;
  final int? cityId;
  final String? birthdate;
  final String? avatarUrl;
  final int? authAccountId;

  UserProfile copyWith({
    int? id,
    String? name,
    UserStatus? status,
    Gender? gender,
    int? age,
    String? shortBio,
    String? longBio,
    String? role,
    List<String>? favoriteCategories,
    List<String>? favoriteProductCategories,
    bool? onboardingCompleted,
    bool? deleted,
    int? cityId,
    String? birthdate,
    String? avatarUrl,
    int? authAccountId,
    bool clearAge = false,
    bool clearCityId = false,
    bool clearBirthdate = false,
    bool clearAvatarUrl = false,
    bool clearAuthAccountId = false,
  }) {
    return UserProfile(
      id: id ?? this.id,
      name: name ?? this.name,
      status: status ?? this.status,
      gender: gender ?? this.gender,
      age: clearAge ? null : (age ?? this.age),
      shortBio: shortBio ?? this.shortBio,
      longBio: longBio ?? this.longBio,
      role: role ?? this.role,
      favoriteCategories: favoriteCategories ?? this.favoriteCategories,
      favoriteProductCategories:
          favoriteProductCategories ?? this.favoriteProductCategories,
      onboardingCompleted: onboardingCompleted ?? this.onboardingCompleted,
      deleted: deleted ?? this.deleted,
      cityId: clearCityId ? null : (cityId ?? this.cityId),
      birthdate: clearBirthdate ? null : (birthdate ?? this.birthdate),
      avatarUrl: clearAvatarUrl ? null : (avatarUrl ?? this.avatarUrl),
      authAccountId:
          clearAuthAccountId ? null : (authAccountId ?? this.authAccountId),
    );
  }

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      id: json['id'] as int,
      name: json['name'] as String,
      status: UserStatus.fromJson(json['status']),
      gender: Gender.fromApi(json['gender'] as String?),
      age: json['age'] as int?,
      shortBio: (json['short_bio'] as String?) ?? '',
      longBio: (json['long_bio'] as String?) ?? '',
      role: (json['role'] as String?) ?? 'REGULAR',
      favoriteCategories: _stringList(json['favorite_categories']),
      favoriteProductCategories: _stringList(json['favorite_product_categories']),
      onboardingCompleted: (json['onboarding_completed'] as bool?) ?? false,
      deleted: (json['deleted'] as bool?) ?? false,
      cityId: json['city_id'] as int?,
      birthdate: json['birthdate']?.toString(),
      avatarUrl: json['avatar_url'] as String?,
      authAccountId: json['auth_account_id'] as int?,
    );
  }

  /// URL для загрузки аватара через gateway (`GET /media/...`).
  String? get avatarDisplayUrl => MediaUrlResolver.resolve(avatarUrl);

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'status': status.apiValue,
        'gender': gender.apiValue,
        'age': age,
        'short_bio': shortBio,
        'long_bio': longBio,
        'role': role,
        'favorite_categories': favoriteCategories,
        'favorite_product_categories': favoriteProductCategories,
        'onboarding_completed': onboardingCompleted,
        'deleted': deleted,
        'city_id': cityId,
        'birthdate': birthdate,
        'avatar_url': avatarUrl,
        'auth_account_id': authAccountId,
      };
}

List<String> _stringList(dynamic raw) {
  if (raw is List) {
    return raw.map((e) => e.toString()).toList(growable: false);
  }
  return const [];
}
