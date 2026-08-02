import 'package:city_vibe/core/api/models/user_models.dart';

/// Профиль Миланы с локально сохранённым аватаром.
class MilanaAccount {
  const MilanaAccount({
    required this.profile,
    this.avatarLocalPath,
  });

  final UserProfile profile;
  final String? avatarLocalPath;

  String get name => profile.name;

  String? get avatarStorageKey => profile.avatarUrl;

  String? get avatarDisplayUrl => profile.avatarDisplayUrl;
}
