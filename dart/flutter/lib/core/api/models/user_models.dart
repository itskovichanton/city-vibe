/// User DTO (минимально под OpenAPI).
library;

class UserProfile {
  const UserProfile({
    required this.id,
    required this.name,
    this.age,
    this.shortBio = '',
    this.longBio = '',
    this.cityId,
    this.avatarUrl,
    this.onboardingCompleted = false,
  });

  final int id;
  final String name;
  final int? age;
  final String shortBio;
  final String longBio;
  final int? cityId;
  final String? avatarUrl;
  final bool onboardingCompleted;

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      id: json['id'] as int,
      name: json['name'] as String,
      age: json['age'] as int?,
      shortBio: (json['short_bio'] as String?) ?? '',
      longBio: (json['long_bio'] as String?) ?? '',
      cityId: json['city_id'] as int?,
      avatarUrl: json['avatar_url'] as String?,
      onboardingCompleted: (json['onboarding_completed'] as bool?) ?? false,
    );
  }
}
